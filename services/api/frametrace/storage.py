"""Private local/S3 clips. URLs are never accepted from clients or returned as public media."""

import hashlib
import logging
import shutil
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import delete, or_, select

from .config import settings
from .db import ClipObject, Job, JobExecution, Session
from .media import InvalidMedia

logger = logging.getLogger(__name__)


def client():
    endpoint = settings.s3_endpoint_url
    parsed = urlparse(endpoint or "")
    # HTTP is allowed only for explicitly configured local S3 emulators.
    if not endpoint or not (
        parsed.scheme == "https"
        or (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"})
    ):
        raise RuntimeError("Private storage endpoint must use HTTPS.")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            connect_timeout=5,
            read_timeout=10,
            retries={"max_attempts": 1},
            request_checksum_calculation="when_required",
        ),
    )


def stage_object(db, job_id: str, path: Path, digest: str, size: int) -> bool:
    if settings.storage_backend == "local":
        return False
    if settings.storage_backend != "s3" or not settings.s3_bucket:
        raise RuntimeError("Private storage is not configured.")
    key = f"queries/{job_id}.mp4"
    try:
        # No public ACL; bucket must deny public access and have a 24h safety lifecycle.
        client().upload_file(
            str(path), settings.s3_bucket, key, ExtraArgs={"ContentType": "video/mp4"}
        )
    except (BotoCoreError, ClientError):
        raise RuntimeError("Private media storage is unavailable.") from None
    db.add(
        ClipObject(
            job_id=job_id,
            bucket=settings.s3_bucket,
            object_key=key,
            content_hash=digest,
            size_bytes=size,
        )
    )
    return True


def available(db, job_id: str) -> bool:
    from .lifecycle import query_path

    blob = db.get(ClipObject, job_id)
    return not blob.pending_delete if blob else query_path(job_id).is_file()


@contextmanager
def materialize(job_id: str):
    from .lifecycle import query_path

    with Session() as db:
        blob = db.get(ClipObject, job_id)
    if blob is None:
        yield query_path(job_id)
        return
    if blob.pending_delete:
        raise InvalidMedia("This clip is no longer available.")
    try:
        response = client().get_object(Bucket=blob.bucket, Key=blob.object_key)
    except (BotoCoreError, ClientError):
        raise RuntimeError("Private media storage is unavailable.") from None
    body = response["Body"]
    try:
        scratch = settings.data_dir / "scratch"
        scratch.mkdir(exist_ok=True, mode=0o700)
        with tempfile.TemporaryDirectory(prefix=job_id + "-", dir=scratch) as folder:
            path = Path(folder) / "clip.mp4"
            size, digest = 0, hashlib.sha256()
            with path.open("xb") as output:
                while chunk := body.read(1024 * 1024):
                    size += len(chunk)
                    if size > settings.max_upload_bytes or size > blob.size_bytes:
                        raise InvalidMedia("Stored clip exceeds its validated size.")
                    digest.update(chunk)
                    output.write(chunk)
            if size != blob.size_bytes or digest.hexdigest() != blob.content_hash:
                raise InvalidMedia("Stored clip failed its integrity check.")
            yield path
    finally:
        body.close()


def remove_clip(job_id: str):
    from .lifecycle import query_path

    query_path(job_id).unlink(missing_ok=True)
    with Session() as db:
        blob = db.get(ClipObject, job_id)
        if not blob:
            return
        blob.pending_delete = True
        db.commit()
    try:
        client().delete_object(Bucket=blob.bucket, Key=blob.object_key)
    except (BotoCoreError, ClientError, RuntimeError):
        logger.warning("private_clip_deletion_pending job=%s", job_id)
        return
    with Session() as db:
        db.execute(
            delete(ClipObject).where(
                ClipObject.job_id == job_id, ClipObject.pending_delete.is_(True)
            )
        )
        db.commit()


def purge_pending():
    with Session() as db:
        ids = list(
            db.scalars(
                select(ClipObject.job_id)
                .outerjoin(Job, Job.id == ClipObject.job_id)
                .where(
                    or_(
                        ClipObject.pending_delete.is_(True),
                        Job.id.is_(None),
                        Job.status.in_(["completed", "failed"]),
                    )
                )
                .limit(10)
            )
        )
    for job_id in ids:
        remove_clip(job_id)


def discard_staged(job_id: str, digest: str, size: int):

    # Never delete an object if a commit succeeded but its acknowledgement was lost.
    with Session() as db:
        if db.get(Job, job_id):
            return
        if not db.get(ClipObject, job_id):
            db.add(
                ClipObject(
                    job_id=job_id,
                    bucket=settings.s3_bucket,
                    object_key=f"queries/{job_id}.mp4",
                    content_hash=digest,
                    size_bytes=size,
                    pending_delete=True,
                )
            )
        db.commit()
    remove_clip(job_id)


def expire_scratch():
    """Hard-killed decoder processes cannot run context-manager cleanup."""
    now = time.time()
    for folder in (settings.data_dir / "scratch").glob("*"):
        try:
            if folder.stat().st_mtime > now - settings.retention_hours * 3600:
                continue
        except FileNotFoundError:
            continue
        with Session() as db:
            execution = db.get(JobExecution, folder.name[:36])
            if execution and execution.lease_until > now:
                continue
        if folder.is_symlink():
            folder.unlink(missing_ok=True)
        elif folder.is_dir():
            shutil.rmtree(folder, ignore_errors=True)
