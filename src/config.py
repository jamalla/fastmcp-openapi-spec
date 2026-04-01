"""Configuration and OpenAPI spec loading."""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# API settings
API_TOKEN = os.getenv("SALLA_API_TOKEN", "")
BASE_URL = os.getenv("SALLA_BASE_URL", "https://api.salla.dev/v2")
TIMEOUT = float(os.getenv("API_TIMEOUT", "30"))

# Server settings
HOST = os.getenv("SERVER_HOST", "0.0.0.0")
PORT = int(os.getenv("SERVER_PORT", "8000"))

# Load OpenAPI spec
SPEC_PATH = os.getenv("OPENAPI_SPEC_PATH", "./openapi.json")
_spec_path = Path(SPEC_PATH)
if not _spec_path.exists():
    print(f"Error: OpenAPI spec not found at {SPEC_PATH}", file=sys.stderr)
    sys.exit(1)

with open(_spec_path, encoding="utf-8") as f:
    OPENAPI_SPEC = json.load(f)

PATHS: dict = OPENAPI_SPEC.get("paths", {})
print(f"Loaded OpenAPI spec – {len(PATHS)} endpoints")
