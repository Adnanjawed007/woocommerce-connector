"""Product-related Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .common import Money, WCStockStatus, PaginatedResponse


class ProductImage(BaseModel):
    """Product image."""
    id: int
    src: str
    name: Optional[str] = None
    alt: Optional[str] = None


class ProductAttribute(BaseModel):
    """Product attribute."""
    id: int
    name: str
    position: int
    visible: bool
    variation: bool
    options: List[str]


class ProductDimension(BaseModel):
    """Product dimensions."""
    length: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None


class Product(BaseModel):
    """WooCommerce product (read-only view for agents)."""
    id: int
    name: str
    slug: str = ""
    permalink: str = ""
    date_created: datetime
    date_modified: Optional[datetime] = None
    type: str = "simple"
    status: str = "publish"
    featured: bool = False
    catalog_visibility: str = "visible"
    description: str = ""
    short_description: str = ""
    sku: Optional[str] = None
    price: Optional[str] = None
    regular_price: Optional[str] = None
    sale_price: Optional[str] = None
    date_on_sale_from: Optional[datetime] = None
    date_on_sale_to: Optional[datetime] = None
    price_html: Optional[str] = None
    on_sale: bool = False
    purchasable: bool = True
    total_sales: Optional[int] = None
    virtual: bool = False
    downloadable: bool = False
    downloads: List[dict] = Field(default_factory=list)
    download_limit: int = -1
    download_expiry: int = -1
    external_url: Optional[str] = None
    button_text: Optional[str] = None
    tax_status: str = "taxable"
    tax_class: str = ""
    manage_stock: bool = False
    stock_quantity: Optional[int] = None
    stock_status: WCStockStatus = WCStockStatus.IN_STOCK
    backorders: str = "no"
    backorders_allowed: bool = False
    backordered: bool = False
    sold_individually: bool = False
    weight: Optional[str] = None
    dimensions: Optional[ProductDimension] = None
    shipping_required: bool = True
    shipping_taxable: bool = True
    shipping_class: Optional[str] = None
    shipping_class_id: int = 0
    reviews_allowed: bool = True
    average_rating: str = "0.00"
    rating_count: int = 0
    upsell_ids: List[int] = Field(default_factory=list)
    cross_sell_ids: List[int] = Field(default_factory=list)
    parent_id: int = 0
    purchase_note: Optional[str] = None
    categories: List[dict] = Field(default_factory=list)
    tags: List[dict] = Field(default_factory=list)
    images: List[ProductImage] = Field(default_factory=list)
    attributes: List[ProductAttribute] = Field(default_factory=list)
    default_attributes: List[dict] = Field(default_factory=list)
    variations: List[int] = Field(default_factory=list)
    grouped_products: List[int] = Field(default_factory=list)
    menu_order: int = 0
    meta_data: List[dict] = Field(default_factory=list)

    def to_inventory_summary(self) -> dict:
        """Return inventory-relevant fields for agent consumption."""
        return {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "stock_quantity": self.stock_quantity,
            "stock_status": self.stock_status.value,
            "manage_stock": self.manage_stock,
            "price": self.price,
            "regular_price": self.regular_price,
            "type": self.type,
        }

    def is_low_stock(self, threshold: int = 10) -> bool:
        """Check if product is low in stock."""
        if not self.manage_stock or self.stock_quantity is None:
            return False
        return self.stock_quantity <= threshold


class ProductSearchParams(BaseModel):
    """Parameters for searching products."""
    search: Optional[str] = Field(default=None, description="Search term for product name/SKU")
    type: Optional[str] = Field(default=None, description="Product type (simple, variable, grouped, external)")
    status: Optional[str] = Field(default=None, description="Product status (publish, draft, private)")
    featured: Optional[bool] = None
    category: Optional[int] = Field(default=None, ge=1, description="Category ID")
    tag: Optional[int] = Field(default=None, ge=1, description="Tag ID")
    min_price: Optional[float] = Field(default=None, ge=0)
    max_price: Optional[float] = Field(default=None, ge=0)
    stock_status: Optional[str] = Field(default=None, description="instock, outofstock, onbackorder")
    low_stock_only: bool = Field(default=False, description="Only return products with low stock")
    low_stock_threshold: int = Field(default=10, ge=1, le=1000)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
