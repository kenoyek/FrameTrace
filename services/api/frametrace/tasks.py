import logging
import time

from celery import Celery
from sqlalchemy import select

from .config import settings
from .db import Job, Match, Reference, Session
from .media import InvalidMedia, extract
from .recognition import match

logger = logging.getLogger(__name__)
celery = Celery("frametrace", broker=settings.broker_url)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    worker_prefetch_multiplier=1,
    task_soft_time_limit=80,
    task_time_limit=90,
    broker_connection_retry_on_startup=True,
)


@celery.task(name="recognize")
def recognize(job_id: str):
    started = time.monotonic()
    path = settings.data_dir / "queries" / f"{job_id}.mp4"
    try:
        with Session() as db:
            job = db.get(Job, job_id)
            if not job or job.status != "queued":
                return
            job.status = "extracting_features"
            db.commit()
        _, query = extract(path, settings.max_query_seconds)
        with Session() as db:
            job = db.get(Job, job_id)
            job.status = "searching_catalog"
            db.commit()
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
            job.status = "verifying_candidates"
            db.commit()
            result = match(query, refs)
            result["elapsed_seconds"] = round(time.monotonic() - started, 3)
            job.result = result
            job.status = "completed"
            for reference_id in {c["reference_id"] for c in result["candidates"]}:
                db.add(Match(job_id=job_id, reference_id=reference_id))
            db.commit()
            logger.info(
                "recognition_completed job=%s classification=%s elapsed=%.3f",
                job_id,
                result["classification"],
                result["elapsed_seconds"],
            )
    except Exception as exc:
        logger.exception("recognition_failed job=%s", job_id)
        with Session() as db:
            job = db.get(Job, job_id)
            if job:
                job.status = "failed"
                job.error = (
                    str(exc)
                    if isinstance(exc, InvalidMedia)
                    else "Recognition failed; please retry."
                )
                db.commit()
    finally:
        path.unlink(missing_ok=True)
