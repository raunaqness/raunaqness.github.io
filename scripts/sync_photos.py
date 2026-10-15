"""
Full Drive -> R2 photo sync, backed by a D1 database for incremental state.

For every album (subfolder) under GOOGLE_DRIVE_ROOT_FOLDER_ID:
  - list photos
  - for each photo, check D1 for a matching (r2_key, drive_modified_time).
    If it matches, SKIP downloading/compressing/uploading -- nothing changed.
    Otherwise download, compress to WebP (locked settings below), upload to
    R2 at a STABLE key "<slug>/<drive_file_id>.webp" (not positional, so
    deleting/reordering photos elsewhere in the album never forces
    re-uploading photos that didn't actually change), and upsert the D1 row.
  - delete any D1/R2 photo rows whose Drive file no longer exists in the
    album (handles deletions)
  - title and date always come from the Drive folder name, re-applied on
    every sync (not just seeded once): the folder name itself is the
    source of truth, not EXIF or Drive's createdTime metadata, since those
    can get mangled by re-exports/edits after the fact. Tag the folder name
    with a trailing "(Month Year)" or "(YYYY-MM)", e.g. "Ooty (April 2023)"
    -- that's stripped for display and used as the date; correcting it is
    just renaming the folder and re-running this script. Without a tag,
    the date auto-detects from the earliest photo's Drive createdTime on
    the album's first sync only (use update_album_date.py to fix it later
    for an untagged album).
  - delete any whole albums from D1/R2 that no longer have a folder in Drive
  - rebuild manifest.json from D1 (not from the sync loop) and upload it

album.date is stored as plain "YYYY-MM" text, which also sorts correctly
as a plain string -- no datetime comparison, no timezone bugs.
"""
import io
import json
import os
import re
from datetime import datetime

import boto3
import requests
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()  # lets Image.open() handle iPhone .HEIC files

load_dotenv()

# ---- locked compression settings (see scripts/test_compress.py) ----
MAX_DIM = 2400
QUALITY = 85

# ---- config ----
GOOGLE_KEY_FILE = os.environ["GOOGLE_SERVICE_ACCOUNT_KEY_FILE"]
ROOT_FOLDER_ID = os.environ["GOOGLE_DRIVE_ROOT_FOLDER_ID"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

R2_ENDPOINT = os.environ["R2_ENDPOINT"]
R2_ACCESS_KEY_ID = os.environ["R2_ACCESS_KEY_ID"]
R2_SECRET_ACCESS_KEY = os.environ["R2_SECRET_ACCESS_KEY"]
R2_BUCKET = os.environ["R2_BUCKET_NAME"]
R2_PUBLIC_BASE_URL = os.environ["R2_PUBLIC_BASE_URL"]

CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ZONE_ID = os.environ.get("CLOUDFLARE_ZONE_ID")

D1_ACCOUNT_ID = os.environ["CLOUDFLARE_D1_ACCOUNT_ID"]
D1_DATABASE_ID = os.environ["CLOUDFLARE_D1_DATABASE_ID"]
D1_API_TOKEN = os.environ["CLOUDFLARE_D1_API_TOKEN"]
D1_URL = f"https://api.cloudflare.com/client/v4/accounts/{D1_ACCOUNT_ID}/d1/database/{D1_DATABASE_ID}/query"

# ---- clients ----
drive_creds = service_account.Credentials.from_service_account_file(
    GOOGLE_KEY_FILE, scopes=DRIVE_SCOPES
)
drive = build("drive", "v3", credentials=drive_creds)

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto",
)


def d1(sql: str, params: list | None = None) -> list[dict]:
    resp = requests.post(
        D1_URL,
        headers={
            "Authorization": f"Bearer {D1_API_TOKEN}",
            "Content-Type": "application/json",
        },
        json={"sql": sql, "params": params or []},
    )
    result = resp.json()
    if not result.get("success"):
        raise RuntimeError(f"D1 query failed: {result.get('errors')}\nSQL: {sql}")
    return result["result"][0]["results"]


