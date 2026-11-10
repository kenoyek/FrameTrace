from datetime import UTC

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from .auth import identity
from .db import Job, JobAccount, Session
from .schemas import ClaimedJob, ClearedHistory, FavoriteResult, HistoryPage

router = APIRouter()


class Favorite(BaseModel):
    saved: bool


@router.get("/v1/history", response_model=HistoryPage)
def history(
    authorization: str | None = Header(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=10000),
    saved_only: bool = False,
):
    user_id = identity(authorization)
    from .app import serialize_job

    with Session() as db:
        query = (
            select(Job, JobAccount)
            .join(JobAccount, Job.id == JobAccount.job_id)
            .where(JobAccount.user_id == user_id)
        )
        if saved_only:
            query = query.where(JobAccount.saved.is_(True))
        rows = db.execute(
            query.order_by(Job.created_at.desc(), Job.id.desc()).offset(offset).limit(limit + 1)
        ).all()
        return {
            "items": [
                dict(
                    serialize_job(db, job),
                    saved=account.saved,
                    created_at=(
                        job.created_at
                        if job.created_at.tzinfo
                        else job.created_at.replace(tzinfo=UTC)
                    ).isoformat(),
                )
                for job, account in rows[:limit]
            ],
            "next_offset": offset + limit
            if len(rows) > limit and offset + limit <= 10000
            else None,
        }


@router.patch("/v1/history/{job_id}", response_model=FavoriteResult)
def favorite(job_id: str, body: Favorite, authorization: str | None = Header(default=None)):
    user_id = identity(authorization)
    with Session() as db:
        account = db.get(JobAccount, job_id)
        if not account or account.user_id != user_id:
            raise HTTPException(404, "Recognition not found.")
        account.saved = body.saved
        db.commit()
        return {"id": job_id, "saved": account.saved}


@router.post("/v1/recognitions/{job_id}/claim", response_model=ClaimedJob)
def claim_guest(
    job_id: str,
    authorization: str | None = Header(default=None),
    x_job_token: str | None = Header(default=None),
):
    import secrets

    from sqlalchemy.exc import IntegrityError

    from .app import token_hash

    user_id = identity(authorization)
    with Session() as db:
        job = db.get(Job, job_id)
        account = db.get(JobAccount, job_id)
        if account:
            if account.user_id != user_id:
                raise HTTPException(404, "Recognition not found.")
            return {"id": job_id}
        if (
            not job
            or not x_job_token
            or not secrets.compare_digest(job.token_hash, token_hash(x_job_token))
        ):
            raise HTTPException(404, "Recognition not found.")
        db.add(JobAccount(job_id=job_id, user_id=user_id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            current = db.get(JobAccount, job_id)
            if current is None or current.user_id != user_id:
                raise HTTPException(404, "Recognition not found.") from None
        return {"id": job_id}


@router.delete("/v1/history", response_model=ClearedHistory)
def clear_history(authorization: str | None = Header(default=None)):
    from sqlalchemy import delete

    from .db import JobExecution, Match
    from .storage import remove_clip

    user_id = identity(authorization)
    with Session() as db:
        active = db.scalar(
            select(Job.id)
            .join(JobAccount, Job.id == JobAccount.job_id)
            .where(JobAccount.user_id == user_id, Job.status.not_in(["completed", "failed"]))
            .limit(1)
        )
        if active:
            raise HTTPException(409, "Wait for active searches to finish before clearing history.")
        ids = list(
            db.scalars(
                select(JobAccount.job_id)
                .join(Job, Job.id == JobAccount.job_id)
                .where(JobAccount.user_id == user_id, Job.status.in_(["completed", "failed"]))
                .limit(1000)
            )
        )
        if ids:
            db.execute(delete(Match).where(Match.job_id.in_(ids)))
            db.execute(delete(JobExecution).where(JobExecution.job_id.in_(ids)))
            db.execute(delete(JobAccount).where(JobAccount.job_id.in_(ids)))
            db.execute(delete(Job).where(Job.id.in_(ids)))
            db.commit()
    for job_id in ids:
        remove_clip(job_id)
    return {"deleted": len(ids), "may_have_more": len(ids) == 1000}
