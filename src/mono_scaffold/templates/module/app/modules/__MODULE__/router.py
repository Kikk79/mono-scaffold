"""HTTP für `__MODULE__` unter /api/v1/__MODULE__. Ruft nur den Service.

Statuswechsel sind POST-Aktionen (`/{id}/deactivate`), kein PATCH auf `status`.
Rollenprüfung: sobald das Modul `auth` existiert, `Depends(require_roles("…"))` an die
schreibenden Endpunkte hängen (docs/conventions/coding.md).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.pagination import Page, Pagination
from app.modules.__MODULE__ import service
from app.modules.__MODULE__.enums import __ENTITY__Status
from app.modules.__MODULE__.schemas import (
    __ENTITY__In,
    __ENTITY__Out,
    __ENTITY__UpdateIn,
)

router = APIRouter(prefix="/api/v1/__MODULE__", tags=["__MODULE__"])

DbSession = Annotated[Session, Depends(get_db)]
StatusFilter = Annotated[__ENTITY__Status | None, Query(alias="status")]


@router.get("", response_model=Page[__ENTITY__Out])
def list___MODULE__(
    session: DbSession, page: Pagination, status_filter: StatusFilter = None
) -> Page[__ENTITY__Out]:
    items, total = service.list___MODULE__(
        session, limit=page.limit, offset=page.offset, status=status_filter
    )
    return Page(
        items=[__ENTITY__Out.model_validate(i) for i in items],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.post("", response_model=__ENTITY__Out, status_code=status.HTTP_201_CREATED)
def create___ENTITY_SNAKE__(session: DbSession, data: __ENTITY__In) -> __ENTITY__Out:
    entity = service.create___ENTITY_SNAKE__(session, data)
    return __ENTITY__Out.model_validate(entity)


@router.get("/{entity_id}", response_model=__ENTITY__Out)
def get___ENTITY_SNAKE__(session: DbSession, entity_id: uuid.UUID) -> __ENTITY__Out:
    entity = service.get___ENTITY_SNAKE__(session, entity_id)
    return __ENTITY__Out.model_validate(entity)


@router.patch("/{entity_id}", response_model=__ENTITY__Out)
def update___ENTITY_SNAKE__(
    session: DbSession,
    entity_id: uuid.UUID,
    data: __ENTITY__UpdateIn,
) -> __ENTITY__Out:
    entity = service.update___ENTITY_SNAKE__(session, entity_id, data)
    return __ENTITY__Out.model_validate(entity)


@router.post("/{entity_id}/deactivate", response_model=__ENTITY__Out)
def deactivate___ENTITY_SNAKE__(
    session: DbSession,
    entity_id: uuid.UUID,
) -> __ENTITY__Out:
    entity = service.deactivate___ENTITY_SNAKE__(session, entity_id)
    return __ENTITY__Out.model_validate(entity)