def slugify(name: str) -> str:
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


# matches a trailing "(March 2025)" or "(2025-03)" tag on a folder name,
# used only to seed a new album's initial date
DATE_TAG_RE = re.compile(r"\s*\(([A-Za-z]+ \d{4}|\d{4}-\d{2})\)\s*$")


def parse_date_tag(folder_name: str):
    """Returns (clean_title, date_str or None), date_str as 'YYYY-MM'."""
    match = DATE_TAG_RE.search(folder_name)
    if not match:
        return folder_name, None

    raw = match.group(1)
    clean_title = folder_name[: match.start()].strip()

    for fmt_in, fmt_out in (("%B %Y", "%Y-%m"), ("%Y-%m", "%Y-%m")):
        try:
            return clean_title, datetime.strptime(raw, fmt_in).strftime(fmt_out)
        except ValueError:
            continue

    return folder_name, None


def list_children(folder_id, mime_type_filter=None, order_by=None):
    q = f"'{folder_id}' in parents and trashed = false"
    if mime_type_filter:
        q += f" and mimeType = '{mime_type_filter}'"
    kwargs = {
        "q": q,
        "fields": "files(id, name, mimeType, createdTime, modifiedTime)",
        "pageSize": 1000,
    }
    if order_by:
        kwargs["orderBy"] = order_by
    return drive.files().list(**kwargs).execute().get("files", [])


def download_file(file_id: str) -> bytes:
    request = drive.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return buf.read()


def compress_to_webp(raw_bytes: bytes) -> tuple[bytes, tuple[int, int]]:
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img)  # bake in EXIF orientation before we strip it
    img = img.convert("RGB")
    img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, "WEBP", quality=QUALITY)
    return out.getvalue(), img.size


def extract_camera_info(raw_bytes: bytes):
    """Returns (camera, lens) strings from EXIF, or (None, None) if unavailable."""
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        exif = img.getexif()

        make = exif.get(0x010F)  # Make
        model = exif.get(0x0110)  # Model
        camera = " ".join(p.strip() for p in (make, model) if p and p.strip()) or None

        lens = None
        try:
            exif_ifd = exif.get_ifd(0x8769)  # Exif SubIFD
            lens = exif_ifd.get(0xA434)  # LensModel
            if lens:
                lens = lens.strip().strip("\x00").strip() or None
        except Exception:
            pass

        return camera, lens
    except Exception:
        return None, None


def upload_bytes(key: str, data: bytes, content_type: str):
    s3.put_object(Bucket=R2_BUCKET, Key=key, Body=data, ContentType=content_type)


