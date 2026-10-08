"""Tests for rate limiting and retry logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import Response, Headers
import asyncio

from app.services.rate_limiter import RateLimitHandler, RateLimitExceeded, RetryConfig


@pytest.fixture
def rate_limiter():
    config = RetryConfig(max_retries=2, base_delay=0.01, max_delay=0.1)
    return RateLimitHandler(config)


@pytest.mark.asyncio
async def test_successful_request_no_retry(rate_limiter):
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    
    mock_func = AsyncMock(return_value=mock_response)
    
    result = await rate_limiter.execute_with_retry(mock_func)
    
    assert result == mock_response
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_429_triggers_retry(rate_limiter):
    responses = [
        create_mock_429(),
        create_mock_429(),
        create_mock_200(),
    ]
    mock_func = AsyncMock(side_effect=responses)
    
    result = await rate_limiter.execute_with_retry(mock_func)
    
    assert result.status_code == 200
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_429_max_retries_exceeded(rate_limiter):
    mock_response = create_mock_429()
    mock_func = AsyncMock(return_value=mock_response)
    
    with pytest.raises(RateLimitExceeded) as exc_info:
        await rate_limiter.execute_with_retry(mock_func)
    
    assert mock_func.call_count == 3
    assert "Rate limit exceeded" in str(exc_info.value)


@pytest.mark.asyncio
async def test_500_triggers_retry(rate_limiter):
    responses = [
        create_mock_response(500),
        create_mock_200(),
    ]
    mock_func = AsyncMock(side_effect=responses)
    
    result = await rate_limiter.execute_with_retry(mock_func)
    
    assert result.status_code == 200
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_400_no_retry(rate_limiter):
    mock_response = create_mock_response(400, {"message": "Bad request"})
    mock_func = AsyncMock(return_value=mock_response)
    
    result = await rate_limiter.execute_with_retry(mock_func)
    
    assert result.status_code == 400
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_retry_after_header_respected(rate_limiter):
    response = create_mock_429(headers={"Retry-After": "5"})
    mock_func = AsyncMock(return_value=response)
    
    with pytest.raises(RateLimitExceeded):
        await rate_limiter.execute_with_retry(mock_func)
    
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_exception_during_request_retries(rate_limiter):
    mock_func = AsyncMock(side_effect=[Exception("Network error"), create_mock_200()])
    
    result = await rate_limiter.execute_with_retry(mock_func)
    
    assert result.status_code == 200
    assert mock_func.call_count == 2


def create_mock_200():
    response = MagicMock(spec=Response)
    response.status_code = 200
    response.headers = Headers({})
    return response


def create_mock_429(headers=None):
    response = MagicMock(spec=Response)
    response.status_code = 429
    response.headers = Headers(headers or {})
    return response


def create_mock_response(status_code, json_data=None):
    response = MagicMock(spec=Response)
    response.status_code = status_code
    response.headers = Headers({})
    response.json.return_value = json_data or {}
    return response