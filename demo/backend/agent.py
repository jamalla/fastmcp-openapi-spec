"""
Demo Backend — FastAPI agent that uses the Salla MCP server.

Connects to the MCP server (streamable-http) and exposes a chat endpoint
that the frontend calls. Uses Gemini for reasoning.
"""

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

# ---------------------------------------------------------------------------
# Persistent HTTP clients — avoid connection overhead per request
# ---------------------------------------------------------------------------
_mcp_client: httpx.AsyncClient | None = None
_llm_client: httpx.AsyncClient | None = None


async def _get_mcp_client() -> httpx.AsyncClient:
    global _mcp_client
    if _mcp_client is None or _mcp_client.is_closed:
        _mcp_client = httpx.AsyncClient(timeout=30)
    return _mcp_client


async def _get_llm_client() -> httpx.AsyncClient:
    global _llm_client
    if _llm_client is None or _llm_client.is_closed:
        _llm_client = httpx.AsyncClient(
            timeout=60,
            base_url="https://generativelanguage.googleapis.com",
            headers={
                "Authorization": f"Bearer {GEMINI_API_KEY}",
                "Content-Type": "application/json",
            },
        )
    return _llm_client


# ---------------------------------------------------------------------------
# MCP client — calls the MCP server over HTTP
# ---------------------------------------------------------------------------
_session_id: str | None = None


def _parse_sse_json(text: str) -> dict | None:
    """Extract JSON-RPC response from SSE event stream or plain JSON."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    for line in text.splitlines():
        if line.startswith("data: "):
            try:
                return json.loads(line[6:])
            except (json.JSONDecodeError, ValueError):
                continue
    return None


async def _mcp_post(payload: dict, session_id: str | None = None) -> tuple[dict | None, str | None]:
    """Post to MCP server, return (parsed_json, session_id)."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id

    client = await _get_mcp_client()
    resp = await client.post(MCP_SERVER_URL, json=payload, headers=headers)
    sid = resp.headers.get("mcp-session-id", session_id)
    data = _parse_sse_json(resp.text)
    return data, sid


async def _mcp_init() -> str:
    """Initialize MCP session and return session ID."""
    global _session_id
    if _session_id:
        return _session_id

    data, sid = await _mcp_post({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "demo-agent", "version": "1.0"},
        },
    })
    _session_id = sid

    await _mcp_post(
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        session_id=_session_id,
    )
    return _session_id


async def mcp_call(tool_name: str, arguments: dict) -> Any:
    """Call an MCP tool and return the result."""
    global _session_id
    session_id = await _mcp_init()

    data, _ = await _mcp_post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        },
        session_id=session_id,
    )

    if data is None:
        _session_id = None
        session_id = await _mcp_init()
        data, _ = await _mcp_post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            },
            session_id=session_id,
        )

    if data is None:
        return {"error": "Failed to get response from MCP server"}

    return data.get("result", data.get("error"))


# ---------------------------------------------------------------------------
# Tool definitions for the LLM
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_api",
            "description": "Search available API endpoints in the Salla API by keyword. Returns matching endpoints AND total_endpoints count. Use this to discover what endpoints exist before calling them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term e.g. products, orders, customers. Use '*' or empty string to match all."},
                    "limit": {"type": "integer", "description": "Max results to return (1-100, default 10)"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_api",
            "description": "Execute an API call to the Salla API. Use search_api first to discover endpoints.",
            "parameters": {
                "type": "object",
                "properties": {
                    "endpoint": {"type": "string", "description": "API path e.g. /products or /orders/123"},
                    "method": {"type": "string", "description": "HTTP method: GET, POST, PUT, DELETE, or PATCH"},
                    "parameters_json": {"type": "string", "description": "Query parameters as JSON string e.g. {\"page\": 1}"},
                    "body_json": {"type": "string", "description": "Request body as JSON string for POST/PUT/PATCH"},
                },
                "required": ["endpoint"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_orders",
            "description": "List orders from the store with optional status filter. Returns order details (id, total, status, date) and total count. Much faster than search_api + execute_api for order queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status: completed, pending, in_progress, canceled. Leave empty for all orders."},
                    "limit": {"type": "integer", "description": "Number of orders to return (1-50, default 10)"},
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "store_dashboard",
            "description": "Get a quick store overview: total products, total orders, recent orders, and store info — all in one call. Use this when the user asks for a general summary or dashboard.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sales_report",
            "description": "Generate a sales report for a date range. Returns total orders, revenue, average order value, and status breakdown. Use this for any sales/revenue questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "Start date in YYYY-MM-DD format"},
                    "date_to": {"type": "string", "description": "End date in YYYY-MM-DD format"},
                },
                "required": ["date_from", "date_to"],
                "additionalProperties": False,
            },
        },
    },
]

