"""Price breakdown: list price, active promotion and final price."""
from decimal import Decimal

import pytest

from emporio.data.loader import load_active_promotions, load_products
from emporio.domain.errors import ErrorCode, ProductNotFound
from emporio.domain.pricing import Promotion
from emporio.services.pricing import PricingService
from tests.factories import make_product, make_promotion

STORE_PRODUCTS = load_products()


@pytest.fixture(scope="module")
def store_pricing() -> PricingService:
    """Pricing service over the real store data."""
    return PricingService(STORE_PRODUCTS, load_active_promotions())


def pricing_for(*promotions: Promotion, price: str = "100.00") -> PricingService:
    return PricingService([make_product(price=price)], promotions)


def test_product_without_promotion_has_no_discount():
    price = pricing_for().get_price(1)

    assert price.list_price == price.final_price == Decimal("100.00")
    assert price.discount_percent == 0
    assert price.discount_amount == Decimal("0.00")
    assert price.promotion_name is None
    assert price.has_active_promotion is False


def test_product_with_promotion_separates_list_price_discount_and_final_price():
    price = pricing_for(make_promotion("20", description="Black Friday"), price="250.00").get_price(1)

    assert price.list_price == Decimal("250.00")
    assert price.discount_percent == Decimal(20)
    assert price.discount_amount == Decimal("50.00")
    assert price.final_price == Decimal("200.00")
    assert price.promotion_name == "Black Friday"
    assert price.has_active_promotion is True


def test_real_product_with_active_promotion(store_pricing: PricingService):
    # Crafter HT-100: R$ 2.399,00 with 18% off.
    price = store_pricing.get_price(90)

    assert price.list_price == Decimal("2399.00")
    assert price.discount_amount == Decimal("431.82")
    assert price.final_price == Decimal("1967.18")


def test_real_final_price_is_positive_and_never_above_list_price(store_pricing: PricingService):
    prices = [store_pricing.get_price(product.id) for product in STORE_PRODUCTS]

    offenders = [
        price.product_id
        for price in prices
        if not 0 < price.final_price <= price.list_price
        or price.has_active_promotion != (price.final_price < price.list_price)
    ]

    assert offenders == []


@pytest.mark.parametrize(
    ("list_price", "percent", "discount", "final"),
    [
        ("99.99", "15", "15.00", "84.99"),   # 14.9985 rounds up
        ("10.05", "10", "1.01", "9.04"),     # 1.005 rounds half up, not to even
        ("100.00", "33.33", "33.33", "66.67"),
        ("50.00", "100", "50.00", "0.00"),
    ],
)
def test_discount_is_rounded_half_up_to_the_cent(
    list_price: str, percent: str, discount: str, final: str
):
    price = pricing_for(make_promotion(percent), price=list_price).get_price(1)

    assert price.discount_amount == Decimal(discount)
    assert price.final_price == Decimal(final)
    assert price.discount_amount + price.final_price == price.list_price


@pytest.mark.parametrize("percents", [("10", "25"), ("25", "10")], ids=["lowest first", "highest first"])
def test_highest_discount_wins_regardless_of_order(percents: tuple[str, str]):
    promotions = [make_promotion(p, promotion_id=i) for i, p in enumerate(percents, start=1)]

    price = pricing_for(*promotions, price="200.00").get_price(1)

    assert price.discount_percent == Decimal(25)
    assert price.final_price == Decimal("150.00")


@pytest.mark.parametrize("ids", [(1, 2), (2, 1)], ids=["lowest id first", "lowest id last"])
def test_equal_discounts_are_resolved_by_the_lowest_promotion_id(ids: tuple[int, int]):
    promotions = [
        make_promotion("10", promotion_id=promotion_id, description=f"promo {promotion_id}")
        for promotion_id in ids
    ]

    price = pricing_for(*promotions).get_price(1)

    assert price.promotion_name == "promo 1"


def test_inactive_promotions_are_ignored():
    inactive = make_promotion("40", promotion_id=2, is_active=False)

    price = pricing_for(inactive).get_price(1)

    assert price.has_active_promotion is False
    assert price.final_price == Decimal("100.00")


def test_inactive_promotion_never_beats_an_active_one():
    promotions = [
        make_promotion("10", promotion_id=1),
        make_promotion("40", promotion_id=2, is_active=False),
    ]

    price = pricing_for(*promotions).get_price(1)

    assert price.discount_percent == Decimal(10)


def test_promotions_of_other_products_do_not_apply():
    service = PricingService(
        [make_product(product_id=1), make_product(product_id=2)],
        [make_promotion("20", product_id=2)],
    )

    assert service.get_price(1).has_active_promotion is False
    assert service.get_price(2).has_active_promotion is True


def test_unknown_product_raises_error_with_reason_code():
    with pytest.raises(ProductNotFound) as error:
        _ = pricing_for().get_price(9999)

    assert error.value.code == ErrorCode.PRODUCT_NOT_FOUND
    assert error.value.product_id == 9999


def test_monetary_values_are_decimals_with_two_places():
    price = pricing_for(make_promotion("15"), price="99.99").get_price(1)

    for value in (price.list_price, price.discount_amount, price.final_price):
        assert isinstance(value, Decimal)
        assert value.as_tuple().exponent == -2
