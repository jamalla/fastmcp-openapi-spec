"""MCP tools: search, execute, and domain-specific helpers."""

from datetime import datetime

import httpx

from .config import API_TOKEN, BASE_URL, PATHS, TIMEOUT


async def _api_get(endpoint: str, params: dict | None = None) -> dict:
    """Internal helper: make an authenticated GET request to the Salla API."""
    if not API_TOKEN:
        return {"error": "SALLA_API_TOKEN is not configured"}
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=headers)
        if resp.status_code >= 400:
            try:
                err = resp.json()
                msg = err.get("message") or err.get("error") or resp.text
            except Exception:
                msg = resp.text or f"HTTP {resp.status_code}"
            return {"error": msg, "statusCode": resp.status_code}
        return resp.json() if resp.text else {}
    except httpx.ConnectError as e:
        return {"error": f"Connection failed: {e}"}
    except httpx.TimeoutException:
        return {"error": "Request timed out"}


def search(query: str, limit: int = 10) -> dict:
    """Search available API endpoints in the OpenAPI specification.

    Returns matching endpoints with path, method, summary, parameters,
    and request body details so you know how to call them via `execute`.

    Args:
        query: Search term (matches path, summary, description, tags)
        limit: Maximum results to return (1-100, default 10)
    """
    limit = max(1, min(limit, 100))
    q = query.strip().lower()
    match_all = q in ("*", "")
    results = []

    for path, path_item in PATHS.items():
        if len(results) >= limit:
            break
        for method in ("get", "post", "put", "delete", "patch"):
            if method not in path_item:
                continue
            op = path_item[method]
            if not match_all:
                searchable = " ".join(
                    [
                        path.lower(),
                        op.get("summary", "").lower(),
                        op.get("description", "").lower(),
                        " ".join(t.lower() for t in op.get("tags", [])),
                    ]
                )
            if match_all or q in searchable:
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

    # Count total endpoints in the spec
    total = sum(
        1
        for pi in PATHS.values()
        for m in ("get", "post", "put", "delete", "patch")
        if m in pi
    )

    return {
        "results": results,
        "count": len(results),
        "total_endpoints": total,
        "query": query,
    }


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


# ---------------------------------------------------------------------------
# Domain-specific tools — higher-level shortcuts
# ---------------------------------------------------------------------------

async def list_orders(status: str = "", limit: int = 10) -> dict:
    """List orders from the store, optionally filtered by status.

    Returns order id, reference_id, total, status, and date for each order,
    plus pagination info showing total count.

    Args:
        status: Filter by order status (e.g. completed, pending, in_progress, canceled). Leave empty for all.
        limit: Number of orders to return (1-50, default 10)
    """
    limit = max(1, min(limit, 50))
    params: dict = {"per_page": limit}
    if status.strip():
        params["status"] = status.strip()

    data = await _api_get("/orders", params=params)
    if "error" in data:
        return data

    orders_raw = data.get("data", [])
    pagination = data.get("pagination", {})

    orders = []
    for o in orders_raw:
        orders.append({
            "id": o.get("id"),
            "reference_id": o.get("reference_id"),
            "status": o.get("status", {}).get("name") if isinstance(o.get("status"), dict) else o.get("status"),
            "total": f"{o['total']['amount']} {o['total'].get('currency', '')}" if isinstance(o.get("total"), dict) else o.get("total"),
            "date": o.get("date", {}).get("date") if isinstance(o.get("date"), dict) else o.get("date", o.get("created_at")),
        })

    return {
        "orders": orders,
        "count": len(orders),
        "total_orders": pagination.get("total", len(orders)),
        "page": pagination.get("currentPage", 1),
        "total_pages": pagination.get("totalPages"),
    }


async def store_dashboard() -> dict:
    """Get a quick dashboard overview of the store.

    Returns product count, order count with recent orders, and basic store info
    — all in a single call. Useful for getting a snapshot of the store.
    """
    import asyncio

    async def _get_products():
        return await _api_get("/products", params={"per_page": 1})

    async def _get_orders():
        return await _api_get("/orders", params={"per_page": 5})

    async def _get_store():
        return await _api_get("/store")

    products_data, orders_data, store_data = await asyncio.gather(
        _get_products(), _get_orders(), _get_store()
    )

    products_total = 0
    if "error" not in products_data:
        products_total = products_data.get("pagination", {}).get("total", 0)

    orders_total = 0
    recent_orders = []
    if "error" not in orders_data:
        orders_total = orders_data.get("pagination", {}).get("total", 0)
        for o in orders_data.get("data", [])[:5]:
            recent_orders.append({
                "id": o.get("id"),
                "reference_id": o.get("reference_id"),
                "status": o.get("status", {}).get("name") if isinstance(o.get("status"), dict) else o.get("status"),
                "total": f"{o['total']['amount']} {o['total'].get('currency', '')}" if isinstance(o.get("total"), dict) else o.get("total"),
            })

    store_info = {}
    if "error" not in store_data:
        sd = store_data.get("data", store_data)
        store_info = {
            "name": sd.get("name"),
            "domain": sd.get("domain"),
            "plan": sd.get("plan"),
        }

    return {
        "store": store_info,
        "total_products": products_total,
        "total_orders": orders_total,
        "recent_orders": recent_orders,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


async def sales_report(date_from: str, date_to: str) -> dict:
    """Generate a sales summary report for a date range.

    Fetches orders within the specified period and calculates totals,
    average order value, and status breakdown.

    Args:
        date_from: Start date in YYYY-MM-DD format (e.g. 2025-01-01)
        date_to: End date in YYYY-MM-DD format (e.g. 2025-12-31)
    """
    params: dict = {"per_page": 50}
    if date_from.strip():
        params["from"] = date_from.strip()
    if date_to.strip():
        params["to"] = date_to.strip()

    data = await _api_get("/orders", params=params)
    if "error" in data:
        return data

    orders = data.get("data", [])
    pagination = data.get("pagination", {})
    total_orders = pagination.get("total", len(orders))

    total_revenue = 0.0
    currency = "SAR"
    status_counts: dict[str, int] = {}

    for o in orders:
        total_field = o.get("total", {})
        if isinstance(total_field, dict):
            try:
                total_revenue += float(total_field.get("amount", 0))
            except (ValueError, TypeError):
                pass
            currency = total_field.get("currency", currency)
        elif total_field:
            try:
                total_revenue += float(total_field)
            except (ValueError, TypeError):
                pass

        status = o.get("status", {})
        status_name = status.get("name") if isinstance(status, dict) else str(status)
        status_counts[status_name] = status_counts.get(status_name, 0) + 1

    avg_order = round(total_revenue / len(orders), 2) if orders else 0

    return {
        "period": {"from": date_from, "to": date_to},
        "total_orders": total_orders,
        "orders_in_sample": len(orders),
        "revenue_in_sample": f"{round(total_revenue, 2)} {currency}",
        "average_order_value": f"{avg_order} {currency}",
        "status_breakdown": status_counts,
        "note": f"Revenue calculated from {len(orders)} most recent orders in this period. Total orders: {total_orders}.",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
