"""Throwaway test: verify D1 credentials by running a trivial query."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.environ["CLOUDFLARE_D1_ACCOUNT_ID"]
DATABASE_ID = os.environ["CLOUDFLARE_D1_DATABASE_ID"]
API_TOKEN = os.environ["CLOUDFLARE_D1_API_TOKEN"]

url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{DATABASE_ID}/query"

resp = requests.post(
    url,
    headers={
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    },
    json={"sql": "SELECT 1 AS ok;"},
)

print("HTTP", resp.status_code)
print(resp.json())
