"""
Pytest configuration and shared fixtures.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from salla_mcp.config import Settings


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        salla_api_token="test-token",
        salla_base_url="https://api.test.salla.dev/v2",
        openapi_spec_path="./openapi.json",
        log_level="DEBUG",
    )
