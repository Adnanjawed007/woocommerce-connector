"""Tests for WooCommerce client."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import Response, Headers

from app.services.wc_client import WooCommerceClient, WooCommerceAPIError
from app.models.orders import Order, OrderSearchParams
from app.models.products import Product, ProductSearchParams
from tests.conftest import create_mock_response


@pytest.mark.asyncio
async def test_get_order_success(wc_client, sample_order_data):
    """Test successful order retrieval."""
    wc_client._client.request = AsyncMock(
        return_value=create_mock_response(200, sample_order_data)
    )
    
    order = await wc_client.get_order(123)
    
    assert isinstance(order, Order)
    assert order.id == 123
    assert order.status.value == "completed"
    assert order.total == "2500.00"


@pytest.mark.asyncio
async def test_get_order_not_found(wc_client):
    """Test 404 error handling."""
    error_data = {"code": "woocommerce_rest_shop_order_invalid_id", "message": "Invalid order ID"}
    wc_client._client.request = AsyncMock(
        return_value=create_mock_response(404, error_data)
    )
    
    with pytest.raises(WooCommerceAPIError) as exc_info:
        await wc_client.get_order(999)
    
    assert exc_info.value.error.error_code == "woocommerce_rest_shop_order_invalid_id"


@pytest.mark.asyncio
async def test_search_orders_success(wc_client, sample_order_data):
    """Test successful order search with pagination."""
    wc_client._client.request = AsyncMock(
        return_value=create_mock_response(
            200, 
            [sample_order_data],
            headers={"X-WP-TotalPages": "5", "X-WP-Total": "100"}
        )
    )
    
    params = OrderSearchParams(status="completed", page=1, per_page=20)
    orders, pagination = await wc_client.search_orders(params)
    
    assert len(orders) == 1
    assert orders[0].id == 123
    assert pagination["total_pages"] == 5
    assert pagination["total_items"] == 100
    assert pagination["has_more"] is True


@pytest.mark.asyncio
async def test_search_orders_with_amount_filters(wc_client, sample_order_data):
    """Test order search with min/max amount filters."""
    wc_client._client.request = AsyncMock(
        return_value=create_mock_response(200, [sample_order_data])
    )
    
    params = OrderSearchParams(min_amount=1000, max_amount=5000, page=1, per_page=20)
    orders, _ = await wc_client.search_orders(params)
    
    # Verify the request was made with correct params
    call_args = wc_client._client.request.call_args
    params_sent = call_args[1]["params"]
    assert params_sent["min_total"] == "1000"
    assert params_sent["max_total"] == "5000"


@pytest.mark.asyncio
async def test_search_products_success(wc_client, sample_product_data):
    """Test successful product search."""
    wc_client._client.request = AsyncMock(
        return_value=create_mock_response(
            200,
            [sample_product_data],
            headers={"X-WP-TotalPages": "1", "X-WP-Total": "1"}
        )
    )
    
    params = ProductSearchParams(search="test", page=1, per_page=20)
    products, pagination = await wc_client.search_products(params)
    
    assert len(products) == 1
    assert products[0].id == 789
    assert products[0].sku == "TEST-001"


@pytest.mark.asyncio
async def test_search_products_low_stock_filter(wc_client, sample_product_data):
    """Test client-side low stock filtering."""
    # Create products with varying stock levels
    product_low = {**sample_product_data, "id": 1, "stock_quantity": 5, "manage_stock": True}
    product_normal = {**sample_product_data, "id": 2, "stock_quantity": 50, "manage_stock": True}
    product_no_stock = {**sample_product_data, "id": 3, "manage_stock": False}
    
    wc_client._client.request = AsyncMock(
        return_value=create_mock_response(200, [product_low, product_normal, product_no_stock])
    )
    
    params = ProductSearchParams(low_stock_only=True, low_stock_threshold=10, page=1, per_page=50)
    products, pagination = await wc_client.search_products(params)
    
    # Only low stock product should remain
    assert len(products) == 1
    assert products[0].id == 1
    assert pagination["total_items"] == 1


@pytest.mark.asyncio
async def test_health_check_success(wc_client):
    """Test health check endpoint."""
    wc_client._client.request = AsyncMock(
        return_value=create_mock_response(200, {"status": "ok"})
    )
    
    health = await wc_client.health_check()
    
    assert health["status"] == "healthy"
    assert health["authenticated"] is True


@pytest.mark.asyncio
async def test_health_check_unauthorized(wc_client):
    """Test health check with invalid credentials."""
    error_data = {"code": "woocommerce_rest_authentication_error", "message": "Invalid credentials"}
    wc_client._client.request = AsyncMock(
        return_value=create_mock_response(401, error_data)
    )
    
    health = await wc_client.health_check()
    
    assert health["status"] == "unauthorized"
    assert health["authenticated"] is False