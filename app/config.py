"""Configuration management for WooCommerce connector."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, HttpUrl
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    woocommerce_url: HttpUrl = Field(
        ...,
        description="Base URL of the WooCommerce store (e.g., https://store.example.com)",
    )
    woocommerce_consumer_key: str = Field(
        ...,
        min_length=1,
        description="WooCommerce REST API consumer key",
    )
    woocommerce_consumer_secret: str = Field(
        ...,
        min_length=1,
        description="WooCommerce REST API consumer secret",
    )

    request_timeout: float = Field(
        default=30.0,
        gt=0,
        le=300,
        description="HTTP request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for rate-limited requests",
    )
    base_retry_delay: float = Field(
        default=1.0,
        gt=0,
        le=60,
        description="Base delay for exponential backoff in seconds",
    )

    @property
    def wc_api_base(self) -> str:
        """Return the WooCommerce REST API base URL."""
        return f"{str(self.woocommerce_url).rstrip('/')}/wp-json/wc/v3"


settings = Settings()