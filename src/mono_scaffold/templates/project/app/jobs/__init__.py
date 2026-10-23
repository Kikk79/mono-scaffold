"""Jobs als idempotente CLI-Kommandos (ADR-0003). Trigger von außen (Timer, cron), kein Celery.

Muster je Job (`app/jobs/<name>.py`):

    def main() -> int:
        configure_logging(get_settings().LOG_LEVEL)
        with SessionLocal(bind=get_engine()) as session:
            ...  # nur Modul-Services aufrufen, nie fremde Repositories
            session.commit()  # der Job ist seine eigene Commit-Grenze
        return 0

    if __name__ == "__main__":
        raise SystemExit(main())

Aufruf: `uv run python -m app.jobs.<name>`.
"""
