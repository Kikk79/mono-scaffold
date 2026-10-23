# ADRs – Architecture Decision Records

Quelle der Wahrheit: [`docs/architecture.md`](../architecture.md). ADRs vertiefen sie, ersetzen sie nicht. Bei Widerspruch gilt architecture.md, bis die ADR-Änderung übernommen ist.

Eine neue ADR bei jeder Grundsatzentscheidung (nicht bei jedem Feature): Dateiname `NNNN-kurztitel.md`, Abschnitte Status · Datum · Entscheidung · Begründung · Verworfen · Konsequenzen. Hier eintragen.

| ADR | Titel | Kurz |
|-----|-------|------|
| [0001](0001-modularer-monolith.md) | Modularer Monolith | Ein Deployment, eine PostgreSQL-DB, Fachmodule unter `app/modules/<name>/`. |
| [0002](0002-modulgrenzen.md) | Modulgrenzen | Schreiben nur über den Service des Besitzers; Repository privat; import-linter erzwingt die Tabelle. |
| [0003](0003-transaktion-und-ereignisse.md) | Transaktion und Ereignisse | Commit-Grenze ist die Anfrage bzw. der Job; Folgeobjekte über den synchronen Ereignisbus. |
