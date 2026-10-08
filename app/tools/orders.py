"""Order tools for Agent Studio / MCP integration."""

import logging
from typing import Dict, Any
from app.services.wc_client import WooCommerceClient, WooCommerceAPIError
from app.models.orders import OrderSearchParams
from app.tools.schemas import get_tool_by_name
from app.models.common import ErrorResponse

logger = logging.getLogger(__name__)


class OrderTools:
    def __init__(self, wc_client: WooCommerceClient):
        self.client = wc_client

    async def search_orders(self, **kwargs) -> Dict[str, Any]:
        try:
            params = OrderSearchParams(**kwargs)
            orders, pagination = await self.client.search_orders(params)
            
            data = [order.to_agent_summary() for order in orders]
            
            return {
                "data": data,
                **pagination,
            }
        except WooCommerceAPIError as e:
            logger.error(f"search_orders failed: {e.error}")
            return e.error.model_dump()
        except Exception as e:
            logger.exception("search_orders unexpected error")
            return ErrorResponse(
                error=str(e),
                error_code="internal_error",
            ).model_dump()

    async def get_order(self, order_id: int) -> Dict[str, Any]:
        try:
            order = await self.client.get_order(order_id)
            return order.model_dump(mode="json")
        except WooCommerceAPIError as e:
            logger.error(f"get_order failed: {e.error}")
            return e.error.model_dump()
        except Exception as e:
            logger.exception("get_order unexpected error")
            return ErrorResponse(
                error=str(e),
                error_code="internal_error",
            ).model_dump()

    def get_schemas(self) -> list:
        return [
            get_tool_by_name("search_orders").model_dump(),
            get_tool_by_name("get_order").model_dump(),
        ]