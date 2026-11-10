import json
import time
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import delete

from frametrace.app import app
from frametrace.auth import jwks_client
from frametrace.config import settings
from frametrace.db import Job, JobAccount, JobExecution, Match, Session

CLIP = b"\x00\x00\x00\x18ftyp" + b"x" * 40


@pytest.fixture
def accounts(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    jwk.update(kid="unit-key", use="sig")
    provider = jwt.PyJWKClient("https://auth.test/keys")
    monkeypatch.setattr(provider, "fetch_data", lambda: {"keys": [jwk]})
    monkeypatch.setattr("frametrace.auth.jwks_client", lambda url: provider)
    monkeypatch.setattr(settings, "supabase_url", "https://auth.test")
    a, b = str(uuid4()), str(uuid4())

    def token(user=a, **overrides):
        claims = {
            "sub": user,
            "exp": int(time.time()) + 600,
            "iat": int(time.time()),
            "aud": "authenticated",
            "iss": "https://auth.test/auth/v1",
            "role": "authenticated",
        }
        claims.update(overrides)
        return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "unit-key"})

    yield a, b, token
    with Session() as db:
        db.execute(delete(JobAccount))
        db.execute(delete(Match))
        db.execute(delete(JobExecution))
        db.execute(delete(Job))
        db.commit()
    jwks_client.cache_clear()


def test_verified_session_is_required_for_account_job_and_private_history(accounts):
    a, b, token = accounts
    auth_a, auth_b = (
        {"Authorization": "Bearer " + token(a)},
        {"Authorization": "Bearer " + token(b)},
    )
    with TestClient(app) as client:
        response = client.post(
            "/v1/recognitions", headers=auth_a, files={"file": ("clip.mp4", CLIP)}
        )
        assert response.status_code == 202, response.text
        access = response.json()
        url = "/v1/recognitions/" + access["id"]
        assert client.get(url, headers=auth_a).status_code == 200
        assert client.get(url, headers=auth_b).status_code == 404
        assert (
            client.get(
                url, headers={"Authorization": "Bearer " + access["access_token"]}
            ).status_code
            == 401
        )
        assert client.get("/v1/history", headers=auth_b).json()["items"] == []
        history_response = client.get("/v1/history", headers=auth_a)
        assert history_response.headers["cache-control"] == "no-store"
        history = history_response.json()
        assert [item["id"] for item in history["items"]] == [access["id"]]
        assert "access_token" not in history["items"][0]
        assert (
            client.patch(
                "/v1/history/" + access["id"], headers=auth_b, json={"saved": True}
            ).status_code
            == 404
        )
        assert (
            client.patch(
                "/v1/history/" + access["id"], headers=auth_a, json={"saved": True}
            ).status_code
            == 200
        )
        assert len(client.get("/v1/history?saved_only=true", headers=auth_a).json()["items"]) == 1
        assert client.delete(url, headers=auth_b).status_code == 404
        assert client.delete("/v1/history", headers=auth_a).json()["deleted"] == 1
        assert client.get(url, headers=auth_a).status_code == 404


@pytest.mark.parametrize(
    "override",
    [
        {"aud": "other"},
        {"iss": "https://attacker.test/auth/v1"},
        {"exp": 1},
        {"role": "service_role"},
        {"sub": "not-a-uuid"},
        {"iat": int(time.time()) + 3600},
    ],
)
def test_wrong_claims_are_rejected_before_job_creation(accounts, override):
    _, _, token = accounts
    with TestClient(app) as client:
        response = client.post(
            "/v1/recognitions",
            headers={"Authorization": "Bearer " + token(**override)},
            files={"file": ("clip.mp4", CLIP)},
        )
        assert response.status_code == 401


def test_forged_signature_and_hmac_confusion_are_rejected(accounts):
    a, _, token = accounts
    real = token(a)
    payload = jwt.decode(real, options={"verify_signature": False})
    forged = jwt.encode(
        payload,
        "attacker-secret-that-is-not-a-supabase-key",
        algorithm="HS256",
        headers={"kid": "unit-key"},
    )
    with TestClient(app) as client:
        assert (
            client.get("/v1/history", headers={"Authorization": "Bearer " + forged}).status_code
            == 401
        )
        assert (
            client.get(
                "/v1/history",
                headers={"Authorization": "Bearer " + real[:-20] + "AAAAAAAAAAAAAAAAAAAA"},
            ).status_code
            == 401
        )
        assert client.get("/v1/history").status_code == 401


