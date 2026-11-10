import logging
import time

from celery import Celery
from sqlalchemy import select

from .config import settings
from .db import Job, JobExecution, Match, Reference, Session
from .lifecycle import claim, cleanup, dispatch_pending, fenced
from .media import InvalidMedia, extract
from .recognition import match
from .storage import materialize, purge_pending, remove_clip

logger = logging.getLogger(__name__)
celery = Celery("frametrace", broker=settings.broker_url)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    worker_prefetch_multiplier=1,
    task_soft_time_limit=80,
    task_time_limit=90,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_transport_options={"visibility_timeout": 120},
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "recover-and-dispatch": {"task": "maintain", "schedule": 15.0, "options": {"expires": 15}},
        "expire-private-clips": {"task": "expire", "schedule": 3600.0},
    },
)


@celery.task(name="maintain")
def maintain():
    dispatched = dispatch_pending()
    purge_pending()
    return dispatched


@celery.task(name="expire")
def expire():
    cleanup()


@celery.task(name="recognize")
def recognize(job_id: str):
    owner = claim(job_id)
    if owner is None:
        return  # A duplicate delivery must never delete the active worker's media.
    started = time.monotonic()
    terminal = False
    try:
        with materialize(job_id) as path:
            _, query = extract(path, settings.max_query_seconds)
        with Session() as db:
            if not fenced(db, job_id, owner):
                return
            job = db.get(Job, job_id)
            job.status = "searching_catalog"
            refs = [
                {
                    "id": r.id,
                    "title": r.title,
                    "publisher": r.publisher,
                    "source_url": r.source_url,
                    "fingerprints": r.fingerprints,
                }
                for r in db.scalars(select(Reference).where(Reference.revoked.is_(False)))
            ]
            db.commit()
        with Session() as db:
            if not fenced(db, job_id, owner):
                return
            db.get(Job, job_id).status = "verifying_candidates"
            db.commit()
        result = match(query, refs)
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
        with Session() as db:
            if not fenced(db, job_id, owner):
                return
            job = db.get(Job, job_id)
            job.result, job.status, job.error = result, "completed", None
            for reference_id in {c["reference_id"] for c in result["candidates"]}:
                db.add(Match(job_id=job_id, reference_id=reference_id))
            execution = db.get(JobExecution, job_id)
            execution.owner, execution.lease_until = None, 0
            db.commit()
            terminal = True
        logger.info("recognition_completed job=%s elapsed=%.3f", job_id, result["elapsed_seconds"])
    except Exception as exc:
        logger.exception("recognition_failed job=%s", job_id)
        with Session() as db:
            if not fenced(db, job_id, owner):
                return
            job, execution = db.get(Job, job_id), db.get(JobExecution, job_id)
            terminal = (
                isinstance(exc, InvalidMedia) or execution.attempts >= settings.max_job_attempts
            )
            job.status = "failed" if terminal else "queued"
            job.error = (
                str(exc)
                if isinstance(exc, InvalidMedia)
                else ("Recognition failed; please retry." if terminal else None)
            )
            execution.owner, execution.lease_until = None, 0
            execution.dispatch_after = time.time() + settings.dispatch_interval
            db.commit()
    finally:
        if terminal:
            remove_clip(job_id)
