"""
Manually correct an album's date in D1, e.g. when Drive/EXIF dates are wrong.
Does NOT touch Drive or R2 -- just the stored date. Run sync_photos.py
afterward to republish manifest.json with the corrected date.

Usage:
    python scripts/update_album_date.py <slug> <YYYY-MM>

Example:
    python scripts/update_album_date.py ooty 2025-03
"""
import os
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.environ["CLOUDFLARE_D1_ACCOUNT_ID"]
DATABASE_ID = os.environ["CLOUDFLARE_D1_DATABASE_ID"]
API_TOKEN = os.environ["CLOUDFLARE_D1_API_TOKEN"]
URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{DATABASE_ID}/query"


def d1(sql, params=None):
    resp = requests.post(
        URL,
        headers={"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"},
        json={"sql": sql, "params": params or []},
    )
    result = resp.json()
    if not result.get("success"):
        raise RuntimeError(result.get("errors"))
    return result["result"][0]["results"]


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    slug, date_str = sys.argv[1], sys.argv[2]

    try:
        datetime.strptime(date_str, "%Y-%m")
    except ValueError:
        print(f"'{date_str}' isn't in YYYY-MM format (e.g. 2025-03)")
        sys.exit(1)

    rows = d1("SELECT slug, title, date FROM albums WHERE slug = ?", [slug])
    if not rows:
        existing = d1("SELECT slug FROM albums")
        print(f"No album with slug '{slug}'. Known slugs: {[r['slug'] for r in existing]}")
        sys.exit(1)

    before = rows[0]
    d1("UPDATE albums SET date = ? WHERE slug = ?", [date_str, slug])
    print(f"'{before['title']}' ({slug}): {before['date']} -> {date_str}")
    print("Run scripts/sync_photos.py to republish manifest.json with this change.")


if __name__ == "__main__":
    main()
