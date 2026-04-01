"""MCP tools: search and execute."""

import httpx

from .config import API_TOKEN, BASE_URL, PATHS, TIMEOUT


def search(query: str, limit: int = 10) -> dict:
    """Search available API endpoints in the OpenAPI specification.

    Returns matching endpoints with path, method, summary, parameters,
    and request body details so you know how to call them via `execute`.

    Args:
        query: Search term (matches path, summary, description, tags)
        limit: Maximum results to return (1-100, default 10)
    """
    limit = max(1, min(limit, 100))
    q = query.lower()
    results = []

    for path, path_item in PATHS.items():
        if len(results) >= limit:
            break
        for method in ("get", "post", "put", "delete", "patch"):
            if method not in path_item:
                continue
            op = path_item[method]
            searchable = " ".join(
                [
                    path.lower(),
                    op.get("summary", "").lower(),
                    op.get("description", "").lower(),
                    " ".join(t.lower() for t in op.get("tags", [])),
                ]
            )
            if q in searchable:
                results.append(
                    {
                        "path": path,
                        "method": method.upper(),
                        "summary": op.get("summary", ""),
                        "description": op.get("description", ""),
                        "tags": op.get("tags", []),
                        "parameters": op.get("parameters", []),
                        "requestBody": op.get("requestBody"),
                    }
                )
                if len(results) >= limit:
                    break

    return {"results": results, "count": len(results), "query": query}


async def execute(
    endpoint: str,
    method: str = "GET",
    parameters: dict | None = None,
    body: dict | None = None,
) -> dict:
    """Execute an API endpoint call with authentication.

    Use `search` first to discover available endpoints and their parameters.

    Args:
        endpoint: API path (e.g. /products, /orders/{id})
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        parameters: Query or path parameters as key-value pairs
        body: Request body for POST/PUT/PATCH
    """
    if not endpoint.startswith("/"):
        return {"error": "Endpoint must start with /"}

    if not API_TOKEN:
        return {"error": "SALLA_API_TOKEN is not configured"}

    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.request(
                method=method.upper(),
                url=url,
                params=parameters,
                json=body,
                headers=headers,
            )

        if resp.status_code >= 400:
            try:
                err = resp.json()
                msg = err.get("message") or err.get("error") or resp.text
            except Exception:
                msg = resp.text or f"HTTP {resp.status_code}"
            return {"error": msg, "statusCode": resp.status_code}

        return {
            "status": "success",
            "statusCode": resp.status_code,
            "data": resp.json() if resp.text else None,
        }
    except httpx.ConnectError as e:
        return {"error": f"Connection failed: {e}"}
    except httpx.TimeoutException:
        return {"error": "Request timed out"}
