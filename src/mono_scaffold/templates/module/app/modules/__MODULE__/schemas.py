"""Pydantic-Schemas von `__MODULE__` (HTTP). Suffixe: In, UpdateIn, Out."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.__MODULE__.enums import __ENTITY__Status


class __ENTITY__In(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class __ENTITY__UpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class __ENTITY__Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: __ENTITY__Status
    created_at: datetime
    updated_at: datetime
