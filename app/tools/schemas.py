"""MCP-compatible tool schemas and definitions."""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.models.orders import OrderSearchParams
from app.models.products import ProductSearchParams
from app.models.common import PaginationParams


class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]


TOOL_DEFINITIONS: List[ToolSchema] = [
    ToolSchema(
        name="search_orders",
        description=(
            "Search and list WooCommerce orders with flexible filtering. "
            "Use this when the merchant wants to see recent orders, find orders by status, "
            "filter by amount range, or search within a date range. "
            "Returns paginated results with order summaries suitable for agent consumption."
        ),
        parameters={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed", "trash"],
                    "description": "Filter by order status",
                },
                "min_amount": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Minimum order total (inclusive)",
                },
                "max_amount": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Maximum order total (inclusive)",
                },
                "date_from": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Orders created after this date (ISO 8601)",
                },
                "date_to": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Orders created before this date (ISO 8601)",
                },
                "customer_id": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Filter by customer ID",
                },
                "product_id": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Filter orders containing this product ID",
                },
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1,
                    "description": "Page number (1-indexed)",
                },
                "per_page": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20,
                    "description": "Number of orders per page",
                },
            },
            "required": [],
        },
        returns={
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "number": {"type": "string"},
                            "status": {"type": "string"},
                            "total": {"type": "string"},
                            "currency": {"type": "string"},
                            "date_created": {"type": "string", "format": "date-time"},
                            "customer_id": {"type": "integer"},
                            "billing_name": {"type": "string"},
                            "item_count": {"type": "integer"},
                            "payment_method": {"type": "string"},
                        },
                        "required": ["id", "number", "status", "total", "currency", "date_created", "customer_id", "billing_name", "item_count", "payment_method"],
                    },
                },
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
                "total_pages": {"type": "integer"},
                "total_items": {"type": "integer"},
                "has_more": {"type": "boolean"},
            },
            "required": ["data", "page", "per_page", "total_pages", "total_items", "has_more"],
        },
    ),
    ToolSchema(
        name="get_order",
        description=(
            "Retrieve complete details for a specific order by ID. "
            "Use this when the merchant asks for details about a particular order. "
            "Returns full order information including line items, shipping, billing, and payment details. "
            "Sensitive fields like customer IP and user agent are excluded."
        ),
        parameters={
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "WooCommerce order ID",
                },
            },
            "required": ["order_id"],
        },
        returns={
            "type": "object",
            "description": "Full order object with all readable fields",
        },
    ),
    ToolSchema(
        name="search_products",
        description=(
            "Search and list WooCommerce products with filtering. "
            "Use this when the merchant wants to browse products, find products by name/SKU, "
            "filter by type/status/category, or find products in a price range. "
            "Returns paginated product listings."
        ),
        parameters={
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Search term for product name or SKU",
                },
                "type": {
                    "type": "string",
                    "enum": ["simple", "variable", "grouped", "external"],
                    "description": "Filter by product type",
                },
                "status": {
                    "type": "string",
                    "enum": ["publish", "draft", "private", "pending"],
                    "description": "Filter by product status",
                },
                "featured": {
                    "type": "boolean",
                    "description": "Filter featured products only",
                },
                "category": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Filter by category ID",
                },
                "tag": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Filter by tag ID",
                },
                "min_price": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Minimum price filter",
                },
                "max_price": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Maximum price filter",
                },
                "stock_status": {
                    "type": "string",
                    "enum": ["instock", "outofstock", "onbackorder"],
                    "description": "Filter by stock status",
                },
                "low_stock_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only return products with stock below threshold",
                },
                "low_stock_threshold": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 10,
                    "description": "Stock quantity threshold for low_stock_only filter",
                },
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1,
                    "description": "Page number (1-indexed)",
                },
                "per_page": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20,
                    "description": "Number of products per page",
                },
            },
            "required": [],
        },
        returns={
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "description": "Product object with all readable fields",
                    },
                },
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
                "total_pages": {"type": "integer"},
                "total_items": {"type": "integer"},
                "has_more": {"type": "boolean"},
            },
            "required": ["data", "page", "per_page", "total_pages", "total_items", "has_more"],
        },
    ),
    ToolSchema(
        name="get_inventory",
        description=(
            "Get inventory information for products. "
            "Use this when the merchant asks about stock levels, low stock items, or out-of-stock products. "
            "Returns product ID, name, SKU, stock quantity, stock status, and price. "
            "Can filter for low/out-of-stock items using low_stock_only parameter."
        ),
        parameters={
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Specific product ID to check inventory for",
                },
                "low_stock_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only return products with low stock",
                },
                "low_stock_threshold": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 10,
                    "description": "Stock quantity threshold for low stock",
                },
                "stock_status": {
                    "type": "string",
                    "enum": ["instock", "outofstock", "onbackorder"],
                    "description": "Filter by stock status",
                },
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1,
                    "description": "Page number (1-indexed)",
                },
                "per_page": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20,
                    "description": "Number of products per page",
                },
            },
            "required": [],
        },
        returns={
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "sku": {"type": "string"},
                            "stock_quantity": {"type": "integer"},
                            "stock_status": {"type": "string"},
                            "manage_stock": {"type": "boolean"},
                            "price": {"type": "string"},
                            "regular_price": {"type": "string"},
                            "type": {"type": "string"},
                        },
                        "required": ["id", "name", "sku", "stock_quantity", "stock_status", "manage_stock", "price", "regular_price", "type"],
                    },
                },
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
                "total_pages": {"type": "integer"},
                "total_items": {"type": "integer"},
                "has_more": {"type": "boolean"},
            },
            "required": ["data", "page", "per_page", "total_pages", "total_items", "has_more"],
        },
    ),
]


def get_tool_schemas() -> List[Dict[str, Any]]:
    return [tool.model_dump() for tool in TOOL_DEFINITIONS]


def get_tool_by_name(name: str) -> ToolSchema:
    for tool in TOOL_DEFINITIONS:
        if tool.name == name:
            return tool
    raise ValueError(f"Unknown tool: {name}")