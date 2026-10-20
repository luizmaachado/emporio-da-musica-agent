"""LangChain tools: thin wrappers over the services that return plain, compact data.

Domain errors are returned as `{"error": code, "message": ...}` so the model can react to them
instead of the run crashing. Tools return facts only; how to behave with them is in the prompt.
The rules themselves stay in the services.
"""
from decimal import Decimal
from typing import Annotated

from langchain_core.tools import BaseTool, tool

from emporio.domain.errors import DomainError
from emporio.domain.money import to_money
from emporio.domain.payment import PaymentMethod, PaymentOption, PaymentQuote
from emporio.services.payment import PaymentService
from emporio.services.search import (
    ProductFilters,
    ProductSearchService,
    SearchItem,
    SortOrder,
    StringType,
)


def _to_decimal(value: float | None) -> Decimal | None:
    """Prices arrive from the model as JSON numbers; going through `str` avoids float noise.

    Models often fill unused bounds with 0, which means "no bound"; a real bound of zero
    would not filter anything useful anyway.
    """
    return None if value is None or value == 0 else to_money(Decimal(str(value)))


def format_brl(amount: Decimal) -> str:
    """1299.9 -> "R$ 1.299,90", so the model never has to format money."""
    text = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {text}"


def format_percent(percent: Decimal) -> str:
    """Decimal(12.5) -> "12,5%", Decimal(10) -> "10%"."""
    return f"{percent.normalize():f}".replace(".", ",") + "%"


def _item_summary(item: SearchItem) -> dict[str, object]:
    """What the model sees of a product: prices already formatted, availability as a label."""
    product, price = item.product, item.price
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "category_id": product.category_id,
        "availability": product.availability.value,
        "list_price": format_brl(price.list_price),
        "final_price": format_brl(price.final_price),
        "discount_percent": (
            format_percent(price.discount_percent) if price.has_active_promotion else None
        ),
        "promotion_name": price.promotion_name,
        "specs": product.specs,
    }


def _credit_summary(option: PaymentOption) -> dict[str, object]:
    return {
        "installments": option.installments,
        "installment_value": format_brl(option.installment_value),
        "total": format_brl(option.total),
        "allowed": option.allowed,
        "refusal": option.refusal.value if option.refusal else None,
        "minimum_installment": (
            format_brl(option.minimum_installment) if option.minimum_installment else None
        ),
    }


def _quote_summary(quote: PaymentQuote) -> dict[str, object]:
    """What the model sees of a quote: money formatted, credit card options that are allowed."""
    by_method = {o.method: o for o in quote.options if o.installments == 1}
    pix = by_method[PaymentMethod.PIX]
    credit = [
        o for o in quote.options if o.method is PaymentMethod.CREDIT_CARD and o.allowed
    ]
    summary: dict[str, object] = {
        "product": quote.product_name,
        "availability": quote.availability.value,
        "list_price": format_brl(quote.list_price),
        "final_price": format_brl(quote.final_price),
        "has_active_promotion": quote.has_active_promotion,
        "pix": {
            "total": format_brl(pix.total),
            "discount": format_brl(pix.discount_amount),
            "discount_applied": pix.discount_amount > 0,
        },
        "debit_card": {"total": format_brl(by_method[PaymentMethod.DEBIT_CARD].total)},
        "bank_slip": {"total": format_brl(by_method[PaymentMethod.BANK_SLIP].total)},
        "credit_card_allowed": [_credit_summary(o) for o in credit],
        "max_installments": max(o.installments for o in credit),
        "can_combine_methods": quote.can_combine_methods,
    }
    if quote.requested is not None:
        summary["requested_installments"] = _credit_summary(quote.requested)
    return summary


def build_tools(search: ProductSearchService, payment: PaymentService) -> list[BaseTool]:
    """The tools, bound to the services. Their names are referenced by the prompt."""

    @tool
    def list_categories() -> list[dict[str, object]]:
        """List the store categories with their id, name, description, number of available
        products and the colors available in each. Use it to find the category_id of an
        instrument type and the valid color names."""
        return [summary.model_dump(mode="json") for summary in search.list_categories()]

    @tool
    def search_products(
        query: Annotated[
            str | None, "Words that must appear in the name, description or category"
        ] = None,
        category_id: Annotated[
            int | None,
            "Category id from list_categories; only for a type of instrument, "
            "never when the customer names a model",
        ] = None,
        min_price: Annotated[
            float | None, "Minimum final price in BRL; only if the customer gave one"
        ] = None,
        max_price: Annotated[
            float | None, "Maximum final price in BRL; only if the customer gave one"
        ] = None,
        string_type: Annotated[
            StringType | None, "nylon or steel; only if the customer asked for it"
        ] = None,
        color: Annotated[
            str | None,
            "Exact color name from list_categories; only if the customer asked for a color",
        ] = None,
        electronics: Annotated[
            bool | None,
            "Only if the customer asked: True for electro-acoustic (with pickup), "
            "False for purely acoustic",
        ] = None,
        include_unavailable: Annotated[
            bool, "Also return out-of-stock and discontinued products"
        ] = False,
        sort: Annotated[SortOrder, "Final price ascending or descending"] = SortOrder.PRICE_ASC,
    ) -> dict[str, object]:
        """Search the catalog. Returns the matching products with list price, final price
        and active promotion, sorted by final price. By default only products available for
        purchase are returned; an empty list means nothing matched."""
        filters = ProductFilters(
            query=query,
            category_id=category_id,
            min_price=_to_decimal(min_price),
            max_price=_to_decimal(max_price),
            string_type=string_type,
            color=color,
            electronics=electronics,
            include_unavailable=include_unavailable,
            sort=sort,
        )
        try:
            result = search.search(filters)
        except DomainError as error:
            return {"error": error.code.value, "message": str(error)}
        return {
            "total": len(result.items),
            # The criteria that were applied, so the answer can say what was searched for.
            "filters": filters.model_dump(mode="json", exclude_none=True, exclude_defaults=True),
            "items": [_item_summary(item) for item in result.items],
        }

    @tool
    def quote_payment(
        product_id: Annotated[int, "Product id from search_products"],
        installments: Annotated[
            int | None,
            "Number of credit card installments, only if the customer asked for one",
        ] = None,
    ) -> dict[str, object]:
        """How a product can be paid: PIX (with its discount), debit card, bank slip and the
        credit card installments that are allowed. Use it for any question about payment
        methods, installments or the PIX discount of a specific product. With `installments`,
        also says whether that number of installments is allowed and the value of each one."""
        try:
            return _quote_summary(payment.quote(product_id, installments))
        except DomainError as error:
            return {"error": error.code.value, "message": str(error)}

    return [list_categories, search_products, quote_payment]
