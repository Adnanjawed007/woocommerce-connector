"""WooCommerce REST API client with authentication and rate limiting."""

import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
import httpx
from pydantic import ValidationError

from app.config import settings
from app.services.rate_limiter import RateLimitHandler, RateLimitExceeded, RetryConfig
from app.models.common import ErrorResponse
from app.models.orders import Order, OrderSearchParams
from app.models.products import Product, ProductSearchParams

logger = logging.getLogger(__name__)


class WooCommerceClient:
    def __init__(self):
        self.base_url = settings.wc_api_base
        self.auth = (settings.woocommerce_consumer_key, settings.woocommerce_consumer_secret)
        self.timeout = settings.request_timeout
        
        retry_config = RetryConfig(
            max_retries=settings.max_retries,
            base_delay=settings.base_retry_delay,
        )
        self.rate_limiter = RateLimitHandler(retry_config)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        # AsyncMock (used by callers and tests) manufactures a truthy
        # ``is_closed`` attribute. Only replace a real client when it is
        # explicitly closed.
        if self._client is None or getattr(self._client, "is_closed", False) is True:
            self._client = httpx.AsyncClient(
                auth=self.auth,
                timeout=self.timeout,
                headers={
                    "User-Agent": "Razorpay-FDE-WooCommerce-Connector/1.0",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        client = await self._get_client()
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        
        async def _do_request():
            return await client.request(method, url, params=params)
        
        return await self.rate_limiter.execute_with_retry(_do_request)

    def _handle_response(self, response: httpx.Response, model_class=None) -> Any:
        if response.is_success:
            data = response.json()
            if model_class:
                if isinstance(data, list):
                    return [model_class.model_validate(item) for item in data]
                return model_class.model_validate(data)
            return data
        
        try:
            error_data = response.json()
            message = error_data.get("message", f"HTTP {response.status_code}")
            code = error_data.get("code", "unknown_error")
        except Exception:
            message = f"HTTP {response.status_code}: {response.text[:200]}"
            code = f"http_{response.status_code}"
        
        error = ErrorResponse(
            error=message,
            error_code=code,
            details={"status_code": response.status_code},
            retry_after=None,
        )
        
        if response.status_code == 429:
            retry_after = self.rate_limiter.get_retry_after(response)
            error.retry_after = retry_after
            raise RateLimitExceeded(message, retry_after=retry_after, response=response)
        
        raise WooCommerceAPIError(error)

    async def get_order(self, order_id: int) -> Order:
        logger.info(f"Fetching order {order_id}")
        response = await self._request("GET", f"orders/{order_id}")
        return self._handle_response(response, Order)

    async def search_orders(self, params: OrderSearchParams) -> tuple[List[Order], Dict[str, Any]]:
        logger.info(f"Searching orders with params: {params.model_dump(exclude_none=True)}")
        
        query_params = params.model_dump(exclude_none=True, mode="json")
        
        if params.date_from:
            query_params["after"] = params.date_from.isoformat()
            del query_params["date_from"]
        if params.date_to:
            query_params["before"] = params.date_to.isoformat()
            del query_params["date_to"]
        
        if params.min_amount is not None:
            query_params["min_total"] = format(params.min_amount, "g")
            del query_params["min_amount"]
        if params.max_amount is not None:
            query_params["max_total"] = format(params.max_amount, "g")
            del query_params["max_amount"]
        
        response = await self._request("GET", "orders", params=query_params)
        
        total_pages = int(response.headers.get("X-WP-TotalPages", "1"))
        total_items = int(response.headers.get("X-WP-Total", "0"))
        
        orders = self._handle_response(response, Order)
        
        pagination_info = {
            "page": params.page,
            "per_page": params.per_page,
            "total_pages": total_pages,
            "total_items": total_items,
            "has_more": params.page < total_pages,
        }
        
        return orders, pagination_info

    async def get_product(self, product_id: int) -> Product:
        logger.info(f"Fetching product {product_id}")
        response = await self._request("GET", f"products/{product_id}")
        return self._handle_response(response, Product)

    async def search_products(self, params: ProductSearchParams) -> tuple[List[Product], Dict[str, Any]]:
        logger.info(f"Searching products with params: {params.model_dump(exclude_none=True)}")
        
        query_params = params.model_dump(exclude_none=True, mode="json")
        
        if params.low_stock_only:
            query_params["per_page"] = min(params.per_page, 50)
        
        response = await self._request("GET", "products", params=query_params)
        
        total_pages = int(response.headers.get("X-WP-TotalPages", "1"))
        total_items = int(response.headers.get("X-WP-Total", "0"))
        
        products = self._handle_response(response, Product)
        
        if params.low_stock_only:
            products = [
                p for p in products 
                if p.manage_stock and p.stock_quantity is not None and p.stock_quantity <= params.low_stock_threshold
            ]
            total_items = len(products)
            total_pages = 1
        
        pagination_info = {
            "page": params.page,
            "per_page": params.per_page,
            "total_pages": total_pages,
            "total_items": total_items,
            "has_more": params.page < total_pages,
        }
        
        return products, pagination_info

    async def health_check(self) -> Dict[str, Any]:
        try:
            response = await self._request("GET", "system_status")
            self._handle_response(response)
            return {"status": "healthy", "authenticated": True}
        except WooCommerceAPIError as e:
            if e.error.error_code in ("woocommerce_rest_cannot_view", "woocommerce_rest_authentication_error"):
                return {"status": "unauthorized", "authenticated": False, "error": str(e.error)}
            return {"status": "error", "authenticated": False, "error": str(e.error)}
        except Exception as e:
            return {"status": "error", "authenticated": False, "error": str(e)}


class WooCommerceAPIError(Exception):
    def __init__(self, error: ErrorResponse):
        self.error = error
        super().__init__(error.error)
