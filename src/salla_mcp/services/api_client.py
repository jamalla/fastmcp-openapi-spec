"""
HTTP API client for calling Salla API endpoints.
Handles authentication, retries, and error handling.
"""

import httpx
from typing import Optional, Dict, Any
from ..utils import ExecutionError, AuthenticationError, get_logger
from ..config import Settings

logger = get_logger(__name__)


class APIClient:
    """HTTP client for API requests."""

    def __init__(self, settings: Settings):
        """
        Initialize API client.

        Args:
            settings: Server configuration
        """
        self.settings = settings
        self.base_url = settings.salla_base_url
        self.token = settings.salla_api_token
        self.timeout = settings.api_timeout

        if not self.token:
            raise AuthenticationError("SALLA_API_TOKEN is not configured")

    async def request(
        self,
        method: str,
        endpoint: str,
        parameters: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            parameters: Query/path parameters
            body: Request body for POST/PUT/PATCH

        Returns:
            API response

        Raises:
            ExecutionError: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "Salla-MCP-Server/1.0.0",
        }

        try:
            logger.info(
                f"Making {method} request",
                extra={"extra_fields": {"url": url, "method": method}},
            )

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    params=parameters,
                    json=body,
                    headers=headers,
                )

            # Check for HTTP errors
            if response.status_code >= 400:
                error_msg = self._extract_error_message(response)
                logger.error(
                    f"API request failed",
                    extra={
                        "extra_fields": {
                            "status_code": response.status_code,
                            "error": error_msg,
                        }
                    },
                )

                if response.status_code == 401:
                    raise AuthenticationError("Invalid API token")
                else:
                    raise ExecutionError(error_msg, response.status_code)

            logger.info(
                f"API request succeeded",
                extra={"extra_fields": {"status_code": response.status_code}},
            )

            return {
                "status": "success",
                "statusCode": response.status_code,
                "data": response.json() if response.text else None,
            }

        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to API: {str(e)}"
            logger.error(error_msg)
            raise ExecutionError(error_msg)
        except httpx.TimeoutException as e:
            error_msg = f"API request timed out: {str(e)}"
            logger.error(error_msg)
            raise ExecutionError(error_msg)
        except Exception as e:
            error_msg = f"API request failed: {str(e)}"
            logger.error(error_msg)
            raise ExecutionError(error_msg)

    def _extract_error_message(self, response: httpx.Response) -> str:
        """Extract error message from response."""
        try:
            data = response.json()
            if isinstance(data, dict):
                return data.get("message") or data.get("error") or response.text
        except Exception:
            pass
        return response.text or f"HTTP {response.status_code}"
