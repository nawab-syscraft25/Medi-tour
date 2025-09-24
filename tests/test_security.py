#!/usr/bin/env python3
"""
Test that protected endpoints are actually protected
"""

import asyncio
import httpx

async def test_protected_endpoints():
    """Test that endpoints are protected from unauthorized access"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🛡️  Testing Protected Endpoints...")
        
        # Test without token
        hospital_data = {
            "name": "Unauthorized Hospital",
            "address": "123 Hack St",
            "phone": "+1234567890",
            "email": "hack@hospital.com"
        }
        
        response = await client.post(f"{base_url}/api/v1/hospitals", json=hospital_data)
        print(f"Hospital creation without auth: {response.status_code}")
        
        if response.status_code == 401 or response.status_code == 403:
            print("✅ Hospital creation properly protected")
        else:
            print(f"❌ Hospital creation not protected: {response.text}")
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid-token"}
        response = await client.post(
            f"{base_url}/api/v1/hospitals", 
            json=hospital_data, 
            headers=headers
        )
        print(f"Hospital creation with invalid token: {response.status_code}")
        
        if response.status_code == 401 or response.status_code == 403:
            print("✅ Invalid token properly rejected")
        else:
            print(f"❌ Invalid token accepted: {response.text}")
        
        # Test that public endpoints still work
        response = await client.get(f"{base_url}/api/v1/hospitals")
        print(f"Hospital list (public): {response.status_code}")
        
        if response.status_code == 200:
            hospitals = response.json()
            print(f"✅ Public hospital list works: {len(hospitals)} hospitals")
        else:
            print(f"❌ Public endpoint failed: {response.text}")


if __name__ == "__main__":
    asyncio.run(test_protected_endpoints())