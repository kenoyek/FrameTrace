from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FRAMETRACE_")
    database_url: str = "sqlite:///./var/frametrace.db"
    data_dir: Path = Path("var")
    broker_url: str = "redis://127.0.0.1:6379/0"
    execution: str = "celery"
    max_upload_bytes: int = 50 * 1024 * 1024
    max_query_seconds: float = 30
    max_reference_seconds: float = 600
    decoder_timeout: int = 60
    max_pixels: int = 3840 * 2160
    retention_hours: int = 24
    max_inflight_uploads: int = Field(default=4, ge=1)
    multipart_overhead_bytes: int = Field(default=128 * 1024, ge=0)
    lease_seconds: int = Field(default=120, ge=120)
    max_job_attempts: int = Field(default=3, ge=1)
    supabase_url: str | None = None
    storage_backend: str = "local"
    s3_endpoint_url: str | None = None
    s3_bucket: str | None = None
    history_days: int = Field(default=30, ge=1)
    dispatch_interval: int = Field(default=30, ge=1)


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
