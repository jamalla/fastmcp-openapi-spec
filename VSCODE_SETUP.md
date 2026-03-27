# VS Code Integration Configuration

This file shows how to configure the Salla API MCP Server with VS Code Copilot.

## Setup Instructions

### 1. Add to VS Code settings.json

Open `.vscode/settings.json` (or create it) and add:

```json
{
  "claude.mcpServers": {
    "salla-api": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "${workspaceFolder}/fastmcp-openapi-spec",
      "env": {
        "SALLA_API_TOKEN": "${env:SALLA_API_TOKEN}",
        "SALLA_BASE_URL": "https://api.salla.dev/v2",
        "OPENAPI_SPEC_PATH": "${workspaceFolder}/fastmcp-openapi-spec/openapi.json"
      }
    }
  }
}
```

### 2. Set Environment Variable

Create or update `.env` in the workspace root:

```
SALLA_API_TOKEN=your-actual-token-here
```

Or set as system environment variable:

```bash
# Windows (PowerShell)
$env:SALLA_API_TOKEN = "your-token"

# macOS/Linux
export SALLA_API_TOKEN="your-token"
```

### 3. Restart VS Code

After configuration, restart VS Code to load the MCP server.

## Usage in Copilot Agent Mode

Once configured, ask Copilot to use the Salla API:

```
@agent Search for products in the Salla store and list them with prices.
```

The agent will:
1. Use the `search` tool to find relevant endpoints
2. Use the `execute` tool to call the API
3. Return results based on your query

## Troubleshooting

**Issue: "MCP server failed to start"**
- Check Python is installed: `python --version`
- Verify virtual environment is activated
- Check `server.py` exists in the specified path

**Issue: "No tools available"**
- Restart VS Code
- Check server startup logs in Output > MCP Logs
- Verify `openapi.json` file exists

**Issue: "Unauthorized API calls"**
- Verify `SALLA_API_TOKEN` is set correctly
- Check token hasn't expired in Salla console
- Ensure token has required scopes

## Advanced Configuration

### Custom Environment Setup

For more control, use a `.env` file approach:

```json
{
  "claude.mcpServers": {
    "salla-api": {
      "command": "bash",
      "args": ["-c", "source .env && python server.py"],
      "cwd": "${workspaceFolder}/fastmcp-openapi-spec"
    }
  }
}
```

### Multiple Environments

Set up different MCP servers for staging/production:

```json
{
  "claude.mcpServers": {
    "salla-api-prod": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "${workspaceFolder}/fastmcp-openapi-spec",
      "env": {
        "SALLA_API_TOKEN": "${env:SALLA_API_TOKEN_PROD}"
      }
    },
    "salla-api-staging": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "${workspaceFolder}/fastmcp-openapi-spec",
      "env": {
        "SALLA_API_TOKEN": "${env:SALLA_API_TOKEN_STAGING}",
        "SALLA_BASE_URL": "https://staging-api.salla.dev/v2"
      }
    }
  }
}
```

## Testing the MCP Connection

Open VS Code terminal and run:

```bash
# Start the server directly
python server.py

# In another terminal, test with MCP client tools
# (MCP tools will be available in Copilot once server is running)
```

You should see output like:
```
Loaded OpenAPI spec from ./openapi.json
Found 47 endpoints
```

This confirms the server is ready for agent connections.
