"""
Demo Backend — FastAPI agent that uses the Salla MCP server.

Connects to the MCP server (streamable-http) and exposes a chat endpoint
that the CopilotKit frontend calls. Uses Groq/Llama for reasoning.
"""

import json
import os
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
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

# ---------------------------------------------------------------------------
# MCP client — calls the MCP server over HTTP
# ---------------------------------------------------------------------------
_session_id: str | None = None


def _parse_sse_json(text: str) -> dict | None:
    """Extract JSON-RPC response from SSE event stream or plain JSON."""
    # Try plain JSON first
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    # Parse SSE: look for "data: {...}" lines
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

    async with httpx.AsyncClient(timeout=30) as client:
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

    # Send initialized notification
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
        # Session may have expired, retry once
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
            "description": "Search available API endpoints in the Salla API by keyword. Use this to discover what endpoints exist before calling them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term e.g. products, orders, customers"},
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
]

SYSTEM_PROMPT = (
    "You are an assistant for the Salla e-commerce API. "
    "You MUST use the provided tools to answer questions. "
    "Step 1: ALWAYS call search_api first to find relevant endpoints. "
    "Step 2: Call execute_api with the endpoint found in step 1. "
    "NEVER guess endpoints. NEVER say you don't have access. "
    "Always use the tools. Present results in markdown."
)


def _trim_search_results(result: Any) -> Any:
    """Trim verbose fields from search results to reduce token usage."""
    if isinstance(result, dict) and "content" in result:
        # MCP wraps results in content array
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


async def handle_tool_call(name: str, args: dict) -> str:
    """Execute a tool call and return the result as a string."""
    if name == "search_api":
        result = await mcp_call("search", {"query": args["query"], "limit": 5})
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
    else:
        result = {"error": f"Unknown tool: {name}"}
    text = json.dumps(result, indent=2, default=str)
    # Truncate to stay within Groq token limits
    if len(text) > 3000:
        text = text[:3000] + "\n... (truncated)"
    return text


# ---------------------------------------------------------------------------
# Groq chat with tool-use loop
# ---------------------------------------------------------------------------
async def _groq_request(messages: list[dict], tools: list | None = None) -> dict:
    """Make a single Groq API request."""
    body: dict = {"model": GROQ_MODEL, "messages": messages}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
        body["parallel_tool_calls"] = False
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=body,
        )
    return resp.json()


async def chat_with_tools(messages: list[dict]) -> str:
    """Send messages to Groq, handle tool calls in a loop, return final response."""
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    for round_num in range(5):
        data = await _groq_request(full_messages, tools=TOOLS)

        # On tool-call failure, retry without tools so the model responds with text
        if "error" in data:
            err_msg = data["error"].get("message", "")
            if "Failed to call a function" in err_msg or "tool call validation" in err_msg:
                print(f"[Agent] Tool call failed, retrying without tools")
                data = await _groq_request(full_messages, tools=None)
                if "error" in data:
                    return f"Groq API error: {data['error'].get('message', data['error'])}"
            else:
                return f"Groq API error: {err_msg}"

        choice = data["choices"][0]
        msg = choice["message"]
        full_messages.append(msg)

        if not msg.get("tool_calls"):
            return msg.get("content", "")

        print(f"[Agent] Round {round_num+1} tool calls: {[tc['function']['name'] for tc in msg['tool_calls']]}")

        for tc in msg["tool_calls"]:
            fn = tc["function"]
            try:
                args = json.loads(fn["arguments"])
            except json.JSONDecodeError:
                args = {}

            result = await handle_tool_call(fn["name"], args)
            print(f"[Agent] {fn['name']}({args}) => {result[:200]}")
            full_messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    return "Reached maximum tool call rounds."


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Salla API Agent")

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
    response = await chat_with_tools(req.messages)
    return {"response": response}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
