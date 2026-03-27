# Code Mode: Two-Tool Design Pattern Explained

## What is Code Mode?

**Code Mode** is an optimization pattern for MCP servers that reduces agent context usage by:
- Limiting tools to a small, composable set (typically 2-3)
- Making API specs queryable on-demand
- Letting agents discover capabilities dynamically

This project demonstrates Code Mode with a **two-tool design**: `search` + `execute`.

## The Problem It Solves

### Traditional Approach: Large Tool Catalog

Imagine a Salla API with 47 endpoints. The naive implementation creates one tool per operation:

```
Tools Available:
  GET /products
  POST /products
  GET /orders
  POST /orders
  GET /orders/{id}
  PUT /orders/{id}
  [... 41 more ...]
```

**Issues**:
1. **Context Bloat**: Agent must know about all 47 tools
2. **Expensive Reasoning**: Agent spends tokens listing/selecting tools
3. **Inflexible**: Adding an endpoint requires adding a new tool
4. **Poor Discovery**: Agent may miss less-obvious endpoints
5. **Token Waste**: Full documentation embedded in every request

**Token Cost Example**:
```
Agent context per request:
- 47 tool definitions × 400 tokens avg = 18,800 tokens
- Plus parameters for each = +8,000 tokens  
- Total overhead: ~27,000 tokens JUST for tool setup

Per 10 agent calls: 270,000 tokens spent on tool definitions
```

## The Code Mode Solution

### Two-Tool Pattern

Instead, we provide just two tools:

```
Tools Available:
  1. search(query) → Find endpoints matching a query
  2. execute(endpoint, method, ...) → Call an endpoint
```

**Benefits**:
1. **Minimal Context**: Only 2 tools in agent mental model
2. **Fast Reasoning**: Agent quickly decides which tool to use
3. **Flexible**: New endpoints automatically discoverable
4. **Better UX**: Agent explores capabilities naturally
5. **Token Efficient**: ~1,000 tokens for tool definitions

**Token Cost Example**:
```
Agent context per request:
- 2 tool definitions × 500 tokens avg = 1,000 tokens
- Lightweight JSON schema = +200 tokens
- Total overhead: ~1,200 tokens

Per 10 agent calls: 12,000 tokens spent on tool setup
= 22x more efficient than large catalog!
```

## How It Works: Agent Workflow

### Scenario: "Find products under $50"

#### Traditional Approach (Inefficient)
```
Agent thinks: "Which of 47 tools should I use?"
         ↓
Agent: "I need the 'GET /products' tool..."
         ↓
Agent: "...with filter parameters..."
         ↓ (After tokens spent on reasoning)
Calls: GET /products with {"filter.price": {"$lt": 50}}
         ↓
Result: Product list
```

#### Code Mode Approach (Efficient)
```
Agent thinks: "I'll search for 'products'"
         ↓
Agent calls: search("products")
         ↓
Server returns: 
  [{path: "/products", method: "GET", params: {...}}, ...]
         ↓
Agent thinks: "I'll use GET /products with filters"
         ↓
Agent calls: execute("/products", "GET", {filter.price: {$lt: 50}})
         ↓
Result: Product list
```

**Key Difference**: Agent discovers tools dynamically, not statically.

## Implementation Details

### The `search` Tool

```python
def search_endpoints(query: str, limit: int = 10) -> list[dict]:
    """
    Query OpenAPI spec for matching endpoints.
    - Agent provides: natural language query
    - Server returns: structured endpoint metadata
    - No large documentation dumped on agent
    """
    # Search across:
    # - Endpoint paths: /products, /orders, etc.
    # - Summaries: "Get all products"
    # - Descriptions: Full description text
    # - Tags: ["Products"], ["Orders"], etc.
```

**Example**:
```
Agent: search("products")
Server returns:
{
  "results": [
    {
      "path": "/products",
      "method": "GET",
      "summary": "Get all products",
      "parameters": [
        {"name": "limit", "schema": {"type": "integer"}},
        {"name": "filter", "schema": {"type": "object"}}
      ]
    }
  ]
}
```

The agent now knows:
- There's a GET /products endpoint
- What parameters it accepts
- What the endpoint does

### The `execute` Tool

```python
async def execute_endpoint(
    endpoint: str,
    method: str,
    parameters: Optional[dict] = None,
    body: Optional[dict] = None
) -> dict:
    """
    Call an actual API endpoint.
    - Agent provides: endpoint path + method + params
    - Server handles: auth, HTTP, error handling
    """
```

**Example**:
```
Agent: execute(
  endpoint="/products",
  method="GET",
  parameters={"limit": 5, "sort": "price"}
)
Server:
1. Adds Authorization header (Bearer token)
2. Makes HTTP GET request to https://api.salla.dev/v2/products?limit=5&sort=price
3. Returns {"status": "success", "statusCode": 200, "data": {...}}
```

## Why This Pattern Scales Better

