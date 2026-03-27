"""
OpenAPI specification loader and manager.
Handles loading, parsing, and querying the OpenAPI specification.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..utils import OpenAPSpecError, get_logger

logger = get_logger(__name__)


class OpenAPILoader:
    """Load and manage OpenAPI specifications."""

    def __init__(self):
        """Initialize the loader."""
        self.spec: Dict[str, Any] = {}
        self.paths: Dict[str, Dict] = {}

    def load_from_file(self, spec_path: str) -> Dict[str, Any]:
        """
        Load OpenAPI specification from file.

        Args:
            spec_path: Path to OpenAPI JSON file

        Returns:
            Loaded specification dictionary

        Raises:
            OpenAPSpecError: If file cannot be read or parsed
        """
        try:
            path = Path(spec_path)

            if not path.exists():
                raise OpenAPSpecError(f"OpenAPI spec not found at {spec_path}")

            with open(path, "r", encoding="utf-8") as f:
                self.spec = json.load(f)

            # Validate basic structure
            if "openapi" not in self.spec:
                raise OpenAPSpecError("Invalid OpenAPI spec: missing 'openapi' version")

            # Cache paths
            self.paths = self.spec.get("paths", {})

            logger.info(
                f"Loaded OpenAPI spec version {self.spec['openapi']}",
                extra={"extra_fields": {"endpoint_count": len(self.paths)}},
            )

            return self.spec

        except json.JSONDecodeError as e:
            raise OpenAPSpecError(f"Failed to parse OpenAPI spec JSON: {str(e)}")
        except IOError as e:
            raise OpenAPSpecError(f"Failed to read OpenAPI spec file: {str(e)}")

    def get_spec(self) -> Dict[str, Any]:
        """Get loaded specification."""
        return self.spec

    def get_info(self) -> Dict[str, Any]:
        """Get API information from spec."""
        return self.spec.get("info", {})

    def get_paths(self) -> Dict[str, Dict]:
        """Get all paths from spec."""
        return self.paths

    def get_path_item(self, path: str) -> Optional[Dict]:
        """Get specific path item."""
        return self.paths.get(path)

    def search_endpoints(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for endpoints matching query.

        Args:
            query: Search query (matches path, summary, description, tags)
            limit: Maximum number of results

        Returns:
            List of matching endpoints
        """
        results = []
        query_lower = query.lower()

        for path, path_item in self.paths.items():
            if len(results) >= limit:
                break

            for method in ["get", "post", "put", "delete", "patch"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                summary = operation.get("summary", "").lower()
                description = operation.get("description", "").lower()
                tags = [tag.lower() for tag in operation.get("tags", [])]

                # Check if query matches
                match_found = (
                    query_lower in path.lower()
                    or query_lower in summary
                    or query_lower in description
                    or any(query_lower in tag for tag in tags)
                )

                if match_found:
                    results.append(
                        {
                            "path": path,
                            "method": method.upper(),
                            "summary": operation.get("summary", ""),
                            "description": operation.get("description", ""),
                            "tags": operation.get("tags", []),
                            "parameters": operation.get("parameters", []),
                            "requestBody": operation.get("requestBody"),
                            "responses": operation.get("responses", {}),
                        }
                    )
                    if len(results) >= limit:
                        break

        logger.info(
            f"Search completed",
            extra={"extra_fields": {"query": query, "results": len(results)}},
        )

        return results[:limit]

    def get_operation(self, path: str, method: str) -> Optional[Dict]:
        """
        Get specific operation by path and method.

        Args:
            path: Endpoint path
            method: HTTP method

        Returns:
            Operation definition or None
        """
        path_item = self.paths.get(path)
        if not path_item:
            return None

        return path_item.get(method.lower())
