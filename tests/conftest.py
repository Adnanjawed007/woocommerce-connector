"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import Response, Headers
import json

from app.config import Settings
from app.services.wc_client import WooCommerceClient
from app.models.orders import Order, OrderSearchParams
from app.models.products import Product, ProductSearchParams
from app.models.common import WCOrderStatus, Address


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    test_settings = Settings(
        woocommerce_url="https://test-store.example.com",
        woocommerce_consumer_key="ck_test_key",
        woocommerce_consumer_secret="cs_test_secret",
        request_timeout=5.0,
        max_retries=2,
        base_retry_delay=0.01,
    )
    # Patch at module level where used
    monkeypatch.setattr("app.config.settings", test_settings)
    monkeypatch.setattr("app.services.wc_client.settings", test_settings)
    return test_settings


@pytest.fixture
def wc_client(mock_settings):
    """Create a WooCommerceClient with fully mocked HTTP client."""
    client = WooCommerceClient()
    # Create a fully mocked async client
    mock_client = AsyncMock()
    client._client = mock_client
    return client


@pytest.fixture
def sample_order_data():
    """Sample order data from WooCommerce API."""
    return {
        "id": 123,
        "parent_id": 0,
        "number": "123",
        "order_key": "wc_order_abc123",
        "created_via": "checkout",
        "version": "9.0",
        "status": "completed",
        "currency": "INR",
        "date_created": "2024-01-15T10:30:00",
        "date_modified": "2024-01-15T10:35:00",
        "discount_total": "0.00",
        "discount_tax": "0.00",
        "shipping_total": "50.00",
        "shipping_tax": "9.00",
        "cart_tax": "180.00",
        "total": "2500.00",
        "total_tax": "189.00",
        "prices_include_tax": False,
        "customer_id": 456,
        "customer_ip_address": "192.168.1.1",
        "customer_user_agent": "Mozilla/5.0...",
        "customer_note": "Please deliver by Friday",
        "billing": {
            "first_name": "John",
            "last_name": "Doe",
            "company": "",
            "address_1": "123 Main St",
            "address_2": "",
            "city": "Mumbai",
            "state": "MH",
            "postcode": "400001",
            "country": "IN",
            "phone": "+91-9876543210",
            "email": "john@example.com",
        },
        "shipping": {
            "first_name": "John",
            "last_name": "Doe",
            "company": "",
            "address_1": "123 Main St",
            "address_2": "",
            "city": "Mumbai",
            "state": "MH",
            "postcode": "400001",
            "country": "IN",
            "phone": "+91-9876543210",
        },
        "payment_method": "bacs",
        "payment_method_title": "Direct Bank Transfer",
        "transaction_id": "TXN123456",
        "date_paid": "2024-01-15T10:30:00",
        "date_completed": "2024-01-15T10:35:00",
        "cart_hash": "abc123",
        "line_items": [
            {
                "id": 1,
                "name": "Test Product",
                "product_id": 789,
                "variation_id": 0,
                "quantity": 2,
                "subtotal": "2400.00",
                "subtotal_tax": "180.00",
                "total": "2400.00",
                "total_tax": "180.00",
                "sku": "TEST-001",
                "price": "1200.00",
            }
        ],
        "shipping_lines": [
            {
                "id": 1,
                "method_title": "Flat Rate",
                "method_id": "flat_rate",
                "total": "50.00",
                "total_tax": "9.00",
            }
        ],
        "fee_lines": [],
        "coupon_lines": [],
        "refunds": [],
    }


@pytest.fixture
def sample_product_data():
    """Sample product data from WooCommerce API."""
    return {
        "id": 789,
        "name": "Test Product",
        "slug": "test-product",
        "permalink": "https://test-store.example.com/product/test-product/",
        "date_created": "2024-01-01T10:00:00",
        "date_modified": "2024-01-10T10:00:00",
        "type": "simple",
        "status": "publish",
        "featured": False,
        "catalog_visibility": "visible",
        "description": "<p>Test product description</p>",
        "short_description": "Test product",
        "sku": "TEST-001",
        "price": "1200.00",
        "regular_price": "1200.00",
        "sale_price": None,
        "date_on_sale_from": None,
        "date_on_sale_to": None,
        "price_html": "<span class=\"woocommerce-Price-amount amount\">₹1,200.00</span>",
        "on_sale": False,
        "purchasable": True,
        "total_sales": 42,
        "virtual": False,
        "downloadable": False,
        "downloads": [],
        "download_limit": -1,
        "download_expiry": -1,
        "external_url": "",
        "button_text": "",
        "tax_status": "taxable",
        "tax_class": "",
        "manage_stock": True,
        "stock_quantity": 5,
        "stock_status": "instock",
        "backorders": "no",
        "backorders_allowed": False,
        "backordered": False,
        "sold_individually": False,
        "weight": "0.5",
        "dimensions": {"length": "10", "width": "5", "height": "2"},
        "shipping_required": True,
        "shipping_taxable": True,
        "shipping_class": "",
        "shipping_class_id": 0,
        "reviews_allowed": True,
        "average_rating": "4.50",
        "rating_count": 10,
        "upsell_ids": [],
        "cross_sell_ids": [],
        "parent_id": 0,
        "purchase_note": "",
        "categories": [{"id": 1, "name": "Electronics", "slug": "electronics"}],
        "tags": [{"id": 1, "name": "Popular", "slug": "popular"}],
        "images": [{"id": 1, "src": "https://example.com/image.jpg", "name": "Test Product", "alt": ""}],
        "attributes": [],
        "default_attributes": [],
        "variations": [],
        "grouped_products": [],
        "menu_order": 0,
        "meta_data": [],
    }


def create_mock_response(status_code: int, json_data: any, headers: dict = None):
    """Create a mock httpx.Response."""
    response = MagicMock(spec=Response)
    response.status_code = status_code
    response.json.return_value = json_data
    response.text = json.dumps(json_data)
    response.headers = Headers(headers or {})
    response.is_success = 200 <= status_code < 300
    return response