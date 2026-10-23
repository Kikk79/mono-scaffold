"""Synchroner In-Process-Ereignisbus (ADR-0003).

Ein Fachmodul meldet ein Ereignis mit `publish`; Handler anderer Module laufen im selben
Aufruf, in derselben Session und Transaktion. Ausnahmen eines Handlers laufen zum Aufrufer
durch, die Transaktion rollt dann als Ganzes zurück. Kein Nachlaufjob, keine Outbox.

`app.core` importiert kein Fachmodul: Handler melden sich beim Import ihres Moduls an
(`register` in `app/modules/<name>/events.py`; `app/main.py` importiert diese Datei).
Hat ein Ereignis keinen Handler, wirft `publish`, damit nie still ein Folgeobjekt ausbleibt.

Payloads sind eingefrorene Dataclasses mit IDs, Nummern und Beträgen – nie ORM-Objekte.
Ereignisnamen: `<modul>.<vergangenheitsform>`, z. B. `sales.invoice_posted`.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

Handler = Callable[[Session, Any, Any], None]  # (session, actor, payload)

_handlers: defaultdict[str, list[Handler]] = defaultdict(list)


class EventWithoutHandlerError(RuntimeError):
    """Ein Ereignis wurde gemeldet, für das sich kein Modul angemeldet hat."""


def register(event_name: str, handler: Handler) -> None:
    """Meldet einen Handler an (beim Import des Moduls aufrufen)."""
    if handler not in _handlers[event_name]:
        _handlers[event_name].append(handler)


def publish(event_name: str, session: Session, *, actor: Any, payload: Any) -> None:
    """Ruft alle Handler synchron in derselben Transaktion."""
    handlers = _handlers.get(event_name)
    if not handlers:
        raise EventWithoutHandlerError(
            f"Ereignis `{event_name}` hat keinen Handler. "
            "Ist die `events.py` des Zielmoduls in app/main.py importiert?"
        )
    for handler in handlers:
        handler(session, actor, payload)


def has_handler(event_name: str) -> bool:
    return bool(_handlers.get(event_name))
