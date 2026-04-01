import hashlib
from io import BytesIO

import boto3
from botocore.config import Config as BotoConfig

from app.core.config import settings

_client = None


def _get_s3_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=BotoConfig(signature_version="s3v4"),
        )
    return _client


def upload_artifact(data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    """Upload raw bytes to S3 and return the key."""
    client = _get_s3_client()
    client.upload_fileobj(
        BytesIO(data),
        settings.s3_bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return key


def download_artifact(key: str) -> bytes:
    """Download artifact bytes from S3."""
    client = _get_s3_client()
    buf = BytesIO()
    client.download_fileobj(settings.s3_bucket, key, buf)
    buf.seek(0)
    return buf.read()


def content_hash(data: bytes) -> str:
    """Return SHA-256 hex digest of data."""
    return hashlib.sha256(data).hexdigest()


def artifact_key(document_id: int, version_id: int, artifact_type: str, extension: str) -> str:
    """Build a deterministic S3 key for a raw artifact."""
    return f"documents/{document_id}/versions/{version_id}/{artifact_type}.{extension}"
