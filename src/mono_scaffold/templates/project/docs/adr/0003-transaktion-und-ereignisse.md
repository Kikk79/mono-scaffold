# ADR-0003: Transaktion und Ereignisse

- Status: akzeptiert
- Datum: __DATE__

## Entscheidung

- **Commit-Grenze ist die Anfrage.** `TransactionMiddleware` committet die Session, sobald der Handler eine Antwort < 400 erzeugt hat, sonst Rollback. Services und Router committen nie (Test `test_services_und_router_committen_nicht`). Jobs unter `app/jobs/` sind ihre eigene Commit-Grenze.
- **Folgeobjekte über den synchronen Ereignisbus** (`app/core/domain_events.py`): gleiche Session, gleiche Transaktion, kein Nachlaufjob, keine Outbox. Ein Handler-Fehler rollt den ganzen Vorgang zurück. Ein Ereignis ohne Handler wirft.
- **Sperrreihenfolge** projektweit einheitlich und hier festzuhalten (Vorlage: Projekt → Belegkopf → Zeilen → Nummernkreis/Bestand). Repositories bieten `get_x_for_update`; Services sperren nicht selbst. Externe Aufrufe (LLM, HTTP, Mail) laufen vor der Sperre.
- **Geld** als `Numeric(18,4)`/`Decimal`, Rundung nur über `app/core/money.py`.

## Begründung

Ein Commit im Service macht Vorgänge unteilbar testbar und erzeugt Teilbuchungen bei Fehlern. Ein Commit vor dem Senden der Antwort verhindert eine 2xx für etwas, das nie geschrieben wurde. Synchrone Ereignisse in derselben Transaktion sind konsistent, ohne dass eine Outbox oder ein Broker betrieben werden muss.

## Verworfen

- Commit in Services („damit es sicher gespeichert ist“)
- Asynchrone Ereignisse / Message Broker
- Celery oder ein eigener Worker-Prozess für Jobs

## Konsequenzen

- Jeder Handler muss schnell und frei von externen Aufrufen sein.
- Wer eine eigene Session mit eigenem Commit braucht (z. B. ein Zähler, der auch bei Rollback stehen bleiben muss), dokumentiert das hier als Ausnahme.
