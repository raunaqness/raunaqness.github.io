"""One-off: apply d1_schema.sql to the D1 database."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.environ["CLOUDFLARE_D1_ACCOUNT_ID"]
DATABASE_ID = os.environ["CLOUDFLARE_D1_DATABASE_ID"]
API_TOKEN = os.environ["CLOUDFLARE_D1_API_TOKEN"]

url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{DATABASE_ID}/query"

schema_path = os.path.join(os.path.dirname(__file__), "d1_schema.sql")
with open(schema_path) as f:
    sql = f.read()

# D1's query endpoint runs one statement at a time; split on semicolons
statements = [s.strip() for s in sql.split(";") if s.strip()]

for stmt in statements:
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
        },
        json={"sql": stmt},
    )
    result = resp.json()
    ok = result.get("success")
    print(f"{'OK' if ok else 'FAILED'}: {stmt[:60]}...")
    if not ok:
        print(f"  {result.get('errors')}")
