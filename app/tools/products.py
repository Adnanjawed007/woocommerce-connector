"""Product and inventory tools for Agent Studio / MCP integration."""

import logging
from typing import Dict, Any, Optional
from app.services.wc_client import WooCommerceClient, WooCommerceAPIError
from app.models.products import ProductSearchParams
from app.tools.schemas import get_tool_by_name
from app.models.common import ErrorResponse

logger = logging.getLogger(__name__)


class ProductTools:
    def __init__(self, wc_client: WooCommerceClient):
        self.client = wc_client

    async def search_products(self, **kwargs) -> Dict[str, Any]:
        try:
            params = ProductSearchParams(**kwargs)
            products, pagination = await self.client.search_products(params)
            
            data = [product.model_dump(mode="json") for product in products]
            
            return {
                "data": data,
                **pagination,
            }
        except WooCommerceAPIError as e:
            logger.error(f"search_products failed: {e.error}")
            return e.error.model_dump()
        except Exception as e:
            logger.exception("search_products unexpected error")
            return ErrorResponse(
                error=str(e),
                error_code="internal_error",
            ).model_dump()

    async def get_inventory(
        self,
        product_id: Optional[int] = None,
        low_stock_only: bool = False,
        low_stock_threshold: int = 10,
        stock_status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        try:
            if product_id:
                product = await self.client.get_product(product_id)
                data = [product.to_inventory_summary()]
                pagination = {
                    "page": 1,
                    "per_page": 1,
                    "total_pages": 1,
                    "total_items": 1,
                    "has_more": False,
                }
            else:
                params = ProductSearchParams(
                    stock_status=stock_status,
                    low_stock_only=low_stock_only,
                    low_stock_threshold=low_stock_threshold,
                    page=page,
                    per_page=per_page,
                )
                products, pagination = await self.client.search_products(params)
                if low_stock_only:
                    products = [
                        product for product in products
                        if product.manage_stock
                        and product.stock_quantity is not None
                        and product.stock_quantity <= low_stock_threshold
                    ]
                data = [product.to_inventory_summary() for product in products]
            
            return {
                "data": data,
                **pagination,
            }
        except WooCommerceAPIError as e:
            logger.error(f"get_inventory failed: {e.error}")
            return e.error.model_dump()
        except Exception as e:
            logger.exception("get_inventory unexpected error")
            return ErrorResponse(
                error=str(e),
                error_code="internal_error",
            ).model_dump()

    def get_schemas(self) -> list:
        return [
            get_tool_by_name("search_products").model_dump(),
            get_tool_by_name("get_inventory").model_dump(),
        ]
