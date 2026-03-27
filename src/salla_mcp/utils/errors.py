"""
Custom exceptions for Salla MCP Server.
"""


class SallaMCPException(Exception):
    """Base exception for Salla MCP Server."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR"):
        """Initialize exception."""
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ConfigurationError(SallaMCPException):
    """Raised when configuration is invalid."""

    def __init__(self, message: str):
        """Initialize exception."""
        super().__init__(message, "CONFIGURATION_ERROR")


class OpenAPSpecError(SallaMCPException):
    """Raised when OpenAPI spec cannot be loaded or parsed."""

    def __init__(self, message: str):
        """Initialize exception."""
        super().__init__(message, "OPENAPI_SPEC_ERROR")


class SearchError(SallaMCPException):
    """Raised when search operation fails."""

    def __init__(self, message: str):
        """Initialize exception."""
        super().__init__(message, "SEARCH_ERROR")


class ExecutionError(SallaMCPException):
    """Raised when API execution fails."""

    def __init__(self, message: str, status_code: int = None):
        """Initialize exception."""
        self.status_code = status_code
        super().__init__(message, "EXECUTION_ERROR")


class AuthenticationError(SallaMCPException):
    """Raised when authentication fails."""

    def __init__(self, message: str):
        """Initialize exception."""
        super().__init__(message, "AUTHENTICATION_ERROR")


class ValidationError(SallaMCPException):
    """Raised when request validation fails."""

    def __init__(self, message: str, field: str = None):
        """Initialize exception."""
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")
