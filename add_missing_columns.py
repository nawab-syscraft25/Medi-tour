#!/usr/bin/env python3
"""
Script to manually add missing columns and create sample FAQ data.
"""
import asyncio
import sqlite3
from datetime import datetime
from app.db import get_db
from app.models import FAQ, Doctor, Hospital, Treatment
from sqlalchemy import text

async def add_missing_columns_and_data():
    """Add missing columns and create sample FAQ data."""
    
    # Get database connection
    db_generator = get_db()
    db = await db_generator.__anext__()
    
    try:
        # Add missing columns if they don't exist
        print("Adding missing columns...")
        
        # Add is_featured to doctors
        try:
            await db.execute(text("ALTER TABLE doctors ADD COLUMN is_featured BOOLEAN DEFAULT 0"))
            print("✅ Added is_featured column to doctors")
        except Exception as e:
            print(f"⚠️  is_featured column already exists in doctors: {e}")
        
        # Add is_featured to hospitals
        try:
            await db.execute(text("ALTER TABLE hospitals ADD COLUMN is_featured BOOLEAN DEFAULT 0"))
            print("✅ Added is_featured column to hospitals")
        except Exception as e:
            print(f"⚠️  is_featured column already exists in hospitals: {e}")
        
        # Add is_featured to treatments
        try:
            await db.execute(text("ALTER TABLE treatments ADD COLUMN is_featured BOOLEAN DEFAULT 0"))
            print("✅ Added is_featured column to treatments")
        except Exception as e:
            print(f"⚠️  is_featured column already exists in treatments: {e}")
            
        # Create doctor_hospital_association table
        try:
            await db.execute(text("""
                CREATE TABLE doctor_hospital_association (
                    doctor_id INTEGER NOT NULL,
                    hospital_id INTEGER NOT NULL,
                    PRIMARY KEY (doctor_id, hospital_id),
                    FOREIGN KEY(doctor_id) REFERENCES doctors (id),
                    FOREIGN KEY(hospital_id) REFERENCES hospitals (id)
                )
            """))
            print("✅ Created doctor_hospital_association table")
        except Exception as e:
            print(f"⚠️  doctor_hospital_association table already exists: {e}")
        
        await db.commit()
        
        # Create sample FAQ data
        print("\n🔧 Creating sample FAQ data...")
        
        # Sample FAQs for Doctors
        doctor_faqs = [
            ("What are your consultation hours?", "I am available for consultations Monday to Friday from 9:00 AM to 5:00 PM.\nWeekend appointments can be arranged for urgent cases."),
            ("Do you accept international patients?", "Yes, I welcome international patients and provide comprehensive care packages.\nWe assist with medical visa documentation and accommodation arrangements."),
            ("What languages do you speak?", "I am fluent in English, Hindi, and local regional languages.\nTranslation services are available for other languages if needed."),
            ("How can I book an appointment?", "You can book appointments through our online portal, phone, or email.\nEmergency consultations are available 24/7 through our helpline."),
            ("What should I bring for my first consultation?", "Please bring your medical history, current medications list, and any previous test reports.\nInsurance documents and identification are also required.")
        ]
        
        # Sample FAQs for Hospitals  
        hospital_faqs = [
            ("What facilities are available at your hospital?", "Our hospital features state-of-the-art medical equipment, modern operating theaters, and comfortable patient rooms.\nWe have 24/7 emergency services, laboratory, pharmacy, and rehabilitation center."),
            ("Do you provide accommodation for international patients?", "Yes, we offer guest houses and partner with nearby hotels for patient families.\nAirport pickup and local transportation services are also available."),
            ("What insurance plans do you accept?", "We accept major international insurance plans and provide direct billing services.\nCash payment options and medical loan facilities are also available."),
            ("Is there a dedicated international patient coordinator?", "Yes, we have a specialized international patient services team.\nThey assist with treatment planning, documentation, and coordination throughout your stay."),
            ("What safety protocols do you follow?", "We maintain strict infection control measures and international safety standards.\nAll staff are regularly trained on the latest medical protocols and emergency procedures.")
        ]
        
        # Sample FAQs for Treatments
        treatment_faqs = [
            ("What is the duration of this treatment?", "The treatment duration varies based on individual cases, typically ranging from 7-14 days.\nFollow-up consultations may be required for 2-3 months post-treatment."),
            ("Are there any side effects?", "Most patients experience minimal side effects with proper pre-treatment preparation.\nOur medical team provides detailed information about potential effects and management strategies."),
            ("What is included in the treatment package?", "The package includes pre-treatment consultations, procedure costs, hospital stay, and initial medications.\nPost-treatment follow-ups and rehabilitation services are also covered."),
            ("Is this treatment suitable for my age group?", "Treatment suitability depends on individual health conditions rather than age alone.\nOur specialists conduct thorough evaluations to determine the best approach for each patient."),
            ("What is the success rate of this treatment?", "Our treatment success rates exceed international standards with over 95% patient satisfaction.\nDetailed success statistics and patient testimonials are available upon request.")
        ]
        
        # Get first few doctors, hospitals, treatments to add FAQs
        doctors = await db.execute(text("SELECT id FROM doctors LIMIT 3"))
        hospitals = await db.execute(text("SELECT id FROM hospitals LIMIT 3"))
        treatments = await db.execute(text("SELECT id FROM treatments LIMIT 3"))
        
        doctor_ids = [row[0] for row in doctors.fetchall()]
        hospital_ids = [row[0] for row in hospitals.fetchall()]
        treatment_ids = [row[0] for row in treatments.fetchall()]
        
        # Add FAQs for doctors
        for doctor_id in doctor_ids:
            for i, (question, answer) in enumerate(doctor_faqs):
                faq = FAQ(
                    owner_type="doctor",
                    owner_id=doctor_id,
                    question=question,
                    answer=answer,
                    position=i + 1,
                    is_active=True
                )
                db.add(faq)
        
        # Add FAQs for hospitals
        for hospital_id in hospital_ids:
            for i, (question, answer) in enumerate(hospital_faqs):
                faq = FAQ(
                    owner_type="hospital",
                    owner_id=hospital_id,
                    question=question,
                    answer=answer,
                    position=i + 1,
                    is_active=True
                )
                db.add(faq)
        
        # Add FAQs for treatments
        for treatment_id in treatment_ids:
            for i, (question, answer) in enumerate(treatment_faqs):
                faq = FAQ(
                    owner_type="treatment",
                    owner_id=treatment_id,
                    question=question,
                    answer=answer,
                    position=i + 1,
                    is_active=True
                )
                db.add(faq)
        
        await db.commit()
        
        print(f"✅ Added {len(doctor_faqs)} FAQs each for {len(doctor_ids)} doctors")
        print(f"✅ Added {len(hospital_faqs)} FAQs each for {len(hospital_ids)} hospitals") 
        print(f"✅ Added {len(treatment_faqs)} FAQs each for {len(treatment_ids)} treatments")
        
        # Create some doctor-hospital associations
        print("\n🔗 Creating doctor-hospital associations...")
        for i, doctor_id in enumerate(doctor_ids):
            for j, hospital_id in enumerate(hospital_ids):
                if i <= j:  # Create some relationships
                    try:
                        await db.execute(text(
                            "INSERT INTO doctor_hospital_association (doctor_id, hospital_id) VALUES (:doctor_id, :hospital_id)"
                        ), {"doctor_id": doctor_id, "hospital_id": hospital_id})
                    except Exception as e:
                        print(f"⚠️  Association already exists: {e}")
        
        await db.commit()
        print("✅ Created doctor-hospital associations")
        
        print("\n🎉 Successfully set up FAQ functionality and sample data!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await db.rollback()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(add_missing_columns_and_data())