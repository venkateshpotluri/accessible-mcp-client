#!/usr/bin/env python3
import requests
import json

# Test the exact same request our transport makes
url = "http://localhost:8765/mcp"
test_message = {
    "jsonrpc": "2.0",
    "id": "test_connection", 
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {}
    }
}

print(f"Testing connection to: {url}")
print(f"Request payload: {json.dumps(test_message, indent=2)}")

try:
    session = requests.Session()
    response = session.post(
        url,
        json=test_message,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"JSON Response: {json.dumps(result, indent=2)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
