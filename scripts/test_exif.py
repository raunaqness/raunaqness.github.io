"""Throwaway: inspect what EXIF camera/lens info is actually present."""
import io
import os

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import ExifTags, Image

load_dotenv()

KEY_FILE = os.environ["GOOGLE_SERVICE_ACCOUNT_KEY_FILE"]
ROOT_FOLDER_ID = os.environ["GOOGLE_DRIVE_ROOT_FOLDER_ID"]
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

creds = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
drive = build("drive", "v3", credentials=creds)

albums = drive.files().list(
    q=f"'{ROOT_FOLDER_ID}' in parents and trashed = false and mimeType = 'application/vnd.google-apps.folder'",
    fields="files(id, name)",
).execute()["files"]

album = albums[0]
files = drive.files().list(
    q=f"'{album['id']}' in parents and trashed = false",
    fields="files(id, name)",
    orderBy="createdTime",
    pageSize=3,
).execute()["files"]

for f in files:
    print(f"\n=== {f['name']} ===")
    request = drive.files().get_media(fileId=f["id"])
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)

    img = Image.open(buf)
    exif = img.getexif()
    print("Top-level IFD0 tags:")
    for tag_id, value in exif.items():
        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
        if tag_name in ("Make", "Model", "Software", "LensModel"):
            print(f"  {tag_name}: {value}")

    try:
        exif_ifd = exif.get_ifd(0x8769)
        print("Exif SubIFD tags:")
        for tag_id, value in exif_ifd.items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)
            if tag_name in ("LensModel", "LensMake", "FocalLength", "FNumber"):
                print(f"  {tag_name}: {value}")
    except Exception as e:
        print(f"  (no Exif SubIFD: {e})")