SYSTEM_PROMPT = """\
أنت مساعد ذكي لواجهة برمجة تطبيقات سلة للتجارة الإلكترونية.
أجب دائماً باللغة العربية.

القواعد:
1. استخدم دائماً search_api أولاً للبحث عن نقاط الوصول المناسبة.
2. استخدم execute_api مع نقطة الوصول التي وجدتها في الخطوة الأولى.
3. لا تخمن نقاط الوصول أبداً. لا تقل أنه ليس لديك صلاحية. استخدم الأدوات دائماً.
4. عند عرض النتائج، استخدم جداول markdown أو قوائم منسقة.
5. لا تعرض JSON خام أبداً. استخرج الحقول المهمة واعرضها بوضوح.
6. إذا كانت البيانات مقسمة لصفحات، أخبر المستخدم بعدد العناصر الإجمالي والصفحة الحالية.
7. للقوائم، استخدم دائماً معامل per_page أو limit (الافتراضي 10).
8. اجعل الردود مختصرة — اعرض أهم الحقول (id، الاسم، الحالة، السعر، التاريخ، الإجمالي).
9. استجابة search_api تتضمن "total_endpoints" — العدد الإجمالي لنقاط الوصول. استخدمها عندما يسأل المستخدم عن عدد الـ endpoints.
10. استخدم query "*" مع search_api لمطابقة جميع نقاط الوصول. يمكنك تعيين limit حتى 100.
11. كن فعالاً — بمجرد حصولك على البيانات المطلوبة، توقف عن استدعاء الأدوات واعرض النتائج فوراً.
12. حقل "total" في الصفحات يعطيك العدد الإجمالي — لا حاجة للبحث عن endpoints التقارير.
13. استخدم الأدوات المتخصصة عندما تكون متاحة — فهي أسرع:
    - list_orders: لعرض الطلبات (بدلاً من search_api + execute_api)
    - store_dashboard: للحصول على نظرة عامة على المتجر
    - sales_report: لتقارير المبيعات والإيرادات
14. الأدوات المتخصصة لا تحتاج search_api أولاً — استدعها مباشرة."""


def _trim_search_results(result: Any) -> Any:
    """Trim verbose fields from search results to reduce token usage."""
    if isinstance(result, dict) and "content" in result:
        for item in result.get("content", []):
            if item.get("type") == "text":
                try:
                    parsed = json.loads(item["text"])
                    if "results" in parsed:
                        for r in parsed["results"]:
                            r.pop("parameters", None)
                            r.pop("requestBody", None)
                            r.pop("description", None)
                        item["text"] = json.dumps(parsed)
                except (json.JSONDecodeError, TypeError):
                    pass
    return result


