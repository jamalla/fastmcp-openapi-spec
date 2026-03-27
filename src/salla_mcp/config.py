"""
Configuration management for Salla MCP Server.
Uses Pydantic settings for environment-based configuration.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Server configuration."""

    # API Configuration
    salla_api_token: str = Field(
        default="",
        description="Bearer token for Salla API authentication",
        alias="SALLA_API_TOKEN",
    )
    salla_base_url: str = Field(
        default="https://api.salla.dev/v2",
        description="Base URL for Salla API",
        alias="SALLA_BASE_URL",
    )
    openapi_spec_path: str = Field(
        default="./openapi.json",
        description="Path to OpenAPI specification file",
        alias="OPENAPI_SPEC_PATH",
    )

    # Server Configuration
    server_host: str = Field(
        default="localhost",
        description="Server host",
        alias="SERVER_HOST",
    )
    server_port: int = Field(
        default=8000,
        description="Server port",
        alias="SERVER_PORT",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        alias="LOG_LEVEL",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json, text)",
        alias="LOG_FORMAT",
    )

    # API Client Configuration
    api_timeout: float = Field(
        default=30.0,
        description="API request timeout in seconds",
        alias="API_TIMEOUT",
    )
    api_retries: int = Field(
        default=0,
        description="Number of retries for API calls",
        alias="API_RETRIES",
    )

    # Feature Flags
    enable_request_validation: bool = Field(
        default=True,
        description="Enable request parameter validation",
        alias="ENABLE_REQUEST_VALIDATION",
    )
    enable_response_validation: bool = Field(
        default=True,
        description="Enable response validation against schema",
        alias="ENABLE_RESPONSE_VALIDATION",
    )
    enable_metrics: bool = Field(
        default=False,
        description="Enable metrics collection",
        alias="ENABLE_METRICS",
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    def validate_required_fields(self) -> None:
        """Validate that required fields are set."""
        if not self.salla_api_token:
            raise ValueError("SALLA_API_TOKEN environment variable is required")