def test_claiming_guest_requires_both_session_and_original_capability(accounts):
    a, b, token = accounts
    with TestClient(app) as client:
        guest = client.post("/v1/recognitions", files={"file": ("clip.mp4", CLIP)}).json()
        url = "/v1/recognitions/" + guest["id"]
        auth_a = {"Authorization": "Bearer " + token(a)}
        assert client.post(url + "/claim", headers=auth_a).status_code == 404
        auth_a["X-Job-Token"] = guest["access_token"]
        assert client.post(url + "/claim", headers=auth_a).status_code == 200
        assert client.post(url + "/claim", headers=auth_a).status_code == 200
        assert (
            client.get(
                url, headers={"Authorization": "Bearer " + guest["access_token"]}
            ).status_code
            == 401
        )
        assert (
            client.post(
                url + "/claim",
                headers={
                    "Authorization": "Bearer " + token(b),
                    "X-Job-Token": guest["access_token"],
                },
            ).status_code
            == 404
        )


def test_submission_token_does_not_override_account_identity(accounts):
    import secrets

    a, b, token = accounts
    submission = secrets.token_urlsafe(32)
    with TestClient(app) as client:

        def submit(user):
            return client.post(
                "/v1/recognitions",
                headers={
                    "Authorization": "Bearer " + token(user),
                    "X-Submission-Token": submission,
                },
                files={"file": ("clip.mp4", CLIP)},
            )

        first, replay = submit(a), submit(a)
        assert first.status_code == replay.status_code == 202
        assert first.json()["id"] == replay.json()["id"]
        assert submit(b).status_code == 404


def test_raw_clip_expiry_keeps_account_history_but_later_expires_unsaved(accounts):
    from datetime import UTC, datetime, timedelta

    from frametrace.lifecycle import cleanup

    a, _, token = accounts
    with TestClient(app) as client:
        auth = {"Authorization": "Bearer " + token(a)}
        access = client.post(
            "/v1/recognitions", headers=auth, files={"file": ("clip.mp4", CLIP)}
        ).json()
        with Session() as db:
            db.get(Job, access["id"]).created_at = datetime.now(UTC) - timedelta(days=2)
            db.commit()
        cleanup()
        assert len(client.get("/v1/history", headers=auth).json()["items"]) == 1
        with Session() as db:
            assert db.get(JobAccount, access["id"]).clip_expired
            db.get(Job, access["id"]).created_at = datetime.now(UTC) - timedelta(days=31)
            db.commit()
        cleanup()
        assert client.get("/v1/history", headers=auth).json()["items"] == []


def test_jwks_outage_fails_closed(accounts, monkeypatch):
    _, _, token = accounts

    class Unavailable:
        def get_signing_key_from_jwt(self, value):
            raise jwt.PyJWKClientConnectionError("unavailable")

    monkeypatch.setattr("frametrace.auth.jwks_client", lambda url: Unavailable())
    with TestClient(app) as client:
        assert (
            client.get("/v1/history", headers={"Authorization": "Bearer " + token()}).status_code
            == 503
        )


def test_saved_history_outlives_default_metadata_retention(accounts):
    from datetime import UTC, datetime, timedelta

    from frametrace.lifecycle import cleanup

    _, _, token = accounts
    with TestClient(app) as client:
        auth = {"Authorization": "Bearer " + token()}
        access = client.post(
            "/v1/recognitions", headers=auth, files={"file": ("clip.mp4", CLIP)}
        ).json()
        with Session() as db:
            db.get(Job, access["id"]).created_at = datetime.now(UTC) - timedelta(days=31)
            db.get(JobAccount, access["id"]).saved = True
            db.commit()
        cleanup()
        assert len(client.get("/v1/history?saved_only=true", headers=auth).json()["items"]) == 1
        client.patch("/v1/history/" + access["id"], headers=auth, json={"saved": False})
        cleanup()
        assert client.get("/v1/history", headers=auth).json()["items"] == []


def test_unknown_key_ids_have_bounded_jwks_refresh(monkeypatch):
    from frametrace.auth import BoundedJWKClient

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    jwk.update(kid="known-key", use="sig")
    calls = []

    def fetch(_):
        calls.append(True)
        return {"keys": [jwk]}

    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", fetch)
    provider = BoundedJWKClient("https://auth.test/keys")
    for number in range(5):
        token = jwt.encode(
            {"sub": str(uuid4())}, key, algorithm="RS256", headers={"kid": "unknown-" + str(number)}
        )
        with pytest.raises(jwt.PyJWKClientError):
            provider.get_signing_key_from_jwt(token)
    assert len(calls) == 1
