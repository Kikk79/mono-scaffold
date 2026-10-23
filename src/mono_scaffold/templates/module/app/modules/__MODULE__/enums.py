"""Aufzählungstypen von `__MODULE__`. In der DB `VARCHAR` + `CHECK` (siehe models.py)."""

from __future__ import annotations

from enum import StrEnum


class __ENTITY__Status(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
