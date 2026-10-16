"""Validation rules of the catalog models."""
import pytest
from pydantic import ValidationError

from emporio.domain.catalog import Product
from tests.factories import product_row


@pytest.mark.parametrize(
    "overrides",
    [
        {"price_brl": "0"},
        {"price_brl": "10.001"},
        {"stock_quantity": -1},
    ],
    ids=["zero price", "sub-cent price", "negative stock"],
)
def test_product_rejects_invalid_values(overrides: dict[str, object]):
    with pytest.raises(ValidationError):
        _ = Product.model_validate(product_row(**overrides))
