import asyncio
import os
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from frametrace.app import app
from frametrace.config import settings
from frametrace.db import Job, JobExecution, Match, Session, initialize
from frametrace.ingress import UploadBoundary
from frametrace.lifecycle import claim, cleanup, dispatch_pending, fenced, query_path
from frametrace.tasks import recognize

CLIP = b"\x00\x00\x00\x18ftyp" + b"x" * 40


@pytest.fixture(autouse=True)
def isolated_jobs():
    initialize()
    (settings.data_dir / "queries").mkdir(exist_ok=True)
    with Session() as db:
        db.execute(delete(Match))
        db.execute(delete(JobExecution))
        db.execute(delete(Job))
        db.commit()
    yield
    with Session() as db:
        db.execute(delete(Match))
        db.execute(delete(JobExecution))
        db.execute(delete(Job))
        db.commit()
    for path in (settings.data_dir / "queries").glob("*.mp4"):
        path.unlink(missing_ok=True)


def seed():
    job_id = str(uuid4())
    with Session() as db:
        db.add(Job(id=job_id, token_hash="test-only"))
        db.flush()
        db.add(JobExecution(job_id=job_id))
        db.commit()
    query_path(job_id).write_bytes(CLIP)
    return job_id


def test_same_token_replays_without_second_job_and_rejects_new_body(monkeypatch):
    monkeypatch.setattr(settings, "execution", "celery")
    monkeypatch.setattr(recognize, "apply_async", lambda **kwargs: None)
    token = secrets.token_urlsafe(32)
    headers = {"X-Submission-Token": token}
    with TestClient(app) as client:
        first = client.post("/v1/recognitions", headers=headers, files={"file": ("clip.mp4", CLIP)})
        second = client.post(
            "/v1/recognitions", headers=headers, files={"file": ("clip.mp4", CLIP)}
        )
        assert first.status_code == second.status_code == 202
        assert first.json() == second.json()
        assert first.json()["access_token"] == token
        changed = client.post(
            "/v1/recognitions", headers=headers, files={"file": ("clip.mp4", CLIP + b"changed")}
        )
        assert changed.status_code == 409
        assert len(list((settings.data_dir / "queries").glob("*.mp4"))) == 1
        with Session() as db:
            assert len(list(db.scalars(select(Job)))) == 1


def test_concurrent_submissions_create_one_job(monkeypatch):
    monkeypatch.setattr(settings, "execution", "celery")
    monkeypatch.setattr(recognize, "apply_async", lambda **kwargs: None)
    token = secrets.token_urlsafe(32)
    with TestClient(app) as client:

        def submit(_):
            return client.post(
                "/v1/recognitions",
                headers={"X-Submission-Token": token},
                files={"file": ("clip.mp4", CLIP)},
            )

        with ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(submit, range(4)))
        assert all(r.status_code == 202 for r in responses), [r.text for r in responses]
        assert len({r.json()["id"] for r in responses}) == 1
        assert len(list((settings.data_dir / "queries").glob("*.mp4"))) == 1


def test_atomic_claim_and_duplicate_delivery_preserve_media():
    job_id = seed()
    with ThreadPoolExecutor(max_workers=4) as pool:
        owners = list(pool.map(lambda _: claim(job_id), range(4)))
    assert len([owner for owner in owners if owner]) == 1
    recognize.run(job_id)
    assert query_path(job_id).exists()
    with Session() as db:
        assert db.get(JobExecution, job_id).attempts == 1


def test_expired_owner_cannot_change_reclaimed_job():
    job_id = seed()
    old_owner = claim(job_id)
    with Session() as db:
        db.get(JobExecution, job_id).lease_until = time.time() - 1
        db.commit()
    new_owner = claim(job_id)
    assert new_owner and old_owner != new_owner
    with Session() as db:
        assert not fenced(db, job_id, old_owner)
        assert fenced(db, job_id, new_owner)
        db.rollback()


def test_dispatch_recovers_expired_lease_and_throttles_duplicates(monkeypatch):
    job_id = seed()
    claim(job_id)
    with Session() as db:
        db.get(JobExecution, job_id).lease_until = time.time() - 1
        db.commit()
    published = []
    monkeypatch.setattr(
        recognize, "apply_async", lambda **kwargs: published.append(kwargs["args"][0])
    )
    assert dispatch_pending() == 1
    assert dispatch_pending() == 0
    assert published == [job_id]
    with Session() as db:
        assert db.get(Job, job_id).status == "queued"
    assert query_path(job_id).exists()


