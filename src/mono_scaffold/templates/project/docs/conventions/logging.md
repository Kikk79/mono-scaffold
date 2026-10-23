# Konvention: Betriebs-Logging

Umsetzung: `app/core/logging.py`.

- Standardbibliothek `logging`, Ausgabe nach stderr (journald bzw. Docker sammeln). Format `Zeit Level Logger request_id=… Nachricht`. Level aus `LOG_LEVEL` (Default `INFO`).
- Logger je Modul: `logger = logging.getLogger(__name__)` am Dateianfang.
- Eine Zeile je Anfrage (Methode, Pfad ohne Query-String, Status, Dauer in ms). `request_id` kommt aus `X-Request-ID` oder wird vergeben und steht im Antwort-Header.
- **Fachereignisse** (angelegt, gebucht, storniert) meldet der Service über `log_after_commit(session, logger, "sales.invoice_posted", invoice_id=…)`. Geschrieben wird erst im `after_commit`; bei Rollback verworfen, sonst meldet das Log Buchungen, die es nie gab.
- **Ablehnungen** (409, 422, 403) direkt über `log_event(logger, "…", code=…)`; `AppError` < 500 loggt der Handler als INFO mit `code`, ≥ 500 als ERROR, unbehandelte Ausnahmen als ERROR mit Traceback und Request-ID.
- Erlaubte Felder: IDs, Belegnummern, Status, Beträge, Zähler, Dauer.
- **Nie geloggt:** Authorization-Header, Passwörter, Tokens, Query-Strings, Request-Bodies, Mail-Inhalte, Namen, Adressen. Settings zeigen in Startfehlern keine Werte (`hide_input_in_errors`).
