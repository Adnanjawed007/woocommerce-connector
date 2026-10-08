"""MCP-compatible tool server for Agent Studio integration."""

import logging
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.services.wc_client import WooCommerceClient
from app.tools.orders import OrderTools
from app.tools.products import ProductTools
from app.tools.schemas import get_tool_schemas
from app.config import settings

logger = logging.getLogger(__name__)

wc_client: WooCommerceClient = None
order_tools: OrderTools = None
product_tools: ProductTools = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global wc_client, order_tools, product_tools
    
    logger.info("Starting WooCommerce Connector...")
    wc_client = WooCommerceClient()
    order_tools = OrderTools(wc_client)
    product_tools = ProductTools(wc_client)
    
    health = await wc_client.health_check()
    logger.info(f"WooCommerce health check: {health}")
    
    yield
    
    logger.info("Shutting down WooCommerce Connector...")
    await wc_client.close()


app = FastAPI(
    title="WooCommerce Connector for Agent Studio",
    description="Read-only connector enabling AI agents to query WooCommerce orders and inventory",
    version="1.0.0",
    lifespan=lifespan,
)


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    result: Any
    error: str = None


@app.get("/mcp/tools")
async def list_tools() -> List[Dict[str, Any]]:
    return get_tool_schemas()


@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest) -> ToolCallResponse:
    tool_name = request.name
    arguments = request.arguments or {}
    
    logger.info(f"Tool call: {tool_name} with args: {arguments}")
    
    try:
        if tool_name == "search_orders":
            result = await order_tools.search_orders(**arguments)
        elif tool_name == "get_order":
            result = await order_tools.get_order(**arguments)
        elif tool_name == "search_products":
            result = await product_tools.search_products(**arguments)
        elif tool_name == "get_inventory":
            result = await product_tools.get_inventory(**arguments)
        else:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
        
        if isinstance(result, dict) and result.get("error"):
            return ToolCallResponse(result=None, error=result["error"])
        
        return ToolCallResponse(result=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Tool {tool_name} execution failed")
        return ToolCallResponse(result=None, error=str(e))


@app.get("/health")
async def health_check():
    health = await wc_client.health_check()
    return health


@app.get("/info")
async def info():
    return {
        "name": "WooCommerce Connector",
        "version": "1.0.0",
        "description": "Read-only connector for Agent Studio to query WooCommerce orders and inventory",
        "authentication": "API Key (Consumer Key/Secret)",
        "mode": "read-only",
        "tools": [t["name"] for t in get_tool_schemas()],
    }


@app.get("/tools/search_orders")
async def search_orders_direct(
    status: str = None,
    min_amount: float = None,
    max_amount: float = None,
    date_from: str = None,
    date_to: str = None,
    customer_id: int = None,
    product_id: int = None,
    page: int = 1,
    per_page: int = 20,
):
    kwargs = {k: v for k, v in locals().items() if v is not None}
    return await order_tools.search_orders(**kwargs)


@app.get("/tools/get_order/{order_id}")
async def get_order_direct(order_id: int):
    return await order_tools.get_order(order_id)


@app.get("/tools/search_products")
async def search_products_direct(
    search: str = None,
    type: str = None,
    status: str = None,
    featured: bool = None,
    category: int = None,
    tag: int = None,
    min_price: float = None,
    max_price: float = None,
    stock_status: str = None,
    low_stock_only: bool = False,
    low_stock_threshold: int = 10,
    page: int = 1,
    per_page: int = 20,
):
    kwargs = {k: v for k, v in locals().items() if v is not None}
    return await product_tools.search_products(**kwargs)


@app.get("/tools/get_inventory")
async def get_inventory_direct(
    product_id: int = None,
    low_stock_only: bool = False,
    low_stock_threshold: int = 10,
    stock_status: str = None,
    page: int = 1,
    per_page: int = 20,
):
    kwargs = {k: v for k, v in locals().items() if v is not None}
    return await product_tools.get_inventory(**kwargs)