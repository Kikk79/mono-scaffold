"""${message}

Revision: ${up_revision}
Vorgänger: ${down_revision | comma,n}
Datum: ${create_date}

Schema und Daten-Backfill getrennt halten; neue FK-Spalten bekommen hier einen Index
(`ix_…`) oder im Handoff den Grund dagegen. Downgrade stellt Views wortgleich wieder her.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