def purge_cache(urls: list[str]):
    if not CLOUDFLARE_API_TOKEN or not CLOUDFLARE_ZONE_ID:
        print("\n(skipping cache purge -- CLOUDFLARE_API_TOKEN/CLOUDFLARE_ZONE_ID not set)")
        return
    if not urls:
        return

    print(f"\nPurging {len(urls)} URL(s) from Cloudflare cache...")
    for i in range(0, len(urls), 30):
        batch = urls[i : i + 30]
        resp = requests.post(
            f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/purge_cache",
            headers={
                "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"files": batch},
        )
        result = resp.json()
        if not result.get("success"):
            print(f"  purge batch {i // 30 + 1} FAILED: {result.get('errors')}")
        else:
            print(f"  purge batch {i // 30 + 1}: ok ({len(batch)} url(s))")


def resolve_slugs(folders):
    """Returns [(folder, clean_title, tag_date, slug), ...]. Two folders can
    produce the same base slug (e.g. two trips both named "Hanoi, Vietnam"
    tagged with different years) -- when that happens, disambiguate by
    appending the tag's year (or the Drive folder id, if untagged) so
    every album still gets a distinct, stable slug instead of silently
    colliding and overwriting each other in D1."""
    parsed = []
    for folder in folders:
        clean_title, tag_date = parse_date_tag(folder["name"])
        base_slug = slugify(clean_title)
        parsed.append([folder, clean_title, tag_date, base_slug])

    from collections import Counter
    base_counts = Counter(p[3] for p in parsed)

    for p in parsed:
        folder, clean_title, tag_date, base_slug = p
        if base_counts[base_slug] > 1:
            suffix = tag_date[:4] if tag_date else folder["id"][:6]
            p[3] = f"{base_slug}-{suffix}"
            print(f"  slug collision on '{base_slug}' -> disambiguated to '{p[3]}' ({folder['name']})")

    return [tuple(p) for p in parsed]


def sync_album(folder, clean_title, tag_date, slug, purge_urls: list[str]):
    print(f"\n=== Album: {folder['name']} -> slug '{slug}' ===")

    files = list_children(folder["id"], order_by="createdTime")
    files = [f for f in files if f["mimeType"].startswith("image/")]

    # existing D1 rows for this album, keyed by r2_key
    existing = {
        row["r2_key"]: row
        for row in d1("SELECT * FROM photos WHERE album_slug = ?", [slug])
    }

    # camera/lens is an album-level attribute (one device per album), so
    # default to whatever's already stored for this album and only
    # re-extract it if the first photo actually gets (re)processed
    existing_album = d1("SELECT * FROM albums WHERE slug = ?", [slug])
    camera = existing_album[0]["camera"] if existing_album else None
    lens = existing_album[0]["lens"] if existing_album else None

    # seed a minimal album row first if this is a brand new album -- photos
    # below have a foreign key on album_slug, so the row must exist before
    # we can insert any of them
    if not existing_album:
        d1(
            "INSERT INTO albums (slug, title, date, camera, lens, cover_key) VALUES (?, ?, NULL, NULL, NULL, NULL)",
            [slug, clean_title],
        )

    current_keys = set()
    for i, f in enumerate(files, start=1):
        key = f"{slug}/{f['id']}.webp"
        current_keys.add(key)
        row = existing.get(key)

        if row and row["drive_modified_time"] == f["modifiedTime"]:
            print(f"  [{i}/{len(files)}] {f['name']} -> unchanged, skipping")
            continue

        print(f"  [{i}/{len(files)}] {f['name']} -> {key}")
        raw = download_file(f["id"])

        if i == 1:
            camera, lens = extract_camera_info(raw)
            if camera:
                print(f"      camera: {camera}" + (f" / lens: {lens}" if lens else ""))

        webp_bytes, (w, h) = compress_to_webp(raw)
        upload_bytes(key, webp_bytes, "image/webp")
        purge_urls.append(f"{R2_PUBLIC_BASE_URL}/{key}")
        print(f"      {len(raw) / 1024:.0f} KB -> {len(webp_bytes) / 1024:.0f} KB ({w}x{h})")

        d1(
            """
            INSERT INTO photos (r2_key, album_slug, drive_file_id, drive_modified_time, width, height, sort_key)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(r2_key) DO UPDATE SET
              drive_modified_time = excluded.drive_modified_time,
              width = excluded.width,
              height = excluded.height,
              sort_key = excluded.sort_key
            """,
            [key, slug, f["id"], f["modifiedTime"], w, h, f["createdTime"]],
        )

    # remove photos that no longer exist in Drive
    stale_keys = set(existing.keys()) - current_keys
    for key in stale_keys:
        s3.delete_object(Bucket=R2_BUCKET, Key=key)
        d1("DELETE FROM photos WHERE r2_key = ?", [key])
        purge_urls.append(f"{R2_PUBLIC_BASE_URL}/{key}")
        print(f"  removed stale photo: {key}")

    # pick cover: first portrait photo by sort order, else first photo
    photo_rows = d1(
        "SELECT * FROM photos WHERE album_slug = ? ORDER BY sort_key ASC", [slug]
    )
    cover_key = None
    for row in photo_rows:
        if row["height"] and row["width"] and row["height"] > row["width"]:
            cover_key = row["r2_key"]
            break
    if not cover_key and photo_rows:
        cover_key = photo_rows[0]["r2_key"]

    # the folder name is the source of truth for both title and date: a
    # "(Month Year)" / "(YYYY-MM)" tag always wins and is re-applied on
    # every sync (so correcting it is just renaming the Drive folder).
    # Without a tag, fall back to Drive's earliest-photo date, but only on
    # an album's first sync -- don't clobber any value set on a later run.
    if tag_date:
        date_value = tag_date
        print(f"      date from folder name -> {date_value}")
    elif not existing_album:
        if files:
            earliest = min(f["createdTime"] for f in files)
            date_value = earliest[:7]  # "YYYY-MM-DD..." -> "YYYY-MM"
        else:
            date_value = None
        print(f"      no date tag, auto-detected -> {date_value}")
    else:
        date_value = existing_album[0]["date"]

    d1(
        "UPDATE albums SET title = ?, date = ?, camera = ?, lens = ?, cover_key = ? WHERE slug = ?",
        [clean_title, date_value, camera, lens, cover_key, slug],
    )

    return slug


def main():
    albums_folders = list_children(
        ROOT_FOLDER_ID, mime_type_filter="application/vnd.google-apps.folder"
    )
    print(f"Found {len(albums_folders)} album folder(s) in Drive.")

    resolved = resolve_slugs(albums_folders)

    purge_urls = []
    current_slugs = set()
    for folder, clean_title, tag_date, slug in resolved:
        sync_album(folder, clean_title, tag_date, slug, purge_urls)
        current_slugs.add(slug)

    # remove whole albums that no longer have a Drive folder
    all_album_rows = d1("SELECT slug FROM albums")
    for row in all_album_rows:
        if row["slug"] not in current_slugs:
            slug = row["slug"]
            print(f"\nAlbum '{slug}' no longer in Drive -- removing")
            photo_rows = d1("SELECT r2_key FROM photos WHERE album_slug = ?", [slug])
            for p in photo_rows:
                s3.delete_object(Bucket=R2_BUCKET, Key=p["r2_key"])
                purge_urls.append(f"{R2_PUBLIC_BASE_URL}/{p['r2_key']}")
            d1("DELETE FROM photos WHERE album_slug = ?", [slug])
            d1("DELETE FROM albums WHERE slug = ?", [slug])

    # rebuild manifest.json from D1, newest album first (plain string sort
    # works correctly for "YYYY-MM")
    albums = d1("SELECT * FROM albums ORDER BY date DESC")
    manifest = []
    for album in albums:
        photo_rows = d1(
            "SELECT r2_key FROM photos WHERE album_slug = ? ORDER BY sort_key ASC",
            [album["slug"]],
        )
        photos = [row["r2_key"].split("/", 1)[1] for row in photo_rows]
        cover = album["cover_key"].split("/", 1)[1] if album["cover_key"] else None

        date_label = None
        if album["date"]:
            date_label = datetime.strptime(album["date"], "%Y-%m").strftime("%B %Y")

        manifest.append({
            "slug": album["slug"],
            "title": album["title"],
            "date": date_label,
            "camera": album["camera"],
            "lens": album["lens"],
            "cover": cover,
            "count": len(photos),
            "photos": photos,
        })

    manifest_json = json.dumps(manifest, indent=2)
    upload_bytes("manifest.json", manifest_json.encode("utf-8"), "application/json")
    purge_urls.append(f"{R2_PUBLIC_BASE_URL}/manifest.json")
    print("\nUploaded manifest.json:")
    print(manifest_json)

    purge_cache(purge_urls)


if __name__ == "__main__":
    main()
