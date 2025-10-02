#!/usr/bin/env python3
"""
Migration script to create new tables: banners, partner_hospitals, patient_stories
Run this script to add the new tables to your existing database.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base, Banner, PartnerHospital, PatientStory
from app.core.config import settings

async def create_tables():
    """Create the new tables"""
    
    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=True,  # Set to False in production
        future=True
    )
    
    try:
        print("🚀 Starting migration for new tables...")
        
        # Create tables
        async with engine.begin() as conn:
            print("📋 Creating new tables: banners, partner_hospitals, patient_stories")
            
            # Create only the new tables
            await conn.run_sync(Banner.__table__.create, checkfirst=True)
            await conn.run_sync(PartnerHospital.__table__.create, checkfirst=True)
            await conn.run_sync(PatientStory.__table__.create, checkfirst=True)
            
            print("✅ New tables created successfully!")
        
        # Add some sample data
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            print("📝 Adding sample data...")
            
            # Sample banner
            sample_banner = Banner(
                name="Home Page Banner",
                title="Welcome to Medi-Tour",
                subtitle="Your trusted partner for medical tourism",
                description="Discover world-class healthcare with our comprehensive medical tourism services.",
                position=1,
                is_active=True
            )
            session.add(sample_banner)
            
            # Sample partner hospital
            sample_partner = PartnerHospital(
                name="Apollo Hospitals",
                description="Leading healthcare provider with world-class facilities",
                location="Chennai, India",
                position=1,
                is_active=True
            )
            session.add(sample_partner)
            
            # Sample patient story
            sample_story = PatientStory(
                patient_name="John Smith",
                description="I had an amazing experience with the cardiac surgery. The doctors were professional and the facilities were world-class. Highly recommended!",
                rating=5,
                treatment_type="Cardiac Surgery",
                hospital_name="Apollo Hospitals",
                location="USA",
                position=1,
                is_featured=True,
                is_active=True
            )
            session.add(sample_story)
            
            await session.commit()
            print("✅ Sample data added successfully!")
        
        print("🎉 Migration completed successfully!")
        print("\n📋 New admin sections available:")
        print("   • Banners: /admin/banners")
        print("   • Partner Hospitals: /admin/partners") 
        print("   • Patient Stories: /admin/stories")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("🔧 Medi-Tour Database Migration")
    print("=" * 50)
    asyncio.run(create_tables())
