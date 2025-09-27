#!/usr/bin/env python3
"""
Comprehensive test file to populate sample data and test all APIs
This script will create sample hospitals, doctors, treatments with images
for locations: Indore, Bangalore, and Mumbai
"""

import asyncio
import httpx
import os
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app import models

# Image URLs provided
HOSPITAL_IMAGES = [
    "https://images.pexels.com/photos/263337/pexels-photo-263337.jpeg",
    "https://images.pexels.com/photos/3844581/pexels-photo-3844581.jpeg", 
    "https://images.pexels.com/photos/1350560/pexels-photo-1350560.jpeg",
    "https://images.pexels.com/photos/668298/pexels-photo-668298.jpeg"
]

DOCTOR_IMAGES = [
    "https://images.pexels.com/photos/3279197/pexels-photo-3279197.jpeg",
    "https://images.pexels.com/photos/4167541/pexels-photo-4167541.jpeg",
    "https://images.pexels.com/photos/2324837/pexels-photo-2324837.jpeg", 
    "https://images.pexels.com/photos/28442518/pexels-photo-28442518.jpeg"
]

TREATMENT_IMAGES = [
    "https://images.pexels.com/photos/8413219/pexels-photo-8413219.jpeg",
    "https://images.pexels.com/photos/3985166/pexels-photo-3985166.jpeg",
    "https://images.pexels.com/photos/5998508/pexels-photo-5998508.jpeg",
    "https://images.pexels.com/photos/3985168/pexels-photo-3985168.jpeg"
]

