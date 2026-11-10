"""Database leases fence duplicate/stale workers; the dispatch row is a durable outbox."""

import logging
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kombu.exceptions import OperationalError
from sqlalchemy import and_, delete, exists, or_, select, update

from .config import settings
from .db import Job, JobAccount, JobExecution, Match, Session

TERMINAL = ("completed", "failed")
logger = logging.getLogger(__name__)


def query_path(job_id):
    return settings.data_dir / "queries" / f"{job_id}.mp4"


def active_job():
    return exists().where(Job.id == JobExecution.job_id, Job.status.not_in(TERMINAL))


def claim(job_id: str) -> str | None:
    owner, now = str(uuid4()), time.time()
    with Session() as db:
        claimed = db.execute(
            update(JobExecution)
            .where(
                JobExecution.job_id == job_id,
                JobExecution.lease_until <= now,
                JobExecution.attempts < settings.max_job_attempts,
                active_job(),
            )
            .values(
                owner=owner,
                lease_until=now + settings.lease_seconds,
                attempts=JobExecution.attempts + 1,
            )
        ).rowcount
        if not claimed:
            return None
        db.execute(
            update(Job).where(Job.id == job_id).values(status="extracting_features", error=None)
        )
        db.commit()
    return owner


def fenced(db, job_id: str, owner: str) -> bool:
    # Row write lock held until the caller commits its stage/result transaction.
    return bool(
        db.execute(
            update(JobExecution)
            .where(
                JobExecution.job_id == job_id,
                JobExecution.owner == owner,
                JobExecution.lease_until > time.time(),
                active_job(),
            )
            .values(owner=owner)
        ).rowcount
    )


def dispatch_pending(only_job_id: str | None = None) -> int:
    from .storage import available, remove_clip
    from .tasks import recognize

    now = time.time()
    count = 0
    with Session() as db:
        ids = list(
            db.scalars(
                select(JobExecution.job_id)
                .where(
                    active_job(),
                    JobExecution.job_id == only_job_id if only_job_id is not None else True,
                    JobExecution.lease_until <= now,
                    JobExecution.dispatch_after <= now,
                )
                .limit(1000)
            )
        )
    for job_id in ids:
        exhausted = False
        with Session() as db:
            reserved = db.execute(
                update(JobExecution)
                .where(
                    JobExecution.job_id == job_id,
                    JobExecution.lease_until <= now,
                    JobExecution.dispatch_after <= now,
                    active_job(),
                )
                .values(dispatch_after=now + settings.dispatch_interval, owner=None)
            ).rowcount
            if not reserved:
                continue
            execution = db.get(JobExecution, job_id)
            if execution.attempts >= settings.max_job_attempts or not available(db, job_id):
                db.execute(
                    update(Job)
                    .where(Job.id == job_id)
                    .values(
                        status="failed",
                        error="Processing could not recover; please submit a new search.",
                    )
                )
                exhausted = True
            else:
                db.execute(update(Job).where(Job.id == job_id).values(status="queued"))
            db.commit()
        if exhausted:
            remove_clip(job_id)
            continue
        try:
            recognize.apply_async(args=[job_id], retry=False)
            count += 1
        except (OperationalError, ConnectionError, OSError):
            # Accepted files and rows survive a broker outage; next sweep retries.
            logger.warning("dispatch_unavailable job=%s", job_id)
    return count


def cleanup():
    from .storage import expire_scratch, purge_pending, remove_clip

    expire_scratch()
    now = time.time()
    cutoff = datetime.now(UTC) - timedelta(hours=settings.retention_hours)
    history_cutoff = datetime.now(UTC) - timedelta(days=settings.history_days)
    with Session() as db:
        ids = list(
            db.scalars(
                select(Job.id)
                .outerjoin(JobAccount, Job.id == JobAccount.job_id)
                .where(
                    or_(
                        and_(
                            Job.created_at < cutoff,
                            or_(JobAccount.job_id.is_(None), JobAccount.clip_expired.is_(False)),
                        ),
                        and_(Job.created_at < history_cutoff, JobAccount.saved.is_(False)),
                    )
                )
                .limit(1000)
            )
        )
    for job_id in ids:
        with Session() as db:
            # Fence against live workers for both metadata expiry and raw clip expiry.
            locked = db.execute(
                update(JobExecution)
                .where(JobExecution.job_id == job_id, JobExecution.lease_until <= now)
                .values(owner=None)
            ).rowcount
            if not locked:
                continue
            account, job = db.get(JobAccount, job_id), db.get(Job, job_id)
            created = (
                job.created_at.replace(tzinfo=UTC)
                if job.created_at.tzinfo is None
                else job.created_at
            )
            keep_history = account and (account.saved or created >= history_cutoff)
            if keep_history:
                account.clip_expired = True
                if job.status not in TERMINAL:
                    job.status, job.error = "failed", "The clip expired before processing finished."
            else:
                db.execute(delete(Match).where(Match.job_id == job_id))
                db.execute(delete(JobExecution).where(JobExecution.job_id == job_id))
                db.execute(delete(JobAccount).where(JobAccount.job_id == job_id))
                db.execute(delete(Job).where(Job.id == job_id))
            db.commit()
        remove_clip(job_id)
    for path in (settings.data_dir / "queries").glob("*.mp4"):
        try:
            if path.stat().st_mtime > now - settings.retention_hours * 3600:
                continue
        except FileNotFoundError:
            continue
        with Session() as db:
            if db.get(Job, path.stem) is None:
                path.unlink(missing_ok=True)
    purge_pending()
