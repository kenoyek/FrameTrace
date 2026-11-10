import hashlib
import os
import secrets
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, Header, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from .accounts import router as account_router
from .auth import identity
from .config import settings
from .db import Job, JobAccount, JobExecution, Match, Reference, Session, initialize
from .ingress import UploadBoundary
from .lifecycle import dispatch_pending
from .privacy import PrivateResponses
from .schemas import AcceptedJob, RecognitionJob
from .storage import discard_staged, remove_clip, stage_object
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


app.add_middleware(UploadBoundary)
app.add_middleware(PrivateResponses)
app.include_router(account_router)


def replay_submission(db, submission_hash, content_hash, token, user_id):
    execution = db.scalar(
        select(JobExecution).where(JobExecution.submission_hash == submission_hash)
    )
    if execution is None:
        return None
    if execution.content_hash != content_hash:
        raise HTTPException(409, "This submission token was already used for a different clip.")
    job = db.get(Job, execution.job_id)
    account = db.get(JobAccount, job.id)
    if (account.user_id if account else None) != user_id:
        raise HTTPException(404, "Recognition not found.")
    return {"id": job.id, "access_token": token, "status": job.status}


@app.post("/v1/recognitions", status_code=202, response_model=AcceptedJob)
async def create_recognition(
    background: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    authorization: str | None = Header(default=None),
    x_submission_token: Annotated[
        str | None, Header(min_length=43, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    ] = None,
):
    user_id = await run_in_threadpool(identity, authorization, required=False)
    job_id = str(uuid4())
    token = x_submission_token or secrets.token_urlsafe(32)
    submission_hash = token_hash(token) if x_submission_token else None
    path = settings.data_dir / "queries" / f"{job_id}.mp4"
    size, digest, committed, remote = 0, hashlib.sha256(), False, False
    try:
        with path.open("xb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(413, "Clip exceeds the upload limit.")
                digest.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        path.chmod(0o600)
        if size < 12:
            raise HTTPException(422, "Empty or invalid video.")
        with path.open("rb") as stream:
            if stream.read(12)[4:8] != b"ftyp":
                raise HTTPException(415, "Choose a valid MP4 or MOV video.")
        with Session() as db:
            if submission_hash:
                replay = replay_submission(db, submission_hash, digest.hexdigest(), token, user_id)
                if replay:
                    path.unlink(missing_ok=True)
                    return replay
            try:
                remote = await run_in_threadpool(
                    stage_object, db, job_id, path, digest.hexdigest(), size
                )
            except RuntimeError:
                raise HTTPException(503, "Private storage is unavailable; please retry.") from None
            db.add(Job(id=job_id, token_hash=token_hash(token)))
            db.flush()
            db.add(
                JobExecution(
                    job_id=job_id, submission_hash=submission_hash, content_hash=digest.hexdigest()
                )
            )
            if user_id:
                db.add(JobAccount(job_id=job_id, user_id=user_id))
            try:
                db.commit()
                committed = True
            except IntegrityError:
                db.rollback()
                replay = replay_submission(db, submission_hash, digest.hexdigest(), token, user_id)
                if replay is None:
                    raise
                path.unlink(missing_ok=True)
                return replay
        if remote:
            path.unlink(missing_ok=True)
        if settings.execution == "local":
            background.add_task(recognize.run, job_id)
        else:
            background.add_task(dispatch_pending, job_id)
        # Acceptance means durable local DB/file storage, even if Redis is offline.
        return {"id": job_id, "access_token": token, "status": "queued"}
    except Exception:
        if not committed:
            path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
        if remote and not committed:
            await run_in_threadpool(discard_staged, job_id, digest.hexdigest(), size)


def owned_job(db, job_id: str, authorization: str | None) -> Job:
    job = db.get(Job, job_id)
    account = db.get(JobAccount, job_id)
    if account:
        if identity(authorization) != account.user_id:
            raise HTTPException(404, "Recognition not found.")
    else:
        token = authorization.removeprefix("Bearer ") if authorization else ""
        if not job or not secrets.compare_digest(job.token_hash, token_hash(token)):
            raise HTTPException(404, "Recognition not found.")
    return job


@app.get("/v1/recognitions/{job_id}", response_model=RecognitionJob)
def get_recognition(job_id: str, authorization: str | None = Header(default=None)):
    with Session() as db:
        job = owned_job(db, job_id, authorization)
        return serialize_job(db, job)


def serialize_job(db, job):
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
        db.execute(delete(JobExecution).where(JobExecution.job_id == job_id))
        db.execute(delete(JobAccount).where(JobAccount.job_id == job_id))
        db.delete(job)
        db.commit()
    remove_clip(job_id)
