"""Pricing models: promotions and the resulting price breakdown.

Field aliases match the CSV column names, so a CSV row can be validated directly.
"""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class Promotion(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: int = Field(alias="promotion_id")
    product_id: int
    discount_percent: Decimal = Field(gt=0, le=100)
    description: str
    is_active: bool


class PriceBreakdown(BaseModel):
    """What a customer pays for a product, with the discount kept separate from the list price.

    Without a promotion, `discount_percent` and `discount_amount` are zero and
    `promotion_name` is `None`. `final_price` is `list_price - discount_amount`, so the two
    amounts always add up to the list price. `has_active_promotion` lets callers refuse the
    PIX discount, which does not apply to promotional prices.
    """

    model_config = ConfigDict(frozen=True)

    product_id: int
    list_price: Decimal
    discount_percent: Decimal = Decimal(0)
    discount_amount: Decimal = Decimal("0.00")
    promotion_name: str | None = None
    final_price: Decimal

    @computed_field
    @property
    def has_active_promotion(self) -> bool:
        return self.discount_percent > 0
