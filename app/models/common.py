"""Common Pydantic models used across the connector."""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime
from enum import Enum

T = TypeVar('T')


class WCOrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"
    TRASH = "trash"


class WCStockStatus(str, Enum):
    IN_STOCK = "instock"
    OUT_OF_STOCK = "outofstock"
    ON_BACKORDER = "onbackorder"


class PaginationParams(BaseModel):
    """Pagination parameters for list operations."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper."""
    data: List[T]
    page: int
    per_page: int
    total_pages: Optional[int] = None
    total_items: Optional[int] = None
    has_more: bool = False


class ErrorResponse(BaseModel):
    """Structured error response for agent consumption."""
    error: str
    error_code: str
    details: Optional[dict] = None
    retry_after: Optional[float] = None


class Money(BaseModel):
    """Monetary amount with currency."""
    amount: str = Field(description="Amount as string to preserve precision")
    currency: str = Field(default="INR", description="ISO 4217 currency code")


class Address(BaseModel):
    """Address information."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None