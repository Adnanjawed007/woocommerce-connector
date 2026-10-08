"""Tests for product and inventory tools."""

import pytest
from unittest.mock import AsyncMock
from app.tools.products import ProductTools
from app.services.wc_client import WooCommerceClient
from app.models.products import Product
from tests.conftest import sample_product_data


@pytest.fixture
def product_tools(wc_client):
    """Create ProductTools with mocked client."""
    tools = ProductTools(wc_client)
    return tools


@pytest.mark.asyncio
async def test_search_products_tool_success(product_tools, wc_client, sample_product_data):
    """Test search_products tool."""
    wc_client.search_products = AsyncMock(return_value=(
        [Product.model_validate(sample_product_data)],
        {"page": 1, "per_page": 20, "total_pages": 1, "total_items": 1, "has_more": False}
    ))
    
    result = await product_tools.search_products(search="test", page=1)
    
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == 789
    assert result["data"][0]["sku"] == "TEST-001"


@pytest.mark.asyncio
async def test_get_inventory_specific_product(product_tools, wc_client, sample_product_data):
    """Test get_inventory for a specific product."""
    wc_client.get_product = AsyncMock(return_value=Product.model_validate(sample_product_data))
    
    result = await product_tools.get_inventory(product_id=789)
    
    assert "data" in result
    assert len(result["data"]) == 1
    item = result["data"][0]
    assert item["id"] == 789
    assert item["stock_quantity"] == 5
    assert item["stock_status"] == "instock"
    assert item["manage_stock"] is True


@pytest.mark.asyncio
async def test_get_inventory_low_stock_filter(product_tools, wc_client, sample_product_data):
    """Test get_inventory with low_stock_only filter."""
    # Create products with different stock levels
    product_low = {**sample_product_data, "id": 1, "stock_quantity": 5, "manage_stock": True}
    product_high = {**sample_product_data, "id": 2, "stock_quantity": 100, "manage_stock": True}
    
    from app.models.products import Product
    wc_client.search_products = AsyncMock(return_value=(
        [Product.model_validate(product_low), Product.model_validate(product_high)],
        {"page": 1, "per_page": 20, "total_pages": 1, "total_items": 2, "has_more": False}
    ))
    
    result = await product_tools.get_inventory(low_stock_only=True, low_stock_threshold=10)
    
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == 1


@pytest.mark.asyncio
async def test_get_inventory_out_of_stock(product_tools, wc_client, sample_product_data):
    """Test get_inventory with stock_status filter."""
    product_oos = {**sample_product_data, "id": 1, "stock_quantity": 0, "stock_status": "outofstock", "manage_stock": True}
    
    from app.models.products import Product
    wc_client.search_products = AsyncMock(return_value=(
        [Product.model_validate(product_oos)],
        {"page": 1, "per_page": 20, "total_pages": 1, "total_items": 1, "has_more": False}
    ))
    
    result = await product_tools.get_inventory(stock_status="outofstock")
    
    assert len(result["data"]) == 1
    assert result["data"][0]["stock_status"] == "outofstock"
