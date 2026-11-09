from pathlib import Path

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


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
