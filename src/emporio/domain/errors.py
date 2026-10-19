"""Domain errors. Each carries a stable reason code that callers can rely on."""
from enum import StrEnum


class ErrorCode(StrEnum):
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    UNKNOWN_CATEGORY = "UNKNOWN_CATEGORY"
    INVALID_PRICE_RANGE = "INVALID_PRICE_RANGE"


class DomainError(Exception):
    """Base class for errors raised when a business rule refuses a request."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class ProductNotFound(DomainError):
    """The requested product id does not exist in the catalog."""

    def __init__(self, product_id: int) -> None:
        super().__init__(ErrorCode.PRODUCT_NOT_FOUND, f"Product {product_id} not found.")
        self.product_id = product_id


class UnknownCategory(DomainError):
    """The requested category id does not exist."""

    def __init__(self, category_id: int) -> None:
        super().__init__(ErrorCode.UNKNOWN_CATEGORY, f"Category {category_id} not found.")
        self.category_id = category_id


class InvalidPriceRange(DomainError):
    """The minimum price is greater than the maximum price."""

    def __init__(self) -> None:
        super().__init__(
            ErrorCode.INVALID_PRICE_RANGE, "The minimum price cannot exceed the maximum price."
        )
