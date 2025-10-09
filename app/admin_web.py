"""
Admin Web Interface Routes
Handles HTML pages for admin dashboard using Jinja2 templates
"""

from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, Cookie, Response, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update, delete, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
import hashlib
import secrets
from jose import jwt
import json
import os
import uuid
import csv
import io
from datetime import datetime, timedelta

from app.dependencies import get_db
from app.models import Admin, Hospital, Doctor, Treatment, ContactUs as Contact, Image, Offer, PackageBooking, Blog, FAQ, Banner, PartnerHospital, PatientStory, User
from app.schemas import TreatmentUpdate, HospitalUpdate, DoctorUpdate, BlogCreate, BlogUpdate
from app.auth import verify_password
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Add custom Jinja2 filters
def nl2br(value):
    """Convert newlines to <br> tags"""
    if not value:
        return value
    return value.replace('\n', '<br>').replace('\r\n', '<br>')

def linebreaks(value):
    """Convert newlines to <br> tags and wrap in paragraphs if needed"""
    if not value:
        return value
    # Replace newlines with <br> tags
    return value.replace('\n', '<br>').replace('\r\n', '<br>')

# Register the filter
templates.env.filters['nl2br'] = nl2br
templates.env.filters['linebreaks'] = linebreaks

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
    stats["offers"] = await db.scalar(select(func.count(Offer.id)))
    stats["contacts"] = await db.scalar(select(func.count(Contact.id)))
    stats["bookings"] = await db.scalar(select(func.count(PackageBooking.id)))
    stats["blogs"] = await db.scalar(select(func.count(Blog.id)))
    stats["published_blogs"] = await db.scalar(select(func.count(Blog.id)).where(Blog.is_published == True))
    stats["banners"] = await db.scalar(select(func.count(Banner.id)))
    stats["active_banners"] = await db.scalar(select(func.count(Banner.id)).where(Banner.is_active == True))
    stats["partners"] = await db.scalar(select(func.count(PartnerHospital.id)))
    stats["active_partners"] = await db.scalar(select(func.count(PartnerHospital.id)).where(PartnerHospital.is_active == True))
    stats["stories"] = await db.scalar(select(func.count(PatientStory.id)))
    stats["featured_stories"] = await db.scalar(select(func.count(PatientStory.id)).where(PatientStory.is_featured == True))
    stats["admins"] = await db.scalar(select(func.count(Admin.id)))
    stats["images"] = await db.scalar(select(func.count(Image.id)))
    stats["users"] = await db.scalar(select(func.count(User.id)))
    stats["active_users"] = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
    stats["verified_users"] = await db.scalar(select(func.count(User.id)).where(User.is_email_verified == True))
    
    # Recent contacts
    recent_contacts = await db.execute(
        select(Contact).order_by(desc(Contact.created_at)).limit(5)
    )
    stats["recent_contacts"] = recent_contacts.scalars().all()
    
    # Recent bookings with treatment information
    recent_bookings = await db.execute(
        select(PackageBooking)
        .options(selectinload(PackageBooking.treatment))
        .order_by(desc(PackageBooking.created_at))
        .limit(5)
    )
    stats["recent_bookings"] = recent_bookings.scalars().all()
    
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

    # Load FAQs for each hospital (only first 3 for summary)
    hospital_faqs_map = {}
    for hospital in hospitals:
        faqs_result = await db.execute(
            select(FAQ).where(
                FAQ.owner_type == "hospital",
                FAQ.owner_id == hospital.id
            ).order_by(FAQ.position, FAQ.id).limit(3)
        )
        hospital_faqs_map[hospital.id] = faqs_result.scalars().all()

    # Get total count for pagination
    total = await db.scalar(select(func.count(Hospital.id)))
    total_pages = (total + limit - 1) // limit

    return render_template("admin/hospitals.html", {
        "request": request,
        "admin": admin,
        "hospitals": hospitals,
        "hospital_faqs_map": hospital_faqs_map,
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

    # Load hospital FAQs separately to avoid lazy loading in template
    faqs_result = await db.execute(
        select(FAQ).where(
            FAQ.owner_type == "hospital",
            FAQ.owner_id == hospital.id
        ).order_by(FAQ.id)
    )
    hospital_faqs = faqs_result.scalars().all()

    return render_template("admin/hospital_form.html", {
        "request": request,
        "admin": admin,
        "hospital": hospital,  
        "hospital_images": hospital_images,
        "hospital_faqs": hospital_faqs,
        "action": "Update"
    })

# Doctor Management
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

# Offers Management (Attractions / Discount Packages)
@router.get("/admin/offers", response_class=HTMLResponse)
async def admin_offers(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    filter_type: Optional[str] = None,
    filter_location: Optional[str] = None,
    filter_status: Optional[str] = None,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Admin offers listing page with filtering and search"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    limit = 20
    offset = (page - 1) * limit
    
    # Build query with filters
    query = select(Offer).options(selectinload(Offer.treatment))
    
    # Apply search filter
    if search:
        query = query.where(
            Offer.name.ilike(f"%{search}%") |
            Offer.description.ilike(f"%{search}%")
        )
    
    # Apply type filter
    if filter_type:
        query = query.where(Offer.treatment_type == filter_type)
    
    # Apply location filter
    if filter_location:
        query = query.where(Offer.location.ilike(f"%{filter_location}%"))
    
    # Apply status filter
    if filter_status == "active":
        query = query.where(Offer.is_active == True, Offer.end_date > datetime.utcnow())
    elif filter_status == "expired":
        query = query.where(Offer.end_date <= datetime.utcnow())
    elif filter_status == "inactive":
        query = query.where(Offer.is_active == False)
    
    # Get total count for pagination
    total_result = await db.execute(select(func.count(Offer.id)).select_from(query.subquery()))
    total = total_result.scalar()
    total_pages = (total + limit - 1) // limit
    
    # Get offers with pagination
    query = query.order_by(desc(Offer.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    offers = result.scalars().all()
    
    # Get unique treatment types for filter dropdown
    treatment_types_result = await db.execute(
        select(Offer.treatment_type).distinct().where(Offer.treatment_type.isnot(None))
    )
    treatment_types = [t for t in treatment_types_result.scalars().all() if t]
    
    return render_template("admin/offers.html", {
        "request": request,
        "admin": admin,
        "offers": offers,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "filter_type": filter_type,
        "filter_location": filter_location,
        "filter_status": filter_status,
        "treatment_types": treatment_types
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

@router.get("/admin/contacts/{contact_id}")
async def get_contact_details(
    contact_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Get individual contact details (API endpoint for modal)"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Convert contact to dict for JSON response
    return {
        "id": contact.id,
        "name": contact.name,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "email": contact.email,
        "phone": contact.phone,
        "subject": contact.subject,
        "message": contact.message,
        "service_type": contact.service_type,
        "is_read": contact.is_read,
        "admin_response": contact.admin_response,
        "responded_at": contact.responded_at.isoformat() if contact.responded_at else None,
        "created_at": contact.created_at.isoformat() if contact.created_at else None
    }

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
    
    # Update all unread contacts to read
    await db.execute(
        Contact.__table__.update().where(Contact.is_read == False).values(is_read=True)
    )
    await db.commit()
    
    return {"message": "All contacts marked as read"}

# Package Booking Management
@router.get("/admin/bookings", response_class=HTMLResponse)
async def admin_bookings(
    request: Request,
    page: int = 1,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    search: Optional[str] = None,
    export: Optional[str] = None,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Package booking management page with date range and treatment type filters"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Parse date parameters
    from_date_obj = None
    to_date_obj = None
    
    if from_date and from_date.strip():
        try:
            from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
        except ValueError:
            from_date_obj = None
    
    if to_date and to_date.strip():
        try:
            # Set to end of day for to_date
            to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        except ValueError:
            to_date_obj = None
    
    limit = 15
    offset = (page - 1) * limit
    
    # Build query
    query = select(PackageBooking).options(selectinload(PackageBooking.treatment))
    
    # Apply date range filters
    if from_date_obj:
        query = query.where(PackageBooking.created_at >= from_date_obj)
    if to_date_obj:
        query = query.where(PackageBooking.created_at <= to_date_obj)
    
    # Apply treatment type search filter
    if search:
        search_term = f"%{search.strip()}%"
        query = query.join(Treatment, PackageBooking.treatment_id == Treatment.id, isouter=True).where(
            (Treatment.name.ilike(search_term)) |
            (Treatment.treatment_type.ilike(search_term)) |
            # Also match "online consultancy" for bookings with doctor preference but no treatment
            (and_(
                PackageBooking.treatment_id.is_(None),
                PackageBooking.doctor_preference.isnot(None),
                PackageBooking.doctor_preference != 'null',
                PackageBooking.doctor_preference != '',
                or_(
                    search_term.lower().find('online') != -1,
                    search_term.lower().find('consultancy') != -1,
                    search_term.lower().find('consultation') != -1,
                    search_term.lower().find('virtual') != -1
                ).self_group()
            ))
        )
    
    # Add ordering and pagination
    query = query.order_by(desc(PackageBooking.created_at)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    bookings = result.scalars().all()
    
    # Handle export request
    if export == "true":
        # For export, get all matching records without pagination
        export_query = select(PackageBooking).options(selectinload(PackageBooking.treatment))
        
        # Apply same filters
        if from_date_obj:
            export_query = export_query.where(PackageBooking.created_at >= from_date_obj)
        if to_date_obj:
            export_query = export_query.where(PackageBooking.created_at <= to_date_obj)
        if search:
            search_term = f"%{search.strip()}%"
            export_query = export_query.join(Treatment, PackageBooking.treatment_id == Treatment.id, isouter=True).where(
                (Treatment.name.ilike(search_term)) |
                (Treatment.treatment_type.ilike(search_term)) |
                # Also match "online consultancy" for bookings with doctor preference but no treatment
                (and_(
                    PackageBooking.treatment_id.is_(None),
                    PackageBooking.doctor_preference.isnot(None),
                    PackageBooking.doctor_preference != 'null',
                    PackageBooking.doctor_preference != '',  
                    or_(
                        search_term.lower().find('online') != -1,
                        search_term.lower().find('consultancy') != -1,
                        search_term.lower().find('consultation') != -1,
                        search_term.lower().find('virtual') != -1
                    ).self_group()
                ))
            )
        
        export_query = export_query.order_by(desc(PackageBooking.created_at))
        export_result = await db.execute(export_query)
        all_bookings = export_result.scalars().all()
        
        # Generate CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'ID', 'First Name', 'Last Name', 'Email', 'Mobile', 
            'Treatment', 'Treatment Type', 'Budget', 'Doctor Preference', 
            'Hospital Preference', 'Travel Assistant', 'Stay Assistant', 
            'Personal Assistant', 'Medical History File', 'User Query', 
            'Created Date'
        ])
        
        # Write data
        for booking in all_bookings:
            writer.writerow([
                booking.id,
                booking.first_name,
                booking.last_name,
                booking.email,
                booking.mobile_no,
                booking.treatment.name if booking.treatment else 'Not selected',
                booking.treatment.treatment_type if booking.treatment else 'N/A',
                booking.budget or 'Not specified',
                booking.doctor_preference or 'No preference',
                booking.hospital_preference or 'No preference',
                'Yes' if booking.travel_assistant else 'No',
                'Yes' if booking.stay_assistant else 'No',
                'Yes' if booking.personal_assistant else 'No',
                booking.medical_history_file or 'None',
                booking.user_query or 'None',
                booking.created_at.strftime('%Y-%m-%d %H:%M:%S') if booking.created_at else 'N/A'
            ])
        
        output.seek(0)
        
        # Create filename with current date
        filename = f"bookings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Return CSV file
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    # Get total count for pagination
    count_query = select(func.count(PackageBooking.id))
    if from_date_obj:
        count_query = count_query.where(PackageBooking.created_at >= from_date_obj)
    if to_date_obj:
        count_query = count_query.where(PackageBooking.created_at <= to_date_obj)
    if search:
        search_term = f"%{search.strip()}%"
        count_query = count_query.join(Treatment, PackageBooking.treatment_id == Treatment.id, isouter=True).where(
            (Treatment.name.ilike(search_term)) |
            (Treatment.treatment_type.ilike(search_term)) |
            # Also match "online consultancy" for bookings with doctor preference but no treatment
            (and_(
                PackageBooking.treatment_id.is_(None),
                PackageBooking.doctor_preference.isnot(None),
                PackageBooking.doctor_preference != 'null',
                PackageBooking.doctor_preference != '',
                or_(
                    search_term.lower().find('online') != -1,
                    search_term.lower().find('consultancy') != -1,
                    search_term.lower().find('consultation') != -1,
                    search_term.lower().find('virtual') != -1
                ).self_group()
            ))
        )
    
    total = await db.scalar(count_query)
    total_pages = (total + limit - 1) // limit
    
    # Get booking statistics
    stats_query = select(func.count(PackageBooking.id))
    total_bookings = await db.scalar(stats_query)
    
    # Last 7 days bookings
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_bookings = await db.scalar(
        select(func.count(PackageBooking.id)).where(PackageBooking.created_at >= week_ago)
    )
    
    # Last 30 days bookings
    month_ago = datetime.utcnow() - timedelta(days=30)
    month_bookings = await db.scalar(
        select(func.count(PackageBooking.id)).where(PackageBooking.created_at >= month_ago)
    )
    
    return render_template("admin/bookings.html", {
        "request": request,
        "admin": admin,
        "bookings": bookings,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "from_date": from_date,
        "to_date": to_date,
        "search": search or "",
        "total_bookings": total_bookings,
        "week_bookings": week_bookings,
        "month_bookings": month_bookings
    })

@router.get("/admin/bookings/{booking_id}/details")
async def get_booking_details(
    booking_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Get booking details for modal display"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get booking with treatment data
    result = await db.execute(
        select(PackageBooking).options(
            selectinload(PackageBooking.treatment)
        ).where(PackageBooking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Helper function to resolve doctor preference
    async def resolve_doctor_preference(pref_string):
        if not pref_string:
            return "No preference"
        
        # Check if it's a numeric ID
        try:
            doctor_id = int(pref_string.strip())
            doctor = await db.get(Doctor, doctor_id)
            if doctor:
                return doctor.name
            else:
                return f"Doctor ID {doctor_id} (Not found)"
        except ValueError:
            # Not a numeric ID, return as is
            return pref_string
    
    # Helper function to resolve hospital preference
    async def resolve_hospital_preference(pref_string):
        if not pref_string:
            return "No preference"
        
        # Check if it's a numeric ID
        try:
            hospital_id = int(pref_string.strip())
            hospital = await db.get(Hospital, hospital_id)
            if hospital:
                return hospital.name
            else:
                return f"Hospital ID {hospital_id} (Not found)"
        except ValueError:
            # Not a numeric ID, return as is
            return pref_string
    
    # Resolve preferences
    doctor_preference_resolved = await resolve_doctor_preference(booking.doctor_preference)
    hospital_preference_resolved = await resolve_hospital_preference(booking.hospital_preference)
    
    return {
        "id": booking.id,
        "first_name": booking.first_name,
        "last_name": booking.last_name,
        "email": booking.email,
        "mobile_no": booking.mobile_no,
        "treatment": {
            "id": booking.treatment.id if booking.treatment else None,
            "name": booking.treatment.name if booking.treatment else "N/A",
            "treatment_type": booking.treatment.treatment_type if booking.treatment else "N/A"
        } if booking.treatment else None,
        "budget": booking.budget,
        "medical_history_file": booking.medical_history_file,
        "doctor_preference": doctor_preference_resolved,
        "hospital_preference": hospital_preference_resolved,
        "user_query": booking.user_query,
        "travel_assistant": booking.travel_assistant,
        "stay_assistant": booking.stay_assistant,
        "personal_assistant": booking.personal_assistant,
        "created_at": booking.created_at.isoformat() if booking.created_at else None
    }

@router.api_route("/admin/bookings/{booking_id}/download-medical-file", methods=["GET", "HEAD"])
async def download_medical_file(
    booking_id: int,
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Download medical history file for a booking"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get booking to verify it exists and get filename
    result = await db.execute(
        select(PackageBooking).where(PackageBooking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if not booking.medical_history_file or booking.medical_history_file == 'null':
        raise HTTPException(status_code=404, detail="No medical history file found")
    
    # The medical_history_file field already contains the full path (e.g., media/medical/uuid.pdf)
    file_path = booking.medical_history_file
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Medical history file not found on server")
    
    # Extract just the filename for download
    filename = os.path.basename(file_path)
    
    # For HEAD requests, just return headers without file content
    if request.method == "HEAD":
        file_size = os.path.getsize(file_path)
        headers = {
            "Content-Type": "application/octet-stream",
            "Content-Length": str(file_size),
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        return Response(headers=headers)
    
    # For GET requests, return the actual file
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@router.delete("/admin/bookings/{booking_id}")
async def delete_booking(
    booking_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete a booking"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    booking = await db.get(PackageBooking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    await db.delete(booking)
    await db.commit()
    
    return {"message": "Booking deleted successfully"}

@router.delete("/admin/hospitals/{hospital_id}")
async def delete_hospital(
    hospital_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete a hospital"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    hospital = await db.get(Hospital, hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    # Delete associated images first
    await db.execute(
        select(Image).where(
            Image.owner_type == "hospital",
            Image.owner_id == hospital_id
        )
    )
    images_result = await db.execute(
        select(Image).where(
            Image.owner_type == "hospital",
            Image.owner_id == hospital_id
        )
    )
    images = images_result.scalars().all()
    for image in images:
        await db.delete(image)
    
    await db.delete(hospital)
    await db.commit()
    
    return {"message": "Hospital deleted successfully"}

@router.get("/admin/hospitals/{hospital_id}/details")
async def get_hospital_details(
    hospital_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Get hospital details for modal display"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get hospital with related data
    result = await db.execute(
        select(Hospital).options(
            selectinload(Hospital.doctors),
            selectinload(Hospital.treatments)
        ).where(Hospital.id == hospital_id)
    )
    hospital = result.scalar_one_or_none()
    
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    # Get hospital images
    images_result = await db.execute(
        select(Image).where(
            Image.owner_type == "hospital",
            Image.owner_id == hospital_id
        ).order_by(Image.position)
    )
    images = images_result.scalars().all()
    
    return {
        "id": hospital.id,
        "name": hospital.name,
        "description": hospital.description,
        "location": hospital.location,
        "address": hospital.address,
        "phone": hospital.phone,
        "email": hospital.email,
        "features": hospital.features,
        "facilities": hospital.facilities,
        "specializations": hospital.specializations,
        "rating": hospital.rating,
        "is_active": hospital.is_active,
        "created_at": hospital.created_at,
        "images": [{"id": img.id, "url": img.url, "is_primary": img.is_primary} for img in images],
        "doctors_count": len(hospital.doctors) if hospital.doctors else 0,
        "treatments_count": len(hospital.treatments) if hospital.treatments else 0
    }

@router.delete("/admin/doctors/{doctor_id}")
async def delete_doctor(
    doctor_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete a doctor"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    doctor = await db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Delete associated images first
    images_result = await db.execute(
        select(Image).where(
            Image.owner_type == "doctor",
            Image.owner_id == doctor_id
        )
    )
    images = images_result.scalars().all()
    for image in images:
        await db.delete(image)
    
    await db.delete(doctor)
    await db.commit()
    
    return {"message": "Doctor deleted successfully"}

@router.delete("/admin/treatments/{treatment_id}")
async def delete_treatment(
    treatment_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete a treatment"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    treatment = await db.get(Treatment, treatment_id)
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    # Delete associated images first
    images_result = await db.execute(
        select(Image).where(
            Image.owner_type == "treatment",
            Image.owner_id == treatment_id
        )
    )
    images = images_result.scalars().all()
    for image in images:
        await db.delete(image)
    
    await db.delete(treatment)
    await db.commit()
    
    return {"message": "Treatment deleted successfully"}

@router.delete("/admin/offers/{offer_id}")
async def delete_offer(
    offer_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete an offer"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    offer = await db.get(Offer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Delete associated images first
    images_result = await db.execute(
        select(Image).where(
            Image.owner_type == "offer",
            Image.owner_id == offer_id
        )
    )
    images = images_result.scalars().all()
    for image in images:
        await db.delete(image)
    
    await db.delete(offer)
    await db.commit()
    
    return {"message": "Offer deleted successfully"}

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

@router.get("/admin/admins/new", response_class=HTMLResponse)
async def admin_new_admin(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """New admin form (Super Admin only)"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin or not admin.get('is_super_admin'):
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    
    return render_template("admin/admin_form.html", {
        "request": request,
        "admin": admin,
        "admin_user": None,
        "action": "Create"
    })

@router.get("/admin/admins/{admin_id}/edit", response_class=HTMLResponse)
async def admin_edit_admin(
    request: Request,
    admin_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Edit admin form (Super Admin only)"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin or not admin.get('is_super_admin'):
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    
    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    admin_user = result.scalar_one_or_none()
    
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    return render_template("admin/admin_form.html", {
        "request": request,
        "admin": admin,
        "admin_user": admin_user,
        "action": "Update"
    })

@router.post("/admin/admins/new")
async def admin_create_admin(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    is_super_admin: bool = Form(False),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new admin (Super Admin only)"""
    admin = await get_current_admin_object(session_token, db)
    if not admin or not admin.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin privileges required")
    
    try:
        # Check if username or email already exists
        existing_admin = await db.execute(
            select(Admin).where(
                (Admin.username == username) | (Admin.email == email)
            )
        )
        if existing_admin.scalar_one_or_none():
            return render_template("admin/admin_form.html", {
                "request": request,
                "admin": await get_current_admin_dict(session_token, db),
                "admin_user": None,
                "action": "Create",
                "error": "Username or email already exists"
            })
        
        # Hash password
        from app.auth import get_password_hash
        hashed_password = get_password_hash(password)
        
        # Create new admin
        new_admin = Admin(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_super_admin=is_super_admin,
            is_active=True
        )
        
        db.add(new_admin)
        await db.commit()
        
        return RedirectResponse(url="/admin/admins", status_code=302)
        
    except Exception as e:
        await db.rollback()
        return render_template("admin/admin_form.html", {
            "request": request,
            "admin": await get_current_admin_dict(session_token, db),
            "admin_user": None,
            "action": "Create",
            "error": f"Error creating admin: {str(e)}"
        })

@router.post("/admin/admins/{admin_id}/edit")
async def admin_update_admin(
    request: Request,
    admin_id: int,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(None),
    is_super_admin: bool = Form(False),
    is_active: bool = Form(True),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Update admin (Super Admin only)"""
    admin = await get_current_admin_object(session_token, db)
    if not admin or not admin.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin privileges required")
    
    try:
        admin_user = await db.get(Admin, admin_id)
        if not admin_user:
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Check if username or email already exists (excluding current admin)
        existing_admin = await db.execute(
            select(Admin).where(
                ((Admin.username == username) | (Admin.email == email)) &
                (Admin.id != admin_id)
            )
        )
        if existing_admin.scalar_one_or_none():
            return render_template("admin/admin_form.html", {
                "request": request,
                "admin": await get_current_admin_dict(session_token, db),
                "admin_user": admin_user,
                "action": "Update",
                "error": "Username or email already exists"
            })
        
        # Update admin fields
        admin_user.username = username
        admin_user.email = email
        admin_user.is_super_admin = is_super_admin
        admin_user.is_active = is_active
        
        # Update password if provided
        if password and password.strip():
            from app.auth import get_password_hash
            admin_user.hashed_password = get_password_hash(password)
        
        await db.commit()
        
        return RedirectResponse(url="/admin/admins", status_code=302)
        
    except Exception as e:
        await db.rollback()
        return render_template("admin/admin_form.html", {
            "request": request,
            "admin": await get_current_admin_dict(session_token, db),
            "admin_user": admin_user,
            "action": "Update",
            "error": f"Error updating admin: {str(e)}"
        })

@router.delete("/admin/admins/{admin_id}")
async def admin_delete_admin(
    admin_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete admin (Super Admin only)"""
    admin = await get_current_admin_object(session_token, db)
    if not admin or not admin.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin privileges required")
    
    admin_user = await db.get(Admin, admin_id)
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # Prevent deleting self
    if admin_user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Prevent deleting the last super admin
    if admin_user.is_super_admin:
        super_admin_count = await db.scalar(
            select(func.count(Admin.id)).where(Admin.is_super_admin == True)
        )
        if super_admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last super admin")
    
    await db.delete(admin_user)
    await db.commit()
    
    return {"message": "Admin deleted successfully"}

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

    # Load doctor FAQs separately to avoid lazy loading in template
    faqs_result = await db.execute(
        select(FAQ).where(
            FAQ.owner_type == "doctor",
            FAQ.owner_id == doctor.id
        ).order_by(FAQ.id)
    )
    doctor_faqs = faqs_result.scalars().all()
    
    # Load doctor images separately to avoid lazy loading in template
    images_result = await db.execute(
        select(Image).where(
            Image.owner_type == "doctor",
            Image.owner_id == doctor.id
        ).order_by(Image.position, Image.id)
    )
    doctor_images = images_result.scalars().all()
    
    # Debug: Check FAQ loading
    print(f"DEBUG DOCTOR EDIT: Loading FAQs for doctor {doctor.id}")
    print(f"DEBUG DOCTOR EDIT: Found {len(doctor_faqs)} FAQs")
    for i, faq in enumerate(doctor_faqs):
        print(f"DEBUG DOCTOR EDIT: FAQ {i+1}: Q='{faq.question}', A='{faq.answer}'")
        print(f"DEBUG DOCTOR EDIT: FAQ {i+1} Answer repr: {repr(faq.answer)}")
    
    return render_template("admin/doctor_form.html", {
        "request": request,
        "admin": admin,
        "doctor": doctor,
        "hospitals": hospitals,
        "doctor_faqs": doctor_faqs,
        "doctor_images": doctor_images,
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
        ).order_by(Image.position.asc(), Image.id.asc())
    )
    treatment_images = images_result.scalars().all()

    # Load treatment FAQs separately to avoid lazy loading in template
    print(f"DEBUG QUERY: Looking for FAQs with owner_type='treatment' and owner_id={treatment.id}")
    
    # Ensure we have a fresh database session by expunging and re-querying if needed
    await db.commit()  # Commit any pending changes
    
    faqs_result = await db.execute(
        select(FAQ).where(
            FAQ.owner_type == "treatment",
            FAQ.owner_id == treatment.id
        ).order_by(FAQ.position.asc(), FAQ.id.asc())
    )
    treatment_faqs = faqs_result.scalars().all()
    
    print(f"Loading treatment {treatment.id}: Found {len(treatment_faqs)} FAQs")
    if len(treatment_faqs) > 0:
        for faq in treatment_faqs:
            print(f"  - FAQ {faq.id}: {faq.question[:50]}... (Position: {faq.position}, Active: {faq.is_active})")
    else:
        print("  - No FAQs found for this treatment")
        
    # Additional verification query to ensure we're seeing all FAQs
    all_treatment_faqs = await db.execute(
        select(FAQ).where(FAQ.owner_type == "treatment", FAQ.owner_id == treatment.id)
    )
    all_faqs_for_treatment = all_treatment_faqs.scalars().all()
    print(f"Direct query found {len(all_faqs_for_treatment)} FAQs for treatment {treatment.id}")
    
    if len(all_faqs_for_treatment) != len(treatment_faqs):
        print(f"WARNING: Mismatch in FAQ counts! Ordered query: {len(treatment_faqs)}, Direct query: {len(all_faqs_for_treatment)}")
        # Use the direct query result if there's a mismatch
        treatment_faqs = all_faqs_for_treatment
    
    return render_template("admin/treatment_form.html", {
        "request": request,
        "admin": admin,
        "treatment": treatment,
        "treatment_images": treatment_images,
        "hospitals": hospitals,
        "doctors": doctors,
        "treatment_types": treatment_types,
        "treatment_faqs": treatment_faqs,
        "action": "Update"
    })

@router.get("/admin/offers/new", response_class=HTMLResponse)
async def admin_offer_new(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """New offer form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get treatments for dropdown
    treatments = await db.execute(select(Treatment).order_by(Treatment.name))
    treatments = treatments.scalars().all()
    
    # Get unique treatment types for dropdown
    treatment_types_result = await db.execute(
        select(Treatment.treatment_type).distinct().where(Treatment.treatment_type.isnot(None))
    )
    treatment_types = [t for t in treatment_types_result.scalars().all() if t]
    
    return render_template("admin/offer_form.html", {
        "request": request,
        "admin": admin,
        "offer": None,
        "treatments": treatments,
        "treatment_types": treatment_types,
        "action": "Create"
    })

@router.get("/admin/offers/{offer_id}/edit", response_class=HTMLResponse)
async def admin_offer_edit(
    request: Request,
    offer_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Edit offer form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Get treatments for dropdown
    treatments = await db.execute(select(Treatment).order_by(Treatment.name))
    treatments = treatments.scalars().all()
    
    # Get unique treatment types for dropdown
    treatment_types_result = await db.execute(
        select(Treatment.treatment_type).distinct().where(Treatment.treatment_type.isnot(None))
    )
    treatment_types = [t for t in treatment_types_result.scalars().all() if t]
    
    # Load offer images separately to avoid lazy loading in template
    images_result = await db.execute(
        select(Image).where(
            Image.owner_type == "offer",
            Image.owner_id == offer.id
        ).order_by(Image.position, Image.id)
    )
    offer_images = images_result.scalars().all()
    
    return render_template("admin/offer_form.html", {
        "request": request,
        "admin": admin,
        "offer": offer,
        "offer_images": offer_images,
        "treatments": treatments,
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
    is_featured: bool = Form(False),
    faq1_question: str = Form(""),
    faq1_answer: str = Form(""),
    faq2_question: str = Form(""),
    faq2_answer: str = Form(""),
    faq3_question: str = Form(""),
    faq3_answer: str = Form(""),
    faq4_question: str = Form(""),
    faq4_answer: str = Form(""),
    faq5_question: str = Form(""),
    faq5_answer: str = Form(""),
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
            faq1_question=faq1_question.strip() if faq1_question else None,
            faq1_answer=faq1_answer.strip() if faq1_answer else None,
            faq2_question=faq2_question.strip() if faq2_question else None,
            faq2_answer=faq2_answer.strip() if faq2_answer else None,
            faq3_question=faq3_question.strip() if faq3_question else None,
            faq3_answer=faq3_answer.strip() if faq3_answer else None,
            faq4_question=faq4_question.strip() if faq4_question else None,
            faq4_answer=faq4_answer.strip() if faq4_answer else None,
            faq5_question=faq5_question.strip() if faq5_question else None,
            faq5_answer=faq5_answer.strip() if faq5_answer else None,
            is_featured=is_featured,
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

        # FAQ fields are now saved directly to the hospital model
        
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
    description: str = Form("") ,
    location: str = Form("") ,
    phone: str = Form("") ,
    email: str = Form("") ,
    address: str = Form("") ,
    rating: str = Form("") ,
    specializations: str = Form("") ,
    features: str = Form("") ,
    facilities: str = Form("") ,
    is_featured: bool = Form(False),
    faq1_question: str = Form(""),
    faq1_answer: str = Form(""),
    faq2_question: str = Form(""),
    faq2_answer: str = Form(""),
    faq3_question: str = Form(""),
    faq3_answer: str = Form(""),
    faq4_question: str = Form(""),
    faq4_answer: str = Form(""),
    faq5_question: str = Form(""),
    faq5_answer: str = Form(""),
    images: List[UploadFile] = File(default=[]),
    delete_image_id: str = Form(None),
    update_image_order: str = Form(None),
    image_order: str = Form(None),
    set_primary_image: str = Form(None),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    import logging
    import traceback
    logger = logging.getLogger("admin")
    # Debug line removed
    # Debug line removed
    # Debug line removed
    # Debug line removed
    # Extra debug: print all POSTed form data
    try:
        print(f"[DEBUG] POST form data: name={name}, location={location}, phone={phone}, email={email}, address={address}, rating={rating}, specializations={specializations}, features={features}, facilities={facilities}, is_featured={is_featured}")
    except Exception as e:
        print(f"[DEBUG] Error printing POST form data: {e}")
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

        # Handle AJAX image operations
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle image deletion
            if delete_image_id and delete_image_id.isdigit():
                print(f"Processing hospital image deletion for image ID: {delete_image_id}, hospital ID: {hospital_id}")
                image_id = int(delete_image_id)
                # Get the image to delete
                result = await db.execute(
                    select(Image)
                    .where(Image.id == image_id, Image.owner_type == "hospital", Image.owner_id == hospital_id)
                )
                image_to_delete = result.scalar_one_or_none()
                
                if image_to_delete:
                    await db.delete(image_to_delete)
                    await db.commit()
                    print(f"Successfully deleted hospital image {image_id}")
                    return {"success": True, "message": "Image deleted successfully"}
                else:
                    print(f"Hospital image {image_id} not found")
                    return {"success": False, "message": "Image not found"}
            
            # Handle image reordering
            if update_image_order and image_order:
                try:
                    order_data = json.loads(image_order)
                    print(f"Processing hospital image reordering for hospital {hospital_id}: {order_data}")
                    
                    for item in order_data:
                        image_id = item['id']
                        new_position = item['position']
                        
                        await db.execute(
                            update(Image)
                            .where(Image.id == image_id, Image.owner_type == "hospital", Image.owner_id == hospital_id)
                            .values(position=new_position)
                        )
                    
                    await db.commit()
                    print(f"Successfully updated hospital image positions for hospital {hospital_id}")
                    return {"success": True, "message": "Image order updated successfully"}
                except json.JSONDecodeError:
                    return {"success": False, "message": "Invalid image order data"}
            
            # Handle primary image selection
            if set_primary_image and set_primary_image.isdigit():
                print(f"Processing primary image selection for hospital {hospital_id}, image {set_primary_image}")
                image_id = int(set_primary_image)
                
                # First, set all images as non-primary
                await db.execute(
                    update(Image)
                    .where(Image.owner_type == "hospital", Image.owner_id == hospital_id)
                    .values(is_primary=False)
                )
                
                # Then set the selected image as primary
                await db.execute(
                    update(Image)
                    .where(Image.id == image_id, Image.owner_type == "hospital", Image.owner_id == hospital_id)
                    .values(is_primary=True)
                )
                
                await db.commit()
                print(f"Successfully set hospital image {image_id} as primary")
                return {"success": True, "message": "Primary image updated successfully"}

        # Update hospital fields
        update_data = HospitalUpdate(
            name=name,
            description=description or None,
            location=location or None,
            phone=phone or None,
            rating=rating,
            features=parse_comma_separated_string(features),
            facilities=parse_comma_separated_string(facilities)
        )
        hospital.name = update_data.name
        hospital.description = update_data.description
        hospital.location = update_data.location
        hospital.phone = update_data.phone
        hospital.email = email or None
        hospital.address = address or None
        hospital.rating = update_data.rating
        hospital.specializations = parse_comma_separated_string(specializations)
        hospital.features = update_data.features
        hospital.facilities = update_data.facilities
        hospital.is_featured = is_featured
        
        # Update FAQ fields
        print(f"DEBUG HOSPITAL: Updating FAQ fields for hospital {hospital_id}")
        print(f"  - FAQ 1: Q='{faq1_question}' A='{faq1_answer}'")
        print(f"  - FAQ 2: Q='{faq2_question}' A='{faq2_answer}'")
        print(f"  - FAQ 3: Q='{faq3_question}' A='{faq3_answer}'")
        print(f"  - FAQ 4: Q='{faq4_question}' A='{faq4_answer}'")
        print(f"  - FAQ 5: Q='{faq5_question}' A='{faq5_answer}'")
        
        hospital.faq1_question = faq1_question.strip() if faq1_question else None
        hospital.faq1_answer = faq1_answer.strip() if faq1_answer else None
        hospital.faq2_question = faq2_question.strip() if faq2_question else None
        hospital.faq2_answer = faq2_answer.strip() if faq2_answer else None
        hospital.faq3_question = faq3_question.strip() if faq3_question else None
        hospital.faq3_answer = faq3_answer.strip() if faq3_answer else None
        hospital.faq4_question = faq4_question.strip() if faq4_question else None
        hospital.faq4_answer = faq4_answer.strip() if faq4_answer else None
        hospital.faq5_question = faq5_question.strip() if faq5_question else None
        hospital.faq5_answer = faq5_answer.strip() if faq5_answer else None

        # Handle new image uploads
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

        # FAQ fields are now saved directly to the hospital model
        
        await db.commit()
        return RedirectResponse(url="/admin/hospitals", status_code=302)
        
    except Exception as e:
        await db.rollback()
        logger.error(f"[ERROR] Exception in admin_hospital_update: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"[ERROR] Exception in admin_hospital_update: {str(e)}")
        print(traceback.format_exc())
        # Load latest FAQs for this hospital
        hospital_faqs = []
        if hospital and hospital.id:
            try:
                faqs_result = await db.execute(
                    select(FAQ).where(
                        FAQ.owner_type == "hospital",
                        FAQ.owner_id == hospital.id
                    ).order_by(FAQ.position, FAQ.id)
                )
                hospital_faqs = faqs_result.scalars().all()
            except Exception as e2:
                print(f"[ERROR] Exception loading hospital FAQs after error: {e2}")
        return render_template(
            "admin/hospital_form.html",
            {
                "request": request,
                "admin": admin,
                "hospital": hospital,
                "hospital_faqs": hospital_faqs,
                "action": "Update",
                "error": f"Error updating hospital: {str(e)}"
            }
        )

@router.post("/admin/doctors")
async def admin_doctor_create(
    request: Request,
    name: str = Form(...),
    designation: str = Form(""),
    hospital_id: Optional[int] = Form(None),
    location: str = Form(""),
    experience_years: Optional[int] = Form(None),
    rating: Optional[float] = Form(None),
    gender: str = Form(""),
    short_description: str = Form(""),
    long_description: str = Form(""),
    specialization: str = Form(""),
    qualification: str = Form(""),
    consultancy_fee: Optional[float] = Form(None),
    skills: str = Form(""),
    qualifications: str = Form(""),
    highlights: str = Form(""),
    awards: str = Form(""),
    is_featured: bool = Form(False),
    faq1_question: str = Form(""),
    faq1_answer: str = Form(""),
    faq2_question: str = Form(""),
    faq2_answer: str = Form(""),
    faq3_question: str = Form(""),
    faq3_answer: str = Form(""),
    faq4_question: str = Form(""),
    faq4_answer: str = Form(""),
    faq5_question: str = Form(""),
    faq5_answer: str = Form(""),
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
            location=location or None,
            experience_years=experience_years,
            rating=rating,
            gender=gender or None,
            short_description=short_description or None,
            long_description=long_description or None,
            specialization=specialization or None,
            qualification=qualification or None,
            consultancy_fee=consultancy_fee,
            skills=parse_comma_separated_string(skills),
            qualifications=parse_comma_separated_string(qualifications),
            highlights=parse_comma_separated_string(highlights),
            awards=parse_comma_separated_string(awards),
            profile_photo=f"/media/doctor/{profile_photo_filename}" if profile_photo_filename else None,
            is_featured=is_featured,
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

        # Set FAQ fields directly on doctor model
        doctor.faq1_question = faq1_question.strip() if faq1_question else None
        doctor.faq1_answer = faq1_answer.strip() if faq1_answer else None
        doctor.faq2_question = faq2_question.strip() if faq2_question else None
        doctor.faq2_answer = faq2_answer.strip() if faq2_answer else None
        doctor.faq3_question = faq3_question.strip() if faq3_question else None
        doctor.faq3_answer = faq3_answer.strip() if faq3_answer else None
        doctor.faq4_question = faq4_question.strip() if faq4_question else None
        doctor.faq4_answer = faq4_answer.strip() if faq4_answer else None
        doctor.faq5_question = faq5_question.strip() if faq5_question else None
        doctor.faq5_answer = faq5_answer.strip() if faq5_answer else None
        
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
    hospital_id: str = Form(""),
    location: str = Form(""),
    experience_years: str = Form(""),
    rating: str = Form(""),
    gender: str = Form(""),
    short_description: str = Form(""),
    long_description: str = Form(""),
    specialization: str = Form(""),
    qualification: str = Form(""),
    consultancy_fee: str = Form(""),
    skills: str = Form(""),
    qualifications: str = Form(""),
    highlights: str = Form(""),
    awards: str = Form(""),
    is_featured: bool = Form(False),
    faq1_question: str = Form(""),
    faq1_answer: str = Form(""),
    faq2_question: str = Form(""),
    faq2_answer: str = Form(""),
    faq3_question: str = Form(""),
    faq3_answer: str = Form(""),
    faq4_question: str = Form(""),
    faq4_answer: str = Form(""),
    faq5_question: str = Form(""),
    faq5_answer: str = Form(""),
    profile_photo: UploadFile = File(default=None),
    images: List[UploadFile] = File(default=[]),
    delete_image_id: str = Form(None),
    update_image_order: str = Form(None),
    image_order: str = Form(None),
    delete_profile_photo: str = Form(None),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Update existing doctor"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Debug: Print FAQ data received
    # Debug line removed
    # Debug line removed
    # Debug line removed
    print(f"DEBUG DOCTOR: is_featured: {is_featured}")
    print(f"DEBUG DOCTOR: delete_image_id: {delete_image_id}")
    print(f"DEBUG DOCTOR: update_image_order: {update_image_order}")
    print(f"DEBUG DOCTOR: delete_profile_photo: {delete_profile_photo}")
    print(f"DEBUG DOCTOR: Request headers: {dict(request.headers)}")
    
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
        
        # Handle AJAX image operations
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle profile photo deletion
            if delete_profile_photo == 'true':
                print(f"Processing profile photo deletion for doctor ID: {doctor_id}")
                if doctor.profile_photo:
                    doctor.profile_photo = None
                    await db.commit()
                    print(f"Successfully deleted profile photo for doctor {doctor_id}")
                    return {"success": True, "message": "Profile photo deleted successfully"}
                else:
                    print(f"No profile photo found for doctor {doctor_id}")
                    return {"success": False, "message": "No profile photo to delete"}
            
            # Handle image deletion
            if delete_image_id and delete_image_id.isdigit():
                print(f"Processing image deletion for image ID: {delete_image_id}, doctor ID: {doctor_id}")
                image_id = int(delete_image_id)
                # Get the image to delete
                result = await db.execute(
                    select(Image)
                    .where(Image.id == image_id, Image.owner_type == "doctor", Image.owner_id == doctor_id)
                )
                image_to_delete = result.scalar_one_or_none()
                
                if image_to_delete:
                    await db.delete(image_to_delete)
                    await db.commit()
                    print(f"Successfully deleted image {image_id}")
                    return {"success": True, "message": "Image deleted successfully"}
                else:
                    print(f"Image {image_id} not found")
                    return {"success": False, "message": "Image not found"}
            
            # Handle image reordering
            if update_image_order and image_order:
                try:
                    order_data = json.loads(image_order)
                    print(f"Processing image reordering for doctor {doctor_id}: {order_data}")
                    
                    for item in order_data:
                        image_id = item['id']
                        new_position = item['position']
                        
                        await db.execute(
                            update(Image)
                            .where(Image.id == image_id, Image.owner_type == "doctor", Image.owner_id == doctor_id)
                            .values(position=new_position)
                        )
                    
                    await db.commit()
                    print(f"Successfully updated image positions for doctor {doctor_id}")
                    return {"success": True, "message": "Image order updated successfully"}
                except json.JSONDecodeError:
                    return {"success": False, "message": "Invalid image order data"}
        
        # Create and validate the update data using Pydantic schema
        update_data = DoctorUpdate(
            name=name,
            designation=designation or None,
            hospital_id=int(hospital_id) if hospital_id and hospital_id.strip() else None,
            location=location or None,
            experience_years=experience_years,
            rating=rating,
            gender=gender or None,
            short_description=short_description or None,
            long_description=long_description or None,
            specialization=specialization or None,
            qualification=qualification or None,
            consultancy_fee=consultancy_fee,
            skills=parse_comma_separated_string(skills),
            qualifications=parse_comma_separated_string(qualifications),
            highlights=parse_comma_separated_string(highlights),
            awards=parse_comma_separated_string(awards)
        )
        
        # Update doctor fields
        doctor.name = update_data.name
        doctor.designation = update_data.designation
        doctor.hospital_id = update_data.hospital_id
        doctor.location = update_data.location
        doctor.experience_years = update_data.experience_years
        doctor.rating = update_data.rating
        doctor.gender = update_data.gender
        doctor.short_description = update_data.short_description
        doctor.long_description = update_data.long_description
        doctor.specialization = update_data.specialization
        doctor.qualification = update_data.qualification
        doctor.consultancy_fee = update_data.consultancy_fee
        doctor.skills = update_data.skills
        doctor.qualifications = update_data.qualifications
        doctor.highlights = update_data.highlights
        doctor.awards = update_data.awards
        doctor.is_featured = is_featured
        
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

        # Handle FAQ updates - remove existing FAQs and create new ones
        print(f"DEBUG DOCTOR: Deleting existing FAQs for doctor {doctor.id}")
        # Update FAQ fields directly on doctor model
        doctor.faq1_question = faq1_question.strip() if faq1_question else None
        doctor.faq1_answer = faq1_answer.strip() if faq1_answer else None
        doctor.faq2_question = faq2_question.strip() if faq2_question else None
        doctor.faq2_answer = faq2_answer.strip() if faq2_answer else None
        doctor.faq3_question = faq3_question.strip() if faq3_question else None
        doctor.faq3_answer = faq3_answer.strip() if faq3_answer else None
        doctor.faq4_question = faq4_question.strip() if faq4_question else None
        doctor.faq4_answer = faq4_answer.strip() if faq4_answer else None
        doctor.faq5_question = faq5_question.strip() if faq5_question else None
        doctor.faq5_answer = faq5_answer.strip() if faq5_answer else None
        print(f"DEBUG DOCTOR: Updated FAQ fields for doctor {doctor.id}")

        await db.commit()
        print(f"DEBUG DOCTOR: Data committed successfully")
        
        # Verify FAQs were saved
        verify_faqs = (await db.execute(select(FAQ).where(FAQ.owner_type == "doctor", FAQ.owner_id == doctor.id))).scalars().all()
        print(f"DEBUG DOCTOR: Verification - Found {len(verify_faqs)} FAQs in database after commit")
        for i, faq in enumerate(verify_faqs):
            print(f"DEBUG DOCTOR: Verification FAQ {i+1}: Q='{faq.question}', A='{faq.answer}'")
        
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
    features: str = Form(""),
    price_min: Optional[float] = Form(None),
    price_max: Optional[float] = Form(None),
    price_exact: Optional[float] = Form(None),
    rating: Optional[float] = Form(None),
    hospital_id: Optional[int] = Form(None),
    other_hospital_name: str = Form(""),
    doctor_id: Optional[int] = Form(None),
    other_doctor_name: str = Form(""),
    is_featured: bool = Form(False),
    faq_questions: List[str] = Form(default=[]),
    faq_answers: List[str] = Form(default=[]),
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
            features=parse_comma_separated_string(features) if features else None,
            price_min=price_min,
            price_max=price_max,
            price_exact=price_exact,
            rating=rating,
            hospital_id=hospital_id,
            other_hospital_name=other_hospital_name or None,
            doctor_id=doctor_id,
            other_doctor_name=other_doctor_name or None,
            is_featured=is_featured,
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

        # Handle FAQ creation
        for question, answer in zip(faq_questions, faq_answers):
            if question.strip() and answer.strip():  # Only create FAQ if both fields have content
                faq = FAQ(
                    owner_type="treatment",
                    owner_id=treatment.id,
                    question=question.strip(),
                    answer=answer.strip()
                )
                db.add(faq)
        
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
    features: str = Form(""),
    price_min: str = Form(""),
    price_max: str = Form(""),
    price_exact: str = Form(""),
    rating: str = Form(""),
    hospital_id: str = Form(""),
    other_hospital_name: str = Form(""),
    doctor_id: str = Form(""),
    other_doctor_name: str = Form(""),
    is_featured: bool = Form(False),
    faq1_question: str = Form(""),
    faq1_answer: str = Form(""),
    faq2_question: str = Form(""),
    faq2_answer: str = Form(""),
    faq3_question: str = Form(""),
    faq3_answer: str = Form(""),
    faq4_question: str = Form(""),
    faq4_answer: str = Form(""),
    faq5_question: str = Form(""),
    faq5_answer: str = Form(""),
    images: List[UploadFile] = File(default=[]),
    update_image_order: str = Form(None),
    delete_image_id: str = Form(None),
    set_primary_image: str = Form(None),
    image_order: str = Form(None),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Update existing treatment with image management"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Debug: Log all form data received
    print(f"DEBUG TREATMENT UPDATE: Received FAQ data:")
    print(f"  - FAQ 1: Q='{faq1_question}' A='{faq1_answer}'")
    print(f"  - FAQ 2: Q='{faq2_question}' A='{faq2_answer}'")
    print(f"  - FAQ 3: Q='{faq3_question}' A='{faq3_answer}'")
    print(f"  - FAQ 4: Q='{faq4_question}' A='{faq4_answer}'")
    print(f"  - FAQ 5: Q='{faq5_question}' A='{faq5_answer}'")
    
    try:
        # Get existing treatment with images
        result = await db.execute(
            select(Treatment)
            .options(selectinload(Treatment.images))
            .where(Treatment.id == treatment_id)
        )
        treatment = result.scalar_one_or_none()
        
        if not treatment:
            raise HTTPException(status_code=404, detail="Treatment not found")
        
        # Handle image deletion
        if delete_image_id and delete_image_id.isdigit():
            print(f"Processing image deletion for image ID: {delete_image_id}, treatment ID: {treatment_id}")
            image_id = int(delete_image_id)
            # Get the image to delete
            result = await db.execute(
                select(Image)
                .where(Image.id == image_id)
                .where(Image.owner_type == "treatment")
                .where(Image.owner_id == treatment_id)
            )
            image = result.scalar_one_or_none()
            print(f"Found image to delete: {image}")
            
            if image:
                # Delete the image file
                try:
                    if image.url and image.url.startswith("/media/treatment/"):
                        filepath = f"static{image.url}"
                        if os.path.exists(filepath):
                            os.remove(filepath)
                except Exception as e:
                    print(f"Error deleting image file: {e}")
                
                # Delete the image record
                await db.execute(
                    delete(Image)
                    .where(Image.id == image_id)
                )
                await db.commit()
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return {"success": True, "message": "Image deleted successfully"}
                return RedirectResponse(
                    f"/admin/treatments/{treatment_id}/edit", 
                    status_code=303,
                    headers={"HX-Redirect": f"/admin/treatments/{treatment_id}/edit"}
                )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return {"success": False, "message": "Image not found"}
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Handle setting primary image
        if set_primary_image and set_primary_image.isdigit():
            image_id = int(set_primary_image)
            
            # First, unset any existing primary image
            await db.execute(
                update(Image)
                .where(Image.owner_type == "treatment")
                .where(Image.owner_id == treatment_id)
                .where(Image.is_primary == True)
                .values(is_primary=False)
            )
            
            # Set the new primary image
            await db.execute(
                update(Image)
                .where(Image.id == image_id)
                .where(Image.owner_type == "treatment")
                .where(Image.owner_id == treatment_id)
                .values(is_primary=True)
            )
            
            await db.commit()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return {"success": True, "message": "Primary image updated successfully"}
            return RedirectResponse(
                f"/admin/treatments/{treatment_id}/edit", 
                status_code=303,
                headers={"HX-Redirect": f"/admin/treatments/{treatment_id}/edit"}
            )
        
        # Handle image reordering
        if update_image_order and image_order:
            print(f"Processing image reordering for treatment ID: {treatment_id}")
            print(f"Image order data: {image_order}")
            try:
                order_data = json.loads(image_order)
                print(f"Parsed order data: {order_data}")
                for item in order_data:
                    await db.execute(
                        update(Image)
                        .where(Image.id == item['id'])
                        .where(Image.owner_type == "treatment")
                        .where(Image.owner_id == treatment_id)
                        .values(position=item['position'])
                    )
                await db.commit()
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return {"success": True, "message": "Image order updated successfully"}
                return RedirectResponse(
                    f"/admin/treatments/{treatment_id}/edit", 
                    status_code=303,
                    headers={"HX-Redirect": f"/admin/treatments/{treatment_id}/edit"}
                )
            except json.JSONDecodeError:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return {"success": False, "message": "Invalid image order data"}
                raise HTTPException(status_code=400, detail="Invalid image order data")
        
        # Handle regular form submission
        # Create and validate the update data using Pydantic schema
        update_data = TreatmentUpdate(
            name=name,
            short_description=short_description,
            long_description=long_description or None,
            treatment_type=treatment_type,
            location=location,
            features=parse_comma_separated_string(features) if features else None,
            price_min=price_min,
            price_max=price_max,
            price_exact=price_exact,
            rating=rating,
            hospital_id=int(hospital_id) if hospital_id and hospital_id.strip() else None,
            other_hospital_name=other_hospital_name or None,
            doctor_id=int(doctor_id) if doctor_id and doctor_id.strip() else None,
            other_doctor_name=other_doctor_name or None
        )
        
        # Update treatment fields
        treatment.name = update_data.name
        treatment.short_description = update_data.short_description
        treatment.long_description = update_data.long_description
        treatment.treatment_type = update_data.treatment_type
        treatment.location = update_data.location
        treatment.features = update_data.features
        treatment.price_min = update_data.price_min
        treatment.price_max = update_data.price_max
        treatment.price_exact = update_data.price_exact
        treatment.rating = update_data.rating
        treatment.hospital_id = update_data.hospital_id
        treatment.other_hospital_name = update_data.other_hospital_name
        treatment.doctor_id = update_data.doctor_id
        treatment.other_doctor_name = update_data.other_doctor_name
        treatment.is_featured = is_featured
        
        # Update FAQ fields
        treatment.faq1_question = faq1_question.strip() if faq1_question else None
        treatment.faq1_answer = faq1_answer.strip() if faq1_answer else None
        treatment.faq2_question = faq2_question.strip() if faq2_question else None
        treatment.faq2_answer = faq2_answer.strip() if faq2_answer else None
        treatment.faq3_question = faq3_question.strip() if faq3_question else None
        treatment.faq3_answer = faq3_answer.strip() if faq3_answer else None
        treatment.faq4_question = faq4_question.strip() if faq4_question else None
        treatment.faq4_answer = faq4_answer.strip() if faq4_answer else None
        treatment.faq5_question = faq5_question.strip() if faq5_question else None
        treatment.faq5_answer = faq5_answer.strip() if faq5_answer else None
        
        # Handle new image uploads
        existing_images_result = await db.execute(
            select(Image)
            .where(Image.owner_type == "treatment")
            .where(Image.owner_id == treatment.id)
            .order_by(Image.position)
        )
        existing_images = existing_images_result.scalars().all()
        next_position = len(existing_images)
        
        for image_file in images:
            if image_file and image_file.filename:
                filename = await save_uploaded_file(image_file, "treatment")
                if filename:
                    image = Image(
                        owner_type="treatment",
                        owner_id=treatment.id,
                        url=f"/media/treatment/{filename}",
                        is_primary=next_position == 0,  # First image is primary
                        position=next_position
                    )
                    db.add(image)
                    next_position += 1

        print(f"DEBUG: Updated FAQ fields for treatment {treatment.id}")
        
        await db.commit()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {"success": True, "message": "Treatment updated successfully"}
            
        return RedirectResponse(url="/admin/treatments", status_code=302)
        
    except Exception as e:
        await db.rollback()
        error_msg = f"Error updating treatment: {str(e)}"
        print(error_msg)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {"success": False, "message": error_msg}
            
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
            "error": error_msg
        })

# Offer CRUD Operations
@router.post("/admin/offers")
async def admin_offer_create(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    treatment_type: str = Form(""),
    location: str = Form(""),
    start_date: str = Form(...),
    end_date: str = Form(...),
    discount_percentage: Optional[float] = Form(None),
    is_free_camp: Optional[str] = Form(None),
    treatment_id: Optional[int] = Form(None),
    is_active: Optional[str] = Form(None),
    images: List[UploadFile] = File(default=[]),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new offer"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Parse dates
        start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
        end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
        
        # Create offer object
        offer = Offer(
            name=name,
            description=description,
            treatment_type=treatment_type or None,
            location=location or None,
            start_date=start_datetime,
            end_date=end_datetime,
            discount_percentage=discount_percentage,
            is_free_camp=bool(is_free_camp),
            treatment_id=treatment_id,
            is_active=bool(is_active) if is_active is not None else True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(offer)
        await db.flush()  # Get offer ID
        
        # Handle image uploads
        image_count = 0
        for image_file in images:
            if image_file and image_file.filename:
                filename = await save_uploaded_file(image_file, "offer")
                if filename:
                    image = Image(
                        owner_type="offer",
                        owner_id=offer.id,
                        url=f"/media/offer/{filename}",
                        is_primary=image_count == 0,
                        position=image_count
                    )
                    db.add(image)
                    image_count += 1
        
        await db.commit()
        return RedirectResponse(url="/admin/offers", status_code=302)
        
    except Exception as e:
        await db.rollback()
        # Get data for form
        treatments = await db.execute(select(Treatment).order_by(Treatment.name))
        treatments = treatments.scalars().all()
        treatment_types_result = await db.execute(
            select(Treatment.treatment_type).distinct().where(Treatment.treatment_type.isnot(None))
        )
        treatment_types = [t for t in treatment_types_result.scalars().all() if t]
        
        return render_template("admin/offer_form.html", {
            "request": request,
            "admin": admin,
            "offer": None,
            "treatments": treatments,
            "treatment_types": treatment_types,
            "action": "Create",
            "error": f"Error creating offer: {str(e)}"
        })

@router.post("/admin/offers/{offer_id}")
async def admin_offer_update(
    request: Request,
    offer_id: int,
    name: str = Form(...),
    description: str = Form(...),
    treatment_type: str = Form(""),
    location: str = Form(""),
    start_date: str = Form(...),
    end_date: str = Form(...),
    discount_percentage: Optional[float] = Form(None),
    is_free_camp: Optional[str] = Form(None),
    treatment_id: Optional[int] = Form(None),
    is_active: Optional[str] = Form(None),
    images: List[UploadFile] = File(default=[]),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Update existing offer"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get existing offer
        result = await db.execute(select(Offer).where(Offer.id == offer_id))
        offer = result.scalar_one_or_none()
        
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        # Parse dates
        start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
        end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
        
        # Update offer fields
        offer.name = name
        offer.description = description
        offer.treatment_type = treatment_type or None
        offer.location = location or None
        offer.start_date = start_datetime
        offer.end_date = end_datetime
        offer.discount_percentage = discount_percentage
        offer.is_free_camp = bool(is_free_camp)
        offer.treatment_id = treatment_id
        offer.is_active = bool(is_active) if is_active is not None else True
        offer.updated_at = datetime.now()
        
        # Handle new image uploads
        # Get current image count for this offer
        existing_images_result = await db.execute(
            select(func.count(Image.id)).where(
                Image.owner_type == "offer",
                Image.owner_id == offer.id
            )
        )
        image_count = existing_images_result.scalar() or 0
        
        for image_file in images:
            if image_file and image_file.filename:
                filename = await save_uploaded_file(image_file, "offer")
                if filename:
                    image = Image(
                        owner_type="offer",
                        owner_id=offer.id,
                        url=f"/media/offer/{filename}",
                        is_primary=image_count == 0,
                        position=image_count
                    )
                    db.add(image)
                    image_count += 1
        
        await db.commit()
        return RedirectResponse(url="/admin/offers", status_code=302)
        
    except Exception as e:
        await db.rollback()
        # Get data for form
        treatments = await db.execute(select(Treatment).order_by(Treatment.name))
        treatments = treatments.scalars().all()
        treatment_types_result = await db.execute(
            select(Treatment.treatment_type).distinct().where(Treatment.treatment_type.isnot(None))
        )
        treatment_types = [t for t in treatment_types_result.scalars().all() if t]
        
        return render_template("admin/offer_form.html", {
            "request": request,
            "admin": admin,
            "offer": offer,
            "treatments": treatments,
            "treatment_types": treatment_types,
            "action": "Update",
            "error": f"Error updating offer: {str(e)}"
        })

# Treatment Type Management API Endpoints
@router.get("/admin/api/treatment-types")
async def get_treatment_types_api(
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all treatment types for API"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    result = await db.execute(
        select(Treatment.treatment_type).distinct().where(Treatment.treatment_type.isnot(None))
    )
    treatment_types = [t for t in result.scalars().all() if t and t.strip()]
    
    return {"treatment_types": sorted(treatment_types)}

@router.post("/admin/api/treatment-types/rename")
async def rename_treatment_type(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Rename a treatment type globally"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        data = await request.json()
        old_name = data.get("old_name", "").strip()
        new_name = data.get("new_name", "").strip()
        
        if not old_name or not new_name:
            raise HTTPException(status_code=400, detail="Both old_name and new_name are required")
        
        if old_name == new_name:
            raise HTTPException(status_code=400, detail="New name must be different from old name")
        
        # Check if new name already exists
        existing_check = await db.execute(
            select(Treatment).where(Treatment.treatment_type == new_name).limit(1)
        )
        if existing_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="A treatment type with this name already exists")
        
        # Update all treatments with the old type
        result = await db.execute(
            update(Treatment)
            .where(Treatment.treatment_type == old_name)
            .values(treatment_type=new_name)
        )
        
        # Also update offers if they have this treatment type
        await db.execute(
            update(Offer)
            .where(Offer.treatment_type == old_name)
            .values(treatment_type=new_name)
        )
        
        await db.commit()
        
        affected_count = result.rowcount
        return {
            "message": f"Treatment type renamed successfully",
            "affected_treatments": affected_count,
            "old_name": old_name,
            "new_name": new_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error renaming treatment type: {str(e)}")

@router.post("/admin/api/treatment-types/delete")
async def delete_treatment_type(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete a treatment type globally"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        data = await request.json()
        type_name = data.get("type_name", "").strip()
        replacement_type = data.get("replacement_type")
        
        if not type_name:
            raise HTTPException(status_code=400, detail="type_name is required")
        
        if replacement_type:
            replacement_type = replacement_type.strip() or None
        
        # Count affected treatments
        count_result = await db.execute(
            select(func.count(Treatment.id)).where(Treatment.treatment_type == type_name)
        )
        affected_treatments = count_result.scalar()
        
        # Update treatments
        if replacement_type:
            await db.execute(
                update(Treatment)
                .where(Treatment.treatment_type == type_name)
                .values(treatment_type=replacement_type)
            )
        else:
            await db.execute(
                update(Treatment)
                .where(Treatment.treatment_type == type_name)
                .values(treatment_type=None)
            )
        
        # Update offers as well
        if replacement_type:
            await db.execute(
                update(Offer)
                .where(Offer.treatment_type == type_name)
                .values(treatment_type=replacement_type)
            )
        else:
            await db.execute(
                update(Offer)
                .where(Offer.treatment_type == type_name)
                .values(treatment_type=None)
            )
        
        await db.commit()
        
        return {
            "message": f"Treatment type deleted successfully",
            "affected_treatments": affected_treatments,
            "deleted_type": type_name,
            "replacement_type": replacement_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting treatment type: {str(e)}")


# ================================
# BLOG MANAGEMENT ROUTES
# ================================

@router.get("/admin/blogs", response_class=HTMLResponse)
async def admin_blogs_list(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Display blogs list page"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get all blogs with pagination
    result = await db.execute(
        select(Blog)
        .order_by(desc(Blog.created_at))
        .limit(50)
    )
    blogs = result.scalars().all()
    
    return templates.TemplateResponse("admin/blogs.html", {
        "request": request,
        "admin": admin,
        "blogs": blogs
    })


@router.get("/admin/blogs/new", response_class=HTMLResponse)
async def admin_blog_new(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Display new blog form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    return templates.TemplateResponse("admin/blog_form.html", {
        "request": request,
        "admin": admin,
        "blog": None,
        "action": "create"
    })


@router.post("/admin/blogs")
async def admin_blog_create(
    request: Request,
    title: str = Form(...),
    subtitle: str = Form(""),
    content: str = Form(...),
    excerpt: str = Form(""),
    meta_description: str = Form(""),
    tags: str = Form(""),
    category: str = Form(""),
    author_name: str = Form(""),
    reading_time: str = Form(""),
    is_published: bool = Form(False),
    is_featured: bool = Form(False),
    featured_image: Optional[UploadFile] = File(None),
    content_images: List[UploadFile] = File(default=[]),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new blog"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    print(f"DEBUG: Creating blog with title: {title}")
    print(f"DEBUG: Content length: {len(content) if content else 0}")
    print(f"DEBUG: Reading time: {reading_time}")
    print(f"DEBUG: Is published: {is_published}")
    
    try:
        # Generate slug from title
        import re
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = re.sub(r'-+', '-', slug)
        
        # Ensure slug is unique
        base_slug = slug
        counter = 1
        while True:
            result = await db.execute(select(Blog).where(Blog.slug == slug))
            existing = result.scalar_one_or_none()
            if not existing:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Handle featured image upload
        featured_image_url = None
        if featured_image and featured_image.filename:
            filename = await save_uploaded_file(featured_image, "blog")
            if filename:
                featured_image_url = f"/media/blog/{filename}"
        
        # Convert reading_time to int if provided
        reading_time_int = None
        if reading_time and reading_time.strip():
            try:
                reading_time_int = int(reading_time)
            except ValueError:
                reading_time_int = None
        
        # Create and validate the blog data using Pydantic schema
        blog_data = BlogCreate(
            title=title,
            subtitle=subtitle or None,
            content=content,
            excerpt=excerpt or None,
            featured_image=featured_image_url,
            meta_description=meta_description or None,
            tags=tags or None,
            category=category or None,
            author_name=author_name or None,
            reading_time=reading_time_int,
            is_published=is_published,
            is_featured=is_featured,
            published_at=datetime.utcnow() if is_published else None
        )
        
        # Create new blog
        blog = Blog(
            title=blog_data.title,
            subtitle=blog_data.subtitle,
            slug=slug,
            content=blog_data.content,
            excerpt=blog_data.excerpt,
            featured_image=blog_data.featured_image,
            meta_description=blog_data.meta_description,
            tags=blog_data.tags,
            category=blog_data.category,
            author_name=blog_data.author_name,
            reading_time=blog_data.reading_time,
            is_published=blog_data.is_published,
            is_featured=blog_data.is_featured,
            published_at=blog_data.published_at
        )
        
        db.add(blog)
        await db.flush()  # Get the blog ID
        
        # Handle content images upload
        for image_file in content_images:
            if image_file and image_file.filename:
                filename = await save_uploaded_file(image_file, "blog")
                if filename:
                    image = Image(
                        owner_type="blog",
                        owner_id=blog.id,
                        url=f"/media/blog/{filename}",
                        is_primary=False
                    )
                    db.add(image)
        
        await db.commit()
        
        return RedirectResponse(url="/admin/blogs", status_code=302)
        
    except Exception as e:
        await db.rollback()
        return templates.TemplateResponse("admin/blog_form.html", {
            "request": request,
            "admin": admin,
            "blog": None,
            "action": "create",
            "error": f"Error creating blog: {str(e)}"
        })


@router.get("/admin/blogs/{blog_id}/edit", response_class=HTMLResponse)
async def admin_blog_edit(
    request: Request,
    blog_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Display edit blog form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get blog with images
    result = await db.execute(
        select(Blog)
        .where(Blog.id == blog_id)
    )
    blog = result.scalar_one_or_none()
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Get blog images
    images_result = await db.execute(
        select(Image)
        .where(Image.owner_type == "blog", Image.owner_id == blog_id)
        .order_by(Image.position.asc().nullslast(), Image.id.asc())
    )
    images = images_result.scalars().all()
    
    return templates.TemplateResponse("admin/blog_form.html", {
        "request": request,
        "admin": admin,
        "blog": blog,
        "images": images,
        "action": "edit"
    })


@router.post("/admin/blogs/{blog_id}")
async def admin_blog_update(
    request: Request,
    blog_id: int,
    title: str = Form(...),
    subtitle: str = Form(""),
    content: str = Form(...),
    excerpt: str = Form(""),
    meta_description: str = Form(""),
    tags: str = Form(""),
    category: str = Form(""),
    author_name: str = Form(""),
    reading_time: str = Form(""),
    is_published: bool = Form(False),
    is_featured: bool = Form(False),
    featured_image: Optional[UploadFile] = File(None),
    content_images: List[UploadFile] = File(default=[]),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Update existing blog"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get existing blog
        result = await db.execute(select(Blog).where(Blog.id == blog_id))
        blog = result.scalar_one_or_none()
        
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        # Handle featured image upload
        featured_image_url = blog.featured_image
        if featured_image and featured_image.filename:
            filename = await save_uploaded_file(featured_image, "blog")
            if filename:
                featured_image_url = f"/media/blog/{filename}"
        
        # Convert reading_time to int if provided
        reading_time_int = None
        if reading_time and reading_time.strip():
            try:
                reading_time_int = int(reading_time)
            except ValueError:
                reading_time_int = None
        
        # Create and validate the update data using Pydantic schema
        update_data = BlogUpdate(
            title=title,
            subtitle=subtitle or None,
            content=content,
            excerpt=excerpt or None,
            featured_image=featured_image_url,
            meta_description=meta_description or None,
            tags=tags or None,
            category=category or None,
            author_name=author_name or None,
            reading_time=reading_time_int,
            is_published=is_published,
            is_featured=is_featured,
            published_at=datetime.utcnow() if is_published and not blog.published_at else blog.published_at
        )
        
        # Update blog fields
        blog.title = update_data.title
        blog.subtitle = update_data.subtitle
        blog.content = update_data.content
        blog.excerpt = update_data.excerpt
        blog.featured_image = update_data.featured_image
        blog.meta_description = update_data.meta_description
        blog.tags = update_data.tags
        blog.category = update_data.category
        blog.author_name = update_data.author_name
        blog.reading_time = update_data.reading_time
        blog.is_published = update_data.is_published
        blog.is_featured = update_data.is_featured
        blog.published_at = update_data.published_at
        
        # Handle new content images upload
        for image_file in content_images:
            if image_file and image_file.filename:
                filename = await save_uploaded_file(image_file, "blog")
                if filename:
                    image = Image(
                        owner_type="blog",
                        owner_id=blog.id,
                        url=f"/media/blog/{filename}",
                        is_primary=False
                    )
                    db.add(image)
        
        await db.commit()
        
        return RedirectResponse(url="/admin/blogs", status_code=302)
        
    except Exception as e:
        await db.rollback()
        # Get blog images for form redisplay
        images_result = await db.execute(
            select(Image)
            .where(Image.owner_type == "blog", Image.owner_id == blog_id)
            .order_by(Image.position.asc().nullslast(), Image.id.asc())
        )
        images = images_result.scalars().all()
        
        return templates.TemplateResponse("admin/blog_form.html", {
            "request": request,
            "admin": admin,
            "blog": blog,
            "images": images,
            "action": "edit",
            "error": f"Error updating blog: {str(e)}"
        })


@router.delete("/admin/blogs/{blog_id}")
async def admin_blog_delete(
    request: Request,
    blog_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete blog"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Get blog
        result = await db.execute(select(Blog).where(Blog.id == blog_id))
        blog = result.scalar_one_or_none()
        
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        # Delete associated images
        await db.execute(
            select(Image).where(Image.owner_type == "blog", Image.owner_id == blog_id)
        )
        
        # Delete blog
        await db.delete(blog)
        await db.commit()
        
        return {"message": "Blog deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting blog: {str(e)}")


@router.get("/admin/blogs/{blog_id}/images")
async def admin_blog_images(
    request: Request,
    blog_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Get blog images for content editor"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get blog images
    result = await db.execute(
        select(Image)
        .where(Image.owner_type == "blog", Image.owner_id == blog_id)
        .order_by(Image.position.asc().nullslast(), Image.id.asc())
    )
    images = result.scalars().all()
    
    return {
        "images": [
            {
                "id": img.id,
                "url": img.url,
                "is_primary": img.is_primary,
                "uploaded_at": img.uploaded_at.isoformat()
            }
            for img in images
        ]
    }


# ================================
# BANNER MANAGEMENT ROUTES
# ================================

@router.get("/admin/banners", response_class=HTMLResponse)
async def admin_banners_list(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Banner management page"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get all banners
    result = await db.execute(
        select(Banner).order_by(Banner.position.asc(), Banner.id.desc())
    )
    banners = result.scalars().all()
    
    return render_template("admin/banners.html", {
        "request": request,
        "admin": admin,
        "banners": banners
    })


@router.get("/admin/banners/new", response_class=HTMLResponse)
async def admin_banner_new(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """New banner form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    return render_template("admin/banner_form.html", {
        "request": request,
        "admin": admin,
        "action": "Create",
        "banner": None
    })


@router.post("/admin/banners/new")
async def admin_banner_create(
    request: Request,
    name: str = Form(...),
    title: str = Form(""),
    subtitle: str = Form(""),
    description: str = Form(""),
    link_url: str = Form(""),
    button_text: str = Form(""),
    position: int = Form(0),
    is_active: bool = Form(False),
    banner_image: UploadFile = File(default=None),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new banner"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Handle image upload
        image_url = None
        if banner_image and banner_image.filename:
            filename = await save_uploaded_file(banner_image, "banner")
            image_url = f"/media/banner/{filename}"
        
        # Create banner
        banner = Banner(
            name=name,
            title=title or None,
            subtitle=subtitle or None,
            description=description or None,
            image_url=image_url,
            link_url=link_url or None,
            button_text=button_text or None,
            position=position,
            is_active=is_active
        )
        
        db.add(banner)
        await db.commit()
        
        return RedirectResponse(url="/admin/banners", status_code=302)
        
    except Exception as e:
        await db.rollback()
        print(f"Error creating banner: {str(e)}")
        return render_template("admin/banner_form.html", {
            "request": request,
            "admin": admin,
            "action": "Create",
            "banner": None,
            "error": f"Error creating banner: {str(e)}"
        })


@router.get("/admin/banners/{banner_id}/edit", response_class=HTMLResponse)
async def admin_banner_edit(
    request: Request,
    banner_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Edit banner form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get banner
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    return render_template("admin/banner_form.html", {
        "request": request,
        "admin": admin,
        "action": "Edit",
        "banner": banner
    })


@router.post("/admin/banners/{banner_id}")
async def admin_banner_update(
    request: Request,
    banner_id: int,
    name: str = Form(...),
    title: str = Form(""),
    subtitle: str = Form(""),
    description: str = Form(""),
    link_url: str = Form(""),
    button_text: str = Form(""),
    position: int = Form(0),
    is_active: bool = Form(False),
    banner_image: UploadFile = File(default=None),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Update banner"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get existing banner
        result = await db.execute(select(Banner).where(Banner.id == banner_id))
        banner = result.scalar_one_or_none()
        
        if not banner:
            raise HTTPException(status_code=404, detail="Banner not found")
        
        # Handle image upload
        if banner_image and banner_image.filename:
            filename = await save_uploaded_file(banner_image, "banner")
            banner.image_url = f"/media/banner/{filename}"
        
        # Update banner fields
        banner.name = name
        banner.title = title or None
        banner.subtitle = subtitle or None
        banner.description = description or None
        banner.link_url = link_url or None
        banner.button_text = button_text or None
        banner.position = position
        banner.is_active = is_active
        banner.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return RedirectResponse(url="/admin/banners", status_code=302)
        
    except Exception as e:
        await db.rollback()
        print(f"Error updating banner: {str(e)}")
        return render_template("admin/banner_form.html", {
            "request": request,
            "admin": admin,
            "action": "Edit",
            "banner": banner,
            "error": f"Error updating banner: {str(e)}"
        })


@router.post("/admin/banners/{banner_id}/delete")
async def admin_banner_delete(
    banner_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete banner"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get banner
        result = await db.execute(select(Banner).where(Banner.id == banner_id))
        banner = result.scalar_one_or_none()
        
        if banner:
            await db.delete(banner)
            await db.commit()
        
        return RedirectResponse(url="/admin/banners", status_code=302)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting banner: {str(e)}")


# ================================
# PARTNER HOSPITAL MANAGEMENT ROUTES
# ================================

@router.get("/admin/partners", response_class=HTMLResponse)
async def admin_partners_list(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Partner hospitals management page"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get all partner hospitals
    result = await db.execute(
        select(PartnerHospital).order_by(PartnerHospital.position.asc(), PartnerHospital.id.desc())
    )
    partners = result.scalars().all()
    
    return render_template("admin/partners.html", {
        "request": request,
        "admin": admin,
        "partners": partners
    })


@router.get("/admin/partners/new", response_class=HTMLResponse)
async def admin_partner_new(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """New partner hospital form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    return render_template("admin/partner_form.html", {
        "request": request,
        "admin": admin,
        "action": "Create",
        "partner": None
    })


@router.post("/admin/partners/new")
async def admin_partner_create(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    website_url: str = Form(""),
    location: str = Form(""),
    position: int = Form(0),
    is_active: bool = Form(False),
    logo_image: UploadFile = File(default=None),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new partner hospital"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Handle logo upload
        logo_url = None
        if logo_image and logo_image.filename:
            filename = await save_uploaded_file(logo_image, "partner")
            logo_url = f"/media/partner/{filename}"
        
        # Create partner
        partner = PartnerHospital(
            name=name,
            description=description or None,
            logo_url=logo_url,
            website_url=website_url or None,
            location=location or None,
            position=position,
            is_active=is_active
        )
        
        db.add(partner)
        await db.commit()
        
        return RedirectResponse(url="/admin/partners", status_code=302)
        
    except Exception as e:
        await db.rollback()
        print(f"Error creating partner: {str(e)}")
        return render_template("admin/partner_form.html", {
            "request": request,
            "admin": admin,
            "action": "Create",
            "partner": None,
            "error": f"Error creating partner: {str(e)}"
        })


@router.get("/admin/partners/{partner_id}/edit", response_class=HTMLResponse)
async def admin_partner_edit(
    request: Request,
    partner_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Edit partner hospital form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get partner
    result = await db.execute(select(PartnerHospital).where(PartnerHospital.id == partner_id))
    partner = result.scalar_one_or_none()
    
    if not partner:
        raise HTTPException(status_code=404, detail="Partner hospital not found")
    
    return render_template("admin/partner_form.html", {
        "request": request,
        "admin": admin,
        "action": "Edit",
        "partner": partner
    })


@router.post("/admin/partners/{partner_id}")
async def admin_partner_update(
    request: Request,
    partner_id: int,
    name: str = Form(...),
    description: str = Form(""),
    website_url: str = Form(""),
    location: str = Form(""),
    position: int = Form(0),
    is_active: bool = Form(False),
    logo_image: UploadFile = File(default=None),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Update partner hospital"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get existing partner
        result = await db.execute(select(PartnerHospital).where(PartnerHospital.id == partner_id))
        partner = result.scalar_one_or_none()
        
        if not partner:
            raise HTTPException(status_code=404, detail="Partner hospital not found")
        
        # Handle logo upload
        if logo_image and logo_image.filename:
            filename = await save_uploaded_file(logo_image, "partner")
            partner.logo_url = f"/media/partner/{filename}"
        
        # Update partner fields
        partner.name = name
        partner.description = description or None
        partner.website_url = website_url or None
        partner.location = location or None
        partner.position = position
        partner.is_active = is_active
        partner.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return RedirectResponse(url="/admin/partners", status_code=302)
        
    except Exception as e:
        await db.rollback()
        print(f"Error updating partner: {str(e)}")
        return render_template("admin/partner_form.html", {
            "request": request,
            "admin": admin,
            "action": "Edit",
            "partner": partner,
            "error": f"Error updating partner: {str(e)}"
        })


@router.post("/admin/partners/{partner_id}/delete")
async def admin_partner_delete(
    partner_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete partner hospital"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get partner
        result = await db.execute(select(PartnerHospital).where(PartnerHospital.id == partner_id))
        partner = result.scalar_one_or_none()
        
        if partner:
            await db.delete(partner)
            await db.commit()
        
        return RedirectResponse(url="/admin/partners", status_code=302)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting partner: {str(e)}")


# ================================
# PATIENT STORIES MANAGEMENT ROUTES
# ================================

@router.get("/admin/stories", response_class=HTMLResponse)
async def admin_stories_list(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Patient stories management page"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get all patient stories
    result = await db.execute(
        select(PatientStory).order_by(PatientStory.position.asc(), PatientStory.id.desc())
    )
    stories = result.scalars().all()
    
    return render_template("admin/stories.html", {
        "request": request,
        "admin": admin,
        "stories": stories
    })


@router.get("/admin/stories/new", response_class=HTMLResponse)
async def admin_story_new(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """New patient story form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    return render_template("admin/story_form.html", {
        "request": request,
        "admin": admin,
        "action": "Create",
        "story": None
    })


@router.post("/admin/stories/new")
async def admin_story_create(
    request: Request,
    patient_name: str = Form(...),
    description: str = Form(...),
    rating: int = Form(...),
    treatment_type: str = Form(""),
    hospital_name: str = Form(""),
    location: str = Form(""),
    position: int = Form(0),
    is_featured: bool = Form(False),
    is_active: bool = Form(False),
    profile_image: UploadFile = File(default=None),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new patient story"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Validate rating
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        # Handle profile photo upload
        profile_photo = None
        if profile_image and profile_image.filename:
            filename = await save_uploaded_file(profile_image, "patient")
            profile_photo = f"/media/patient/{filename}"
        
        # Create patient story
        story = PatientStory(
            patient_name=patient_name,
            description=description,
            rating=rating,
            profile_photo=profile_photo,
            treatment_type=treatment_type or None,
            hospital_name=hospital_name or None,
            location=location or None,
            position=position,
            is_featured=is_featured,
            is_active=is_active
        )
        
        db.add(story)
        await db.commit()
        
        return RedirectResponse(url="/admin/stories", status_code=302)
        
    except Exception as e:
        await db.rollback()
        print(f"Error creating patient story: {str(e)}")
        return render_template("admin/story_form.html", {
            "request": request,
            "admin": admin,
            "action": "Create",
            "story": None,
            "error": f"Error creating patient story: {str(e)}"
        })


@router.get("/admin/stories/{story_id}/edit", response_class=HTMLResponse)
async def admin_story_edit(
    request: Request,
    story_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Edit patient story form"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get story
    result = await db.execute(select(PatientStory).where(PatientStory.id == story_id))
    story = result.scalar_one_or_none()
    
    if not story:
        raise HTTPException(status_code=404, detail="Patient story not found")
    
    return render_template("admin/story_form.html", {
        "request": request,
        "admin": admin,
        "action": "Edit",
        "story": story
    })


@router.post("/admin/stories/{story_id}")
async def admin_story_update(
    request: Request,
    story_id: int,
    patient_name: str = Form(...),
    description: str = Form(...),
    rating: int = Form(...),
    treatment_type: str = Form(""),
    hospital_name: str = Form(""),
    location: str = Form(""),
    position: int = Form(0),
    is_featured: bool = Form(False),
    is_active: bool = Form(False),
    profile_image: UploadFile = File(default=None),
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Update patient story"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get existing story
        result = await db.execute(select(PatientStory).where(PatientStory.id == story_id))
        story = result.scalar_one_or_none()
        
        if not story:
            raise HTTPException(status_code=404, detail="Patient story not found")
        
        # Validate rating
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        # Handle profile photo upload
        if profile_image and profile_image.filename:
            filename = await save_uploaded_file(profile_image, "patient")
            story.profile_photo = f"/media/patient/{filename}"
        
        # Update story fields
        story.patient_name = patient_name
        story.description = description
        story.rating = rating
        story.treatment_type = treatment_type or None
        story.hospital_name = hospital_name or None
        story.location = location or None
        story.position = position
        story.is_featured = is_featured
        story.is_active = is_active
        story.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return RedirectResponse(url="/admin/stories", status_code=302)
        
    except Exception as e:
        await db.rollback()
        print(f"Error updating patient story: {str(e)}")
        return render_template("admin/story_form.html", {
            "request": request,
            "admin": admin,
            "action": "Edit",
            "story": story,
            "error": f"Error updating patient story: {str(e)}"
        })


@router.post("/admin/stories/{story_id}/delete")
async def admin_story_delete(
    story_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete patient story"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    try:
        # Get story
        result = await db.execute(select(PatientStory).where(PatientStory.id == story_id))
        story = result.scalar_one_or_none()
        
        if story:
            await db.delete(story)
            await db.commit()
        
        return RedirectResponse(url="/admin/stories", status_code=302)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting patient story: {str(e)}")


# User Management
@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    status: Optional[str] = None,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """User management page"""
    admin = await get_current_admin_dict(session_token, db)
    if not admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    limit = 15
    offset = (page - 1) * limit
    
    # Build query
    query = select(User)
    
    # Apply search filter
    if search:
        search_term = f"%{search.strip()}%"
        query = query.where(
            (User.name.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.phone.ilike(search_term))
        )
    
    # Apply status filter
    if status:
        if status == "active":
            query = query.where(User.is_active == True)
        elif status == "inactive":
            query = query.where(User.is_active == False)
        elif status == "verified":
            query = query.where(User.is_email_verified == True)
        elif status == "unverified":
            query = query.where(User.is_email_verified == False)
    
    # Add ordering and pagination
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Get total count for pagination
    count_query = select(func.count(User.id))
    if search:
        search_term = f"%{search.strip()}%"
        count_query = count_query.where(
            (User.name.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.phone.ilike(search_term))
        )
    if status:
        if status == "active":
            count_query = count_query.where(User.is_active == True)
        elif status == "inactive":
            count_query = count_query.where(User.is_active == False)
        elif status == "verified":
            count_query = count_query.where(User.is_email_verified == True)
        elif status == "unverified":
            count_query = count_query.where(User.is_email_verified == False)
    
    total = await db.scalar(count_query)
    total_pages = (total + limit - 1) // limit
    
    # Get user statistics
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
    verified_users = await db.scalar(select(func.count(User.id)).where(User.is_email_verified == True))
    
    # Recent users (last 30 days)
    month_ago = datetime.utcnow() - timedelta(days=30)
    recent_users = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= month_ago)
    )
    
    return render_template("admin/users.html", {
        "request": request,
        "admin": admin,
        "users": users,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search or "",
        "status": status,
        "total_users": total_users,
        "active_users": active_users,
        "verified_users": verified_users,
        "recent_users": recent_users
    })

@router.get("/admin/users/{user_id}")
async def get_user_details(
    user_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Get individual user details (API endpoint for modal)"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert user to dict for JSON response (excluding sensitive fields)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "is_email_verified": user.is_email_verified,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None
    }

@router.post("/admin/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Toggle user active status"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    await db.commit()
    
    status_text = "activated" if user.is_active else "deactivated"
    return {"message": f"User {status_text} successfully"}

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user"""
    admin = await get_current_admin_object(session_token, db)
    if not admin:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "User deleted successfully"}


