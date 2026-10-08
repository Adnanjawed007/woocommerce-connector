"""Tests for MCP tool schemas."""

from app.tools.schemas import get_tool_schemas, get_tool_by_name, TOOL_DEFINITIONS


def test_all_tools_defined():
    tool_names = [t.name for t in TOOL_DEFINITIONS]
    assert "search_orders" in tool_names
    assert "get_order" in tool_names
    assert "search_products" in tool_names
    assert "get_inventory" in tool_names
    assert len(tool_names) == 4


def test_tool_schemas_have_required_fields():
    for tool in TOOL_DEFINITIONS:
        assert tool.name
        assert tool.description
        assert tool.parameters
        assert tool.returns
        assert tool.parameters["type"] == "object"
        assert "properties" in tool.parameters


def test_search_orders_parameters():
    tool = get_tool_by_name("search_orders")
    props = tool.parameters["properties"]
    
    required_filters = ["status", "min_amount", "max_amount", "date_from", "date_to", "page", "per_page"]
    for f in required_filters:
        assert f in props, f"Missing parameter: {f}"
    
    assert "enum" in props["status"]
    assert "pending" in props["status"]["enum"]
    assert "completed" in props["status"]["enum"]


def test_get_order_parameters():
    tool = get_tool_by_name("get_order")
    props = tool.parameters["properties"]
    
    assert "order_id" in props
    assert props["order_id"]["type"] == "integer"
    assert tool.parameters["required"] == ["order_id"]


def test_get_inventory_parameters():
    tool = get_tool_by_name("get_inventory")
    props = tool.parameters["properties"]
    
    assert "product_id" in props
    assert "low_stock_only" in props
    assert "low_stock_threshold" in props
    assert "stock_status" in props


def test_get_tool_schemas_format():
    schemas = get_tool_schemas()
    
    assert len(schemas) == 4
    for schema in schemas:
        assert "name" in schema
        assert "description" in schema
        assert "parameters" in schema
        assert "returns" in schema