def _simplify_execute_result(result: Any) -> Any:
    """Extract and simplify API response data to reduce token usage."""
    if not isinstance(result, dict) or "content" not in result:
        return result

    for item in result.get("content", []):
        if item.get("type") != "text":
            continue
        try:
            parsed = json.loads(item["text"])
        except (json.JSONDecodeError, TypeError):
            continue

        data = parsed.get("data", parsed)
        if isinstance(data, dict):
            inner = data.get("data", data)
        else:
            inner = data

        summary = {"status": parsed.get("status", "success"), "statusCode": parsed.get("statusCode")}

        if isinstance(data, dict):
            pagination = data.get("pagination") or data.get("meta") or data.get("cursor")
            if pagination:
                summary["pagination"] = pagination

        KEY_FIELDS = {"id", "name", "title", "status", "price", "total", "quantity",
                      "email", "phone", "date", "created_at", "updated_at", "slug",
                      "reference_id", "sku", "type", "source", "currency", "amount",
                      "url", "image", "thumbnail", "description"}

        if isinstance(inner, list):
            simplified = []
            for obj in inner:
                if isinstance(obj, dict):
                    slim = {}
                    for k, v in obj.items():
                        if k in KEY_FIELDS:
                            if isinstance(v, dict) and "amount" in v:
                                slim[k] = f"{v['amount']} {v.get('currency', '')}"
                            elif isinstance(v, dict) and "name" in v:
                                slim[k] = v["name"]
                            elif isinstance(v, dict) and "slug" in v:
                                slim[k] = v["slug"]
                            elif isinstance(v, dict) and "date" in v:
                                slim[k] = v["date"]
                            elif not isinstance(v, (dict, list)):
                                slim[k] = v
                    simplified.append(slim)
                else:
                    simplified.append(obj)
            summary["data"] = simplified
            summary["count"] = len(simplified)
        elif isinstance(inner, dict):
            slim = {}
            for k, v in inner.items():
                if k in KEY_FIELDS or k in ("id", "name", "status"):
                    if isinstance(v, dict) and "amount" in v:
                        slim[k] = f"{v['amount']} {v.get('currency', '')}"
                    elif isinstance(v, dict) and "name" in v:
                        slim[k] = v["name"]
                    elif not isinstance(v, (dict, list)):
                        slim[k] = v
            summary["data"] = slim
        else:
            summary["data"] = inner

        item["text"] = json.dumps(summary, default=str)

    return result


async def handle_tool_call(name: str, args: dict) -> str:
    """Execute a tool call and return the result as a string."""
    if name == "search_api":
        try:
            limit = int(args.get("limit", "10"))
        except (ValueError, TypeError):
            limit = 10
        result = await mcp_call("search", {"query": args["query"], "limit": limit})
        result = _trim_search_results(result)
    elif name == "execute_api":
        mcp_args = {"endpoint": args["endpoint"], "method": args.get("method", "GET")}
        if args.get("parameters_json"):
            try:
                mcp_args["parameters"] = json.loads(args["parameters_json"])
            except json.JSONDecodeError:
                pass
        if args.get("body_json"):
            try:
                mcp_args["body"] = json.loads(args["body_json"])
            except json.JSONDecodeError:
                pass
        result = await mcp_call("execute", mcp_args)
        result = _simplify_execute_result(result)
    elif name == "list_orders":
        mcp_args = {}
        if args.get("status"):
            mcp_args["status"] = args["status"]
        if args.get("limit"):
            try:
                mcp_args["limit"] = int(args["limit"])
            except (ValueError, TypeError):
                pass
        result = await mcp_call("list_orders", mcp_args)
    elif name == "store_dashboard":
        result = await mcp_call("store_dashboard", {})
    elif name == "sales_report":
        result = await mcp_call("sales_report", {
            "date_from": args.get("date_from", ""),
            "date_to": args.get("date_to", ""),
        })
    else:
        result = {"error": f"Unknown tool: {name}"}
    text = json.dumps(result, indent=2, default=str)
    if len(text) > 3000:
        text = text[:3000] + "\n... (truncated)"
    return text


# ---------------------------------------------------------------------------
# Gemini chat with tool-use loop (OpenAI-compatible endpoint)
# ---------------------------------------------------------------------------
async def _llm_request(messages: list[dict], tools: list | None = None, stream: bool = False) -> dict:
    """Make a single Gemini API request via OpenAI-compatible endpoint."""
    body: dict = {"model": GEMINI_MODEL, "messages": messages, "stream": stream}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    client = await _get_llm_client()
    resp = await client.post("/v1beta/openai/chat/completions", json=body)
    return resp.json()


