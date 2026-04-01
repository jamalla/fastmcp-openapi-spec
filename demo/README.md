# Salla API Agent Demo

A web-based AI agent that lets you interact with the Salla e-commerce API using natural language. Built with CopilotKit + LangGraph + Groq (Llama 3.3 70B).

## Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────┐     ┌───────────┐
│  Next.js Frontend   │────▶│  Python Backend      │────▶│  MCP Server  │────▶│ Salla API │
│  (CopilotKit Chat)  │◀────│  (LangGraph + Groq)  │◀────│  (FastMCP)   │◀────│           │
│  Port 3000          │     │  Port 8888           │     │  Port 8000   │     │           │
└─────────────────────┘     └──────────────────────┘     └──────────────┘     └───────────┘
```

### How it works

1. **You type** a natural language message in the chat UI (e.g., "Show me all products")
2. **CopilotKit frontend** sends your message to the Python backend via AG-UI protocol
3. **LangGraph agent** (powered by Groq/Llama 3.3) decides which tools to call:
   - `search_api` — discovers relevant API endpoints from the OpenAPI spec
   - `execute_api` — makes authenticated HTTP calls to the Salla API
4. **MCP Server** handles the actual API interaction (search the spec, proxy HTTP calls with auth)
5. **Groq** formats the results and responds in the chat

### Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js + CopilotKit React | Chat UI with streaming, tool-call rendering |
| **Backend** | FastAPI + CopilotKit Python SDK | Hosts the LangGraph agent, exposes AG-UI endpoint |
| **Agent** | LangGraph + Llama 3.3 70B (Groq) | Autonomous reasoning, decides when to search/execute |
| **MCP Server** | FastMCP (Python) | Converts OpenAPI spec into searchable/executable tools |
| **Protocol** | AG-UI | Real-time sync between frontend and agent backend |

## Prerequisites

- Python 3.10+
- Node.js 18+
- [Groq API key](https://console.groq.com/) (free tier available)
- Salla API token (already configured in the parent project's `.env`)

## Setup

### 1. Start the MCP Server (from project root)

```bash
cd ..
python server.py streamable-http
# Running on http://localhost:8000
```

### 2. Start the Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env → set GROQ_API_KEY

# Run
python agent.py
# Running on http://localhost:8888
```

### 3. Start the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run
npm run dev
# Running on http://localhost:3000
```

### 4. Open the App

Go to [http://localhost:3000](http://localhost:3000) and start chatting.

## Example Prompts

| Prompt | What the agent does |
|--------|-------------------|
| "What endpoints are available for products?" | Calls `search_api("products")` and lists results |
| "List the first 5 orders" | Searches for order endpoints, then executes `GET /orders` |
| "Get details for product ID 123" | Searches, finds `GET /products/{id}`, executes it |
| "Create a new product called Test" | Searches for create product endpoint, executes `POST /products` |
| "What's the status of order 456?" | Multi-step: gets order, may also fetch customer info |

## Deployment

### Frontend (Vercel)

```bash
cd frontend
npx vercel
```

Set environment variable in Vercel dashboard:
- `NEXT_PUBLIC_COPILOTKIT_URL` → your backend URL

Update `layout.tsx` to use the env var:
```tsx
<CopilotKit runtimeUrl={process.env.NEXT_PUBLIC_COPILOTKIT_URL!} agent="salla_agent">
```

### Backend (Railway / Render / any VPS)

```bash
cd backend
# Deploy with Docker or directly
python agent.py
```

Required env vars:
- `GROQ_API_KEY`
- `MCP_SERVER_URL` → your MCP server URL

### MCP Server

Deploy alongside the backend or separately. Needs:
- `SALLA_API_TOKEN`
- `openapi.json` file
