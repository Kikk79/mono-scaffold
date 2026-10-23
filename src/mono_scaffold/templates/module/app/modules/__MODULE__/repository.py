"""Repository von `__MODULE__`: nur Queries, keine Business-Regeln, privat."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.__MODULE__.enums import __ENTITY__Status
from app.modules.__MODULE__.models import __ENTITY__


def get(session: Session, entity_id: uuid.UUID) -> __ENTITY__ | None:
    return session.get(__ENTITY__, entity_id)


def get_for_update(session: Session, entity_id: uuid.UUID) -> __ENTITY__ | None:
    """Zeilensperre für Statuswechsel. Sperrreihenfolge: siehe ADR-0003."""
    stmt = (
        select(__ENTITY__)
        .where(__ENTITY__.id == entity_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return session.execute(stmt).scalar_one_or_none()


def find_by_name(session: Session, name: str) -> __ENTITY__ | None:
    stmt = select(__ENTITY__).where(func.lower(__ENTITY__.name) == name.lower())
    return session.execute(stmt).scalar_one_or_none()


def list_page(
    session: Session,
    *,
    limit: int,
    offset: int,
    status: __ENTITY__Status | None = None,
) -> tuple[list[__ENTITY__], int]:
    stmt = select(__ENTITY__)
    if status is not None:
        stmt = stmt.where(__ENTITY__.status == status)
    total = session.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    page = stmt.order_by(__ENTITY__.name).limit(limit).offset(offset)
    items = session.execute(page).scalars().all()
    return list(items), total
