# ADR-0001: Modularer Monolith

- Status: akzeptiert
- Datum: __DATE__

## Entscheidung

Ein Deployment, eine PostgreSQL-16-Datenbank, ein Alembic-Baum. Fachmodule als Pakete unter `app/modules/<name>/` mit strikten Grenzen ([ADR-0002](0002-modulgrenzen.md), [module-grenzen.md](../module-grenzen.md)).

## Begründung

Ein Team, überschaubare Last, Vorgänge brauchen **eine** DB-Transaktion über Modulgrenzen (z. B. Beleg buchen → Bestand + Nummer + Folgeobjekt). Die Modularität liegt in der Code-Struktur und wird von Werkzeugen erzwungen, nicht vom Netzwerk.

## Verworfen

- Microservices (Netzwerk zwischen Modulen, verteilte Transaktionen, Betrieb mehrerer Dienste)
- Datenbank pro Modul
- Ein globales `models.py`

## Konsequenzen

- In-Prozess-Serviceaufrufe, keine REST-Calls zwischen Modulen
- Grenzen per import-linter + Review + Tests (`scripts/check.sh`)
- Ein Modul lässt sich später herauslösen, weil es nur über seinen Service und über Ereignisse mit anderen spricht
