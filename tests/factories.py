"""Builders for synthetic domain objects, so rule tests do not depend on the store CSVs."""
from datetime import date
from decimal import Decimal

from emporio.domain.catalog import Product
from emporio.domain.pricing import Promotion


def product_row(**overrides: object) -> dict[str, object]:
    """A valid product as a CSV-style row; overrides use the CSV column names."""
    row: dict[str, object] = {
        "product_id": 1,
        "name": "Test guitar",
        "category_id": 1,
        "description": "Synthetic product for tests",
        "price_brl": "100.00",
        "stock_quantity": 1,
        "status": "active",
        "specs": "{}",
        "created_at": date(2025, 1, 1),
    }
    return row | overrides


def make_product(product_id: int = 1, price: str = "100.00") -> Product:
    """Built with `model_validate`, the same path the loader uses for CSV rows."""
    return Product.model_validate(product_row(product_id=product_id, price_brl=price))


def make_promotion(
    percent: str,
    product_id: int = 1,
    promotion_id: int = 1,
    is_active: bool = True,
    description: str | None = None,
) -> Promotion:
    return Promotion(
        promotion_id=promotion_id,
        product_id=product_id,
        discount_percent=Decimal(percent),
        description=description or f"{percent}% off",
        is_active=is_active,
    )