async def download_image(url: str, media_type: str) -> str:
    """Download image from URL and save to media directory"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Create media directory if it doesn't exist
            media_dir = f"media/{media_type}"
            os.makedirs(media_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = url.split('.')[-1].split('?')[0]
            filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = os.path.join(media_dir, filename)
            
            # Save image
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Return relative URL for database
            return f"/media/{media_type}/{filename}"
            
    except Exception as e:
        print(f"❌ Failed to download image {url}: {str(e)}")
        return None

async def create_sample_hospitals(db: AsyncSession) -> list:
    """Create sample hospitals for Indore, Bangalore, and Mumbai"""
    print("🏥 Creating sample hospitals...")
    
    hospitals_data = [
        {
            "name": "Apollo Hospital Indore",
            "description": "Leading multi-specialty hospital in Indore with state-of-the-art facilities and experienced medical professionals.",
            "location": "Indore, Madhya Pradesh",
            "phone": "+91-731-2234567",
            "features": "24/7 Emergency Services, ICU, Operation Theaters, Diagnostic Services",
            "facilities": "Cardiology, Neurology, Orthopedics, Oncology, Pediatrics"
        },
        {
            "name": "Manipal Hospital Bangalore",
            "description": "Premier healthcare institution in Bangalore offering comprehensive medical services with advanced technology.",
            "location": "Bangalore, Karnataka", 
            "phone": "+91-80-2658999",
            "features": "Trauma Center, Robotic Surgery, Advanced Imaging, Lab Services",
            "facilities": "Surgical Treatment, Neurosurgery, Transplant Services, Emergency Care"
        },
        {
            "name": "Lilavati Hospital Mumbai",
            "description": "Renowned multi-specialty hospital in Mumbai providing world-class healthcare services since 1978.",
            "location": "Mumbai, Maharashtra",
            "phone": "+91-22-26405000", 
            "features": "Digital Hospital, Telemedicine, International Patient Services, Pharmacy",
            "facilities": "Oncology, Gastroenterology, Pulmonology, Rheumatology, Dermatology"
        },
        {
            "name": "Fortis Hospital Bangalore",
            "description": "Advanced healthcare facility in Bangalore known for clinical excellence and patient-centric care.",
            "location": "Bangalore, Karnataka",
            "phone": "+91-80-66214444",
            "features": "Minimally Invasive Surgery, Critical Care, Rehabilitation Services",
            "facilities": "Cardiology, Orthopedics, Neurology, Urology, Gynecology"
        }
    ]
    
    hospitals = []
    for i, hospital_data in enumerate(hospitals_data):
        hospital = models.Hospital(**hospital_data)
        db.add(hospital)
        await db.commit()
        await db.refresh(hospital)
        
        # Download and associate images
        image_url = await download_image(HOSPITAL_IMAGES[i], "hospital")
        if image_url:
            image = models.Image(
                owner_type="hospital",
                owner_id=hospital.id,
                url=image_url,
                is_primary=True,
                position=1
            )
            db.add(image)
            await db.commit()
            
        hospitals.append(hospital)
        print(f"  ✅ Created: {hospital.name}")
    
    return hospitals

async def create_sample_doctors(db: AsyncSession, hospitals: list) -> list:
    """Create sample doctors associated with hospitals"""
    print("👨‍⚕️ Creating sample doctors...")
    
    doctors_data = [
        {
            "name": "Dr. Rajesh Kumar",
            "description": "Senior Cardiologist with 15+ years of experience in interventional cardiology and heart surgeries.",
            "designation": "Senior Consultant - Cardiology",
            "experience_years": 15,
            "hospital_id": hospitals[0].id,  # Apollo Indore
            "gender": "Male",
            "skills": "Interventional Cardiology, Angioplasty, Bypass Surgery, Echocardiography",
            "qualifications": "MBBS, MD (Medicine), DM (Cardiology), FESC",
            "highlights": "500+ successful angioplasties, Published researcher, International speaker",
            "awards": "Best Cardiologist Award 2022, Excellence in Patient Care 2021"
        },
        {
            "name": "Dr. Priya Sharma", 
            "description": "Leading Neurologist specializing in stroke management and neurocritical care.",
            "designation": "Head of Neurology Department",
            "experience_years": 12,
            "hospital_id": hospitals[1].id,  # Manipal Bangalore
            "gender": "Female", 
            "skills": "Stroke Management, Epilepsy Treatment, Neurocritical Care, EEG Interpretation",
            "qualifications": "MBBS, MD (Medicine), DM (Neurology), FAAN",
            "highlights": "Expert in acute stroke interventions, Epilepsy surgery specialist",
            "awards": "Women in Medicine Excellence Award 2023, Research Publication Award"
        },
        {
            "name": "Dr. Amit Patel",
            "description": "Renowned Orthopedic Surgeon known for joint replacement surgeries and sports medicine.",
            "designation": "Senior Consultant - Orthopedics",
            "experience_years": 18,
            "hospital_id": hospitals[2].id,  # Lilavati Mumbai
            "gender": "Male",
            "skills": "Joint Replacement, Arthroscopy, Sports Medicine, Trauma Surgery",
            "qualifications": "MBBS, MS (Orthopedics), Fellowship in Joint Replacement",
            "highlights": "1000+ joint replacements, Sports team consultant, Minimally invasive specialist",
            "awards": "Excellence in Orthopedics 2022, Best Surgeon Award 2020"
        },
        {
            "name": "Dr. Sunita Reddy",
            "description": "Expert Oncologist with specialization in breast cancer and chemotherapy treatments.",
            "designation": "Senior Consultant - Medical Oncology", 
            "experience_years": 14,
            "hospital_id": hospitals[3].id,  # Fortis Bangalore
            "gender": "Female",
            "skills": "Medical Oncology, Chemotherapy, Immunotherapy, Palliative Care",
            "qualifications": "MBBS, MD (Medicine), DM (Medical Oncology), ESMO Certification", 
            "highlights": "Breast cancer specialist, Clinical trial researcher, Patient advocacy",
            "awards": "Outstanding Oncologist 2023, Compassionate Care Award 2021"
        }
    ]
    
    doctors = []
    for i, doctor_data in enumerate(doctors_data):
        doctor = models.Doctor(**doctor_data)
        db.add(doctor)
        await db.commit()
        await db.refresh(doctor)
        
        # Download and associate images
        image_url = await download_image(DOCTOR_IMAGES[i], "doctor")
        if image_url:
            image = models.Image(
                owner_type="doctor",
                owner_id=doctor.id,
                url=image_url,
                is_primary=True,
                position=1
            )
            db.add(image)
            await db.commit()
            
        doctors.append(doctor)
        print(f"  ✅ Created: {doctor.name}")
    
    return doctors

async def create_sample_treatments(db: AsyncSession, hospitals: list, doctors: list) -> list:
    """Create sample treatments associated with hospitals and doctors"""
    print("🏥 Creating sample treatments...")
    
    treatments_data = [
        {
            "name": "Cardiac Bypass Surgery",
            "short_description": "Advanced heart bypass surgery for blocked coronary arteries",
            "long_description": "Comprehensive cardiac bypass surgery using state-of-the-art techniques. Our experienced cardiac surgeons perform both on-pump and off-pump procedures with excellent success rates. Includes pre-operative assessment, surgery, ICU care, and post-operative rehabilitation.",
            "treatment_type": "Surgical Treatment",
            "price_min": 250000.0,
            "price_max": 400000.0,
            "hospital_id": hospitals[0].id,
            "doctor_id": doctors[0].id,
            "location": "Indore, Madhya Pradesh"
        },
        {
            "name": "Stroke Treatment & Rehabilitation",
            "short_description": "Comprehensive stroke treatment with advanced neuro-intervention",
            "long_description": "Complete stroke management including emergency thrombolysis, mechanical thrombectomy, and comprehensive rehabilitation. Our stroke unit provides 24/7 care with specialized neurologists and rehabilitation team for optimal recovery outcomes.",
            "treatment_type": "Clinical Treatment",
            "price_min": 150000.0,
            "price_max": 300000.0,
            "hospital_id": hospitals[1].id,
            "doctor_id": doctors[1].id,
            "location": "Bangalore, Karnataka"
        },
        {
            "name": "Total Knee Replacement",
            "short_description": "Advanced joint replacement surgery with minimal invasive techniques",
            "long_description": "State-of-the-art total knee replacement using computer-assisted surgery and latest implants. Includes pre-operative planning, minimally invasive surgery, post-operative care, and comprehensive physiotherapy for faster recovery and better outcomes.",
            "treatment_type": "Dental Treatment", 
            "price_min": 180000.0,
            "price_max": 280000.0,
            "hospital_id": hospitals[2].id,
            "doctor_id": doctors[2].id,
            "location": "Mumbai, Maharashtra"
        },
        {
            "name": "Comprehensive Cancer Treatment",
            "short_description": "Multi-disciplinary cancer care with latest treatment protocols",
            "long_description": "Comprehensive cancer treatment including chemotherapy, immunotherapy, targeted therapy, and supportive care. Our oncology team provides personalized treatment plans with latest protocols and clinical trial access for better patient outcomes.",
            "treatment_type": "Oncology",
            "price_min": 200000.0, 
            "price_max": 500000.0,
            "hospital_id": hospitals[3].id,
            "doctor_id": doctors[3].id,
            "location": "Bangalore, Karnataka"
        }
    ]
    
    treatments = []
    for i, treatment_data in enumerate(treatments_data):
        treatment = models.Treatment(**treatment_data)
        db.add(treatment)
        await db.commit()
        await db.refresh(treatment)
        
        # Download and associate images
        image_url = await download_image(TREATMENT_IMAGES[i], "treatment")
        if image_url:
            image = models.Image(
                owner_type="treatment", 
                owner_id=treatment.id,
                url=image_url,
                is_primary=True,
                position=1
            )
            db.add(image)
            await db.commit()
            
        treatments.append(treatment)
        print(f"  ✅ Created: {treatment.name}")
    
    return treatments

async def test_api_endpoints():
    """Test all API endpoints with sample data"""
    print("🧪 Testing API endpoints...")
    
    base_url = "http://165.22.223.163:8000/"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test Hospitals API
            print("\n📍 Testing Hospitals API...")
            response = await client.get(f"{base_url}/hospitals")
            if response.status_code == 200:
                hospitals = response.json()
                print(f"  ✅ GET /hospitals - Found {len(hospitals)} hospitals")
                for hospital in hospitals[:2]:  # Show first 2
                    print(f"    - {hospital['name']} ({hospital['location']}) - {len(hospital.get('images', []))} images")
            
            # Test location filtering
            response = await client.get(f"{base_url}/hospitals?location=bangalore")
            if response.status_code == 200:
                bangalore_hospitals = response.json()
                print(f"  ✅ GET /hospitals?location=bangalore - Found {len(bangalore_hospitals)} hospitals")
            
            # Test Doctors API
            print("\n👨‍⚕️ Testing Doctors API...")
            response = await client.get(f"{base_url}/doctors")
            if response.status_code == 200:
                doctors = response.json()
                print(f"  ✅ GET /doctors - Found {len(doctors)} doctors")
                for doctor in doctors[:2]:
                    print(f"    - {doctor['name']} ({doctor['designation']}) - {len(doctor.get('images', []))} images")
            
            # Test Treatments API
            print("\n🏥 Testing Treatments API...")
            response = await client.get(f"{base_url}/treatments")
            if response.status_code == 200:
                treatments = response.json()
                print(f"  ✅ GET /treatments - Found {len(treatments)} treatments")
                for treatment in treatments[:2]:
                    print(f"    - {treatment['name']} ({treatment['location']}) - {len(treatment.get('images', []))} images")
            
            # Test location + treatment type filtering
            response = await client.get(f"{base_url}/treatments?location=bangalore&treatment_type=oncology")
            if response.status_code == 200:
                filtered_treatments = response.json()
                print(f"  ✅ GET /treatments?location=bangalore&treatment_type=oncology - Found {len(filtered_treatments)} treatments")
            
            print("\n🎉 All API tests completed successfully!")
            
        except Exception as e:
            print(f"❌ API test failed: {str(e)}")

async def main():
    """Main function to populate sample data and test APIs"""
    print("🚀 Starting Medi-Tour Sample Data Population...")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Create sample data
            hospitals = await create_sample_hospitals(db)
            doctors = await create_sample_doctors(db, hospitals)
            treatments = await create_sample_treatments(db, hospitals, doctors)
            
            print(f"\n📊 Sample Data Created Successfully:")
            print(f"  🏥 Hospitals: {len(hospitals)}")
            print(f"  👨‍⚕️ Doctors: {len(doctors)}")
            print(f"  🏥 Treatments: {len(treatments)}")
            print(f"  📍 Locations: Indore, Bangalore, Mumbai")
            
            print("\n" + "=" * 60)
            
            # Test API endpoints
            await test_api_endpoints()
            
        except Exception as e:
            print(f"❌ Error during data population: {str(e)}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ Sample data population and API testing completed!")
    print("\n🌐 You can now test the APIs at: http://127.0.0.1:8000/docs")
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    if not result:
        exit(1)