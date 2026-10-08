"""Tests for order tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.tools.orders import OrderTools
from app.services.wc_client import WooCommerceClient
from app.models.orders import Order
from tests.conftest import sample_order_data, create_mock_response


@pytest.fixture
def order_tools(wc_client):
    tools = OrderTools(wc_client)
    return tools


@pytest.mark.asyncio
async def test_search_orders_tool_success(order_tools, wc_client, sample_order_data):
    wc_client.search_orders = AsyncMock(return_value=(
        [Order.model_validate(sample_order_data)],
        {"page": 1, "per_page": 20, "total_pages": 1, "total_items": 1, "has_more": False}
    ))
    
    result = await order_tools.search_orders(status="completed", page=1, per_page=20)
    
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == 123
    assert result["data"][0]["status"] == "completed"
    assert "billing_name" in result["data"][0]


@pytest.mark.asyncio
async def test_search_orders_tool_error_handling(order_tools, wc_client):
    from app.services.wc_client import WooCommerceAPIError
    from app.models.common import ErrorResponse
    
    error = ErrorResponse(error="API Error", error_code="api_error")
    wc_client.search_orders = AsyncMock(side_effect=WooCommerceAPIError(error))
    
    result = await order_tools.search_orders()
    
    assert "error" in result
    assert result["error"] == "API Error"
    assert result["error_code"] == "api_error"


@pytest.mark.asyncio
async def test_get_order_tool_success(order_tools, wc_client, sample_order_data):
    wc_client.get_order = AsyncMock(return_value=Order.model_validate(sample_order_data))
    
    result = await order_tools.get_order(order_id=123)
    
    assert result["id"] == 123
    assert result["total"] == "2500.00"
    assert "line_items" in result


@pytest.mark.asyncio
async def test_get_order_tool_not_found(order_tools, wc_client):
    from app.services.wc_client import WooCommerceAPIError
    from app.models.common import ErrorResponse
    
    error = ErrorResponse(error="Order not found", error_code="not_found")
    wc_client.get_order = AsyncMock(side_effect=WooCommerceAPIError(error))
    
    result = await order_tools.get_order(order_id=999)
    
    assert "error" in result
    assert result["error_code"] == "not_found"