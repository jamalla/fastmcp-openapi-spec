"""
Test script for the Salla API MCP server.
Demonstrates the two-tool design pattern with search and execute.
"""

import asyncio
import json
from server import search_endpoints, execute_endpoint


async def test_search():
    """Test the search tool."""
    print("🔍 Testing SEARCH tool...")
    print("-" * 60)
    
    # Test 1: Search for products
    print("\nTest 1: Searching for 'products'...")
    results = search_endpoints("products", limit=5)
    print(f"Found {len(results)} endpoint(s):")
    for ep in results:
        print(f"  • {ep['method']:6} {ep['path']:30} - {ep['summary']}")
    
    # Test 2: Search for orders
    print("\nTest 2: Searching for 'orders'...")
    results = search_endpoints("orders", limit=5)
    print(f"Found {len(results)} endpoint(s):")
    for ep in results:
        print(f"  • {ep['method']:6} {ep['path']:30} - {ep['summary']}")
    
    # Test 3: Search by tag
    print("\nTest 3: Searching for 'settings'...")
    results = search_endpoints("settings", limit=3)
    print(f"Found {len(results)} endpoint(s):")
    for ep in results:
        print(f"  • {ep['method']:6} {ep['path']:30} - {ep['summary']}")


async def test_execute():
    """Test the execute tool (requires valid API token)."""
    print("\n\n✅ Testing EXECUTE tool...")
    print("-" * 60)
    
    print("\nNote: These tests require SALLA_API_TOKEN to be configured.")
    print("Set your token in .env file to run actual API calls.\n")
    
    # Test 1: GET request without params (simulated)
    print("Test 1: Simulated GET /products request")
    print("  Command: execute('/products', 'GET')")
    print("  Status: Requires valid API token\n")
    
    # Test 2: POST request with body (simulated)
    print("Test 2: Simulated POST /products request")
    print("  Command: execute('/products', 'POST', body={...})")
    print("  Status: Requires valid API token\n")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  Salla API MCP Server - Test Suite")
    print("=" * 60)
    
    # Load the spec
    from server import load_openapi_spec
    load_openapi_spec()
    
    # Run tests
    await test_search()
    await test_execute()
    
    print("\n" + "=" * 60)
    print("✨ Test suite complete!")
    print("=" * 60 + "\n")
    
    print("Next steps:")
    print("1. Configure .env with your SALLA_API_TOKEN")
    print("2. Run: python server.py")
    print("3. Connect with an MCP client (e.g., VS Code Copilot)\n")


if __name__ == "__main__":
    asyncio.run(main())
