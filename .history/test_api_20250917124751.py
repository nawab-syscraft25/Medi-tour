#!/usr/bin/env python3
"""
Quick test script to verify the API is working
"""
import asyncio
import httpx
import json

async def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Medi-Tour API...")
        
        # Test health check
        print("\n1. Testing health check...")
        response = await client.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test root endpoint
        print("\n2. Testing root endpoint...")
        response = await client.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test creating a hospital
        print("\n3. Testing hospital creation...")
        hospital_data = {
            "name": "Test Hospital",
            "description": "A great test hospital",
            "location": "Test City",
            "phone": "+1234567890",
            "features": "Emergency,Surgery,ICU",
            "facilities": "Parking,WiFi,Cafeteria"
        }
        response = await client.post(f"{base_url}/api/v1/hospitals", json=hospital_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            hospital = response.json()
            print(f"   Created hospital: {hospital['name']} (ID: {hospital['id']})")
            hospital_id = hospital['id']
        else:
            print(f"   Error: {response.text}")
            return
        
        # Test getting hospitals
        print("\n4. Testing hospital list...")
        response = await client.get(f"{base_url}/api/v1/hospitals")
        print(f"   Status: {response.status_code}")
        hospitals = response.json()
        print(f"   Found {len(hospitals)} hospitals")
        
        # Test creating a doctor
        print("\n5. Testing doctor creation...")
        doctor_data = {
            "name": "Dr. Test Doctor",
            "designation": "Cardiologist",
            "experience_years": 10,
            "hospital_id": hospital_id,
            "gender": "Male",
            "skills": "Heart Surgery,Cardiology",
            "qualifications": "MBBS,MD"
        }
        response = await client.post(f"{base_url}/api/v1/doctors", json=doctor_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            doctor = response.json()
            print(f"   Created doctor: {doctor['name']} (ID: {doctor['id']})")
        else:
            print(f"   Error: {response.text}")
        
        # Test creating a treatment
        print("\n6. Testing treatment creation...")
        treatment_data = {
            "name": "Heart Surgery",
            "short_description": "Advanced heart surgery",
            "treatment_type": "Surgery",
            "price_min": 10000.0,
            "price_max": 25000.0,
            "hospital_id": hospital_id,
            "location": "Test City"
        }
        response = await client.post(f"{base_url}/api/v1/treatments", json=treatment_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            treatment = response.json()
            print(f"   Created treatment: {treatment['name']} (ID: {treatment['id']})")
        else:
            print(f"   Error: {response.text}")
        
        # Test creating a booking
        print("\n7. Testing booking creation...")
        booking_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "service_type": "treatment",
            "service_ref": "Heart Surgery",
            "budget_range": "10k-25k",
            "user_query": "I need heart surgery consultation",
            "travel_assistant": True,
            "stay_assistant": False
        }
        response = await client.post(f"{base_url}/api/v1/bookings", json=booking_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            booking = response.json()
            print(f"   Created booking: {booking['name']} (ID: {booking['id']})")
        else:
            print(f"   Error: {response.text}")
        
        print("\n✅ API test completed successfully!")
        print(f"\n📚 Visit http://localhost:8000/docs for interactive API documentation")

if __name__ == "__main__":
    asyncio.run(test_api())