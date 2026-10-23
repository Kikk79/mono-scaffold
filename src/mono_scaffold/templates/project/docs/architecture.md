# __TITLE__ – Architektur

Fachliche Quelle der Wahrheit. ADRs unter [`adr/`](adr/README.md) vertiefen die Entscheidungen, [`module-grenzen.md`](module-grenzen.md) hält die Abhängigkeitstabelle, [`conventions/coding.md`](conventions/coding.md) die Arbeitsregeln.

## 1. Zweck

<!-- Wer nutzt das System wofür? Welche Vorgänge laufen darüber? Ein Absatz. -->

## 2. Grundentscheidungen

- **Modularer Monolith** ([ADR-0001](adr/0001-modularer-monolith.md)): ein Deployment, eine PostgreSQL-Datenbank, ein Alembic-Baum. Fachmodule als Pakete unter `app/modules/<name>/`, In-Prozess-Serviceaufrufe, kein Netzwerk zwischen Modulen.
- **Modulgrenzen** ([ADR-0002](adr/0002-modulgrenzen.md)): Schreiben nur über den Service des Besitzers; Repository privat; Grenzen per import-linter erzwungen.
- **Transaktion und Ereignisse** ([ADR-0003](adr/0003-transaktion-und-ereignisse.md)): Commit-Grenze ist die Anfrage bzw. der Job; Folgeobjekte über den synchronen Ereignisbus in derselben Transaktion.

## 3. Aufbau

```
app/main.py            Composition Root
app/core/              Kern, importiert kein Fachmodul
app/modules/<name>/    enums · models · schemas · repository · service · router · events
app/read_models/       modulübergreifende Lesesichten
app/jobs/              idempotente CLI-Kommandos
```

## 4. Module

Siehe Tabelle in [`module-grenzen.md`](module-grenzen.md). Reihenfolge beim Aufbau: `auth` → Stammdaten → Belegmodule → Folgemodule → `read_models`.

## 5. Belegfluss

<!-- Welche Belegarten gibt es, wie gehen sie ineinander über, wer besitzt die Umwandlung? -->

## 6. Schnittstellen nach außen

HTTP-API unter `/api/v1/<modul>/…` (OpenAPI führend). Externe Clients (Frontend, MCP-Server, Integrationen) sprechen nur diese API und liegen außerhalb von `app/`.
