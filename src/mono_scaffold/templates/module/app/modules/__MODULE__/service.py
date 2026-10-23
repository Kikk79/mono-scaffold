"""Geschäftslogik von `__MODULE__`. Einzige Schreibstelle des Moduls. Kein Commit.

Andere Module rufen nur diese Funktionen, nie das Repository (Schnittstelle: siehe
docs/interfaces/). Fachereignisse werden über `log_after_commit` erst nach dem Commit geloggt.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.core.logging import log_after_commit
from app.modules.__MODULE__ import repository as repo
from app.modules.__MODULE__.enums import __ENTITY__Status
from app.modules.__MODULE__.models import __ENTITY__
from app.modules.__MODULE__.schemas import (
    __ENTITY__In,
    __ENTITY__UpdateIn,
)

logger = logging.getLogger(__name__)


def _flush(session: Session) -> None:
    """flush; Unique-Verletzung → 409 mit Hinweis statt DB-Fehler."""
    try:
        with session.begin_nested():
            session.flush()
    except IntegrityError as exc:
        raise ConflictError("Es gibt schon einen Eintrag mit diesem Namen.") from exc


def get___ENTITY_SNAKE__(session: Session, entity_id: uuid.UUID) -> __ENTITY__:
    entity = repo.get(session, entity_id)
    if entity is None:
        raise NotFoundError("__ENTITY__ nicht gefunden.")
    return entity


def list___MODULE__(
    session: Session,
    *,
    limit: int,
    offset: int,
    status: __ENTITY__Status | None = None,
) -> tuple[list[__ENTITY__], int]:
    return repo.list_page(session, limit=limit, offset=offset, status=status)


def create___ENTITY_SNAKE__(
    session: Session,
    data: __ENTITY__In,
    *,
    actor_id: uuid.UUID | None = None,
) -> __ENTITY__:
    name = data.name.strip()
    if not name:
        raise ValidationAppError("Name darf nicht leer sein.")
    entity = __ENTITY__(
        name=name,
        status=__ENTITY__Status.ACTIVE,
        created_by=actor_id,
        updated_by=actor_id,
    )
    session.add(entity)
    _flush(session)
    log_after_commit(session, logger, "__MODULE__.created", id=entity.id)
    return entity


def update___ENTITY_SNAKE__(
    session: Session,
    entity_id: uuid.UUID,
    data: __ENTITY__UpdateIn,
    *,
    actor_id: uuid.UUID | None = None,
) -> __ENTITY__:
    entity = get___ENTITY_SNAKE__(session, entity_id)
    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise ValidationAppError("Name darf nicht leer sein.")
        entity.name = name
    entity.updated_by = actor_id
    _flush(session)
    return entity


def deactivate___ENTITY_SNAKE__(
    session: Session,
    entity_id: uuid.UUID,
    *,
    actor_id: uuid.UUID | None = None,
) -> __ENTITY__:
    """Statuswechsel ACTIVE → INACTIVE unter Zeilensperre; idempotent abgelehnt mit 409."""
    entity = repo.get_for_update(session, entity_id)
    if entity is None:
        raise NotFoundError("__ENTITY__ nicht gefunden.")
    if entity.status == __ENTITY__Status.INACTIVE:
        raise ConflictError("__ENTITY__ ist schon deaktiviert.")
    entity.status = __ENTITY__Status.INACTIVE
    entity.updated_by = actor_id
    _flush(session)
    log_after_commit(session, logger, "__MODULE__.deactivated", id=entity.id)
    return entity
