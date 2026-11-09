import hashlib
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, Header, HTTPException, UploadFile
from sqlalchemy import delete, select

from .config import settings
from .db import Job, Match, Reference, Session, initialize
from .schemas import AcceptedJob, RecognitionJob
from .tasks import recognize


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize()
    (settings.data_dir / "queries").mkdir(parents=True, exist_ok=True, mode=0o700)
    yield


app = FastAPI(
    title="FrameTrace",
    version="0.1.0",
    lifespan=lifespan,
    description="Controlled-catalog video recognition. Local development API.",
)


@app.get("/health")
def health():
    with Session() as db:
        db.execute(select(1))
    return {"status": "ok", "execution": settings.execution}


@app.post("/v1/recognitions", status_code=202, response_model=AcceptedJob)
async def create_recognition(background: BackgroundTasks, file: Annotated[UploadFile, File()]):
    job_id, token = str(uuid4()), secrets.token_urlsafe(32)
    path = settings.data_dir / "queries" / f"{job_id}.mp4"
    size = 0
    try:
        with path.open("xb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(413, "Clip exceeds the upload limit.")
                output.write(chunk)
        path.chmod(0o600)
        if size < 12:
            raise HTTPException(422, "Empty or invalid video.")
        with path.open("rb") as stream:
            if stream.read(12)[4:8] != b"ftyp":
                raise HTTPException(415, "Choose a valid MP4 or MOV video.")
        with Session() as db:
            db.add(Job(id=job_id, token_hash=token_hash(token)))
            db.commit()
        if settings.execution == "local":
            background.add_task(recognize.run, job_id)
        else:
            try:
                recognize.apply_async(args=[job_id], retry=False)
            except Exception as exc:
                with Session() as db:
                    job = db.get(Job, job_id)
                    job.status, job.error = "failed", "Worker queue unavailable."
                    db.commit()
                raise HTTPException(503, "Worker queue unavailable; please retry.") from exc
        return {"id": job_id, "access_token": token, "status": "queued"}
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


def owned_job(db, job_id: str, authorization: str | None) -> Job:
    job = db.get(Job, job_id)
    token = authorization.removeprefix("Bearer ") if authorization else ""
    if not job or not secrets.compare_digest(job.token_hash, token_hash(token)):
        raise HTTPException(404, "Recognition not found.")
    return job


@app.get("/v1/recognitions/{job_id}", response_model=RecognitionJob)
def get_recognition(job_id: str, authorization: str | None = Header(default=None)):
    with Session() as db:
        job = owned_job(db, job_id, authorization)
        result = job.result
        # Revocation applies to previously returned/stored matches, too.
        if result and result.get("candidates"):
            ids = {r.id for r in db.scalars(select(Reference).where(Reference.revoked.is_(False)))}
            if any(c["reference_id"] not in ids for c in result["candidates"]):
                result = {
                    "classification": "no_match",
                    "candidates": [],
                    "reason": "Reference availability changed; please search again.",
                }
        return {"id": job.id, "status": job.status, "result": result, "error": job.error}


@app.delete("/v1/recognitions/{job_id}", status_code=204)
def delete_recognition(job_id: str, authorization: str | None = Header(default=None)):
    with Session() as db:
        job = owned_job(db, job_id, authorization)
        if job.status not in {"completed", "failed"}:
            raise HTTPException(409, "Processing is active; retry deletion after completion.")
        db.execute(delete(Match).where(Match.job_id == job_id))
        db.delete(job)
        db.commit()
    (settings.data_dir / "queries" / f"{job_id}.mp4").unlink(missing_ok=True)


def cleanup():
    cutoff = datetime.now(UTC) - timedelta(hours=settings.retention_hours)
    with Session() as db:
        for job in db.scalars(select(Job).where(Job.created_at < cutoff)):
            (settings.data_dir / "queries" / f"{job.id}.mp4").unlink(missing_ok=True)
            db.execute(delete(Match).where(Match.job_id == job.id))
            db.delete(job)
        db.commit()
