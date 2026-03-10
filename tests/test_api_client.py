from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.api_client import ApiError, PowercordApiClient


@pytest.fixture
def api_client():
    return PowercordApiClient(base_url="http://testserver", api_key="test_key")


@pytest.mark.asyncio
async def test_api_client_initialization():
    client = PowercordApiClient(base_url="http://localhost:8000", api_key="secret")
    assert client.base_url == "http://localhost:8000"
    assert client.api_key == "secret"


@pytest.mark.asyncio
async def test_api_client_configuration(api_client):
    api_client.configure("https://newserver.com", "new_key")
    assert api_client.base_url == "https://newserver.com"
    assert api_client.api_key == "new_key"


@pytest.mark.asyncio
async def test_api_client_get_success(api_client):
    mock_response = httpx.Response(200, json={"status": "ok"})

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        result = await api_client.get("/test-endpoint")

        # Verify the client makes the correct request
        mock_request.assert_called_once_with("GET", "test-endpoint")
        assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_api_client_post_error(api_client):
    mock_response = httpx.Response(403, json={"detail": "Unauthorized access"})

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        with pytest.raises(ApiError, match="Unauthorized access"):
            await api_client.post("/protected-endpoint", json={"data": "test"})


@pytest.mark.asyncio
async def test_api_client_unconfigured_error():
    client = PowercordApiClient()  # No base URL
    with pytest.raises(ValueError, match="API Client is not configured with a server URL."):
        await client.get("/endpoint")


@pytest.mark.asyncio
async def test_api_client_close(api_client):
    # Initialize the client property
    _ = api_client.client
    assert api_client._client is not None

    await api_client.close()
    assert api_client._client is None
