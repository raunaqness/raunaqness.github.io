"""
Throwaway test: verify R2 credentials by listing bucket contents and
uploading/deleting a small test object via the S3-compatible API.
"""
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["R2_ENDPOINT"],
    aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    region_name="auto",
)

bucket = os.environ["R2_BUCKET_NAME"]

print(f"Listing objects in bucket '{bucket}':\n")
resp = s3.list_objects_v2(Bucket=bucket)
for obj in resp.get("Contents", []):
    print(f"  {obj['Key']}  ({obj['Size']} bytes)")

print("\nUploading test object...")
s3.put_object(Bucket=bucket, Key="_credential_test.txt", Body=b"r2 credentials ok")
print("Uploaded _credential_test.txt")

print("\nDeleting test object...")
s3.delete_object(Bucket=bucket, Key="_credential_test.txt")
print("Deleted. R2 read/write/delete all confirmed working.")
