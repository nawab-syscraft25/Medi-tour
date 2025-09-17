#!/usr/bin/env python3
"""
Test file upload functionality with new folder structure
"""

import asyncio
import httpx
import io
from PIL import Image
import os

async def test_upload_structure():
    """Test that uploads are organized correctly by owner type"""
    base_url = "http://localhost:8000"
    
    # Create a test image
    test_image = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🧪 Testing Upload Organization...")
        
        # Test hospital image upload
        files = {"files": ("test_hospital.png", img_bytes, "image/png")}
        data = {
            "owner_type": "hospital",
            "owner_id": 1,
            "is_primary": False
        }
        
        response = await client.post(f"{base_url}/api/v1/uploads/image", files=files, data=data)
        print(f"Hospital upload status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Hospital image URL: {result['images'][0]['url']}")
            
            # Check if file exists in correct folder
            expected_path = result['images'][0]['url'].lstrip('/')
            if os.path.exists(expected_path):
                print(f"✅ Hospital image saved to: {expected_path}")
            else:
                print(f"❌ Hospital image not found at: {expected_path}")
        
        # Reset image bytes for next test
        img_bytes.seek(0)
        
        # Test doctor image upload
        files = {"files": ("test_doctor.png", img_bytes, "image/png")}
        data = {
            "owner_type": "doctor", 
            "owner_id": 1,
            "is_primary": False
        }
        
        response = await client.post(f"{base_url}/api/v1/uploads/image", files=files, data=data)
        print(f"Doctor upload status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Doctor image URL: {result['images'][0]['url']}")
            
            # Check if file exists in correct folder
            expected_path = result['images'][0]['url'].lstrip('/')
            if os.path.exists(expected_path):
                print(f"✅ Doctor image saved to: {expected_path}")
            else:
                print(f"❌ Doctor image not found at: {expected_path}")
        
        # Reset image bytes for next test
        img_bytes.seek(0)
        
        # Test treatment image upload
        files = {"files": ("test_treatment.png", img_bytes, "image/png")}
        data = {
            "owner_type": "treatment",
            "owner_id": 1, 
            "is_primary": False
        }
        
        response = await client.post(f"{base_url}/api/v1/uploads/image", files=files, data=data)
        print(f"Treatment upload status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Treatment image URL: {result['images'][0]['url']}")
            
            # Check if file exists in correct folder
            expected_path = result['images'][0]['url'].lstrip('/')
            if os.path.exists(expected_path):
                print(f"✅ Treatment image saved to: {expected_path}")
            else:
                print(f"❌ Treatment image not found at: {expected_path}")
    
    print("\n📁 Directory structure check:")
    for folder in ["hospital", "doctor", "treatment", "slider"]:
        folder_path = f"media/{folder}"
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            print(f"  {folder}/: {len(files)} files")
            if files:
                print(f"    └── {files[:3]}{'...' if len(files) > 3 else ''}")
        else:
            print(f"  {folder}/: directory not found")


if __name__ == "__main__":
    asyncio.run(test_upload_structure())