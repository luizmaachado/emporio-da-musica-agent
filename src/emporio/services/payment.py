"""Payment quote: PIX, debit, bank slip and credit card installments for a product."""
from collections.abc import Iterable
from decimal import Decimal

from emporio.domain.catalog import Product
from emporio.domain.errors import InvalidInstallments, ProductNotFound
from emporio.domain.money import to_money
from emporio.domain.payment import (
    PaymentMethod,
    PaymentOption,
    PaymentQuote,
    PaymentRefusal,
)
from emporio.domain.pricing import Promotion
from emporio.services.pricing import PricingService

PIX_DISCOUNT_PERCENT = Decimal(5)
MAX_INSTALLMENTS = 12
# Below this total a purchase cannot be split at all.
MIN_TOTAL_TO_SPLIT = Decimal("50.00")
# Minimum installment value by the highest installment count of each tier (manual, section 3.1).
# The table in section 3 says R$ 100.00 for any credit purchase; the detailed rule wins.
_MINIMUM_INSTALLMENT_BY_TIER = ((3, Decimal("0.00")), (6, Decimal("80.00")), (12, Decimal("100.00")))
# Different payment methods may be combined on purchases above this total.
COMBINE_METHODS_ABOVE = Decimal("2000.00")


def minimum_installment(installments: int) -> Decimal:
    """The smallest installment the store accepts for this number of installments.

    Raises:
        ValueError: when `installments` is above the store's maximum.
    """
    for highest, minimum in _MINIMUM_INSTALLMENT_BY_TIER:
        if installments <= highest:
            return minimum
    raise ValueError(f"No tier covers {installments} installments.")


class PaymentService:
    """Quotes how a product can be paid, from its final price (promotion included)."""

    def __init__(self, products: Iterable[Product], promotions: Iterable[Promotion]) -> None:
        """Prices come from a `PricingService` built here, so products and prices agree."""
        self._products = {product.id: product for product in products}
        self._pricing = PricingService(self._products.values(), promotions)

    def quote(self, product_id: int, installments: int | None = None) -> PaymentQuote:
        """All payment options of a product, whatever its status or stock.

        - PIX takes 5% off the list price, but not on a promotional price.
        - Debit card and bank slip are paid at once, with no discount.
        - Credit card goes up to 12 installments without interest. A purchase under R$ 50.00 is
          not split; up to 3 installments have no minimum; 4 to 6 need R$ 80.00 each and 7 to 12
          need R$ 100.00 each. An installment is the total divided by the count, rounded half up
          to the cent, and that rounded value is the one compared with the minimum.

        With `installments`, the result also holds that credit card option in `requested`.

        Raises:
            ProductNotFound: `PRODUCT_NOT_FOUND`, when the product id does not exist.
            InvalidInstallments: `INVALID_INSTALLMENTS`, when `installments` is not 1 to 12.
        """
        product = self._products.get(product_id)
        if product is None:
            raise ProductNotFound(product_id)
        if installments is not None and not 1 <= installments <= MAX_INSTALLMENTS:
            raise InvalidInstallments(installments, MAX_INSTALLMENTS)

        price = self._pricing.get_price(product_id)
        pix_discount = (
            Decimal("0.00")
            if price.has_active_promotion
            else to_money(price.list_price * PIX_DISCOUNT_PERCENT / 100)
        )
        pix_total = price.final_price - pix_discount
        credit = [_credit_option(price.final_price, n) for n in range(1, MAX_INSTALLMENTS + 1)]
        return PaymentQuote(
            product_id=product.id,
            product_name=product.name,
            availability=product.availability,
            list_price=price.list_price,
            final_price=price.final_price,
            has_active_promotion=price.has_active_promotion,
            options=[
                PaymentOption(
                    method=PaymentMethod.PIX,
                    total=pix_total,
                    installment_value=pix_total,
                    discount_amount=pix_discount,
                ),
                _single_payment(PaymentMethod.DEBIT_CARD, price.final_price),
                _single_payment(PaymentMethod.BANK_SLIP, price.final_price),
                *credit,
            ],
            requested=None if installments is None else credit[installments - 1],
            can_combine_methods=price.final_price > COMBINE_METHODS_ABOVE,
        )


def _single_payment(method: PaymentMethod, total: Decimal) -> PaymentOption:
    return PaymentOption(method=method, total=total, installment_value=total)


def _credit_option(total: Decimal, installments: int) -> PaymentOption:
    value = to_money(total / installments)
    minimum = minimum_installment(installments)
    refusal: PaymentRefusal | None = None
    if installments > 1 and total < MIN_TOTAL_TO_SPLIT:
        refusal = PaymentRefusal.BELOW_MINIMUM_TOTAL
    elif installments > 1 and value < minimum:
        refusal = PaymentRefusal.BELOW_MINIMUM_INSTALLMENT
    return PaymentOption(
        method=PaymentMethod.CREDIT_CARD,
        installments=installments,
        total=total,
        installment_value=value,
        allowed=refusal is None,
        refusal=refusal,
        minimum_installment=minimum if minimum > 0 else None,
    )
