"""
Contact Us form endpoints
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional

from app.db import get_db
from app import models, schemas
from app.dependencies import get_current_admin

router = APIRouter()


@router.post("/contact", response_model=schemas.ContactUsResponse)
async def create_contact(
    contact_data: schemas.ContactUsCreate,
    db: AsyncSession = Depends(get_db)
):
    """Submit a contact form (public endpoint)"""
    db_contact = models.ContactUs(**contact_data.model_dump())
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    
    return {
        "id": db_contact.id,
        "first_name": db_contact.first_name,
        "last_name": db_contact.last_name,
        "email": db_contact.email,
        "phone": db_contact.phone,
        "subject": db_contact.subject,
        "message": db_contact.message,
        "service_type": db_contact.service_type,
        "is_read": db_contact.is_read,
        "admin_response": db_contact.admin_response,
        "responded_at": db_contact.responded_at,
        "created_at": db_contact.created_at
    }


@router.get("/contact", response_model=List[schemas.ContactUsResponse])
async def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_read: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    service_type: Optional[str] = Query(None),
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """List contact form submissions (admin only)"""
    
    query = select(models.ContactUs)
    
    filters = []
    if is_read is not None:
        filters.append(models.ContactUs.is_read == is_read)
    
    if search:
        filters.append(or_(
            models.ContactUs.first_name.ilike(f"%{search}%"),
            models.ContactUs.last_name.ilike(f"%{search}%"),
            models.ContactUs.email.ilike(f"%{search}%"),
            models.ContactUs.subject.ilike(f"%{search}%"),
            models.ContactUs.message.ilike(f"%{search}%"),
            models.ContactUs.service_type.ilike(f"%{search}%")
        ))
    
    if service_type:
        filters.append(models.ContactUs.service_type.ilike(f"%{service_type}%"))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(models.ContactUs.created_at.desc())
    
    result = await db.execute(query)
    contacts = result.scalars().all()
    
    return [
        {
            "id": contact.id,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "phone": contact.phone,
            "subject": contact.subject,
            "message": contact.message,
            "service_type": contact.service_type,
            "is_read": contact.is_read,
            "admin_response": contact.admin_response,
            "responded_at": contact.responded_at,
            "created_at": contact.created_at
        }
        for contact in contacts
    ]


@router.get("/contact/{contact_id}", response_model=schemas.ContactUsResponse)
async def get_contact(
    contact_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific contact form submission (admin only)"""
    
    result = await db.execute(select(models.ContactUs).where(models.ContactUs.id == contact_id))
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Mark as read
    if not contact.is_read:
        contact.is_read = True
        await db.commit()
    
    return {
        "id": contact.id,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "email": contact.email,
        "phone": contact.phone,
        "subject": contact.subject,
        "message": contact.message,
        "service_type": contact.service_type,
        "is_read": contact.is_read,
        "admin_response": contact.admin_response,
        "responded_at": contact.responded_at,
        "created_at": contact.created_at
    }


@router.put("/contact/{contact_id}/respond", response_model=schemas.ContactUsResponse)
async def respond_to_contact(
    contact_id: int,
    update_data: schemas.ContactUsUpdate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Respond to a contact form submission (admin only)"""
    
    result = await db.execute(select(models.ContactUs).where(models.ContactUs.id == contact_id))
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Update contact
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(contact, field, value)
    
    # Set response timestamp if admin_response is provided
    if update_data.admin_response:
        contact.responded_at = datetime.utcnow()
        contact.is_read = True
    
    await db.commit()
    await db.refresh(contact)
    
    return {
        "id": contact.id,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "email": contact.email,
        "phone": contact.phone,
        "subject": contact.subject,
        "message": contact.message,
        "service_type": contact.service_type,
        "is_read": contact.is_read,
        "admin_response": contact.admin_response,
        "responded_at": contact.responded_at,
        "created_at": contact.created_at
    }


@router.delete("/contact/{contact_id}")
async def delete_contact(
    contact_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a contact form submission (admin only)"""
    
    result = await db.execute(select(models.ContactUs).where(models.ContactUs.id == contact_id))
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    await db.delete(contact)
    await db.commit()
    
    return {"message": "Contact deleted successfully"}


@router.get("/filters/service-types", response_model=List[str])
async def get_service_types(db: AsyncSession = Depends(get_db)):
    """Get all unique service types for dropdown"""
    result = await db.execute(
        select(models.ContactUs.service_type).distinct().where(models.ContactUs.service_type.isnot(None))
    )
    service_types = result.scalars().all()
    
    # Filter out empty values and sort
    valid_types = [s.strip() for s in service_types if s and s.strip()]
    return sorted(valid_types)