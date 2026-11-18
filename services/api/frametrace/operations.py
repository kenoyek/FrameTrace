"""Local operator queries; never expose these through the untrusted client API."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, select

from .db import CatalogAudit, Feedback, Job, Reference


def record_catalog_event(db, reference_id, action, actor, reason):
    # Caller commits this event and the catalog mutation in one transaction.
    db.add(
        CatalogAudit(
            id=str(uuid4()), reference_id=reference_id, action=action, actor=actor, reason=reason
        )
    )


def catalog_page(db, limit=20, offset=0, include_revoked=False):
    query = select(
        Reference.id, Reference.title, Reference.publisher, Reference.duration, Reference.revoked
    ).order_by(Reference.id)
    if not include_revoked:
        query = query.where(Reference.revoked.is_(False))
    rows = db.execute(query.offset(offset).limit(limit + 1)).mappings().all()
    return {
        "items": [dict(row) for row in rows[:limit]],
        "next_offset": offset + limit if len(rows) > limit else None,
    }


def audit_page(db, limit=20, offset=0, reference_id=None):
    query = select(CatalogAudit).order_by(CatalogAudit.created_at.desc(), CatalogAudit.id.desc())
    if reference_id:
        query = query.where(CatalogAudit.reference_id == reference_id)
    rows = list(db.scalars(query.offset(offset).limit(limit + 1)))
    return {
        "items": [
            {
                "id": row.id,
                "reference_id": row.reference_id,
                "action": row.action,
                "actor": row.actor,
                "reason": row.reason,
                "created_at": (
                    row.created_at.replace(tzinfo=UTC)
                    if row.created_at.tzinfo is None
                    else row.created_at
                ).isoformat(),
            }
            for row in rows[:limit]
        ],
        "next_offset": offset + limit if len(rows) > limit else None,
    }


def feedback_summary(db, days=30):
    cutoff = datetime.now(UTC) - timedelta(days=days)
    classification = Job.result["classification"].as_string()
    rows = (
        db.execute(
            select(
                classification.label("classification"), Feedback.rating, func.count().label("count")
            )
            .join(Job, Job.id == Feedback.job_id)
            .where(Job.created_at >= cutoff)
            .group_by(classification, Feedback.rating)
            .order_by(classification, Feedback.rating)
        )
        .mappings()
        .all()
    )
    return {
        "recognitions_created_since": cutoff.isoformat(),
        "ratings": [dict(row) for row in rows],
        "total": sum(row["count"] for row in rows),
    }
