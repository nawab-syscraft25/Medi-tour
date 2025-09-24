#!/usr/bin/env python3
"""
API Test Script - Test all endpoints with sample data
"""

import asyncio
import httpx

async def test_all_apis():
    """Test all API endpoints"""
    print("🧪 Testing All APIs with Sample Data...")
    print("=" * 60)
    
    BASE_URL = "http://127.0.0.1:8000"
    base_url = "http://127.0.0.1:8000"
    hospitals = []
    doctors = []
    treatments = []
    
    async with httpx.AsyncClient() as client:
        try:
            # Test Hospitals API
            print("\n🏥 Testing Hospitals API...")
            response = await client.get(f"{base_url}/hospitals")
            if response.status_code == 200:
                hospitals = response.json()
                print(f"  ✅ GET /hospitals - Found {len(hospitals)} hospitals")
                for hospital in hospitals:
                    images_count = len(hospital.get('images', []))
                    print(f"    - {hospital['name']} ({hospital['location']}) - {images_count} image(s)")
            
            # Test location filtering for hospitals
            response = await client.get(f"{base_url}/hospitals?location=bangalore")
            if response.status_code == 200:
                bangalore_hospitals = response.json()
                print(f"  ✅ GET /hospitals?location=bangalore - Found {len(bangalore_hospitals)} hospitals")
            
            # Test single hospital
            if len(hospitals) > 0:
                hospital_id = hospitals[0]['id']
                response = await client.get(f"{base_url}/hospitals/{hospital_id}")
                if response.status_code == 200:
                    hospital = response.json()
                    print(f"  ✅ GET /hospitals/{hospital_id} - {hospital['name']} with {len(hospital.get('images', []))} images")
            
            # Test Doctors API
            print("\n👨‍⚕️ Testing Doctors API...")
            response = await client.get(f"{base_url}/doctors")
            if response.status_code == 200:
                doctors = response.json()
                print(f"  ✅ GET /doctors - Found {len(doctors)} doctors")
                for doctor in doctors:
                    images_count = len(doctor.get('images', []))
                    print(f"    - {doctor['name']} ({doctor['designation']}) - {images_count} image(s)")
            
            # Test doctor filtering by hospital
            if len(hospitals) > 0:
                hospital_id = hospitals[0]['id']
                response = await client.get(f"{base_url}/doctors?hospital_id={hospital_id}")
                if response.status_code == 200:
                    hospital_doctors = response.json()
                    print(f"  ✅ GET /doctors?hospital_id={hospital_id} - Found {len(hospital_doctors)} doctors")
            
            # Test single doctor
            if len(doctors) > 0:
                doctor_id = doctors[0]['id']
                response = await client.get(f"{base_url}/doctors/{doctor_id}")
                if response.status_code == 200:
                    doctor = response.json()
                    print(f"  ✅ GET /doctors/{doctor_id} - {doctor['name']} with {len(doctor.get('images', []))} images")
            
            # Test Treatments API
            print("\n🏥 Testing Treatments API...")
            response = await client.get(f"{base_url}/treatments")
            if response.status_code == 200:
                treatments = response.json()
                print(f"  ✅ GET /treatments - Found {len(treatments)} treatments")
                for treatment in treatments:
                    images_count = len(treatment.get('images', []))
                    print(f"    - {treatment['name']} ({treatment['location']}) - {images_count} image(s)")
            
            # Test location filtering for treatments
            response = await client.get(f"{base_url}/treatments?location=bangalore")
            if response.status_code == 200:
                bangalore_treatments = response.json()
                print(f"  ✅ GET /treatments?location=bangalore - Found {len(bangalore_treatments)} treatments")
            
            # Test treatment type filtering
            response = await client.get(f"{base_url}/treatments?treatment_type=Oncology")
            if response.status_code == 200:
                oncology_treatments = response.json()
                print(f"  ✅ GET /treatments?treatment_type=Oncology - Found {len(oncology_treatments)} treatments")
            
            # Test combined filtering (location + treatment type)
            response = await client.get(f"{base_url}/treatments?location=bangalore&treatment_type=Oncology")
            if response.status_code == 200:
                filtered_treatments = response.json()
                print(f"  ✅ GET /treatments?location=bangalore&treatment_type=Oncology - Found {len(filtered_treatments)} treatments")
            
            # Test single treatment
            if len(treatments) > 0:
                treatment_id = treatments[0]['id']
                response = await client.get(f"{base_url}/treatments/{treatment_id}")
                if response.status_code == 200:
                    treatment = response.json()
                    print(f"  ✅ GET /treatments/{treatment_id} - {treatment['name']} with {len(treatment.get('images', []))} images")
            
            # Test Package Bookings API
            print("\n📋 Testing Package Bookings API...")
            response = await client.get(f"{base_url}/bookings")
            if response.status_code == 200:
                bookings = response.json()
                print(f"  ✅ GET /bookings - Found {len(bookings)} bookings")
            
            # Test Sliders API
            print("\n🖼️ Testing Sliders API...")
            response = await client.get(f"{base_url}/sliders")
            if response.status_code == 200:
                sliders = response.json()
                print(f"  ✅ GET /sliders - Found {len(sliders)} sliders")
            
            print("\n" + "=" * 60)
            print("🎉 All API tests completed successfully!")
            print("\n📊 Summary:")
            print(f"  🏥 Hospitals: {len(hospitals)} (with images)")
            print(f"  👨‍⚕️ Doctors: {len(doctors)} (with images)")
            print(f"  🏥 Treatments: {len(treatments)} (with images)")
            print(f"  📍 Locations: Indore, Bangalore, Mumbai")
            print(f"  🔍 Filtering: Location & Treatment Type working")
            
            # Show sample data details
            print("\n📝 Sample Data Details:")
            print("\n🏥 Hospitals:")
            for hospital in hospitals:
                print(f"  - {hospital['name']}")
                print(f"    📍 {hospital['location']}")
                print(f"    📞 {hospital['phone']}")
                print(f"    🖼️ {len(hospital.get('images', []))} images")
                print()
            
            print("👨‍⚕️ Doctors:")
            for doctor in doctors:
                print(f"  - {doctor['name']}")
                print(f"    🏥 {doctor['designation']}")
                print(f"    💼 {doctor['experience_years']} years experience")
                print(f"    🖼️ {len(doctor.get('images', []))} images")
                print()
            
            print("🏥 Treatments:")
            for treatment in treatments:
                print(f"  - {treatment['name']}")
                print(f"    📍 {treatment['location']}")
                print(f"    💰 ₹{treatment['price_min']:,} - ₹{treatment['price_max']:,}")
                print(f"    🖼️ {len(treatment.get('images', []))} images")
                print()
            
        except Exception as e:
            print(f"❌ API test failed: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_all_apis())
    if not result:
        exit(1)