def test_attempt_budget_is_terminal_without_unbounded_retries():
    job_id = seed()
    with Session() as db:
        db.get(JobExecution, job_id).attempts = settings.max_job_attempts
        db.commit()
    assert dispatch_pending() == 0
    with Session() as db:
        assert db.get(Job, job_id).status == "failed"
    assert not query_path(job_id).exists()


def test_transient_failure_retains_clip_for_retry(monkeypatch):
    job_id = seed()

    def unavailable(*args):
        raise ConnectionError("transient processing failure")

    monkeypatch.setattr("frametrace.tasks.extract", unavailable)
    recognize.run(job_id)
    with Session() as db:
        assert db.get(Job, job_id).status == "queued"
        assert db.get(JobExecution, job_id).attempts == 1
    assert query_path(job_id).exists()
    # Test lifecycle only; real decoding/matching is exercised in test_api.py.
    monkeypatch.setattr("frametrace.tasks.extract", lambda *args: (6, []))
    recognize.run(job_id)
    with Session() as db:
        assert db.get(Job, job_id).status == "completed"
        assert db.get(JobExecution, job_id).attempts == 2
    assert not query_path(job_id).exists()


def test_retention_skips_active_lease_and_removes_orphan():
    job_id = seed()
    claim(job_id)
    with Session() as db:
        db.get(Job, job_id).created_at = datetime.now(UTC) - timedelta(hours=25)
        db.commit()
    orphan = query_path(str(uuid4()))
    orphan.write_bytes(CLIP)
    os.utime(orphan, (time.time() - 25 * 3600,) * 2)
    cleanup()
    assert query_path(job_id).exists()
    assert not orphan.exists()
    with Session() as db:
        db.get(JobExecution, job_id).lease_until = 0
        db.commit()
    cleanup()
    with Session() as db:
        assert db.get(Job, job_id) is None
        assert db.get(JobExecution, job_id) is None
    assert not query_path(job_id).exists()


def test_chunked_ingress_rejects_before_parser_and_releases_slot(monkeypatch):
    monkeypatch.setattr(settings, "max_upload_bytes", 32)
    monkeypatch.setattr(settings, "multipart_overhead_bytes", 0)
    invoked, messages = [], []

    async def downstream(scope, receive, send):
        invoked.append(True)

    boundary = UploadBoundary(downstream)

    async def run():
        chunks = iter(
            [
                {"type": "http.request", "body": b"x" * 20, "more_body": True},
                {"type": "http.request", "body": b"x" * 20, "more_body": False},
            ]
        )

        async def receive():
            return next(chunks)

        async def send(message):
            messages.append(message)

        await boundary(
            {"type": "http", "method": "POST", "path": "/v1/recognitions", "headers": []},
            receive,
            send,
        )

    asyncio.run(run())
    assert not invoked
    assert messages[0]["status"] == 413
    assert boundary.active == 0


def test_upload_admission_returns_retry_after(monkeypatch):
    monkeypatch.setattr(settings, "max_inflight_uploads", 0)
    with TestClient(app) as client:
        response = client.post("/v1/recognitions", files={"file": ("clip.mp4", CLIP)})
        assert response.status_code == 429
        assert response.headers["retry-after"] == "5"


def test_existing_job_is_backfilled_without_replacing_capability():
    job_id = str(uuid4())
    with Session() as db:
        db.add(Job(id=job_id, token_hash="legacy-secret-hash", status="queued"))
        db.commit()
    initialize()
    initialize()
    with Session() as db:
        assert db.get(Job, job_id).token_hash == "legacy-secret-hash"
        assert db.get(JobExecution, job_id).attempts == 0
        assert len(list(db.scalars(select(JobExecution)))) == 1


def test_abandoned_scratch_is_expired_without_touching_live_worker():
    job_id = seed()
    claim(job_id)
    root = settings.data_dir / "scratch"
    active = root / (job_id + "-attempt")
    orphan = root / (str(uuid4()) + "-attempt")
    for folder in [active, orphan]:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "clip.mp4").write_bytes(CLIP)
        os.utime(folder, (time.time() - 25 * 3600,) * 2)
    cleanup()
    assert active.exists()
    assert not orphan.exists()
    with Session() as db:
        db.get(JobExecution, job_id).lease_until = 0
        db.commit()
    cleanup()
    assert not active.exists()
