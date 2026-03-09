import logging
from typing import Any, Dict, Optional

import httpx


class ApiError(Exception):
    """Raised when the API returns an error response."""

    pass


class PowercordApiClient:
    """
    Core HTTP Client for communicating with a Powercord server.
    Handles base URL joining, authentication headers, and standard error parsing.
    """

    def __init__(self, base_url: str = "", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    def configure(self, base_url: str, api_key: str):
        """Update the client configuration."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        if self._client:
            self._client.base_url = httpx.URL(self.base_url)
            self._client.headers["Authorization"] = f"Bearer {self.api_key}"

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy initialization of the highly-reusable AsyncClient."""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers)
        return self._client

    async def close(self):
        """Close the underlying HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _prepare_url(self, endpoint: str) -> str:
        if endpoint.startswith("http"):
            return endpoint
        return endpoint.lstrip("/")

    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Perform a GET request."""
        return await self._request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Perform a POST request."""
        return await self._request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Perform a PUT request."""
        return await self._request("PUT", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Perform a DELETE request."""
        return await self._request("DELETE", endpoint, **kwargs)

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Internal method to handle requests and error parsing."""
        if not self.base_url:
            raise ValueError("API Client is not configured with a server URL.")

        url = self._prepare_url(endpoint)
        try:
            response = await self.client.request(method, url, **kwargs)

            # Try parsing JSON on success or failure, as FastAPI often returns JSON errors
            try:
                data = response.json()
            except Exception:
                data = {"detail": response.text}

            if not response.is_success:
                error_msg = data.get("detail", f"HTTP Error {response.status_code}")
                logging.error(f"API Error ({method} {endpoint}): {error_msg}")
                raise ApiError(error_msg)

            from typing import cast

            return cast(Dict[str, Any], data)

        except httpx.RequestError as e:
            logging.error(f"Request Error ({method} {endpoint}): {str(e)}")
            raise ApiError(f"Network error: {str(e)}") from e


# Singleton instance for the application to share
api = PowercordApiClient()
