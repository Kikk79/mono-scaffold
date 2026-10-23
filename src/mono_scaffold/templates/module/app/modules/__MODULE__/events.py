"""Ereignisse von `__MODULE__` (ADR-0003).

Hier stehen (a) die Ereignisse, die dieses Modul meldet, und (b) die Handler für Ereignisse
anderer Module. `app/main.py` importiert diese Datei, damit die Handler registriert sind.

Melden (im Service, nach dem Flush):

    from app.core.domain_events import publish
    publish(DEACTIVATED, session, actor=actor_id, payload=__ENTITY__Deactivated(id=entity.id))

Verarbeiten (ein Ereignis eines anderen Moduls, z. B. `sales.invoice_posted`):

    def _on_invoice_posted(session: Session, actor, payload) -> None:
        service.…(session, …)   # nur der eigene Service schreibt
    register("sales.invoice_posted", _on_invoice_posted)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

DEACTIVATED = "__MODULE__.__ENTITY_SNAKE___deactivated"


@dataclass(frozen=True)
class __ENTITY__Deactivated:
    """Payload von `__MODULE__.__ENTITY_SNAKE___deactivated`."""

    id: uuid.UUID
