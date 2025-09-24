"""
Admin Web Interface Routes
Handles HTML pages for admin dashboard using Jinja2 templates
"""

from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, Cookie, Response, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from sqlalchemy.orm import selectinload
from typing import Optional, List
import hashlib
import secrets
from jose import jwt
import json
import os
import uuid
from datetime import datetime, timedelta

from app.dependencies import get_db
from app.models import Admin, Hospital, Doctor, Treatment, ContactUs as Contact, Image
from app.auth import verify_password
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def render_template(name: str, context: dict):
    """Helper function to render templates with common context"""
    context["datetime"] = datetime
    return templates.TemplateResponse(name, context)

# JWT configuration
JWT_SECRET_KEY = settings.secret_key if hasattr(settings, 'secret_key') else "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

def create_access_token(admin_id: int, username: str, is_super_admin: bool) -> str:
    """Create a JWT access token for admin session"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "admin_id": admin_id,
        "username": username,
        "is_super_admin": is_super_admin,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "admin_access"
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_access_token(token: str) -> Optional[dict]:
    """Verify and decode JWT access token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "admin_access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

async def get_current_admin_from_token(
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[Admin]:
    """Get current admin from JWT token stored in cookie"""
    if not session_token:
        return None
    
    payload = verify_access_token(session_token)
    if not payload:
        return None
    
    # Get fresh admin data from database
    result = await db.execute(
        select(Admin).where(
            Admin.id == payload["admin_id"],
            Admin.is_active == True
        )
    )
    admin = result.scalar_one_or_none()
    return admin

def require_admin_login(admin: Optional[Admin] = Depends(get_current_admin_from_token)):
    """Dependency to require admin login"""
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return admin

def require_super_admin(admin: Admin = Depends(require_admin_login)):
    """Dependency to require super admin privileges"""
    if not admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return admin

def get_current_admin_from_session(session_token: Optional[str]) -> Optional[dict]:
    """Helper function to get admin info from session token (JWT)"""
    if not session_token:
        return None
    
    payload = verify_access_token(session_token)
    if not payload:
        return None
        
    return {
        "admin_id": payload.get("admin_id"),
        "username": payload.get("username"),
        "is_super_admin": payload.get("is_super_admin", False)
    }

async def get_treatment_types(db: AsyncSession) -> List[str]:
    """Get all unique treatment types from database"""
    result = await db.execute(
        select(Treatment.treatment_type).distinct().where(Treatment.treatment_type.isnot(None))
    )
    treatment_types = result.scalars().all()
    
    # Filter out empty values and sort
    valid_types = [t.strip() for t in treatment_types if t and t.strip()]
    return sorted(valid_types)

async def get_current_admin_object(session_token: Optional[str], db: AsyncSession) -> Optional[Admin]:
    """Helper function to get full Admin object from session token"""
    token_data = get_current_admin_from_session(session_token)
    if not token_data:
        return None
        
    # Get full admin object from database
    result = await db.execute(
        select(Admin).where(
            Admin.id == token_data["admin_id"],
            Admin.is_active == True
        )
    )
    return result.scalar_one_or_none()

async def get_current_admin_dict(session_token: Optional[str], db: AsyncSession) -> Optional[dict]:
    """Helper function to get admin data as dict for template rendering (avoids lazy loading)"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        return None
        
    return {
        "id": admin.id,
        "username": admin.username,
        "is_super_admin": admin.is_super_admin,
        "is_active": admin.is_active,
        "last_login": admin.last_login,
        "created_at": admin.created_at
    }

async def get_dashboard_stats(db: AsyncSession):
    """Get dashboard statistics"""
    stats = {}
    
    # Count totals
    stats["hospitals"] = await db.scalar(select(func.count(Hospital.id)))
    stats["doctors"] = await db.scalar(select(func.count(Doctor.id)))
    stats["treatments"] = await db.scalar(select(func.count(Treatment.id)))
    stats["contacts"] = await db.scalar(select(func.count(Contact.id)))
    stats["admins"] = await db.scalar(select(func.count(Admin.id)))
    stats["images"] = await db.scalar(select(func.count(Image.id)))
    
    # Recent contacts
    recent_contacts = await db.execute(
        select(Contact).order_by(desc(Contact.created_at)).limit(5)
    )
    stats["recent_contacts"] = recent_contacts.scalars().all()
    
    return stats

@router.get("/admin", response_class=HTMLResponse)
async def admin_login_page(request: Request, session_token: Optional[str] = Cookie(None)):
    """Admin login page"""
    # Check if already logged in
    current_admin = get_current_admin_from_session(session_token)
    if current_admin:
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    
    return render_template("admin/login.html", {"request": request})

@router.post("/admin/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Process admin login"""
    # Find admin by username
    result = await db.execute(select(Admin).where(Admin.username == username))
    admin = result.scalar_one_or_none()
    
    if not admin or not admin.is_active or not verify_password(password, admin.password_hash):
        return render_template(
            "admin/login.html", 
            {"request": request, "error": "Invalid username or password"}
        )
    
    # Update last login
    admin.last_login = datetime.now()
    await db.commit()
    
    # Create JWT access token
    access_token = create_access_token(
        admin_id=admin.id,
        username=admin.username,
        is_super_admin=admin.is_super_admin
    )
    
    # Redirect to dashboard with JWT token cookie
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(
        "session_token", 
        access_token, 
        httponly=True, 
        max_age=JWT_EXPIRE_HOURS * 3600,  # Convert hours to seconds
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    return response

@router.get("/admin/logout")
async def admin_logout():
    """Admin logout"""
    response = RedirectResponse(url="/admin", status_code=302)
    response.delete_cookie("session_token")
    return response

@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Admin dashboard"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    stats = await get_dashboard_stats(db)
    
    return render_template("admin/dashboard.html", {
        "request": request,
        "admin": admin,
        "stats": stats
    })

# Hospital Management
@router.get("/admin/hospitals", response_class=HTMLResponse)
async def admin_hospitals(
    request: Request,
    page: int = 1,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Hospital management page"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    limit = 10
    offset = (page - 1) * limit
    
    # Get hospitals with pagination
    result = await db.execute(
        select(Hospital).order_by(desc(Hospital.created_at)).offset(offset).limit(limit)
    )
    hospitals = result.scalars().all()
    
    # Get total count for pagination
    total = await db.scalar(select(func.count(Hospital.id)))
    total_pages = (total + limit - 1) // limit
    
    return render_template("admin/hospitals.html", {
        "request": request,
        "admin": admin,
        "hospitals": hospitals,
        "page": page,
        "total_pages": total_pages,
        "total": total
    })

@router.get("/admin/hospitals/new", response_class=HTMLResponse)
async def admin_hospital_new(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """New hospital form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    return render_template("admin/hospital_form.html", {
        "request": request,
        "admin": admin,
        "hospital": None,
        "action": "Create"
    })

@router.get("/admin/hospitals/{hospital_id}/edit", response_class=HTMLResponse)
async def admin_hospital_edit(
    request: Request,
    hospital_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Edit hospital form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    result = await db.execute(select(Hospital).where(Hospital.id == hospital_id))
    hospital = result.scalar_one_or_none()

    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    # Load hospital images separately to avoid lazy loading in template
    images_result = await db.execute(
        select(Image).where(
            Image.owner_type == "hospital",
            Image.owner_id == hospital.id
        ).order_by(Image.position, Image.id)
    )
    hospital_images = images_result.scalars().all()

    return render_template("admin/hospital_form.html", {
        "request": request,
        "admin": admin,
        "hospital": hospital,  
        "hospital_images": hospital_images,
        "action": "Update"
    })# Doctor Management
@router.get("/admin/doctors", response_class=HTMLResponse)
async def admin_doctors(
    request: Request,
    page: int = 1,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Doctor management page"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    limit = 10
    offset = (page - 1) * limit
    
    # Get doctors with pagination, loading hospital relationship eagerly
    result = await db.execute(
        select(Doctor).options(selectinload(Doctor.hospital)).order_by(desc(Doctor.created_at)).offset(offset).limit(limit)
    )
    doctors = result.scalars().all()
    
    # Get total count for pagination
    total = await db.scalar(select(func.count(Doctor.id)))
    total_pages = (total + limit - 1) // limit
    
    return render_template("admin/doctors.html", {
        "request": request,
        "admin": admin,
        "doctors": doctors,
        "page": page,
        "total_pages": total_pages,
        "total": total
    })

# Treatment Management
@router.get("/admin/treatments", response_class=HTMLResponse)
async def admin_treatments(
    request: Request,
    page: int = 1,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Treatment management page"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    limit = 10
    offset = (page - 1) * limit
    
    # Get treatments with pagination, loading hospital and doctor relationships eagerly
    result = await db.execute(
        select(Treatment).options(
            selectinload(Treatment.hospital),
            selectinload(Treatment.doctor)
        ).order_by(desc(Treatment.created_at)).offset(offset).limit(limit)
    )
    treatments = result.scalars().all()
    
    # Get total count for pagination
    total = await db.scalar(select(func.count(Treatment.id)))
    total_pages = (total + limit - 1) // limit
    
    return render_template("admin/treatments.html", {
        "request": request,
        "admin": admin,
        "treatments": treatments,
        "page": page,
        "total_pages": total_pages,
        "total": total
    })

# Contact Management
@router.get("/admin/contacts", response_class=HTMLResponse)
async def admin_contacts(
    request: Request,
    page: int = 1,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Contact management page"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    limit = 10
    offset = (page - 1) * limit
    
    # Get contacts with pagination
    result = await db.execute(
        select(Contact).order_by(desc(Contact.created_at)).offset(offset).limit(limit)
    )
    contacts = result.scalars().all()
    
    # Get total count for pagination
    total = await db.scalar(select(func.count(Contact.id)))
    total_pages = (total + limit - 1) // limit
    
    return render_template("admin/contacts.html", {
        "request": request,
        "admin": admin,
        "contacts": contacts,
        "page": page,
        "total_pages": total_pages,
        "total": total
    })

@router.post("/admin/contacts/{contact_id}/mark-read")
async def mark_contact_read(
    contact_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Mark a contact as read"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.is_read = True
    await db.commit()
    
    return {"message": "Contact marked as read"}

@router.post("/admin/contacts/{contact_id}/reply")
async def reply_to_contact(
    contact_id: int,
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Reply to a contact"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    form = await request.form()
    response_text = form.get("response", "").strip()
    
    if not response_text:
        raise HTTPException(status_code=400, detail="Response text is required")
    
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.admin_response = response_text
    contact.responded_at = datetime.utcnow()
    contact.is_read = True
    await db.commit()
    
    return {"message": "Reply sent successfully"}

@router.delete("/admin/contacts/{contact_id}")
async def delete_contact(
    contact_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete a contact"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    await db.delete(contact)
    await db.commit()
    
    return {"message": "Contact deleted successfully"}

@router.post("/admin/contacts/mark-all-read")
async def mark_all_contacts_read(
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Mark all contacts as read"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    await db.execute(
        update(Contact).values(is_read=True).where(Contact.is_read == False)
    )
    await db.commit()
    
    return {"message": "All contacts marked as read"}

@router.get("/admin/api/treatment-types")
async def get_treatment_types_api(
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """API endpoint to get all treatment types"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    treatment_types = await get_treatment_types(db)
    return {"treatment_types": treatment_types}

# Admin Management (Super Admin only)
@router.get("/admin/admins", response_class=HTMLResponse)
async def admin_admins(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Admin management page (Super Admin only)"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin or not admin.get('is_super_admin'):
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    
    # Get all admins
    result = await db.execute(
        select(Admin).order_by(desc(Admin.created_at))
    )
    admins = result.scalars().all()
    
    return render_template("admin/admins.html", {
        "request": request,
        "admin": admin,
        "admins": admins
    })

# Additional form routes for doctors and treatments
@router.get("/admin/doctors/new", response_class=HTMLResponse)
async def admin_doctor_new(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """New doctor form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get hospitals for dropdown
    hospitals = await db.execute(select(Hospital).order_by(Hospital.name))
    hospitals = hospitals.scalars().all()
    
    return render_template("admin/doctor_form.html", {
        "request": request,
        "admin": admin,
        "doctor": None,
        "hospitals": hospitals,
        "action": "Create"
    })

@router.get("/admin/doctors/{doctor_id}/edit", response_class=HTMLResponse)
async def admin_doctor_edit(
    request: Request,
    doctor_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Edit doctor form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Get hospitals for dropdown
    hospitals = await db.execute(select(Hospital).order_by(Hospital.name))
    hospitals = hospitals.scalars().all()
    
    return render_template("admin/doctor_form.html", {
        "request": request,
        "admin": admin,
        "doctor": doctor,
        "hospitals": hospitals,
        "action": "Update"
    })

@router.get("/admin/treatments/new", response_class=HTMLResponse)
async def admin_treatment_new(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """New treatment form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get hospitals and doctors for dropdown
    hospitals = await db.execute(select(Hospital).order_by(Hospital.name))
    hospitals = hospitals.scalars().all()
    
    doctors = await db.execute(select(Doctor).order_by(Doctor.name))
    doctors = doctors.scalars().all()
    
    # Get treatment types for dropdown
    treatment_types = await get_treatment_types(db)
    
    return render_template("admin/treatment_form.html", {
        "request": request,
        "admin": admin,
        "treatment": None,
        "hospitals": hospitals,
        "doctors": doctors,
        "treatment_types": treatment_types,
        "action": "Create"
    })

@router.get("/admin/treatments/{treatment_id}/edit", response_class=HTMLResponse)
async def admin_treatment_edit(
    request: Request,
    treatment_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Edit treatment form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    result = await db.execute(select(Treatment).where(Treatment.id == treatment_id))
    treatment = result.scalar_one_or_none()
    
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    # Get hospitals and doctors for dropdown
    hospitals = await db.execute(select(Hospital).order_by(Hospital.name))
    hospitals = hospitals.scalars().all()
    
    doctors = await db.execute(select(Doctor).order_by(Doctor.name))
    doctors = doctors.scalars().all()
    
    # Get treatment types for dropdown
    treatment_types = await get_treatment_types(db)

    # Load treatment images separately to avoid lazy loading in template
    images_result = await db.execute(
        select(Image).where(
            Image.owner_type == "treatment",
            Image.owner_id == treatment.id
        ).order_by(Image.position, Image.id)
    )
    treatment_images = images_result.scalars().all()
    
    return render_template("admin/treatment_form.html", {
        "request": request,
        "admin": admin,
        "treatment": treatment,
        "treatment_images": treatment_images,
        "hospitals": hospitals,
        "doctors": doctors,
        "treatment_types": treatment_types,
        "action": "Update"
    })

# POST Routes for CRUD Operations

def parse_comma_separated_string(value: str) -> str:
    """Convert comma-separated input to clean comma-separated string for database storage"""
    if not value or not value.strip():
        return ""
    # Split, strip whitespace, filter empty, and rejoin
    items = [item.strip() for item in value.split(',') if item.strip()]
    return ', '.join(items)


async def save_uploaded_file(file: UploadFile, category: str) -> str:
    """Save uploaded file and return filename"""
    if not file or not file.filename:
        return None
    
    # Create media directory if it doesn't exist
    media_dir = f"media/{category}"
    os.makedirs(media_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(media_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return unique_filename

@router.post("/admin/hospitals")
async def admin_hospital_create(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    rating: Optional[float] = Form(None),
    specializations: str = Form(""),
    features: str = Form(""),
    facilities: str = Form(""),
    images: List[UploadFile] = File(default=[]),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new hospital"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get admin data for templates (to avoid SQLAlchemy lazy loading issues)
    admin_dict = await get_current_admin_dict(session_token, db)
    
    try:
        # Create hospital object
        hospital = Hospital(
            name=name,
            description=description or None,
            location=location or None,
            phone=phone or None,
            email=email or None,
            address=address or None,
            rating=rating,
            specializations=parse_comma_separated_string(specializations),
            features=parse_comma_separated_string(features),
            facilities=parse_comma_separated_string(facilities),
            created_at=datetime.now()
        )
        
        db.add(hospital)
        await db.flush()  # Get hospital ID
        
        # Handle image uploads
        image_count = 0
        for image_file in images:
            if image_file and image_file.filename:
                filename = await save_uploaded_file(image_file, "hospital")
                if filename:
                    image = Image(
                        owner_type="hospital",
                        owner_id=hospital.id,
                        url=f"/media/hospital/{filename}",
                        is_primary=image_count == 0,  # First image is primary
                        position=image_count
                    )
                    db.add(image)
                    image_count += 1
        
        await db.commit()
        return RedirectResponse(url="/admin/hospitals", status_code=302)
        
    except Exception as e:
        await db.rollback()
        # Return to form with error
        return render_template("admin/hospital_form.html", {
            "request": request,
            "admin": admin_dict,
            "hospital": None,
            "action": "Create",
            "error": f"Error creating hospital: {str(e)}"
        })

@router.post("/admin/hospitals/{hospital_id}")
async def admin_hospital_update(
    request: Request,
    hospital_id: int,
    name: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    rating: Optional[float] = Form(None),
    specializations: str = Form(""),
    features: str = Form(""),
    facilities: str = Form(""),
    images: List[UploadFile] = File(default=[]),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Update existing hospital"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get existing hospital
        result = await db.execute(select(Hospital).where(Hospital.id == hospital_id))
        hospital = result.scalar_one_or_none()
        
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        # Update hospital fields
        hospital.name = name
        hospital.description = description or None
        hospital.location = location or None
        hospital.phone = phone or None
        hospital.email = email or None
        hospital.address = address or None
        hospital.rating = rating
        hospital.specializations = parse_comma_separated_string(specializations)
        hospital.features = parse_comma_separated_string(features)
        hospital.facilities = parse_comma_separated_string(facilities)
        
        # Handle new image uploads
        # Get current image count for this hospital
        existing_images_result = await db.execute(
            select(func.count(Image.id)).where(
                Image.owner_type == "hospital",
                Image.owner_id == hospital.id
            )
        )
        image_count = existing_images_result.scalar() or 0
        
        for image_file in images:
            if image_file and image_file.filename:
                filename = await save_uploaded_file(image_file, "hospital")
                if filename:
                    image = Image(
                        owner_type="hospital",
                        owner_id=hospital.id,
                        url=f"/media/hospital/{filename}",
                        is_primary=image_count == 0,  # First image is primary
                        position=image_count
                    )
                    db.add(image)
                    image_count += 1
        
        await db.commit()
        return RedirectResponse(url="/admin/hospitals", status_code=302)
        
    except Exception as e:
        await db.rollback()
        return render_template("admin/hospital_form.html", {
            "request": request,
            "admin": admin,
            "hospital": hospital,
            "action": "Update",
            "error": f"Error updating hospital: {str(e)}"
        })

@router.post("/admin/doctors")
async def admin_doctor_create(
    request: Request,
    name: str = Form(...),
    designation: str = Form(""),
    hospital_id: Optional[int] = Form(None),
    experience_years: Optional[int] = Form(None),
    gender: str = Form(""),
    description: str = Form(""),
    specialization: str = Form(""),
    skills: str = Form(""),
    qualifications: str = Form(""),
    highlights: str = Form(""),
    awards: str = Form(""),
    profile_photo: UploadFile = File(default=None),
    images: List[UploadFile] = File(default=[]),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new doctor"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get admin data for templates (to avoid SQLAlchemy lazy loading issues)
    admin_dict = await get_current_admin_dict(session_token, db)
    
    try:
        # Handle profile photo upload
        profile_photo_filename = None
        if profile_photo and profile_photo.filename:
            profile_photo_filename = await save_uploaded_file(profile_photo, "doctor")
        
        # Create doctor object
        doctor = Doctor(
            name=name,
            designation=designation or None,
            hospital_id=hospital_id,
            experience_years=experience_years,
            gender=gender or None,
            description=description or None,
            specialization=specialization or None,
            skills=parse_comma_separated_string(skills),
            qualifications=parse_comma_separated_string(qualifications),
            highlights=parse_comma_separated_string(highlights),
            awards=parse_comma_separated_string(awards),
            profile_photo=f"/media/doctor/{profile_photo_filename}" if profile_photo_filename else None,
            created_at=datetime.now()
        )
        
        db.add(doctor)
        await db.flush()  # Get doctor ID
        
        # Handle image uploads
        image_count = 0
        for image_file in images:
            if image_file and image_file.filename:
                filename = await save_uploaded_file(image_file, "doctor")
                if filename:
                    image = Image(
                        owner_type="doctor",
                        owner_id=doctor.id,
                        url=f"/media/doctor/{filename}",
                        is_primary=image_count == 0,
                        position=image_count
                    )
                    db.add(image)
                    image_count += 1
        
        await db.commit()
        return RedirectResponse(url="/admin/doctors", status_code=302)
        
    except Exception as e:
        await db.rollback()
        # Get hospitals for form
        hospitals = await db.execute(select(Hospital).order_by(Hospital.name))
        hospitals = hospitals.scalars().all()
        
        return render_template("admin/doctor_form.html", {
            "request": request,
            "admin": admin_dict,
            "doctor": None,
            "hospitals": hospitals,
            "action": "Create",
            "error": f"Error creating doctor: {str(e)}"
        })

@router.post("/admin/doctors/{doctor_id}")
async def admin_doctor_update(
    request: Request,
    doctor_id: int,
    name: str = Form(...),
    designation: str = Form(""),
    hospital_id: Optional[int] = Form(None),
    experience_years: Optional[int] = Form(None),
    gender: str = Form(""),
    description: str = Form(""),
    specialization: str = Form(""),
    skills: str = Form(""),
    qualifications: str = Form(""),
    highlights: str = Form(""),
    awards: str = Form(""),
    profile_photo: UploadFile = File(default=None),
    images: List[UploadFile] = File(default=[]),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Update existing doctor"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get existing doctor
        result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
        doctor = result.scalar_one_or_none()
        
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Handle profile photo upload
        if profile_photo and profile_photo.filename:
            profile_photo_filename = await save_uploaded_file(profile_photo, "doctor")
            doctor.profile_photo = f"/media/doctor/{profile_photo_filename}"
        
        # Update doctor fields
        doctor.name = name
        doctor.designation = designation or None
        doctor.hospital_id = hospital_id
        doctor.experience_years = experience_years
        doctor.gender = gender or None
        doctor.description = description or None
        doctor.specialization = specialization or None
        doctor.skills = parse_comma_separated_string(skills)
        doctor.qualifications = parse_comma_separated_string(qualifications)
        doctor.highlights = parse_comma_separated_string(highlights)
        doctor.awards = parse_comma_separated_string(awards)
        
        # Handle new image uploads
        # Get current image count for this doctor
        existing_images_result = await db.execute(
            select(func.count(Image.id)).where(
                Image.owner_type == "doctor",
                Image.owner_id == doctor.id
            )
        )
        image_count = existing_images_result.scalar() or 0
        
        for image_file in images:
            if image_file and image_file.filename:
                filename = await save_uploaded_file(image_file, "doctor")
                if filename:
                    image = Image(
                        owner_type="doctor",
                        owner_id=doctor.id,
                        url=f"/media/doctor/{filename}",
                        is_primary=image_count == 0,
                        position=image_count
                    )
                    db.add(image)
                    image_count += 1
        
        await db.commit()
        return RedirectResponse(url="/admin/doctors", status_code=302)
        
    except Exception as e:
        await db.rollback()
        hospitals = await db.execute(select(Hospital).order_by(Hospital.name))
        hospitals = hospitals.scalars().all()
        
        return render_template("admin/doctor_form.html", {
            "request": request,
            "admin": admin,
            "doctor": doctor,
            "hospitals": hospitals,
            "action": "Update",
            "error": f"Error updating doctor: {str(e)}"
        })

@router.post("/admin/treatments")
async def admin_treatment_create(
    request: Request,
    name: str = Form(...),
    short_description: str = Form(...),
    long_description: str = Form(""),
    treatment_type: str = Form(...),
    location: str = Form(...),
    price_min: Optional[float] = Form(None),
    price_max: Optional[float] = Form(None),
    price_exact: Optional[float] = Form(None),
    hospital_id: Optional[int] = Form(None),
    other_hospital_name: str = Form(""),
    doctor_id: Optional[int] = Form(None),
    other_doctor_name: str = Form(""),
    images: List[UploadFile] = File(default=[]),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new treatment"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Create treatment object
        treatment = Treatment(
            name=name,
            short_description=short_description,
            long_description=long_description or None,
            treatment_type=treatment_type,
            location=location,
            price_min=price_min,
            price_max=price_max,
            price_exact=price_exact,
            hospital_id=hospital_id,
            other_hospital_name=other_hospital_name or None,
            doctor_id=doctor_id,
            other_doctor_name=other_doctor_name or None,
            created_at=datetime.now()
        )
        
        db.add(treatment)
        await db.flush()  # Get treatment ID
        
        # Handle image uploads
        image_count = 0
        for image_file in images:
            if image_file and image_file.filename:
                filename = await save_uploaded_file(image_file, "treatment")
                if filename:
                    image = Image(
                        owner_type="treatment",
                        owner_id=treatment.id,
                        url=f"/media/treatment/{filename}",
                        is_primary=image_count == 0,
                        position=image_count
                    )
                    db.add(image)
                    image_count += 1
        
        await db.commit()
        return RedirectResponse(url="/admin/treatments", status_code=302)
        
    except Exception as e:
        await db.rollback()
        # Get hospitals and doctors for form
        hospitals = await db.execute(select(Hospital).order_by(Hospital.name))
        hospitals = hospitals.scalars().all()
        doctors = await db.execute(select(Doctor).order_by(Doctor.name))
        doctors = doctors.scalars().all()
        
        return render_template("admin/treatment_form.html", {
            "request": request,
            "admin": admin,
            "treatment": None,
            "hospitals": hospitals,
            "doctors": doctors,
            "action": "Create",
            "error": f"Error creating treatment: {str(e)}"
        })

@router.post("/admin/treatments/{treatment_id}")
async def admin_treatment_update(
    request: Request,
    treatment_id: int,
    name: str = Form(...),
    short_description: str = Form(...),
    long_description: str = Form(""),
    treatment_type: str = Form(...),
    location: str = Form(...),
    price_min: Optional[float] = Form(None),
    price_max: Optional[float] = Form(None),
    price_exact: Optional[float] = Form(None),
    hospital_id: Optional[int] = Form(None),
    other_hospital_name: str = Form(""),
    doctor_id: Optional[int] = Form(None),
    other_doctor_name: str = Form(""),
    images: List[UploadFile] = File(default=[]),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Update existing treatment"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get existing treatment
        result = await db.execute(select(Treatment).where(Treatment.id == treatment_id))
        treatment = result.scalar_one_or_none()
        
        if not treatment:
            raise HTTPException(status_code=404, detail="Treatment not found")
        
        # Update treatment fields
        treatment.name = name
        treatment.short_description = short_description
        treatment.long_description = long_description or None
        treatment.treatment_type = treatment_type
        treatment.location = location
        treatment.price_min = price_min
        treatment.price_max = price_max
        treatment.price_exact = price_exact
        treatment.hospital_id = hospital_id
        treatment.other_hospital_name = other_hospital_name or None
        treatment.doctor_id = doctor_id
        treatment.other_doctor_name = other_doctor_name or None
        
        # Handle new image uploads
        # Get current image count for this treatment
        existing_images_result = await db.execute(
            select(func.count(Image.id)).where(
                Image.owner_type == "treatment",
                Image.owner_id == treatment.id
            )
        )
        image_count = existing_images_result.scalar() or 0
        
        for image_file in images:
            if image_file and image_file.filename:
                filename = await save_uploaded_file(image_file, "treatment")
                if filename:
                    image = Image(
                        owner_type="treatment",
                        owner_id=treatment.id,
                        url=f"/media/treatment/{filename}",
                        is_primary=image_count == 0,
                        position=image_count
                    )
                    db.add(image)
                    image_count += 1
        
        await db.commit()
        return RedirectResponse(url="/admin/treatments", status_code=302)
        
    except Exception as e:
        await db.rollback()
        hospitals = await db.execute(select(Hospital).order_by(Hospital.name))
        hospitals = hospitals.scalars().all()
        doctors = await db.execute(select(Doctor).order_by(Doctor.name))
        doctors = doctors.scalars().all()
        
        return render_template("admin/treatment_form.html", {
            "request": request,
            "admin": admin,
            "treatment": treatment,
            "hospitals": hospitals,
            "doctors": doctors,
            "action": "Update",
            "error": f"Error updating treatment: {str(e)}"
        })
