"""Product search and category listing, over the available catalog by default."""
from collections.abc import Iterable
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from emporio.domain.catalog import Availability, Category, Product
from emporio.domain.errors import InvalidPriceRange, UnknownCategory
from emporio.domain.pricing import PriceBreakdown, Promotion
from emporio.domain.text import normalize_text
from emporio.services.pricing import PricingService


class StringType(StrEnum):
    """String material of guitars and ukuleles (basses and electric guitars have a count)."""

    NYLON = "nylon"
    STEEL = "steel"


class SortOrder(StrEnum):
    """Sorting is always by final price; ties are broken by product name."""

    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"


class ProductFilters(BaseModel):
    """Every filter is optional and filters combine with AND.

    - `query`: every word must appear in the product name (which carries the brand), its
      description or its category name, ignoring case and accents. An empty query does not
      filter by text.
    - `min_price` / `max_price`: inclusive, applied to the final price (promotion included).
    - `color`: exact match on the color name, ignoring case and accents.
    - `electronics`: whether an acoustic guitar or ukulele has a pickup (is electro-acoustic).
      `True` keeps those that do, `False` the purely acoustic ones. Products with no
      `electronics` spec (electric guitars, basses, drums, keyboards) match neither.
    - `include_unavailable`: also return out-of-stock and unavailable products.
    """

    model_config = ConfigDict(frozen=True)

    query: str | None = None
    category_id: int | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    string_type: StringType | None = None
    color: str | None = None
    electronics: bool | None = None
    include_unavailable: bool = False
    sort: SortOrder = SortOrder.PRICE_ASC


class SearchItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    product: Product  # carries its `availability`
    price: PriceBreakdown


class SearchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[SearchItem]


class CategorySummary(BaseModel):
    """A category with what is currently available in it, so the agent knows what to ask for."""

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    description: str
    available_products: int
    colors: list[str]


_ELECTRONICS_SPEC = {True: "yes", False: "no"}


class ProductSearchService:
    def __init__(
        self,
        products: Iterable[Product],
        categories: Iterable[Category],
        promotions: Iterable[Promotion],
    ) -> None:
        """Prices come from a `PricingService` built here, so products and prices always agree."""
        self._products = list(products)
        self._categories = {category.id: category for category in categories}
        self._pricing = PricingService(self._products, promotions)

    def search(self, filters: ProductFilters) -> SearchResult:
        """Products matching every filter. No match is an empty result, not an error.

        Raises:
            UnknownCategory: `UNKNOWN_CATEGORY`, when `category_id` does not exist.
            InvalidPriceRange: `INVALID_PRICE_RANGE`, when `min_price` exceeds `max_price`.
        """
        if filters.category_id is not None and filters.category_id not in self._categories:
            raise UnknownCategory(filters.category_id)
        if (
            filters.min_price is not None
            and filters.max_price is not None
            and filters.min_price > filters.max_price
        ):
            raise InvalidPriceRange

        items = [
            SearchItem(
                product=product,
                price=self._pricing.get_price(product.id),
            )
            for product in self._products
            if self._matches_product(product, filters)
        ]
        items = [item for item in items if _matches_price(item.price, filters)]
        descending = filters.sort is SortOrder.PRICE_DESC
        # Two stable passes: name first, so equal prices keep name order in both directions.
        items.sort(key=lambda item: item.product.name)
        items.sort(key=lambda item: item.price.final_price, reverse=descending)
        return SearchResult(items=items)

    def list_categories(self) -> list[CategorySummary]:
        """Every category, including empty ones; counts and colors cover available products."""
        summaries: list[CategorySummary] = []
        for category in self._categories.values():
            available = [
                product
                for product in self._products
                if product.category_id == category.id
                and product.availability is Availability.AVAILABLE
            ]
            colors = {product.specs["color"] for product in available if "color" in product.specs}
            summaries.append(
                CategorySummary(
                    id=category.id,
                    name=category.name,
                    description=category.description,
                    available_products=len(available),
                    colors=sorted(colors),
                )
            )
        return summaries

    def _matches_product(self, product: Product, filters: ProductFilters) -> bool:
        if not filters.include_unavailable and product.availability is not Availability.AVAILABLE:
            return False
        if filters.category_id is not None and product.category_id != filters.category_id:
            return False
        if filters.string_type is not None and product.specs.get("strings") != filters.string_type:
            return False
        if filters.color is not None and not _same_text(product.specs.get("color"), filters.color):
            return False
        if (
            filters.electronics is not None
            and product.specs.get("electronics") != _ELECTRONICS_SPEC[filters.electronics]
        ):
            return False
        return filters.query is None or self._matches_query(product, filters.query)

    def _matches_query(self, product: Product, query: str) -> bool:
        category = self._categories.get(product.category_id)
        category_name = category.name if category else ""
        text = normalize_text(f"{product.name} {product.description} {category_name}")
        return all(word in text for word in normalize_text(query).split())


def _same_text(left: str | None, right: str) -> bool:
    return left is not None and normalize_text(left) == normalize_text(right)


def _matches_price(price: PriceBreakdown, filters: ProductFilters) -> bool:
    if filters.min_price is not None and price.final_price < filters.min_price:
        return False
    return filters.max_price is None or price.final_price <= filters.max_price
