"""Tests for configuration management."""

import pytest
from pydantic import ValidationError
from app.config import Settings


def test_settings_loads_from_env(monkeypatch):
    """Test settings load correctly from environment."""
    monkeypatch.setenv("WOOCOMMERCE_URL", "https://test.example.com")
    monkeypatch.setenv("WOOCOMMERCE_CONSUMER_KEY", "ck_test")
    monkeypatch.setenv("WOOCOMMERCE_CONSUMER_SECRET", "cs_test")
    
    settings = Settings()
    
    # Pydantic HttpUrl normalizes with trailing slash
    assert str(settings.woocommerce_url).rstrip('/') == "https://test.example.com"
    assert settings.woocommerce_consumer_key == "ck_test"
    assert settings.woocommerce_consumer_secret == "cs_test"


def test_settings_defaults(monkeypatch):
    """Test default values for optional settings."""
    monkeypatch.setenv("WOOCOMMERCE_URL", "https://test.example.com")
    monkeypatch.setenv("WOOCOMMERCE_CONSUMER_KEY", "ck_test")
    monkeypatch.setenv("WOOCOMMERCE_CONSUMER_SECRET", "cs_test")
    
    settings = Settings()
    
    assert settings.request_timeout == 30.0
    assert settings.max_retries == 3
    assert settings.base_retry_delay == 1.0


def test_settings_validation_errors(monkeypatch):
    """Test validation errors for missing/invalid settings."""
    # Clear any existing env vars
    monkeypatch.delenv("WOOCOMMERCE_URL", raising=False)
    monkeypatch.delenv("WOOCOMMERCE_CONSUMER_KEY", raising=False)
    monkeypatch.delenv("WOOCOMMERCE_CONSUMER_SECRET", raising=False)
    
    # Missing required fields should raise ValidationError
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
    
    # Invalid URL
    monkeypatch.setenv("WOOCOMMERCE_URL", "not-a-url")
    monkeypatch.setenv("WOOCOMMERCE_CONSUMER_KEY", "ck_test")
    monkeypatch.setenv("WOOCOMMERCE_CONSUMER_SECRET", "cs_test")
    
    with pytest.raises(ValidationError):
        Settings()


def test_wc_api_base_property(monkeypatch):
    """Test wc_api_base property construction."""
    monkeypatch.setenv("WOOCOMMERCE_URL", "https://test.example.com/")
    monkeypatch.setenv("WOOCOMMERCE_CONSUMER_KEY", "ck_test")
    monkeypatch.setenv("WOOCOMMERCE_CONSUMER_SECRET", "cs_test")
    
    settings = Settings()
    assert settings.wc_api_base == "https://test.example.com/wp-json/wc/v3"
    
    # Without trailing slash
    monkeypatch.setenv("WOOCOMMERCE_URL", "https://test.example.com")
    settings = Settings()
    assert settings.wc_api_base == "https://test.example.com/wp-json/wc/v3"
