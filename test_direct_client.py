#!/usr/bin/env python3
import sys
sys.path.append('.')

from mcp.transport import HTTPTransport
from mcp.client import MCPClient

# Test the HTTP transport and client directly
url = "http://localhost:8765/mcp"
transport = HTTPTransport(url)

try:
    print("Testing transport connection...")
    transport.connect()
    print("✅ Transport connected successfully")

    print("\nTesting MCP client...")
    client = MCPClient(transport)

    # Test the client initialization
    client_info = {
        'name': 'Test MCP Client',
        'version': '1.0.0'
    }

    result = client.initialize(client_info)
    print("✅ Client initialized successfully")
    print(f"Server info: {result}")

    client.disconnect()
    print("✅ Client disconnected successfully")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
