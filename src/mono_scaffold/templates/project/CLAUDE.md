# __TITLE__ – Arbeitsweise für Coding-Agents

Quelle der Wahrheit für Fachliches: `docs/architecture.md`. Modulgrenzen: `docs/module-grenzen.md` (erzwungen durch `uv run lint-imports`). Code-Konventionen: `docs/conventions/coding.md`. Logging: `docs/conventions/logging.md`. Entscheidungen: `docs/adr/`.

## Struktur (nicht verhandelbar)

- Modularer Monolith: ein Deployment, eine PostgreSQL-DB, ein Alembic-Baum. Fachmodule unter `app/modules/<name>/` mit `enums`, `models`, `schemas`, `repository`, `service`, `router`, `events`.
- **Neues Modul nur mit `mono module <name> --imports <a,b>`** (optional `--entity Name`, `--responsibility "…"`). Das Kommando legt alle Dateien an, trägt das Modul in `docs/module-grenzen.md`, `app/main.py` und `app/core/model_registry.py` ein und erzeugt die import-linter-Contracts. Nie von Hand nachbauen. Nach einer Änderung der Modultabelle: `mono contracts`.
- Schreiben nur über den Service des besitzenden Moduls. Repository und Models eines Moduls sind privat. Fremde Module nur über deren `service`.
- Services und Router committen nie; die Commit-Grenze ist die Anfrage (`TransactionMiddleware`) bzw. der Job.
- Folgeobjekte in anderen Modulen entstehen über `app/core/domain_events.py` (synchron, gleiche Transaktion); Handler liegen in `app/modules/<ziel>/events.py`.
- Modulübergreifende Lesesichten gehören nach `app/read_models/`, nie in einen Service.
- Fachfehler nur als `AppError`-Unterklassen; Antwort `{code, message}`, Meldung deutsch.
- Geld nur als `Decimal` über `app/core/money.py`.

## Ablauf einer Aufgabe

1. Zuerst lesen: `docs/architecture.md`, `docs/module-grenzen.md`, `docs/interfaces/<modul>.md` des betroffenen Moduls.
2. Fehlerbehebung: erst der Test, der den Fehler zeigt und rot ist, dann der Fix, dann Mutationsprobe (Fix kurz zurücknehmen, Test muss wieder rot werden).
3. Feature: Service zuerst (mit Tests), dann Router, dann Doku in `docs/interfaces/<modul>.md`. Braucht es eine Grundsatzentscheidung, eine ADR unter `docs/adr/` anlegen und in `docs/adr/README.md` eintragen.
4. Migration: `uv run alembic revision --autogenerate -m "<modul>-<zweck>"`, Datei prüfen (Constraint-Namen, FK-Index), `upgrade head`, `downgrade -1`, `upgrade head`. Eine Migration zur Zeit, nie parallel.
5. **Gate vor jedem Merge: `bash scripts/check.sh`** (Windows `scripts/check.ps1`). Ruff über den ganzen Bestand, `lint-imports`, pytest. Rot heißt nicht fertig.
6. Handoff: geänderte Dateien, Belege (Befehl → Ergebnis), offene Fragen. Eine für Benutzer sichtbare Änderung ändert die Doku im selben Commit.

## Verboten

- `session.commit()` in `service.py` oder `router.py`.
- Import von `app.modules.<fremd>.repository` oder `.models` aus einem anderen Modul.
- Neue `ignore_imports`-Zeile ohne Kommentar und Grund; Contracts von Hand ändern.
- PATCH auf `status`; Statuswechsel sind POST-Aktionen (`/{id}/confirm`, `/cancel`).
- Natives Postgres-ENUM, `float` für Geld, Tests gegen SQLite, `CURRENT_DATE` statt `(now() AT TIME ZONE 'Europe/Berlin')::date`.
- Externer Aufruf (LLM, HTTP, Mail) unter gehaltener Zeilensperre.
- Logging von Passwörtern, Tokens, Query-Strings, Bodies, Namen, Adressen.

## Werkzeuge

`uv` für Python (nie pip), `bun` für Frontend/Skripte (nie npm). Postgres per `docker compose up -d postgres` (Passwort aus `.env`). Tests brauchen `TEST_DATABASE_URL` mit DB-Name auf `_test`; je Arbeitskopie eine eigene Test-DB. Alembic per CLI liest `DATABASE_URL`: in Worktrees immer `DATABASE_URL=<test-db> uv run alembic …`, sonst migriert man die Dev-DB.

## Sprache

Code-Identifier englisch. Docstrings, Kommentare, Doku, Fehlermeldungen, Commit-Texte deutsch. Ein Test nennt im Namen den Fehler, den er fängt.
