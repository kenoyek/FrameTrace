from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from frametrace.app import app, token_hash
from frametrace.db import Feedback, Job, JobAccount, JobExecution, Session, engine
from frametrace.lifecycle import cleanup


@pytest.fixture
def result():
    job_id, token = str(uuid4()), "private-guest-token"
    with TestClient(app) as client:
        with Session() as db:
            db.add(
                Job(
                    id=job_id,
                    token_hash=token_hash(token),
                    status="completed",
                    result={
                        "classification": "no_match",
                        "candidates": [],
                        "reason": "Not enough evidence.",
                    },
                )
            )
            db.commit()
            db.add(JobExecution(job_id=job_id))
            db.commit()
        yield client, job_id, {"Authorization": "Bearer " + token}
        with Session() as db:
            for table in (Feedback, JobExecution, JobAccount):
                db.execute(delete(table).where(table.job_id == job_id))
            db.execute(delete(Job).where(Job.id == job_id))
            db.commit()


def test_feedback_retries_update_one_row_and_restore_with_private_result(result):
    client, job_id, headers = result
    url = f"/v1/recognitions/{job_id}"
    assert client.get(url, headers=headers).json()["feedback"] is None
    for rating in ("helpful", "helpful", "not_helpful", "unsure"):
        response = client.post(url + "/feedback", headers=headers, json={"rating": rating})
        assert response.status_code == 200
        assert response.json() == {"rating": rating}
        assert response.headers["cache-control"] == "no-store"
        assert client.get(url, headers=headers).json()["feedback"] == rating
    with Session() as db:
        assert db.get(Feedback, job_id).rating == "unsure"
        assert db.get(Job, job_id).result["classification"] == "no_match"


def test_feedback_rejects_wrong_guest_and_nonexistent_job(result):
    client, job_id, _ = result
    for target in (job_id, str(uuid4())):
        response = client.post(f"/v1/recognitions/{target}/feedback", json={"rating": "helpful"})
        assert response.status_code == 404
    with Session() as db:
        assert db.get(Feedback, job_id) is None


def test_feedback_is_bounded_and_only_accepts_completed_results(result):
    client, job_id, headers = result
    url = f"/v1/recognitions/{job_id}/feedback"
    for body in ({"rating": "invented"}, {"rating": "helpful", "comment": "private"}, {}):
        assert client.post(url, headers=headers, json=body).status_code == 422
    with Session() as db:
        db.get(Job, job_id).status = "queued"
        db.commit()
    assert client.post(url, headers=headers, json={"rating": "helpful"}).status_code == 409


def test_account_feedback_excludes_guest_and_other_account_and_clears_with_history(
    result, monkeypatch
):
    client, job_id, guest = result
    # JWT cryptography is covered in test_accounts; isolate job ownership here.
    monkeypatch.setattr("frametrace.app.identity", lambda value: value)
    monkeypatch.setattr("frametrace.accounts.identity", lambda value: value)
    with Session() as db:
        db.add(JobAccount(job_id=job_id, user_id="account-a"))
        db.commit()
    url = f"/v1/recognitions/{job_id}/feedback"
    for headers in (guest, {"Authorization": "account-b"}):
        assert client.post(url, headers=headers, json={"rating": "helpful"}).status_code == 404
    headers = {"Authorization": "account-a"}
    assert client.post(url, headers=headers, json={"rating": "helpful"}).status_code == 200
    assert client.get("/v1/history", headers=headers).json()["items"][0]["feedback"] == "helpful"
    assert client.delete("/v1/history", headers=headers).status_code == 200
    with Session() as db:
        assert db.get(Feedback, job_id) is None


def test_feedback_removed_by_result_deletion_and_retention(result):
    client, job_id, headers = result
    url = f"/v1/recognitions/{job_id}"
    assert (
        client.post(url + "/feedback", headers=headers, json={"rating": "helpful"}).status_code
        == 200
    )
    with Session() as db:
        db.get(Job, job_id).created_at = datetime.now(UTC) - timedelta(days=100)
        db.commit()
    cleanup()
    with Session() as db:
        assert db.get(Job, job_id) is None
        assert db.get(Feedback, job_id) is None


def test_explicit_deletion_removes_feedback(result):
    client, job_id, headers = result
    url = f"/v1/recognitions/{job_id}"
    assert (
        client.post(url + "/feedback", headers=headers, json={"rating": "not_helpful"}).status_code
        == 200
    )
    assert client.delete(url, headers=headers).status_code == 204
    with Session() as db:
        assert db.get(Feedback, job_id) is None


@pytest.mark.skipif(engine.dialect.name != "postgresql", reason="Requires PostgreSQL row locks")
def test_concurrent_feedback_upserts_remain_single_owner_row(result):
    client, job_id, headers = result
    url = f"/v1/recognitions/{job_id}/feedback"
    ratings = ["helpful", "not_helpful", "unsure"] * 3

    def submit(rating):
        return client.post(url, headers=headers, json={"rating": rating}).status_code

    with ThreadPoolExecutor(max_workers=3) as pool:
        assert list(pool.map(submit, ratings)) == [200] * len(ratings)
    with Session() as db:
        assert db.get(Feedback, job_id).rating in ratings
