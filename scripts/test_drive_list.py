"""
Throwaway test: list the contents of the shared Google Drive root folder
using the service account credentials. No writes, no R2, just a read check.
"""
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

KEY_FILE = os.environ["GOOGLE_SERVICE_ACCOUNT_KEY_FILE"]
ROOT_FOLDER_ID = os.environ["GOOGLE_DRIVE_ROOT_FOLDER_ID"]

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

creds = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
drive = build("drive", "v3", credentials=creds)


def list_children(folder_id, indent=0):
    resp = drive.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields="files(id, name, mimeType, createdTime)",
        pageSize=100,
    ).execute()
    for f in resp.get("files", []):
        prefix = "  " * indent
        if f["mimeType"] == "application/vnd.google-apps.folder":
            print(f"{prefix}[folder] {f['name']}  (id={f['id']})")
            list_children(f["id"], indent + 1)
        else:
            print(f"{prefix}{f['name']}  ({f['mimeType']}, created {f['createdTime']})")


print(f"Listing contents of root folder {ROOT_FOLDER_ID}:\n")
list_children(ROOT_FOLDER_ID)
