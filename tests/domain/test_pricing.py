"""Validation rules of the pricing models."""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from tests.factories import make_promotion


@pytest.mark.parametrize("percent", ["0", "-5", "100.01", "101"])
def test_promotion_rejects_discount_outside_valid_range(percent: str):
    with pytest.raises(ValidationError):
        _ = make_promotion(percent)


@pytest.mark.parametrize("percent", ["0.01", "50", "100"])
def test_promotion_accepts_discount_inside_valid_range(percent: str):
    assert make_promotion(percent).discount_percent == Decimal(percent)
