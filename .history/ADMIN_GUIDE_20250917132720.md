# Medi-Tour Backend API - Admin Guide

## 🔐 Admin Authentication System

The Medi-Tour API now includes a comprehensive admin authentication system using JWT tokens. Only authenticated admin users can create, update, and delete hospitals, doctors, and treatments.

## 🚀 Quick Start

### 1. Create Your First Admin User

```bash
# Create a super admin
python create_admin.py create admin admin@meditour.com SecurePassword123 --super

# Create a regular admin
python create_admin.py create staff staff@meditour.com StaffPassword123
```

### 2. List All Admin Users

```bash
python create_admin.py list
```

### 3. Admin Login

**POST** `/api/v1/admin/login`

```json
{
  "username": "admin",
  "password": "SecurePassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "admin": {
    "id": 1,
    "username": "admin",
    "email": "admin@meditour.com",
    "is_active": true,
    "is_super_admin": true,
    "created_at": "2025-09-17T07:54:00.061262",
    "last_login": "2025-09-17T07:55:30.123456"
  }
}
```

## 🛡️ Protected Endpoints

The following endpoints require admin authentication (include `Authorization: Bearer <token>` header):

### Hospitals
- **POST** `/api/v1/hospitals` - Create hospital
- **PUT** `/api/v1/hospitals/{id}` - Update hospital  
- **DELETE** `/api/v1/hospitals/{id}` - Delete hospital

### Doctors
- **POST** `/api/v1/doctors` - Create doctor
- **PUT** `/api/v1/doctors/{id}` - Update doctor
- **DELETE** `/api/v1/doctors/{id}` - Delete doctor

### Treatments
- **POST** `/api/v1/treatments` - Create treatment
- **PUT** `/api/v1/treatments/{id}` - Update treatment
- **DELETE** `/api/v1/treatments/{id}` - Delete treatment

### Admin Management (Super Admin Only)
- **GET** `/api/v1/admin/admins` - List all admins
- **POST** `/api/v1/admin/admins` - Create new admin
- **PUT** `/api/v1/admin/admins/{id}/toggle-active` - Toggle admin status

### Contact Form Management (Admin Only)
- **GET** `/api/v1/contact` - List contact submissions
- **GET** `/api/v1/contact/{id}` - View specific contact
- **PUT** `/api/v1/contact/{id}/respond` - Respond to contact
- **DELETE** `/api/v1/contact/{id}` - Delete contact

## 📝 Contact Us Form

### Public Contact Form

**POST** `/api/v1/contact`

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "subject": "Inquiry about heart surgery",
  "message": "I would like to know more about your heart surgery packages."
}
```

### Admin Contact Management

```bash
# Get all contacts (with filters)
GET /api/v1/contact?is_read=false&search=heart

# Respond to a contact
PUT /api/v1/contact/1/respond
{
  "admin_response": "Thank you for your inquiry. We'll get back to you shortly.",
  "is_read": true
}
```

## 🖼️ File Upload Organization

Files are now organized by type:
- `/media/hospital/` - Hospital images
- `/media/doctor/` - Doctor images  
- `/media/treatment/` - Treatment images
- `/media/slider/` - Slider images

## 📊 Example Admin Workflow

### 1. Login and Get Token
```bash
curl -X POST http://localhost:8000/api/v1/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 2. Create Hospital (with token)
```bash
curl -X POST http://localhost:8000/api/v1/hospitals \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "City Medical Center",
    "address": "123 Health St, Medical City",
    "phone": "+1-555-0123",
    "email": "info@citymedical.com",
    "features": "24/7 Emergency, ICU, Surgery Center",
    "facilities": "MRI, CT Scan, Laboratory, Pharmacy"
  }'
```

### 3. Upload Hospital Image
```bash
curl -X POST http://localhost:8000/api/v1/uploads/image \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "files=@hospital-image.jpg" \
  -F "owner_type=hospital" \
  -F "owner_id=1" \
  -F "is_primary=true"
```

### 4. View Contact Submissions
```bash
curl -X GET http://localhost:8000/api/v1/contact \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🔧 Admin Command Reference

```bash
# Create admin user
python create_admin.py create <username> <email> <password> [--super]

# List all admins
python create_admin.py list

# Examples:
python create_admin.py create admin admin@hospital.com SecurePass123 --super
python create_admin.py create staff staff@hospital.com StaffPass123
```

## 🛠️ Development Testing

Run the admin tests:
```bash
python test_admin.py     # Test admin authentication
python test_security.py  # Test endpoint protection
```

## 📚 API Documentation

Visit the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Security Features

- ✅ JWT token-based authentication
- ✅ Password hashing with bcrypt
- ✅ Protected CRUD endpoints
- ✅ Super admin vs regular admin roles
- ✅ Token expiration (30 minutes)
- ✅ Input validation with Pydantic
- ✅ SQL injection protection with SQLAlchemy
- ✅ CORS middleware configuration

## 📝 Notes

- Tokens expire after 30 minutes
- Only super admins can create/manage other admins
- Contact form submissions are public (no auth required)
- File uploads are organized by entity type
- All admin actions are logged with timestamps