"""ORM-Modelle von `__MODULE__`. Privat: kein anderes Modul importiert diese Datei.

Constraint-Namen explizit (`uq_`, `ck_`, `ix_`), Enums als VARCHAR + CHECK, Pflichtspalten
über `EntityMixin`. FKs auf fremde Tabellen sind hier erlaubt (nur hier).
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, EntityMixin
from app.modules.__MODULE__.enums import __ENTITY__Status


class __ENTITY__(EntityMixin, Base):
    __tablename__ = "__ENTITY_SNAKE__"
    __table_args__ = (
        UniqueConstraint("name", name="uq___ENTITY_SNAKE___name"),
        CheckConstraint(
            "status IN ('" + "', '".join(s.value for s in __ENTITY__Status) + "')",
            name="status",  # wird zu ck___ENTITY_SNAKE___status
        ),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[__ENTITY__Status] = mapped_column(
        String(20), nullable=False, default=__ENTITY__Status.ACTIVE
    )
