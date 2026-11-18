import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete

from frametrace import cli
from frametrace.db import CatalogAudit, Feedback, Job, Reference, Session, initialize
from frametrace.operations import audit_page, catalog_page, feedback_summary, record_catalog_event


@pytest.fixture
def catalog(tmp_path):
    initialize()
    path = tmp_path / "authorized.mp4"
    path.write_bytes(str(uuid4()).encode())
    reference_id = hashlib.sha256(path.read_bytes()).hexdigest()
    yield path, reference_id
    with Session() as db:
        db.execute(delete(CatalogAudit).where(CatalogAudit.reference_id == reference_id))
        db.execute(delete(Reference).where(Reference.id == reference_id))
        db.commit()


def run_cli(monkeypatch, capsys, *args):
    monkeypatch.setattr("sys.argv", ["frametrace", *args])
    cli.main()
    return json.loads(capsys.readouterr().out)


def test_ingest_and_revoke_have_atomic_audit_and_repeat_revoke_is_noop(
    catalog, monkeypatch, capsys
):
    path, reference_id = catalog
    monkeypatch.setattr(
        cli, "extract", lambda *_: (8, [{"time": n, "hash": "f" * 16} for n in range(8)])
    )
    args = (
        "ingest",
        str(path),
        "--title",
        "Authorized fixture",
        "--publisher",
        "Operator",
        "--rights-basis",
        "Original footage",
        "--actor",
        "test-operator",
    )
    assert run_cli(monkeypatch, capsys, *args)["id"] == reference_id
    with pytest.raises(SystemExit):
        run_cli(monkeypatch, capsys, *args)
    capsys.readouterr()
    revoked = run_cli(
        monkeypatch,
        capsys,
        "revoke",
        reference_id,
        "--actor",
        "test-operator",
        "--reason",
        "Rights withdrawn",
    )
    assert revoked["changed"] is True
    assert (
        run_cli(
            monkeypatch,
            capsys,
            "revoke",
            reference_id,
            "--actor",
            "test-operator",
            "--reason",
            "Repeat",
        )["changed"]
        is False
    )
    with Session() as db:
        events = audit_page(db, reference_id=reference_id)["items"]
        assert {row["action"] for row in events} == {"ingest", "revoke"}
        assert len(events) == 2
        assert (
            next(row for row in events if row["action"] == "revoke")["reason"] == "Rights withdrawn"
        )
        assert db.get(Reference, reference_id).revoked
        assert not any(row["id"] == reference_id for row in catalog_page(db)["items"])
        row = next(
            row
            for row in catalog_page(db, limit=100, include_revoked=True)["items"]
            if row["id"] == reference_id
        )
        assert set(row) == {"id", "title", "publisher", "duration", "revoked"}


def test_audit_is_rolled_back_with_failed_mutation(catalog):
    _, reference_id = catalog
    with Session() as db:
        record_catalog_event(db, reference_id, "revoke", "operator", "rollback")
        db.flush()
        db.rollback()
        assert audit_page(db, reference_id=reference_id)["items"] == []


def test_audit_pagination_and_cli_output(catalog, monkeypatch, capsys):
    _, reference_id = catalog
    with Session() as db:
        for n in range(3):
            record_catalog_event(db, reference_id, "ingest", "operator", str(n))
        db.commit()
        first = audit_page(db, limit=2, reference_id=reference_id)
        second = audit_page(db, limit=2, offset=first["next_offset"], reference_id=reference_id)
        assert len(first["items"]) == 2 and len(second["items"]) == 1
        assert second["next_offset"] is None
        assert len({row["id"] for row in first["items"] + second["items"]}) == 3
    output = run_cli(monkeypatch, capsys, "catalog-audit", "--reference-id", reference_id)
    assert len(output["items"]) == 3


def test_summary_counts_retained_feedback_by_job_creation_window_without_identifiers(
    monkeypatch, capsys
):
    initialize()
    ids = [str(uuid4()) for _ in range(3)]
    try:
        with Session() as db:
            for n, job_id in enumerate(ids):
                db.add(
                    Job(
                        id=job_id,
                        token_hash="private-token-hash",
                        status="completed",
                        result={"classification": "no_match"},
                        created_at=datetime.now(UTC) - timedelta(days=100 if n == 2 else 0),
                    )
                )
            db.commit()
            for job_id in ids:
                db.add(Feedback(job_id=job_id, rating="helpful"))
            db.commit()
            summary = feedback_summary(db, days=1)
            row = next(
                row
                for row in summary["ratings"]
                if row["classification"] == "no_match" and row["rating"] == "helpful"
            )
            assert row["count"] == 2
            assert set(row) == {"classification", "rating", "count"}
        output = run_cli(monkeypatch, capsys, "feedback-summary", "--days", "1")
        assert "private-token-hash" not in json.dumps(output)
        assert all(job_id not in json.dumps(output) for job_id in ids)
    finally:
        with Session() as db:
            db.execute(delete(Feedback).where(Feedback.job_id.in_(ids)))
            db.execute(delete(Job).where(Job.id.in_(ids)))
            db.commit()


@pytest.mark.parametrize(
    "args",
    [
        ["catalog", "--limit", "101"],
        ["catalog", "--offset", "-1"],
        ["feedback-summary", "--days", "0"],
        ["revoke", "missing", "--actor", "operator"],
        ["revoke", "missing", "--actor", " ", "--reason", "test"],
    ],
)
def test_cli_rejects_unbounded_queries_and_missing_audit_context(monkeypatch, args):
    monkeypatch.setattr("sys.argv", ["frametrace", *args])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
