# ADR-0002: Modulgrenzen

- Status: akzeptiert
- Datum: __DATE__

## Entscheidung

Vier Regeln, erzwungen durch die Contracts in `pyproject.toml` (erzeugt aus der Tabelle in [module-grenzen.md](../module-grenzen.md)) und `tests/unit/test_architecture.py`:

1. Schreiben nur über den Service des besitzenden Moduls.
2. Geteilte Ressourcen haben genau einen Schreibweg, in derselben Transaktion.
3. Modulübergreifende Lesesichten liegen in `app/read_models/` (lesen, nie schreiben, keine fremden Services).
4. Infrastruktur (`app/jobs`, KI-Worker) ruft nur Modul-Services.

Pro Modul: `enums`, `models`, `schemas`, `repository` (privat), `service` (einzige Schreibstelle, kein Commit), `router` (HTTP), `events` (Handler für Ereignisse anderer Module).

## Begründung

Ohne erzwungene Grenzen wird aus einem Ordnerbaum in Monaten ein Geflecht, in dem jede Änderung drei andere Module bricht. Mit erzwungenen Grenzen bleibt jedes Modul allein verständlich, testbar und für einen Coding-Agenten in einem kleinen Kontext bearbeitbar.

## Verworfen

- Grenzen nur per Konvention (hält kein Review dauerhaft)
- Repositories als öffentliche Schnittstelle (dann fließt Business-Logik in den Aufrufer)
- Gemeinsame „Utils“-Module mit Fachlogik

## Konsequenzen

- Neue Module nur über `mono module <name> --imports …`; die Tabelle ist Quelle der Wahrheit.
- Eine `ignore_imports`-Zeile braucht Grund und Kommentar; ein behobener `TODO(grenzen)` wird gelöscht.
- Ein Modul, das ein fremdes Modell schreiben will, hat ein Modellierungsproblem: Ereignis oder Service-Funktion des Besitzers.
