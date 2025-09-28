#!/usr/bin/env python3
"""
Script to check what FAQs are currently in the database
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import FAQ, Doctor
from app.core.config import settings

async def check_faqs():
    # Create database engine
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get all FAQs
        print("=== Checking all FAQs in database ===")
        result = await session.execute(select(FAQ))
        all_faqs = result.scalars().all()
        
        print(f"Total FAQs found: {len(all_faqs)}")
        
        for faq in all_faqs:
            print(f"FAQ ID: {faq.id}")
            print(f"  Owner: {faq.owner_type} (ID: {faq.owner_id})")
            print(f"  Question: '{faq.question}'")
            print(f"  Answer: '{faq.answer}'")
            print(f"  Created: {faq.created_at}")
            print("-" * 50)
        
        # Check specific doctor FAQs
        print("\n=== Checking Doctor FAQs ===")
        doctor_faqs = await session.execute(
            select(FAQ).where(FAQ.owner_type == "doctor")
        )
        doctor_faqs = doctor_faqs.scalars().all()
        
        print(f"Doctor FAQs found: {len(doctor_faqs)}")
        for faq in doctor_faqs:
            print(f"Doctor {faq.owner_id}: Q='{faq.question}', A='{faq.answer}'")
        
        # Check doctors
        print("\n=== Checking Doctors ===")
        doctors = await session.execute(select(Doctor))
        doctors = doctors.scalars().all()
        
        print(f"Doctors found: {len(doctors)}")
        for doctor in doctors:
            print(f"Doctor ID: {doctor.id}, Name: {doctor.name}")

if __name__ == "__main__":
    asyncio.run(check_faqs())