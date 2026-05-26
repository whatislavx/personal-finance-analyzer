from __future__ import annotations

import boto3
from botocore.client import Config

from app.core.config import settings


def _build_session_kwargs() -> dict[str, str]:
    kwargs: dict[str, str] = {}
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    if settings.AWS_SESSION_TOKEN:
        kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN
    return kwargs


def get_s3_client():
    session = boto3.session.Session(
        region_name=settings.S3_REGION,
        **_build_session_kwargs(),
    )
    return session.client("s3", config=Config(signature_version="s3v4"))


def build_result_s3_key(job_id: str) -> str:
    prefix = settings.S3_KEY_PREFIX.strip("/")
    if prefix:
        return f"{prefix}/{job_id}.json"
    return f"{job_id}.json"


s3_client = get_s3_client()
