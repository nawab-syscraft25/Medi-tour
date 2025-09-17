#!/usr/bin/env python3
"""
Test admin authentication and protected endpoints
"""

import asyncio
import httpx
import json

async def test_admin_auth():
    """Test admin authentication flow"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🧪 Testing Admin Authentication...")
        
        # Test admin login
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = await client.post(f"{base_url}/api/v1/admin/login", json=login_data)
        print(f"Admin login status: {response.status_code}")
        
        if response.status_code == 200:
            auth_result = response.json()
            token = auth_result["access_token"]
            admin_info = auth_result["admin"]
            
            print(f"✅ Login successful!")
            print(f"   Admin: {admin_info['username']} ({admin_info['email']})")
            print(f"   Super Admin: {admin_info['is_super_admin']}")
            print(f"   Token: {token[:20]}...")
            
            # Test protected endpoint - create hospital
            headers = {"Authorization": f"Bearer {token}"}
            hospital_data = {
                "name": "Admin Test Hospital",
                "address": "123 Admin St",
                "phone": "+1234567890",
                "email": "admin@hospital.com"
            }
            
            response = await client.post(
                f"{base_url}/api/v1/hospitals", 
                json=hospital_data, 
                headers=headers
            )
            print(f"Protected hospital creation status: {response.status_code}")
            
            if response.status_code == 200:
                hospital = response.json()
                print(f"✅ Hospital created: {hospital['name']} (ID: {hospital['id']})")
            else:
                print(f"❌ Hospital creation failed: {response.text}")
            
            # Test admin info endpoint
            response = await client.get(f"{base_url}/api/v1/admin/me", headers=headers)
            print(f"Admin info status: {response.status_code}")
            
            if response.status_code == 200:
                info = response.json()
                print(f"✅ Admin info retrieved: {info['username']}")
        
        else:
            print(f"❌ Login failed: {response.text}")
        
        # Test contact form (public endpoint)
        contact_data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test Contact",
            "message": "This is a test contact form submission."
        }
        
        response = await client.post(f"{base_url}/api/v1/contact", json=contact_data)
        print(f"Contact form status: {response.status_code}")
        
        if response.status_code == 200:
            contact = response.json()
            print(f"✅ Contact form submitted: {contact['name']} (ID: {contact['id']})")
        else:
            print(f"❌ Contact form failed: {response.text}")


if __name__ == "__main__":
    asyncio.run(test_admin_auth())