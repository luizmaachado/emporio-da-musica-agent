"""Payment quote: PIX, debit, bank slip and credit card installments."""
from decimal import Decimal

import pytest

from emporio.data.loader import load_active_promotions, load_products
from emporio.domain.catalog import Availability
from emporio.domain.errors import DomainError, ErrorCode
from emporio.domain.payment import PaymentMethod, PaymentOption, PaymentRefusal
from emporio.domain.pricing import Promotion
from emporio.services.payment import PaymentService, minimum_installment
from tests.factories import make_product, make_promotion


def quote_for(price: str, *promotions: Promotion, **kwargs: object):
    service = PaymentService([make_product(1, price)], promotions)
    return service.quote(1, **kwargs)  # pyright: ignore[reportArgumentType]


def option(price: str, method: PaymentMethod, installments: int = 1) -> PaymentOption:
    quote = quote_for(price)
    return next(
        o for o in quote.options if o.method is method and o.installments == installments
    )


def credit(price: str, installments: int) -> PaymentOption:
    return option(price, PaymentMethod.CREDIT_CARD, installments)


# PIX, debit and bank slip


def test_pix_takes_five_percent_off_the_list_price():
    pix = option("200.00", PaymentMethod.PIX)

    assert pix.discount_amount == Decimal("10.00")
    assert pix.total == Decimal("190.00")


def test_pix_discount_is_rounded_half_up_to_the_cent():
    pix = option("100.10", PaymentMethod.PIX)  # 5% = 5.005

    assert pix.discount_amount == Decimal("5.01")
    assert pix.total == Decimal("95.09")


def test_pix_does_not_discount_a_promotional_price():
    quote = quote_for("200.00", make_promotion("10"))
    pix = next(o for o in quote.options if o.method is PaymentMethod.PIX)

    assert quote.has_active_promotion is True
    assert pix.discount_amount == Decimal("0.00")
    assert pix.total == Decimal("180.00")


@pytest.mark.parametrize("method", [PaymentMethod.DEBIT_CARD, PaymentMethod.BANK_SLIP])
def test_debit_and_bank_slip_pay_the_final_price_at_once(method: PaymentMethod):
    paid = option("200.00", method)

    assert paid.total == Decimal("200.00")
    assert paid.installment_value == Decimal("200.00")
    assert paid.discount_amount == Decimal("0.00")


def test_debit_and_bank_slip_use_the_promotional_price():
    quote = quote_for("200.00", make_promotion("10"))

    totals = {o.method: o.total for o in quote.options if o.installments == 1}

    assert totals[PaymentMethod.DEBIT_CARD] == Decimal("180.00")
    assert totals[PaymentMethod.BANK_SLIP] == Decimal("180.00")


# Credit card


def test_credit_card_offers_one_to_twelve_installments():
    quote = quote_for("5000.00")

    credit_options = [o for o in quote.options if o.method is PaymentMethod.CREDIT_CARD]

    assert [o.installments for o in credit_options] == list(range(1, 13))
    assert all(o.allowed for o in credit_options)


def test_up_to_three_installments_have_no_minimum_installment():
    split = credit("60.00", 3)

    assert split.allowed
    assert split.installment_value == Decimal("20.00")
    assert split.minimum_installment is None


def test_a_purchase_of_exactly_fifty_reais_can_be_split():
    assert credit("50.00", 3).allowed
    assert credit("50.00", 3).installment_value == Decimal("16.67")


def test_a_purchase_under_fifty_reais_is_not_split_but_can_be_paid_once():
    assert credit("49.99", 1).allowed
    refused = credit("49.99", 2)

    assert not refused.allowed
    assert refused.refusal is PaymentRefusal.BELOW_MINIMUM_TOTAL


@pytest.mark.parametrize(("price", "installments"), [("480.00", 6), ("700.00", 7), ("480.00", 4)])
def test_an_installment_exactly_at_the_minimum_is_allowed(price: str, installments: int):
    assert credit(price, installments).allowed


@pytest.mark.parametrize(("price", "installments"), [("479.94", 6), ("699.93", 7)])
def test_an_installment_one_cent_below_the_minimum_is_refused(price: str, installments: int):
    refused = credit(price, installments)

    assert not refused.allowed
    assert refused.refusal is PaymentRefusal.BELOW_MINIMUM_INSTALLMENT


def test_the_minimum_is_80_from_4_to_6_installments_and_100_from_7_to_12():
    assert credit("1000.00", 4).minimum_installment == Decimal("80.00")
    assert credit("1000.00", 6).minimum_installment == Decimal("80.00")
    assert credit("1000.00", 7).minimum_installment == Decimal("100.00")
    assert credit("1000.00", 12).minimum_installment == Decimal("100.00")


def test_the_installment_is_the_total_divided_and_rounded_half_up():
    assert credit("1000.00", 3).installment_value == Decimal("333.33")
    assert credit("100.05", 2).installment_value == Decimal("50.03")  # 50.025


def test_credit_card_is_computed_on_the_promotional_price():
    quote = quote_for("1000.00", make_promotion("50"), installments=7)

    assert quote.requested is not None
    assert quote.requested.total == Decimal("500.00")
    assert quote.requested.installment_value == Decimal("71.43")
    assert not quote.requested.allowed  # under the R$ 100.00 minimum for 7x


# Asking for a number of installments


def test_without_installments_nothing_is_singled_out():
    assert quote_for("500.00").requested is None


def test_with_installments_the_requested_credit_option_is_returned():
    quote = quote_for("2199.00", installments=10)

    assert quote.requested is not None
    assert quote.requested.installments == 10
    assert quote.requested.installment_value == Decimal("219.90")
    assert quote.requested.allowed


@pytest.mark.parametrize("installments", [0, 13, -1])
def test_a_number_of_installments_outside_one_to_twelve_is_refused(installments: int):
    with pytest.raises(DomainError) as error:
        _ = quote_for("500.00", installments=installments)

    assert error.value.code is ErrorCode.INVALID_INSTALLMENTS


# Combining methods, product, availability


def test_methods_can_be_combined_only_above_two_thousand_reais():
    assert quote_for("2000.01").can_combine_methods is True
    assert quote_for("2000.00").can_combine_methods is False


def test_the_combination_rule_looks_at_the_final_price():
    assert quote_for("3000.00", make_promotion("40")).can_combine_methods is False


def test_an_unknown_product_is_refused():
    service = PaymentService([make_product(1)], [])

    with pytest.raises(DomainError) as error:
        _ = service.quote(99)

    assert error.value.code is ErrorCode.PRODUCT_NOT_FOUND


def test_the_quote_tells_the_availability_and_name_of_the_product():
    service = PaymentService([make_product(1, stock=0, name="Sold out")], [])

    quote = service.quote(1)

    assert quote.availability is Availability.OUT_OF_STOCK
    assert quote.product_name == "Sold out"


# Real store data


def test_the_takamine_gd20_can_be_split_in_ten():
    service = PaymentService(load_products(), load_active_promotions())
    takamine = next(p for p in load_products() if p.name.startswith("Takamine GD20"))

    quote = service.quote(takamine.id, installments=10)

    assert quote.requested is not None
    assert quote.requested.allowed
    assert quote.requested.installment_value == Decimal("219.90")


def test_there_is_no_minimum_for_more_installments_than_the_store_offers():
    with pytest.raises(ValueError, match="13"):
        _ = minimum_installment(13)
