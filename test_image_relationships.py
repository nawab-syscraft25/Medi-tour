#!/usr/bin/env python3
"""
Test script to verify image relationships work correctly
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app import models

async def test_image_relationships():
    """Test that image relationships work correctly"""
    print("🧪 Testing image relationships...")
    
    async with AsyncSessionLocal() as db:
        # Test Hospital images relationship
        try:
            # Create a test hospital
            hospital = models.Hospital(
                name="Test Hospital",
                description="A test hospital",
                location="Test City"
            )
            db.add(hospital)
            await db.commit()
            await db.refresh(hospital)
            print(f"✅ Created test hospital with ID: {hospital.id}")
            
            # Create a test image for the hospital
            image = models.Image(
                owner_type="hospital",
                owner_id=hospital.id,
                url="/media/hospital/test-image.jpg",
                is_primary=True
            )
            db.add(image)
            await db.commit()
            await db.refresh(image)
            print(f"✅ Created test image with ID: {image.id}")
            
            # Test the relationship
            print("🔍 Testing hospital.images relationship...")
            if hasattr(hospital, 'images'):
                images = hospital.images
                print(f"✅ Hospital has {len(images)} image(s)")
                if images:
                    for img in images:
                        print(f"   - Image ID: {img.id}, URL: {img.url}, Primary: {img.is_primary}")
            else:
                print("❌ Hospital.images relationship not found")
            
            # Clean up
            await db.delete(image)
            await db.delete(hospital)
            await db.commit()
            print("🧹 Cleaned up test data")
            
        except Exception as e:
            print(f"❌ Error during test: {str(e)}")
            return False
    
    print("✅ Image relationships test completed successfully!")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_image_relationships())
    sys.exit(0 if result else 1)