"""Rundung kaufmännisch; erwartete Werte als Literal, nie als Nachrechnung mit derselben Formel."""

from __future__ import annotations

from decimal import Decimal

from app.core.money import line_net, quantize_money


def test_halbe_cent_runden_auf() -> None:
    assert quantize_money(Decimal("1.005")) == Decimal("1.01")
    assert quantize_money(Decimal("2.675")) == Decimal("2.68")


def test_vier_stellen_fuer_einzelpreise() -> None:
    assert quantize_money(Decimal("0.12345"), places=4) == Decimal("0.1235")


def test_positionswert_mit_rabatt_und_faktor() -> None:
    assert line_net(Decimal("3"), Decimal("100"), Decimal("10")) == Decimal("270.00")
    assert line_net(Decimal("2"), Decimal("50"), factor=Decimal("0.5")) == Decimal("50.00")
