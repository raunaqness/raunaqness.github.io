"""
Throwaway test: download one real photo from the shared Drive folder,
then resize/convert it into a full-size WebP and a thumbnail WebP,
to confirm the compression step works before wiring everything together.
"""
import io
import os

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image

load_dotenv()

KEY_FILE = os.environ["GOOGLE_SERVICE_ACCOUNT_KEY_FILE"]
ROOT_FOLDER_ID = os.environ["GOOGLE_DRIVE_ROOT_FOLDER_ID"]
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# locked defaults -- change these if quality/size tradeoff needs revisiting
MAX_DIM = 2400
QUALITY = 85

OUT_DIR = "scripts/_test_output"
os.makedirs(OUT_DIR, exist_ok=True)

creds = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
drive = build("drive", "v3", credentials=creds)

# find the Dhobi Ghat subfolder, then grab its first file
albums = drive.files().list(
    q=f"'{ROOT_FOLDER_ID}' in parents and trashed = false and mimeType = 'application/vnd.google-apps.folder'",
    fields="files(id, name)",
).execute()["files"]

album = albums[0]
print(f"Using album: {album['name']} (id={album['id']})")

files = drive.files().list(
    q=f"'{album['id']}' in parents and trashed = false",
    fields="files(id, name, mimeType)",
    orderBy="createdTime",
    pageSize=1,
).execute()["files"]

f = files[0]
print(f"Downloading: {f['name']} ({f['mimeType']})")

request = drive.files().get_media(fileId=f["id"])
buf = io.BytesIO()
downloader = MediaIoBaseDownload(buf, request)
done = False
while not done:
    status, done = downloader.next_chunk()

buf.seek(0)
original_size = len(buf.getvalue())
print(f"Downloaded {original_size / 1024 / 1024:.2f} MB")

img = Image.open(buf)
img = img.convert("RGB")  # drop alpha/EXIF orientation quirks for this test
print(f"Original dimensions: {img.size}")


out_path = f"{OUT_DIR}/output.webp"
resized = img.copy()
resized.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
resized.save(out_path, "WEBP", quality=QUALITY)
size = os.path.getsize(out_path)
print(f"{out_path}: {resized.size}, {size / 1024:.1f} KB")
print(f"Original: {original_size / 1024 / 1024:.2f} MB")
