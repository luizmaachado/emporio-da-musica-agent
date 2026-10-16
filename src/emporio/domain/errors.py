"""Domain errors. Each carries a stable reason code that callers can rely on."""
from enum import StrEnum


class ErrorCode(StrEnum):
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"


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
