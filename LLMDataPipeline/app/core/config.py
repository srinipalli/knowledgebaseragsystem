from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LLMDataPipeline"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://postgres:admin123@localhost:5432/postgres"
    input_dir: Path = Path("./data/input")
    processed_dir: Path = Path("./data/processed")
    failed_dir: Path = Path("./data/failed")
    quarantine_dir: Path = Path("./data/quarantine")
    checkpoint_dir: Path = Path("./data/checkpoints")
    supported_extensions: Annotated[list[str], NoDecode] = [".pdf", ".docx", ".txt", ".md"]
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384
    chunk_size: int = 4000
    chunk_overlap: int = 400
    embed_batch_size: int = 16
    max_concurrency: int = 2
    poll_interval_seconds: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator(
        "input_dir",
        "processed_dir",
        "failed_dir",
        "quarantine_dir",
        "checkpoint_dir",
        mode="before",
    )
    @classmethod
    def _coerce_path(cls, value: str | Path) -> Path:
        return Path(value)

    @field_validator("supported_extensions", mode="before")
    @classmethod
    def _coerce_extensions(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return [item.lower() for item in value]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    for directory in (
        settings.input_dir,
        settings.processed_dir,
        settings.failed_dir,
        settings.quarantine_dir,
        settings.checkpoint_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return settings
