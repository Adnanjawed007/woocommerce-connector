"""Order-related Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .common import Money, Address, WCOrderStatus, PaginatedResponse


class OrderLineItem(BaseModel):
    """Order line item."""
    id: Optional[int] = None
    name: str
    product_id: Optional[int] = None
    variation_id: Optional[int] = None
    quantity: int = 1
    subtotal: str = "0"
    subtotal_tax: str = "0"
    total: str = "0"
    total_tax: str = "0"
    sku: Optional[str] = None
    price: Optional[str] = None


class OrderShippingLine(BaseModel):
    """Order shipping line."""
    id: int
    method_title: str
    method_id: str
    total: str
    total_tax: str = "0"


class OrderFeeLine(BaseModel):
    """Order fee line."""
    id: int
    name: str
    tax_class: str = ""
    tax_status: str = "taxable"
    total: str
    total_tax: str = "0"


class OrderCouponLine(BaseModel):
    """Order coupon line."""
    id: int
    code: str
    discount: str
    discount_tax: str = "0"


class OrderRefund(BaseModel):
    """Order refund."""
    id: int
    reason: str = ""
    total: str


class Order(BaseModel):
    """WooCommerce order (read-only view for agents)."""
    id: int
    parent_id: int = 0
    number: str
    order_key: str = ""
    created_via: str = "checkout"
    version: str = "1.0"
    status: WCOrderStatus
    currency: str = "INR"
    date_created: datetime
    date_modified: Optional[datetime] = None
    discount_total: str = "0"
    discount_tax: str = "0"
    shipping_total: str = "0"
    shipping_tax: str = "0"
    cart_tax: str = "0"
    total: str
    total_tax: str = "0"
    prices_include_tax: bool = False
    customer_id: int
    customer_ip_address: Optional[str] = None
    customer_user_agent: Optional[str] = None
    customer_note: Optional[str] = None
    billing: Address
    shipping: Optional[Address] = None
    payment_method: str = ""
    payment_method_title: str = ""
    transaction_id: Optional[str] = None
    date_paid: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    cart_hash: Optional[str] = None
    line_items: List[OrderLineItem] = Field(default_factory=list)
    shipping_lines: List[OrderShippingLine] = Field(default_factory=list)
    fee_lines: List[OrderFeeLine] = Field(default_factory=list)
    coupon_lines: List[OrderCouponLine] = Field(default_factory=list)
    refunds: List[OrderRefund] = Field(default_factory=list)

    def to_agent_summary(self) -> dict:
        """Return a concise summary for agent consumption."""
        billing_name = ""
        if self.billing:
            billing_name = f"{self.billing.first_name or ''} {self.billing.last_name or ''}".strip()
        
        return {
            "id": self.id,
            "number": self.number,
            "status": self.status.value,
            "total": self.total,
            "currency": self.currency,
            "date_created": self.date_created.isoformat() if self.date_created else "",
            "customer_id": self.customer_id,
            "billing_name": billing_name,
            "item_count": len(self.line_items),
            "payment_method": self.payment_method_title,
        }


class OrderSearchParams(BaseModel):
    """Parameters for searching orders."""
    status: Optional[WCOrderStatus] = None
    min_amount: Optional[float] = Field(default=None, ge=0, description="Minimum order total")
    max_amount: Optional[float] = Field(default=None, ge=0, description="Maximum order total")
    date_from: Optional[datetime] = Field(default=None, description="Orders created after this date (ISO 8601)")
    date_to: Optional[datetime] = Field(default=None, description="Orders created before this date (ISO 8601)")
    customer_id: Optional[int] = Field(default=None, ge=1, description="Filter by customer ID")
    product_id: Optional[int] = Field(default=None, ge=1, description="Filter by product ID")
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
