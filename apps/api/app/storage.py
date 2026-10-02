"""Object storage abstraction. Keys are generated server-side (uuid based), never from
client file names, so path traversal is impossible by construction; LocalStorage additionally
verifies that resolved paths stay inside its root."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.config import get_settings

_KEY = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9/_\-.]{0,500}$")


def _check_key(key: str) -> str:
    if not _KEY.match(key) or ".." in key or key.startswith("/"):
        raise ValueError("invalid storage key")
    return key


class StorageBackend(Protocol):
    name: str

    def put(self, key: str, data: bytes, content_type: str) -> None: ...

    def get(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...

    def healthy(self) -> bool: ...


class LocalStorage:
    name = "local"

    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = (self.root / _check_key(key)).resolve()
        if self.root not in p.parents:
            raise ValueError("invalid storage key")
        return p

    def put(self, key: str, data: bytes, content_type: str) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(p)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        try:
            self._path(key).unlink()
        except FileNotFoundError:
            pass

    def healthy(self) -> bool:
        return self.root.exists()


class S3Storage:
    name = "s3"

    def __init__(self, bucket: str, endpoint_url: str | None, region: str, access_key: str | None, secret_key: str | None, *, sse: str | None = "AES256", path_style: bool = False):
        import boto3
        from botocore.config import Config

        self.bucket = bucket
        self.sse = sse or None
        cfg = Config(s3={"addressing_style": "path"}) if path_style else None
        self.client = boto3.client("s3", endpoint_url=endpoint_url, region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key, config=cfg)

    def ensure_bucket(self) -> None:
        from botocore.exceptions import ClientError

        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        extra = {"ServerSideEncryption": self.sse} if self.sse else {}
        self.client.put_object(Bucket=self.bucket, Key=_check_key(key), Body=data, ContentType=content_type, **extra)

    def get(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=_check_key(key))["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=_check_key(key))

    def healthy(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return True
        except Exception:
            return False


@lru_cache
def get_storage() -> StorageBackend:
    s = get_settings()
    if s.storage_backend == "s3":
        st = S3Storage(s.s3_bucket, s.s3_endpoint_url, s.s3_region, s.s3_access_key, s.s3_secret_key, sse=s.s3_sse, path_style=s.s3_force_path_style)
        st.ensure_bucket()
        return st
    return LocalStorage(s.storage_local_path)