async def chat_with_tools(messages: list[dict]):
    """Send messages to Gemini, handle tool calls, then stream final response."""
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    rate_limit_retries = 0
    for round_num in range(6):
        t0 = time.monotonic()
        data = await _llm_request(full_messages, tools=TOOLS)
        elapsed = time.monotonic() - t0
        print(f"[Agent] LLM round {round_num+1} took {elapsed:.1f}s")

        if isinstance(data, list):
            data = data[0] if data else {"error": {"message": "Empty response"}}

        if "error" in data:
            err_msg = data["error"].get("message", "") if isinstance(data["error"], dict) else str(data["error"])
            err_code = data["error"].get("code") if isinstance(data["error"], dict) else None
            print(f"[Agent] LLM error ({err_code}): {err_msg[:200]}")

            if err_code == 429 or "RESOURCE_EXHAUSTED" in err_msg:
                has_tool_results = any(m.get("role") == "tool" for m in full_messages)
                if has_tool_results:
                    print(f"[Agent] Rate limited but have data — requesting final answer")
                    await asyncio.sleep(5)
                    full_messages.append({"role": "user", "content": "بناءً على البيانات التي حصلت عليها، قدم إجابتك الآن."})
                    data = await _llm_request(full_messages, tools=None)
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    if "error" in data:
                        return "خطأ: تم تجاوز حد الطلبات. يرجى المحاولة بعد دقيقة."
                    if "choices" in data:
                        return data["choices"][0]["message"].get("content", "")
                    return "تم تجاوز حد الطلبات. يرجى المحاولة لاحقاً."
                rate_limit_retries += 1
                if rate_limit_retries > 2:
                    return "تم تجاوز حد الطلبات. يرجى الانتظار دقيقة والمحاولة مرة أخرى."
                print(f"[Agent] Rate limited, waiting 15s (retry {rate_limit_retries}/2)...")
                await asyncio.sleep(15)
                continue

            if "Failed to call a function" in err_msg or "tool call validation" in err_msg:
                failed = data["error"].get("failed_generation", "")
                if failed:
                    print(f"[Agent] Failed generation: {failed[:300]}")
                print(f"[Agent] Retrying without tools")
                data = await _llm_request(full_messages, tools=None)
                if isinstance(data, list):
                    data = data[0] if data else {}
                if "error" in data:
                    return f"خطأ في الـ API: {data['error'].get('message', data['error'])}"
            else:
                return f"خطأ في الـ API: {err_msg}"

        if "choices" not in data:
            print(f"[Agent] Unexpected response: {json.dumps(data, default=str)[:500]}")
            return "خطأ: استجابة غير متوقعة من الـ API"

        choice = data["choices"][0]
        msg = choice["message"]
        full_messages.append(msg)

        if not msg.get("tool_calls"):
            return msg.get("content", "")

        tool_names = [tc['function']['name'] for tc in msg['tool_calls']]
        print(f"[Agent] Round {round_num+1} tool calls: {tool_names}")

        # Execute tool calls in parallel when possible
        async def _exec_tool(tc):
            fn = tc["function"]
            try:
                args = json.loads(fn["arguments"])
            except json.JSONDecodeError:
                args = {}
            t0 = time.monotonic()
            result = await handle_tool_call(fn["name"], args)
            elapsed = time.monotonic() - t0
            print(f"[Agent] {fn['name']}({args}) took {elapsed:.1f}s => {result[:150]}")
            return {"role": "tool", "tool_call_id": tc["id"], "content": result}

        tool_results = await asyncio.gather(*[_exec_tool(tc) for tc in msg["tool_calls"]])
        full_messages.extend(tool_results)

    return "تم الوصول للحد الأقصى من الاستدعاءات."


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-initialize MCP session at startup
    try:
        await _mcp_init()
        print("[Agent] MCP session pre-initialized")
    except Exception as e:
        print(f"[Agent] MCP pre-init failed (will retry on first request): {e}")
    yield
    # Cleanup HTTP clients
    if _mcp_client and not _mcp_client.is_closed:
        await _mcp_client.aclose()
    if _llm_client and not _llm_client.is_closed:
        await _llm_client.aclose()


app = FastAPI(title="Salla API Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    messages: list[dict]


@app.post("/api/chat")
async def chat(req: ChatRequest):
    t0 = time.monotonic()
    response = await chat_with_tools(req.messages)
    elapsed = time.monotonic() - t0
    print(f"[Agent] Total request time: {elapsed:.1f}s")
    return {"response": response}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
