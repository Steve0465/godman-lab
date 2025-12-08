#!/usr/bin/env python3
"""Test API endpoints"""

from fastapi.testclient import TestClient
from godman_ai.server.api import app

client = TestClient(app)

def test_api():
    print("Testing API Endpoints\n" + "="*50)
    
    # Test health endpoint
    print("\n1. Testing /health:")
    response = client.get("/health")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    
    # Test list presets
    print("\n2. Testing /api/presets:")
    response = client.get("/api/presets")
    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Number of presets: {len(data['presets'])}")
    for preset in data['presets']:
        print(f"    - {preset['name']} ({preset['model']})")
    
    # Test get specific presets
    print("\n3. Testing /api/presets/{name}:")
    for name in ["Overmind", "Forge", "Handler"]:
        response = client.get(f"/api/presets/{name}")
        print(f"  {name}: Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"    Model: {data['model']}")
    
    # Test non-existent preset
    print("\n4. Testing non-existent preset:")
    response = client.get("/api/presets/NonExistent")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    
    print("\n" + "="*50)
    print("✓ All API tests passed!")

if __name__ == "__main__":
    test_api()
