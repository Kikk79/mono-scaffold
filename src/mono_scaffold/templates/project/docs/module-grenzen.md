# Modulgrenzen

Verbindlich mit [ADR-0002](adr/0002-modulgrenzen.md). Fachliche Quelle der Wahrheit: [`architecture.md`](architecture.md).

Stack: Python 3.12, FastAPI, SQLAlchemy 2.0 sync + psycopg3, Alembic, PostgreSQL 16, Pydantic v2, pytest.

## Module und Abhängigkeiten

**Diese Tabelle ist die Quelle der Wahrheit.** `mono module <name> --imports …` trägt neue Module ein, `mono contracts` erzeugt daraus die import-linter-Contracts in `pyproject.toml`. Eine Änderung der Tabelle ohne `mono contracts` ist ein Fehler; `uv run lint-imports` zeigt ihn.

Richtung immer: `core` ← Stammdaten ← Belegmodule ← Folgemodule. Ein Modul darf von fremden Modulen **nur deren Services** nutzen, nie `models` (außer FK-Typen in `models.py`) und nie `repository`.

| Modul | Verantwortung | Darf importieren |
|-------|---------------|------------------|
| `core` | Config, Session, Exceptions, Money, Mixins, Pagination, Logging, Ereignisbus | — |
<!-- mono:modules-begin -->
<!-- mono:modules-end -->
| `read_models` | Gemeinsame, schreibgeschützte Belegfluss- und Listenabfragen | core sowie ORM-Modelle und Schemas der gelesenen Module; keine Services/Repositories |

Jede Ausnahme steht hier mit Grund (und in `pyproject.toml` nur als kommentierte `ignore_imports`-Zeile), nie still im Code.

## Paket je Fachmodul

`enums`, `models`, `schemas`, `repository`, `service`, `router`, `events`.

- **Repository ist privat.** Nur Queries, keine Business-Regeln. Fremde Module importieren weder `modules.x.repository` noch `modules.x.models`.
- **Service** ist die einzige Schreibstelle des Moduls und committet nie.
- **Router** macht HTTP unter `/api/v1/<modul>` und ruft nur den Service.
- SQLAlchemy-Relationships sind im besitzenden Modell erlaubt; fremde Modelle fasst kein Service an.

## Vier Regeln (ADR-0002)

1. Schreiben nur über den Service des besitzenden Moduls.
2. Geteilte Ressourcen haben genau einen Schreibweg, in derselben Transaktion (hier eintragen, z. B. „Nummern nur `numbering.next()`“).
3. Modulübergreifende Lesesichten liegen in `app/read_models/`: lesen fremde Modelle, rufen keine fremden Services/Repositories, schreiben nie.
4. Infrastruktur (`app/jobs`, KI-Worker) ruft nur Modul-Services bzw. deren Draft-API, nie fremde Repositories.

Umwandlungen zwischen Belegarten gehören dem Zielmodul (`sales.create_from_quote(quote_id)`); das Quellmodul importiert das Zielmodul nie.

## Modulübergreifende Folgeobjekte

Über den synchronen Ereignisbus `app/core/domain_events.py` (gleiche Session und Transaktion, fehlender Handler wirft). Der Handler liegt in `app/modules/<ziel>/events.py` und wird von `app/main.py` importiert.

## Cross-Module-Schreiben

| Vorgang | Erlaubt | Verboten |
|---------|---------|----------|
| Folgeobjekt in fremdem Modul anlegen | Ereignis + Handler im Zielmodul; direkter Service-Aufruf des Zielmoduls | fremdes Repository/Modell schreiben |
| Fremde Tabelle lesen | `read_models` oder Service-Funktion des Besitzers | `session.query(FremdesModell)` im eigenen Service |
| Statuswechsel | POST-Aktion im Router des Besitzers → Service | PATCH auf `status`; Statusänderung von außen |
