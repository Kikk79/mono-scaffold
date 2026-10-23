"""Einzige Stelle, die alle Fachmodelle importiert (für Alembic und den Mapper).

Dauerhaft begründete Ausnahme vom Contract `core` (siehe `ignore_imports` in pyproject.toml).
`mono module …` trägt neue Module hier ein; nichts von Hand ändern.
"""

from __future__ import annotations

from app.core.models import Base

# mono:models-begin
# mono:models-end

metadata = Base.metadata
