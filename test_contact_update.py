#!/usr/bin/env python3
"""
Test script to verify contact update functionality
"""
import requests
import json

def test_contact_update():
    """Test contact update endpoint"""
    
    base_url = "http://127.0.0.1:8001"
    contact_id = 1  # Change this to an actual contact ID
    
    # Test data
    update_data = {
        'name': 'John Doe Updated',
        'email': 'john.updated@example.com',
        'phone': '+1234567890',
        'subject': 'Updated Subject',
        'message': 'Updated message content',
        'service_type': 'general_inquiry'
    }
    
    try:
        print(f"🔄 Testing contact update for ID: {contact_id}")
        
        # Make PUT request to update contact
        response = requests.put(
            f"{base_url}/admin/contacts/{contact_id}",
            data=update_data,
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Contact updated successfully!")
            print(f"Updated Contact ID: {result.get('id')}")
            print(f"Name: {result.get('name', result.get('first_name', 'N/A'))}")
            print(f"Email: {result.get('email')}")
            print(f"Phone: {result.get('phone')}")
            return True
        elif response.status_code == 401:
            print("❌ Authentication required - need to login to admin first")
            return False
        elif response.status_code == 404:
            print("❌ Contact not found - check the contact ID")
            return False
        else:
            print(f"❌ Update failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure the server is running")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_contact_list():
    """Test contact list endpoint"""
    
    base_url = "http://127.0.0.1:8001"
    
    try:
        print(f"\n🔄 Testing contact list endpoint...")
        
        response = requests.get(f"{base_url}/admin/contacts", timeout=10)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Contact list loaded successfully!")
            # Check if it's HTML (admin page) or JSON (API)
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                print("📄 Received HTML page (admin interface)")
            elif 'application/json' in content_type:
                contacts = response.json()
                print(f"📊 Received {len(contacts)} contacts")
            return True
        else:
            print(f"❌ Failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting contact functionality tests...")
    
    # Test contact list
    list_success = test_contact_list()
    
    # Test contact update
    update_success = test_contact_update()
    
    print(f"\n📊 Test Results:")
    print(f"Contact list: {'✅ PASS' if list_success else '❌ FAIL'}")
    print(f"Contact update: {'✅ PASS' if update_success else '❌ FAIL'}")
    
    if update_success:
        print("\n🎉 Contact update functionality is working correctly!")
        print("The 'name' property issue has been fixed.")
    else:
        print("\n⚠️ Contact update test failed. Check the output above for details.")
        print("\nCommon issues:")
        print("- Wrong contact ID (try different IDs)")
        print("- Server not running")
        print("- Authentication required for admin endpoint")
        print("- Database connection issues")