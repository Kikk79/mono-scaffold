# mono-scaffold

Generator für modulare Monolithen nach dem Muster des Silatec-ERP (`Kikk79/GROKStructuredERP`). Wie `ng new` und `ng generate`, nur für FastAPI + SQLAlchemy + PostgreSQL mit erzwungenen Modulgrenzen.

```
mono new <projekt>                       Grundgerüst: core, main, alembic, tests, docs, ADRs, CLAUDE.md, Gate, CI
mono module <name> [--imports a,b]       Fachmodul: enums, models, schemas, repository, service, router, events,
                                         Test, Interface-Doku; Eintrag in module-grenzen.md, main.py,
                                         model_registry.py; import-linter-Contracts neu erzeugt
mono contracts                           Contracts aus docs/module-grenzen.md neu erzeugen
```

## Installation

```bash
uv tool install --from /pfad/zu/mono-scaffold mono-scaffold   # lokal
# oder, sobald das Repo auf GitHub liegt:
uv tool install --from git+https://github.com/Kikk79/mono-scaffold mono-scaffold
```

Danach ist `mono` auf dem PATH (Windows: `%USERPROFILE%\.local\bin`, Linux: `~/.local/bin`). Ohne Installation: `uvx --from /pfad/zu/mono-scaffold mono new …`.

## Erstes Projekt

```bash
mono new silatec-erp2 --title "Silatec ERP 2"
cd silatec-erp2
docker compose up -d postgres
uv sync
bash scripts/check.sh          # Gate ist auf dem leeren Gerüst grün
mono module auth --entity User
mono module partners
mono module catalog --imports partners
mono module quotes --imports partners,catalog --entity Quote
uv run alembic revision --autogenerate -m "erstes schema" && uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Der Coding-Agent liest `CLAUDE.md` des Projekts und hat damit Struktur, Regeln, Gate und das Kommando für neue Module.

## Was erzwungen wird

- Modulgrenzen aus der Tabelle `docs/module-grenzen.md` → `[tool.importlinter]` in `pyproject.toml` → `uv run lint-imports`.
- Repository je Modul privat; `read_models` rufen keine Services; `core` importiert kein Fachmodul.
- Kein `commit()` in Service oder Router (`tests/unit/test_architecture.py`).
- Modultabelle, Pakete und `main.py`-Imports stimmen überein (derselbe Test).

## Eigene Anpassungen

Die Vorlagen liegen unter `src/mono_scaffold/templates/project` und `…/module`. Tokens: `__PROJECT__`, `__PROJECT_SNAKE__`, `__TITLE__`, `__DATE__`, `__MODULE__`, `__MODULE_TITLE__`, `__ENTITY__`, `__ENTITY_SNAKE__`, `__IMPORTS__`. Dateien mit Präfix `dot_` werden zu Punktdateien.
