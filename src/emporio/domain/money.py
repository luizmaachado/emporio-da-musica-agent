"""Monetary helpers. All amounts are BRL stored as `Decimal` with two places."""
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def to_money(value: Decimal) -> Decimal:
    """Round to the cent, with halves going up (1.005 -> 1.01)."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)
