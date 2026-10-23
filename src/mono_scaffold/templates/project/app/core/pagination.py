"""Seitenweise Listen: `?limit=&offset=` → `Page[T]` mit `items`, `total`, `limit`, `offset`."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)


def _pagination(
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


Pagination = Annotated[PaginationParams, Depends(_pagination)]


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
