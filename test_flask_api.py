#!/usr/bin/env python3
import requests
import json

# Test creating a server and then testing it
flask_url = "http://127.0.0.1:5001"

# Step 1: Create a test server configuration
server_config = {
    "name": "Test NVDA MCP Server",
    "transport_type": "http",
    "config": {
        "url": "http://localhost:8765/mcp",
        "headers": {},
        "timeout": 30
    }
}

print("Step 1: Creating server configuration...")
response = requests.post(f"{flask_url}/api/servers", json=server_config)
print(f"Create server response: {response.status_code}")
if response.status_code == 200 or response.status_code == 201:
    server = response.json()
    server_id = server.get('id')
    print(f"Server created with ID: {server_id}")

    # Step 2: Test the connection
    print("\nStep 2: Testing connection...")
    test_response = requests.post(f"{flask_url}/api/servers/{server_id}/test")
    print(f"Test response: {test_response.status_code}")
    print(f"Test result: {test_response.text}")

    # Step 3: Clean up
    print("\nStep 3: Cleaning up...")
    delete_response = requests.delete(f"{flask_url}/api/servers/{server_id}")
    print(f"Delete response: {delete_response.status_code}")

else:
    print(f"Failed to create server: {response.text}")
