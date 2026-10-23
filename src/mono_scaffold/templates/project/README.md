# __TITLE__

Modularer Monolith: FastAPI, SQLAlchemy 2.0 (sync), Alembic, PostgreSQL 16. Erzeugt mit `mono new __PROJECT__`.

## Start

```bash
cp .env.example .env            # mono new hat das schon getan
docker compose up -d postgres   # oder eigenen Postgres in .env eintragen
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API-Doku unter `/docs`, solange `ENVIRONMENT=development`.

## Arbeiten

- Neues Fachmodul: `mono module <name> --imports <a,b>`
- Gate vor jedem Merge: `bash scripts/check.sh` (Windows: `scripts/check.ps1`)
- Regeln: `CLAUDE.md`, `docs/module-grenzen.md`, `docs/conventions/coding.md`, `docs/adr/`
