# Konvention: Code und Arbeitsweise

- Zweck: Kurzfassung der verbindlichen Regeln, damit Code aus Hauptsession und Agents gleich aussieht.
- Quelle der Wahrheit bleibt die jeweils genannte Datei. Widerspricht diese Seite ihr, gilt die Quelle; diese Seite dann nachziehen.

## Werkzeuge

- Python nur mit `uv`, Python 3.12, nie pip. ruff: `target-version = "py312"`, `line-length = 100`.
- Gate vor jedem Merge: `scripts/check.sh` (Windows: `scripts/check.ps1`). Drei Schritte, die alle laufen, auch wenn einer scheitert: ruff über den ganzen Bestand, `lint-imports`, pytest. Ein neuer ruff-Befund irgendwo macht das Gate rot.
- `ruff check --fix` und `ruff format` nur mit expliziten Dateien aufrufen, nie auf Bestandsverzeichnisse.
- CI (`.github/workflows/gate.yml`): `check.sh` gegen einen Postgres-Service, bei Pull Requests, nächtlich und per `gh workflow run gate.yml`.

## Architektur und Modulgrenzen

Quellen: [module-grenzen.md](../module-grenzen.md), [ADR-0001](../adr/0001-modularer-monolith.md), [ADR-0002](../adr/0002-modulgrenzen.md).

- Modularer Monolith: FastAPI, SQLAlchemy 2.0 sync + psycopg3, Pydantic v2, Alembic, PostgreSQL 16.
- Jedes Fachmodul liegt unter `app/modules/<name>/` mit `enums`, `models`, `schemas`, `repository`, `service`, `router`, `events`. Repositories enthalten nur Queries; Business-Logik steht im Service.
- Geschrieben wird nur über den Service des besitzenden Moduls. Fremde `repository`/`models` werden nie importiert. Fremde `schemas` darf nur `app/read_models` importieren.
- Neues Modul nur über `mono module <name> --imports …`. `import-linter` erzwingt die Tabelle; neue Verstöße nicht per `ignore_imports` wegdrücken.
- Modulübergreifende Lesesichten liegen in `app/read_models/`: nur lesen, keine fremden Services oder Repositories.
- `app/jobs` ist Infrastruktur und ruft Modul-Services. Jobs sind idempotente CLI-Kommandos, kein Celery.

## Backend

- Commit-Grenze einer Anfrage ist die `TransactionMiddleware`, eines Jobs der Job selbst; Services und Router committen nicht, ohne Ausnahme (Test `test_services_und_router_committen_nicht`).
- Sperrreihenfolge in allen Modulen einheitlich ([ADR-0003](../adr/0003-transaktion-und-ereignisse.md)). Repositories stellen `get_…_for_update` bereit; Services sperren nicht selbst. Langsame Aufrufe laufen vor der Sperre; danach sperren, Idempotenz erneut prüfen, dann schreiben.
- Fachfehler nur als `AppError`-Unterklassen aus `app/core/exceptions.py`: `NotFoundError` 404, `ConflictError` 409, `ValidationAppError` 422, `ForbiddenError` 403. Antwort ist JSON `{code, message}`. Fehlermeldungen sind deutsch und sagen dem Anwender, was zu tun ist. Ein `IntegrityError` beim Flush wird zu `ConflictError`.
- Logging nach [logging.md](logging.md): Logger je Modul, Fachereignisse im Service über `log_after_commit`, Ablehnungen direkt über `log_event`.
- Geld: `Money = Numeric(18, 4)`, gerundet über `app/core/money.py`; Geldeingaben nach dem Runden auf `> 0` prüfen (422 statt DB-409).
- API unter `/api/v1/<modul>/…`. Statuswechsel sind POST-Aktionen (`…/{id}/post`, `/confirm`, `/cancel`), kein PATCH auf `status`. Listen nutzen `app.core.pagination`.
- Feature-Flags: kein Framework. Ein riskanter neuer Endpunkt bekommt ein `bool`-Setting in `app/core/config.py` mit sicherem Default (aus in `production`); der Schalter lebt nur bis zur Freigabe.

## Datenbank

- Constraint-Namen: `ix_`, `uq_<tabelle>_<spalte>`, `ck_<tabelle>_<name>`, `fk_<tabelle>_<spalte>_<ziel>`, `pk_<tabelle>`; höchstens 63 Zeichen (Namenskonvention in `app/core/models.py`).
- Enums als `VARCHAR` + `CHECK`, nie als natives PostgreSQL-ENUM; in Python `StrEnum`.
- Jede Entitätstabelle hat `id`, `created_at`, `updated_at`, `created_by`, `updated_by` über `EntityMixin`.
- Geschäftsdatum in SQL immer `(now() AT TIME ZONE 'Europe/Berlin')::date`, nie nacktes `CURRENT_DATE`.
- Migrationen: eine zur Zeit. Vorgänger mit `uv run alembic heads` ermitteln. Up/Down/Up testen. Schema und Daten-Backfill getrennt; `CREATE INDEX CONCURRENTLY` nur im `autocommit_block`. Umbenennung in drei Schritten, solange der Dienst während der Migration läuft.
- Jede neue FK-Spalte bekommt in derselben Migration einen Index mit `ix_`-Namen oder im Handoff den Grund, warum nicht.
- Mehrere Zeilen im selben Vorgang immer in derselben Reihenfolge sperren (`ORDER BY id … FOR UPDATE`). Während einer Sperre läuft kein externer Aufruf.

## Tests

- Nur gegen echtes PostgreSQL (`TEST_DATABASE_URL`, Name endet auf `_test`), nie SQLite. Je Arbeitskopie eine eigene Test-DB.
- API-Tests in `tests/api`, Unit-Tests in `tests/unit`. Ein Test nennt im Namen den Fehler, den er fängt (`test_skonto_wird_nicht_doppelt_abgezogen`), nicht die Funktion. Erwartete Werte als Literal, nie als Neuberechnung mit derselben Formel.
- Wettlauf-Tests brauchen committete Daten und zwei echte Sessions; Barriere per `monkeypatch`-Wrapper mit `entered.wait(5)`, nie feste Sleeps.
- Fehlerbehebung: erst der Test, der den Fehler zeigt und rot ist, dann der Fix. Danach den Fix kurz zurücknehmen und prüfen, dass der Test wieder rot wird (Mutationsprobe).
- Kein Test, der nur festhält, dass eine Zeile unverändert dasteht, und keiner, der Mocks statt Verhalten prüft.

## Fehlersuche und Review-Befunde

- Nach drei gescheiterten Fix-Versuchen am selben Fehler anhalten und die Ursache neu suchen. An jeder Schichtgrenze (Router, Service, Repository, DB) den Wert einmal ausgeben, bevor man eine Schicht verdächtigt.
- Befunde eines Reviewers werden geprüft, nicht abgenickt: gegen den Code lesen, dann beheben oder mit Beleg ablehnen. Ein Vorschlag, der nur Umfang hinzufügt, wird abgelehnt.

## Sprache und Dokumentation

- Code-Identifier sind englisch. Docstrings, Kommentare, Doku, Fehlermeldungen und Commit-Texte sind deutsch.
- Fachliche Quelle der Wahrheit ist [architecture.md](../architecture.md). `docs/interfaces/<modul>.md` ist für sein Modul bindend. Abweichungen werden dokumentiert, nicht still umgesetzt.
- Jede Grundsatzentscheidung bekommt eine ADR unter `docs/adr/`.
