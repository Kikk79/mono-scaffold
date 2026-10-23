"""Geld: `Numeric(18, 4)` in der DB, `Decimal` im Code, nie float.

`quantize_money` ist die einzige Rundung für Beträge. Beträge nach dem Runden auf `> 0`
prüfen, damit der Fehler ein 422 ist und kein 409 aus der Datenbank.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Numeric

Money = Numeric(18, 4)

_PLACES = {2: Decimal("0.01"), 4: Decimal("0.0001")}


def quantize_money(value: Decimal | int | str, places: int = 2) -> Decimal:
    """Rundet kaufmännisch (HALF_UP) auf 2 oder 4 Stellen."""
    return Decimal(value).quantize(_PLACES[places], rounding=ROUND_HALF_UP)


def line_net(
    qty: Decimal,
    unit_price: Decimal,
    discount_pct: Decimal = Decimal(0),
    factor: Decimal = Decimal(1),
) -> Decimal:
    """Positionswert: qty × Faktor × Einzelpreis × (1 − Rabatt %), auf 2 Stellen."""
    return quantize_money(qty * factor * unit_price * (Decimal(1) - discount_pct / Decimal(100)))
