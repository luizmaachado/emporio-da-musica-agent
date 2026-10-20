"""Payment models: how a product can be paid for, and why an option is refused."""
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from emporio.domain.catalog import Availability


class PaymentMethod(StrEnum):
    PIX = "pix"
    DEBIT_CARD = "debit_card"
    BANK_SLIP = "bank_slip"
    CREDIT_CARD = "credit_card"


class PaymentRefusal(StrEnum):
    """Why a credit card option is not offered."""

    BELOW_MINIMUM_TOTAL = "below_minimum_total"  # the purchase is too small to be split
    BELOW_MINIMUM_INSTALLMENT = "below_minimum_installment"


class PaymentOption(BaseModel):
    """One way to pay. Only credit card options have more than one installment.

    `total` is what the customer pays in all. `discount_amount` is the PIX discount (zero for
    every other option, and for PIX on a promotional price). `minimum_installment` is set on
    credit card options of 4 or more installments, the ones with a minimum.
    """

    model_config = ConfigDict(frozen=True)

    method: PaymentMethod
    installments: int = 1
    total: Decimal
    installment_value: Decimal
    discount_amount: Decimal = Decimal("0.00")
    allowed: bool = True
    refusal: PaymentRefusal | None = None
    minimum_installment: Decimal | None = None


class PaymentQuote(BaseModel):
    """Every option for one product, and the credit card option the customer asked about."""

    model_config = ConfigDict(frozen=True)

    product_id: int
    product_name: str
    availability: Availability
    list_price: Decimal
    final_price: Decimal
    has_active_promotion: bool
    options: list[PaymentOption]
    requested: PaymentOption | None = None
    can_combine_methods: bool
