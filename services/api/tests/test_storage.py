import hashlib

import boto3
import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from moto.server import ThreadedMotoServer
from sqlalchemy import delete

from frametrace.app import app
from frametrace.config import settings
from frametrace.db import ClipObject, Job, JobAccount, JobExecution, Match, Reference, Session
from frametrace.media import extract
from frametrace.storage import purge_pending, remove_clip
from frametrace.tasks import recognize


@pytest.fixture
def s3(monkeypatch):
    # Real loopback HTTP using an explicit S3 emulator; not hosted R2 validation.
    server = ThreadedMotoServer(ip_address="127.0.0.1", port=0, verbose=False)
    server.start()
    host, port = server.get_host_and_port()
    endpoint = f"http://{host}:{port}"
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setattr(boto3, "DEFAULT_SESSION", None)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr(settings, "s3_endpoint_url", endpoint)
    monkeypatch.setattr(settings, "s3_bucket", "private-query-tests")
    monkeypatch.setattr(settings, "execution", "celery")
    monkeypatch.setattr(recognize, "apply_async", lambda **kwargs: None)
    client = boto3.client("s3", endpoint_url=endpoint, region_name="us-east-1")
    client.create_bucket(Bucket=settings.s3_bucket)
    yield client
    with Session() as db:
        db.execute(delete(ClipObject))
        db.execute(delete(JobAccount))
        db.execute(delete(Match))
        db.execute(delete(JobExecution))
        db.execute(delete(Job))
        db.commit()
    server.stop()


def test_real_clip_upload_private_object_worker_match_and_deletion(s3, media):
    with TestClient(app) as client:
        duration, fingerprints = extract(media / "reference.mp4", 60)
        with Session() as db:
            if not db.get(Reference, "storage-fixture"):
                db.add(
                    Reference(
                        id="storage-fixture",
                        title="Original storage fixture",
                        publisher="FrameTrace",
                        rights_basis="Generated test footage",
                        duration=duration,
                        fingerprints=fingerprints,
                    )
                )
                db.commit()
        with (media / "clean.mp4").open("rb") as clip:
            response = client.post("/v1/recognitions", files={"file": ("clip.mp4", clip)})
        assert response.status_code == 202, response.text
        access = response.json()
        with Session() as db:
            blob = db.get(ClipObject, access["id"])
            assert (
                blob.content_hash == hashlib.sha256((media / "clean.mp4").read_bytes()).hexdigest()
            )
        acl = s3.get_object_acl(Bucket=blob.bucket, Key=blob.object_key)
        assert all(g["Grantee"]["Type"] != "Group" for g in acl["Grants"])
        assert not (settings.data_dir / "queries" / f"{access['id']}.mp4").exists()
        recognize.run(access["id"])
        result = client.get(
            "/v1/recognitions/" + access["id"],
            headers={"Authorization": "Bearer " + access["access_token"]},
        ).json()
        assert result["status"] == "completed", result
        assert result["result"]["classification"] == "matching_segment", result
        assert result["result"]["candidates"][0]["start_seconds"] == 4
        with pytest.raises(ClientError):
            s3.head_object(Bucket=blob.bucket, Key=blob.object_key)
        with Session() as db:
            assert db.get(ClipObject, access["id"]) is None


def test_remote_tampering_is_rejected_and_deleted(s3, media):
    with TestClient(app) as client:
        with (media / "clean.mp4").open("rb") as clip:
            access = client.post("/v1/recognitions", files={"file": ("clip.mp4", clip)}).json()
        with Session() as db:
            blob = db.get(ClipObject, access["id"])
        original = (media / "clean.mp4").read_bytes()
        s3.put_object(
            Bucket=blob.bucket, Key=blob.object_key, Body=original[:-1] + bytes([original[-1] ^ 1])
        )
        recognize.run(access["id"])
        with Session() as db:
            job = db.get(Job, access["id"])
            assert job.status == "failed"
            assert "integrity" in job.error


def test_remote_deletion_retries_after_job_removal(s3, media, monkeypatch):
    with TestClient(app) as client:
        with (media / "clean.mp4").open("rb") as clip:
            access = client.post("/v1/recognitions", files={"file": ("clip.mp4", clip)}).json()
        with Session() as db:
            blob = db.get(ClipObject, access["id"])

        class Offline:
            def delete_object(self, **kwargs):
                raise ClientError(
                    {"Error": {"Code": "ServiceUnavailable", "Message": "test outage"}},
                    "DeleteObject",
                )

        with monkeypatch.context() as patch:
            patch.setattr("frametrace.storage.client", Offline)
            remove_clip(access["id"])
        with Session() as db:
            assert db.get(ClipObject, access["id"]).pending_delete
            db.execute(delete(JobExecution).where(JobExecution.job_id == access["id"]))
            db.execute(delete(Job).where(Job.id == access["id"]))
            db.commit()
        purge_pending()
        with Session() as db:
            assert db.get(ClipObject, access["id"]) is None
        with pytest.raises(ClientError):
            s3.head_object(Bucket=blob.bucket, Key=blob.object_key)


def test_stale_terminal_object_is_reconciled_even_before_delete_mark(s3, media):
    with TestClient(app) as client:
        with (media / "clean.mp4").open("rb") as clip:
            access = client.post("/v1/recognitions", files={"file": ("clip.mp4", clip)}).json()
        with Session() as db:
            db.get(Job, access["id"]).status = "failed"
            db.commit()
        purge_pending()
        with Session() as db:
            assert db.get(ClipObject, access["id"]) is None