### API Growth Scenario

**Scenario**: Salla API grows from 47 to 200 endpoints.

**Traditional Approach**:
```
Before: 47 tools
After:  200 tools

Agent context explodes from 18,800 → 80,000+ tokens
Performance degrades significantly
```

**Code Mode Approach**:
```
Before: 2 tools
After:  2 tools (same!)

Agent context stays at ~1,200 tokens
Performance unchanged
```

### Adding Features Scenario

**Scenario**: You need to add request validation, rate limiting, caching.

**Traditional Approach**:
```
Update all 47 tool definitions
Create 47 new tool handlers
Update documentation for each
= Massive change surface
```

**Code Mode Approach**:
```
Update search() function (centralized)
Update execute() function (centralized)
Validate in one place
= Minimal change surface
```

## The Trade-offs

### What You Gain

✅ **Scalability**: Works for 50 or 5,000 endpoints  
✅ **Efficiency**: Dramatically reduced token usage  
✅ **Flexibility**: Easy to add/remove endpoints  
✅ **Discovery**: Agents explore capabilities naturally  
✅ **Maintenance**: Changes in one place  

### What You Trade Away

❌ **Simplicity**: Agents must call search first  
❌ **Direct Knowledge**: Agent doesn't see full API upfront  
❌ **One-Step Calls**: May need search → execute flow  
❌ **Type Hints**: Less detailed parameter schemas visible  

**Good Trade-off?** Yes! For most real APIs with 20+ endpoints, Code Mode wins.

## When to Use Code Mode vs. Large Catalog

### Use Code Mode If:
- API has 20+ endpoints
- Endpoints are well-organized (searchable by path/tag/summary)
- New endpoints added frequently
- Agent needs to discover capabilities
- Token efficiency matters

### Use Large Catalog If:
- API has < 10 endpoints
- Each endpoint is truly unique/complex
- Parameter schemas are highly specific
- Endpoints rarely change
- Direct invocation is critical

### Hybrid Approach:
```
Tools:
  [search]        ← For exploration
  [execute]       ← For calling
  [some-special]  ← For complex, frequently-used operations
```

## Real-World Comparison

### Example: Stripe Payment API

**Large Catalog Approach** (Actual):
```
- List Customers: customers.list()
- Create Customer: customers.create()
- Update Customer: customers.update()
- Delete Customer: customers.delete()
- List Charges: charges.list()
- Create Charge: charges.create()
- ... (dozens more)
= Developers memorize API methods
```

**Code Mode Approach** (Alternative):
```
- search("customer") → finds all customer operations
- execute("POST /customers", body=...)
= Developers explore and discover
```

**Result**: Code Mode reduces cognitive load and scales better.

## Implementation Checklist

- [x] Implement `search` tool with query parsing
- [x] Implement `execute` tool with auth handling
- [x] Load OpenAPI spec at server startup
- [x] Error handling for both tools
- [x] Type-safe request/response contracts
- [x] Documentation with clear examples
- [x] Environment-based configuration
- [x] Bearer token authentication

## Further Learning

### Topics to Explore
1. **Semantic Search**: Instead of keyword matching, use embeddings
2. **Request Validation**: Validate parameters before sending
3. **Usage Analytics**: Track which endpoints are called
4. **Caching**: Cache search results and API responses
5. **OAuth Integration**: Token refresh without user intervention

### References
- MCP Protocol: https://modelcontextprotocol.io/
- OpenAPI Spec: https://spec.openapis.org/
- Agent Design Patterns: https://docs.anthropic.com/agents/
- Rate Limiting Best Practices: https://stripe.com/blog/rate-limiters

## Questions & Answers

**Q: Why not just use full documentation?**  
A: Agents are token-limited. Full nested docs explodes context; search is targeted.

**Q: Can agents still make mistakes with Code Mode?**  
A: Yes, but less often. Smaller decision tree reduces reasoning errors.

**Q: How does search handle ambiguous queries?**  
A: Returns all matches (up to limit). Agent selects the right one.

**Q: What if an endpoint changes?**  
A: Update openapi.json, restart server, automatically available.

**Q: Is this specific to Salla?**  
A: No! Works with any OpenAPI 3.1 spec.

## Try It Yourself

1. Start the MCP server: `python server.py`
2. Ask a Copilot agent via VS Code:
   ```
   "Search for order-related endpoints, then fetch my last 5 orders"
   ```
3. Observe the two-step flow:
   - Agent calls `search("orders")`
   - Agent calls `execute()` on a matching endpoint
4. Compare tokens used vs. a large-catalog approach

## Conclusion

Code Mode's two-tool pattern is a **powerful pattern for scaling agent-driven APIs**. By letting agents discover capabilities dynamically through `search` and call them through `execute`, we:

- Reduce token waste
- Improve agent reasoning
- Scale to any API size
- Maintain flexibility

This is the future of intelligent API wrappers. 🚀
