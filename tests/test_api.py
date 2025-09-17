import pytest
from httpx import AsyncClient


class TestBasicEndpoints:
    """Test basic API endpoints"""
    
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestSliderEndpoints:
    """Test slider CRUD operations"""
    
    async def test_create_slider(self, client: AsyncClient):
        """Test creating a new slider"""
        slider_data = {
            "title": "Test Slider",
            "description": "Test Description",
            "image_url": "https://example.com/image.jpg",
            "link": "https://example.com",
            "tags": "test,slider",
            "is_active": True
        }
        
        response = await client.post("/api/v1/sliders", json=slider_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == slider_data["title"]
        assert data["description"] == slider_data["description"]
        assert "id" in data
        assert "created_at" in data
    
    async def test_get_sliders(self, client: AsyncClient):
        """Test getting list of sliders"""
        response = await client.get("/api/v1/sliders")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    async def test_get_slider_by_id(self, client: AsyncClient):
        """Test getting a specific slider"""
        # First create a slider
        slider_data = {
            "title": "Test Slider for Get",
            "description": "Test Description"
        }
        
        create_response = await client.post("/api/v1/sliders", json=slider_data)
        assert create_response.status_code == 200
        
        slider_id = create_response.json()["id"]
        
        # Now get the slider
        response = await client.get(f"/api/v1/sliders/{slider_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == slider_id
        assert data["title"] == slider_data["title"]
    
    async def test_update_slider(self, client: AsyncClient):
        """Test updating a slider"""
        # First create a slider
        slider_data = {
            "title": "Original Title",
            "description": "Original Description"
        }
        
        create_response = await client.post("/api/v1/sliders", json=slider_data)
        assert create_response.status_code == 200
        
        slider_id = create_response.json()["id"]
        
        # Update the slider
        update_data = {
            "title": "Updated Title",
            "is_active": False
        }
        
        response = await client.put(f"/api/v1/sliders/{slider_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["is_active"] == update_data["is_active"]
        assert data["description"] == slider_data["description"]  # Unchanged


class TestHospitalEndpoints:
    """Test hospital CRUD operations"""
    
    async def test_create_hospital(self, client: AsyncClient):
        """Test creating a new hospital"""
        hospital_data = {
            "name": "Test Hospital",
            "description": "A great test hospital",
            "location": "Test City",
            "phone": "+1234567890",
            "features": "Emergency,Surgery,ICU",
            "facilities": "Parking,WiFi,Cafeteria"
        }
        
        response = await client.post("/api/v1/hospitals", json=hospital_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == hospital_data["name"]
        assert data["location"] == hospital_data["location"]
        assert "id" in data
        assert "created_at" in data
    
    async def test_get_hospitals_with_search(self, client: AsyncClient):
        """Test getting hospitals with search filter"""
        # First create a hospital
        hospital_data = {
            "name": "Searchable Hospital",
            "location": "Search City"
        }
        
        await client.post("/api/v1/hospitals", json=hospital_data)
        
        # Search for hospitals
        response = await client.get("/api/v1/hospitals?search=Searchable")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        assert any("Searchable" in hospital["name"] for hospital in data)


class TestDoctorEndpoints:
    """Test doctor CRUD operations"""
    
    async def test_create_doctor(self, client: AsyncClient):
        """Test creating a new doctor"""
        doctor_data = {
            "name": "Dr. Test Doctor",
            "designation": "Cardiologist",
            "experience_years": 10,
            "gender": "Male",
            "skills": "Heart Surgery,Cardiology",
            "qualifications": "MBBS,MD"
        }
        
        response = await client.post("/api/v1/doctors", json=doctor_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == doctor_data["name"]
        assert data["designation"] == doctor_data["designation"]
        assert data["experience_years"] == doctor_data["experience_years"]
        assert "id" in data


class TestTreatmentEndpoints:
    """Test treatment CRUD operations"""
    
    async def test_create_treatment(self, client: AsyncClient):
        """Test creating a new treatment"""
        treatment_data = {
            "name": "Heart Surgery",
            "short_description": "Advanced heart surgery",
            "treatment_type": "Surgery",
            "price_min": 10000.0,
            "price_max": 25000.0,
            "location": "Test City"
        }
        
        response = await client.post("/api/v1/treatments", json=treatment_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == treatment_data["name"]
        assert data["treatment_type"] == treatment_data["treatment_type"]
        assert data["price_min"] == treatment_data["price_min"]
        assert "id" in data


class TestBookingEndpoints:
    """Test booking CRUD operations"""
    
    async def test_create_booking(self, client: AsyncClient):
        """Test creating a new package booking"""
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
        
        response = await client.post("/api/v1/bookings", json=booking_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == booking_data["name"]
        assert data["email"] == booking_data["email"]
        assert data["travel_assistant"] == booking_data["travel_assistant"]
        assert "id" in data


class TestErrorHandling:
    """Test error handling"""
    
    async def test_get_nonexistent_slider(self, client: AsyncClient):
        """Test getting a non-existent slider"""
        response = await client.get("/api/v1/sliders/99999")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
    
    async def test_invalid_email_in_booking(self, client: AsyncClient):
        """Test creating booking with invalid email"""
        booking_data = {
            "name": "John Doe",
            "email": "invalid-email",
            "phone": "+1234567890"
        }
        
        response = await client.post("/api/v1/bookings", json=booking_data)
        assert response.status_code == 422  # Validation error