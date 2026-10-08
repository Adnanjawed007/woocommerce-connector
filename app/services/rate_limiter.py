"""Rate limiting and retry logic for WooCommerce API."""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass
from httpx import Response

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0


class RateLimitHandler:
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    def is_retryable(self, response: Response) -> bool:
        if response.status_code == 429:
            return True
        if response.status_code >= 500:
            return True
        return False

    def get_retry_after(self, response: Response) -> Optional[float]:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return None

    def calculate_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
        if retry_after is not None:
            return min(retry_after, self.config.max_delay)
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        return min(delay, self.config.max_delay)

    async def execute_with_retry(self, func, *args, **kwargs) -> Response:
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await func(*args, **kwargs)
                
                if self.is_retryable(response):
                    if attempt < self.config.max_retries:
                        retry_after = self.get_retry_after(response)
                        delay = self.calculate_delay(attempt, retry_after)
                        
                        logger.warning(
                            f"Rate limited (attempt {attempt + 1}/{self.config.max_retries + 1}). "
                            f"Retrying in {delay:.1f}s. Status: {response.status_code}"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise RateLimitExceeded(
                            f"Rate limit exceeded after {self.config.max_retries} retries",
                            retry_after=retry_after,
                            response=response
                        )
                
                return response
                
            except RateLimitExceeded:
                raise
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.config.max_retries} retries: {e}")
                    raise
        
        raise last_exception


class RateLimitExceeded(Exception):
    def __init__(self, message: str, retry_after: Optional[float] = None, response: Optional[Response] = None):
        super().__init__(message)
        self.retry_after = retry_after
        self.response = response