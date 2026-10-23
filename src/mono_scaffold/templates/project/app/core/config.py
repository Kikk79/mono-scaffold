"""Einstellungen aus Umgebung und `.env`.

`ENVIRONMENT` ohne Eintrag gilt als `production` (sicherer Default: keine API-Doku, keine
Dev-Werte). Die Entwicklungs-`.env` setzt `ENVIRONMENT=development`, Tests setzen `test`.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,  # kein Passwort aus einer URL im Startfehler
    )

    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"

    @property
    def docs_enabled(self) -> bool:
        """`/docs`, `/redoc`, `/openapi.json` nur in der Entwicklung."""
        return self.ENVIRONMENT == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
