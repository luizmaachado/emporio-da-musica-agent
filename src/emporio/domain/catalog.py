"""Catalog models: products and their status.

Field aliases match the CSV column names, so a CSV row can be validated directly.
"""
from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, Json, computed_field


class ProductStatus(StrEnum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    COMING_SOON = "coming_soon"


class Availability(StrEnum):
    """What a customer can do with a product right now."""

    AVAILABLE = "available"
    OUT_OF_STOCK = "out_of_stock"
    UNAVAILABLE = "unavailable"


class Category(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: int = Field(alias="category_id")
    name: str
    description: str


class Product(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: int = Field(alias="product_id")
    name: str
    category_id: int
    description: str
    price: Decimal = Field(alias="price_brl", gt=0, decimal_places=2)
    stock: int = Field(alias="stock_quantity", ge=0)
    status: ProductStatus
    # Parsed from the JSON text in the CSV. Keys differ by category, and `strings` is a
    # material for guitars but a count for basses.
    specs: Json[dict[str, str]]
    created_at: date

    @computed_field
    @property
    def availability(self) -> Availability:
        """Active with stock is available; active without stock is out of stock.

        Any other status is unavailable: discontinued and upcoming products are never offered.
        """
        if self.status is not ProductStatus.ACTIVE:
            return Availability.UNAVAILABLE
        return Availability.AVAILABLE if self.stock > 0 else Availability.OUT_OF_STOCK
