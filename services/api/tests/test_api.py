import pytest
from fastapi.testclient import TestClient

from frametrace.app import app
from frametrace.config import settings
from frametrace.db import Reference, Session
from frametrace.media import InvalidMedia, extract


def test_upload_real_video_match_isolation_revocation_and_delete(media):
    with TestClient(app) as client:
        duration, fingerprints = extract(media / "reference.mp4", 60)
        with Session() as db:
            db.add(
                Reference(
                    id="fixture",
                    title="Synthetic rights-cleared fixture",
                    publisher="FrameTrace",
                    rights_basis="Original generated test footage",
                    duration=duration,
                    fingerprints=fingerprints,
                )
            )
            db.commit()
        with (media / "clean.mp4").open("rb") as clip:
            response = client.post(
                "/v1/recognitions", files={"file": ("../../evil.mp4", clip, "video/mp4")}
            )
        assert response.status_code == 202
        credentials = response.json()
        url = f"/v1/recognitions/{credentials['id']}"
        headers = {"Authorization": f"Bearer {credentials['access_token']}"}
        assert client.get(url).status_code == 404
        assert client.get(url, headers={"Authorization": "Bearer wrong"}).status_code == 404
        result = client.get(url, headers=headers).json()
        assert result["status"] == "completed", result
        assert result["result"]["classification"] == "matching_segment", result
        assert abs(result["result"]["candidates"][0]["start_seconds"] - 4) <= 0.5
        assert not list((settings.data_dir / "queries").glob("*.mp4"))
        with (media / "negative.mp4").open("rb") as clip:
            negative = client.post("/v1/recognitions", files={"file": ("negative.mp4", clip)})
        auth = negative.json()
        unknown = client.get(
            f"/v1/recognitions/{auth['id']}",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        ).json()
        assert unknown["result"]["classification"] == "no_match", unknown
        with Session() as db:
            db.get(Reference, "fixture").revoked = True
            db.commit()
        assert client.get(url, headers=headers).json()["result"]["classification"] == "no_match"
        assert client.delete(url).status_code == 404
        assert client.delete(url, headers=headers).status_code == 204
        assert client.get(url, headers=headers).status_code == 404


def test_invalid_and_oversize_uploads():
    with TestClient(app) as client:
        assert (
            client.post(
                "/v1/recognitions", files={"file": ("x.mp4", b"not a video" * 10)}
            ).status_code
            == 415
        )
        old = settings.max_upload_bytes
        settings.max_upload_bytes = 32
        try:
            assert (
                client.post("/v1/recognitions", files={"file": ("x.mp4", b"x" * 33)}).status_code
                == 413
            )
        finally:
            settings.max_upload_bytes = old
        assert not list((settings.data_dir / "queries").glob("*.mp4"))


def test_malformed_container_rejected_by_worker():
    with TestClient(app) as client:
        response = client.post(
            "/v1/recognitions", files={"file": ("x.mp4", b"\x00\x00\x00\x18ftyp" + b"x" * 30)}
        )
        auth = response.json()
        status = client.get(
            f"/v1/recognitions/{auth['id']}",
            headers={"Authorization": f"Bearer {auth['access_token']}"},
        ).json()
        assert status["status"] == "failed"
        assert not list((settings.data_dir / "queries").glob("*.mp4"))


def test_duration_limits(media):
    with pytest.raises(InvalidMedia):
        extract(media / "reference.mp4", 5)


def test_queue_failure_retains_durable_job(monkeypatch):
    from frametrace.tasks import recognize

    def unavailable(*args, **kwargs):
        raise ConnectionError("queue offline")

    monkeypatch.setattr(recognize, "apply_async", unavailable)
    old = settings.execution
    settings.execution = "celery"
    try:
        with TestClient(app) as client:
            response = client.post(
                "/v1/recognitions",
                files={"file": ("video.mp4", b"\x00\x00\x00\x18ftyp" + b"x" * 30)},
            )
            assert response.status_code == 202
            job_id = response.json()["id"]
            path = settings.data_dir / "queries" / f"{job_id}.mp4"
            assert path.exists()
            from frametrace.db import Job

            with Session() as db:
                assert db.get(Job, job_id).status == "queued"
            # Recovery retains media; actual malformed decode is still terminal.
            recognize.run(job_id)
            assert not path.exists()
    finally:
        settings.execution = old
