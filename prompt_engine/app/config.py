"""Application configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()


def get_settings() -> Settings:
    """Return a fresh settings object."""

    return Settings()
