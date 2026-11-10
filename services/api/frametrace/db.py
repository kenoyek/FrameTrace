from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


class Reference(Base):
    __tablename__ = "reference_media"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    publisher: Mapped[str] = mapped_column(String)
    rights_basis: Mapped[str] = mapped_column(String)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    duration: Mapped[float] = mapped_column(Float)
    fingerprint_version: Mapped[str] = mapped_column(String, default="dhash64-v1-fps2")
    fingerprints: Mapped[list] = mapped_column(JSON)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class Job(Base):
    __tablename__ = "recognition_jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="queued")
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class Match(Base):
    __tablename__ = "recognition_matches"
    job_id: Mapped[str] = mapped_column(ForeignKey("recognition_jobs.id"), primary_key=True)
    reference_id: Mapped[str] = mapped_column(ForeignKey("reference_media.id"), primary_key=True)


class JobExecution(Base):
    """Durable dispatch/outbox and fenced execution lease; no bearer secrets stored here."""

    __tablename__ = "recognition_execution"
    job_id: Mapped[str] = mapped_column(ForeignKey("recognition_jobs.id"), primary_key=True)
    submission_hash: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    owner: Mapped[str | None] = mapped_column(String, nullable=True)
    lease_until: Mapped[float] = mapped_column(Float, default=0)
    dispatch_after: Mapped[float] = mapped_column(Float, default=0)
    attempts: Mapped[int] = mapped_column(default=0)


class JobAccount(Base):
    __tablename__ = "recognition_accounts"
    job_id: Mapped[str] = mapped_column(ForeignKey("recognition_jobs.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    saved: Mapped[bool] = mapped_column(Boolean, default=False)
    clip_expired: Mapped[bool] = mapped_column(Boolean, default=False)


class ClipObject(Base):
    # Independent of jobs so failed remote deletion can survive history removal.
    __tablename__ = "query_objects"
    job_id: Mapped[str] = mapped_column(String, primary_key=True)
    bucket: Mapped[str] = mapped_column(String)
    object_key: Mapped[str] = mapped_column(String, unique=True)
    content_hash: Mapped[str] = mapped_column(String)
    size_bytes: Mapped[int] = mapped_column()
    pending_delete: Mapped[bool] = mapped_column(Boolean, default=False)


engine = create_engine(
    settings.database_url,
    **(
        {"connect_args": {"check_same_thread": False}}
        if settings.database_url.startswith("sqlite")
        else {}
    ),
)
Session = sessionmaker(engine, expire_on_commit=False)


def initialize():
    Base.metadata.create_all(engine)
    # Additive backfill; unique inserts also tolerate concurrent API initialization.
    from sqlalchemy import exists, select
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    insert = sqlite_insert if engine.dialect.name == "sqlite" else pg_insert
    with Session() as db:
        db.execute(
            insert(JobExecution)
            .from_select(
                ["job_id", "lease_until", "dispatch_after", "attempts"],
                select(Job.id, 0, 0, 0).where(~exists().where(JobExecution.job_id == Job.id)),
            )
            .on_conflict_do_nothing(index_elements=["job_id"])
        )
        db.commit()
