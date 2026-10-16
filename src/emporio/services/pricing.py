"""Product pricing: list price, active promotion and final price."""
from collections.abc import Iterable
from decimal import Decimal

from emporio.domain.catalog import Product
from emporio.domain.errors import ProductNotFound
from emporio.domain.money import to_money
from emporio.domain.pricing import PriceBreakdown, Promotion


def _is_better(candidate: Promotion, current: Promotion) -> bool:
    """The highest discount wins; on a tie, the lowest promotion id."""
    if candidate.discount_percent != current.discount_percent:
        return candidate.discount_percent > current.discount_percent
    return candidate.id < current.id


def _best_promotion_per_product(promotions: Iterable[Promotion]) -> dict[int, Promotion]:
    """Promotions do not stack, so each product keeps only its best active promotion."""
    best: dict[int, Promotion] = {}
    for promotion in promotions:
        if not promotion.is_active:
            continue
        current = best.get(promotion.product_id)
        if current is None or _is_better(promotion, current):
            best[promotion.product_id] = promotion
    return best


class PricingService:
    """Prices products, applying at most one active promotion per product."""

    def __init__(self, products: Iterable[Product], promotions: Iterable[Promotion]) -> None:
        """Inactive promotions are ignored, so callers may pass the full promotions table."""
        self._products = {product.id: product for product in products}
        self._promotion_by_product = _best_promotion_per_product(promotions)

    def get_price(self, product_id: int) -> PriceBreakdown:
        """Price breakdown of a product, whatever its status or stock.

        Discontinued and upcoming products can be priced for lookups; whether they may be
        offered to a customer is decided by the search and detail features, not here.
        The discount is rounded half up to the cent and the final price is derived from it.

        Raises:
            ProductNotFound: `PRODUCT_NOT_FOUND`, when the product id does not exist.
        """
        product = self._products.get(product_id)
        if product is None:
            raise ProductNotFound(product_id)

        promotion = self._promotion_by_product.get(product_id)
        percent = promotion.discount_percent if promotion else Decimal(0)
        discount = to_money(product.price * percent / 100)
        return PriceBreakdown(
            product_id=product.id,
            list_price=product.price,
            discount_percent=percent,
            discount_amount=discount,
            promotion_name=promotion.description if promotion else None,
            final_price=product.price - discount,
        )
