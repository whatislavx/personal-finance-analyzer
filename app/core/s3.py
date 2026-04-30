import boto3
from botocore.client import Config
from app.core.config import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{settings.S3_ENDPOINT}",
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
)

