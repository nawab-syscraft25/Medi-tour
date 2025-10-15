from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
import os
import uuid
from pathlib import Path
from app.db import get_db
from app import models, schemas
from app.dependencies import get_current_admin, get_current_user


def hospital_to_dict(hospital: models.Hospital) -> dict:
    """Convert Hospital model to dict for safe serialization"""
    return {
        "id": hospital.id,
        "name": hospital.name,
        "description": hospital.description,
        "location": hospital.location,
        "address": hospital.address,
        "phone": hospital.phone,
        "email": hospital.email,
        "website": hospital.website,
        "established_year": hospital.established_year,
        "bed_count": hospital.bed_count,
        "specializations": hospital.specializations,
        "rating": hospital.rating,
        "features": hospital.features,
        "facilities": hospital.facilities,
        "is_featured": hospital.is_featured if hospital.is_featured is not None else False,
        "is_active": hospital.is_active if hospital.is_active is not None else True,
        "created_at": hospital.created_at,
        "images": [],  # Will be populated separately
        "faqs": [],    # Will be populated separately
        # Direct FAQ fields from model (all 5 FAQ pairs)
        "faq1_question": hospital.faq1_question,
        "faq1_answer": hospital.faq1_answer,
        "faq2_question": hospital.faq2_question,
        "faq2_answer": hospital.faq2_answer,
        "faq3_question": hospital.faq3_question,
        "faq3_answer": hospital.faq3_answer,
        "faq4_question": hospital.faq4_question,
        "faq4_answer": hospital.faq4_answer,
        "faq5_question": hospital.faq5_question,
        "faq5_answer": hospital.faq5_answer
    }


def doctor_to_dict(doctor: models.Doctor) -> dict:
    """Convert Doctor model to dict for safe serialization"""
    return {
        "id": doctor.id,
        "name": doctor.name,
        "profile_photo": doctor.profile_photo,
        "short_description": doctor.short_description,
        "long_description": doctor.long_description,
        "designation": doctor.designation,
        "specialization": doctor.specialization,
        "qualification": doctor.qualification,
        "experience_years": doctor.experience_years,
        "rating": doctor.rating,
        "consultancy_fee": doctor.consultancy_fee,
        "hospital_id": doctor.hospital_id,
        "gender": doctor.gender,
        "skills": doctor.skills,
        "qualifications": doctor.qualifications,
        "highlights": doctor.highlights,
        "awards": doctor.awards,
        "location": doctor.location,
        "time_slots": doctor.time_slots,
        "is_featured": doctor.is_featured if doctor.is_featured is not None else False,
        "is_active": doctor.is_active if doctor.is_active is not None else True,
        "created_at": doctor.created_at,
        "images": [],  # Will be populated separately
        "faqs": [],    # Will be populated separately
        # Direct FAQ fields from model (all 5 FAQ pairs)
        "faq1_question": doctor.faq1_question,
        "faq1_answer": doctor.faq1_answer,
        "faq2_question": doctor.faq2_question,
        "faq2_answer": doctor.faq2_answer,
        "faq3_question": doctor.faq3_question,
        "faq3_answer": doctor.faq3_answer,
        "faq4_question": doctor.faq4_question,
        "faq4_answer": doctor.faq4_answer,
        "faq5_question": doctor.faq5_question,
        "faq5_answer": doctor.faq5_answer
        ,
        # Associated hospitals (will be populated separately when needed)
        "associated_hospitals": []
    }


def treatment_to_dict(treatment: models.Treatment) -> dict:
    """Convert Treatment model to dict for safe serialization"""
    return {
        "id": treatment.id,
        "name": treatment.name,
        "short_description": treatment.short_description,
        "long_description": treatment.long_description,
        "treatment_type": treatment.treatment_type,
        "price_min": treatment.price_min,
        "price_max": treatment.price_max,
        "price_exact": treatment.price_exact,
        "hospital_id": treatment.hospital_id,
        "other_hospital_name": treatment.other_hospital_name,
        "doctor_id": treatment.doctor_id,
        "other_doctor_name": treatment.other_doctor_name,
        "location": treatment.location,
        "features": treatment.features,
        "rating": treatment.rating,
        "is_ayushman": bool(getattr(treatment, 'is_ayushman', False)),
        "Includes": treatment.Includes if hasattr(treatment, 'Includes') else None,
        "excludes": treatment.excludes if hasattr(treatment, 'excludes') else None,
        "is_featured": treatment.is_featured if treatment.is_featured is not None else False,
        "created_at": treatment.created_at,
        "images": [], 
        "faqs": [],   
        "faq1_question": treatment.faq1_question,
        "faq1_answer": treatment.faq1_answer,
        "faq2_question": treatment.faq2_question,
        "faq2_answer": treatment.faq2_answer,
        "faq3_question": treatment.faq3_question,
        "faq3_answer": treatment.faq3_answer,
        "faq4_question": treatment.faq4_question,
        "faq4_answer": treatment.faq4_answer,
        "faq5_question": treatment.faq5_question,
        "faq5_answer": treatment.faq5_answer
    }


def blog_to_dict(blog: models.Blog) -> dict:
    """Convert Blog model to dict for safe serialization"""
    return {
        "id": blog.id,
        "title": blog.title,
        "subtitle": blog.subtitle,
        "slug": blog.slug,
        "content": blog.content,
        "excerpt": blog.excerpt,
        "featured_image": blog.featured_image,
        "meta_description": blog.meta_description,
        "tags": blog.tags,
        "category": blog.category,
        "author_name": blog.author_name,
        "reading_time": blog.reading_time,
        "view_count": blog.view_count,
        "is_published": blog.is_published,
        "is_featured": blog.is_featured,
        "published_at": blog.published_at,
        "created_at": blog.created_at,
        "updated_at": blog.updated_at,
        "images": []  # Will be populated separately
    }

router = APIRouter()


# Slider endpoints
@router.post("/sliders", response_model=schemas.SliderResponse)
async def create_slider(
    slider: schemas.SliderCreate,
    db: AsyncSession = Depends(get_db)
):
    db_slider = models.Slider(**slider.model_dump())
    db.add(db_slider)
    await db.commit()
    await db.refresh(db_slider)
    return db_slider


@router.get("/sliders", response_model=List[schemas.SliderResponse])
async def get_sliders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    query = select(models.Slider)
    if active_only:
        query = query.where(models.Slider.is_active == True)
    query = query.offset(skip).limit(limit).order_by(models.Slider.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/sliders/{slider_id}", response_model=schemas.SliderResponse)
async def get_slider(slider_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Slider).where(models.Slider.id == slider_id))
    slider = result.scalar_one_or_none()
    if not slider:
        raise HTTPException(status_code=404, detail="Slider not found")
    return slider


@router.put("/sliders/{slider_id}", response_model=schemas.SliderResponse)
async def update_slider(
    slider_id: int,
    slider_update: schemas.SliderUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Slider).where(models.Slider.id == slider_id))
    slider = result.scalar_one_or_none()
    if not slider:
        raise HTTPException(status_code=404, detail="Slider not found")
    
    update_data = slider_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(slider, field, value)
    
    await db.commit()
    await db.refresh(slider)
    return slider


@router.delete("/sliders/{slider_id}")
async def delete_slider(slider_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Slider).where(models.Slider.id == slider_id))
    slider = result.scalar_one_or_none()
    if not slider:
        raise HTTPException(status_code=404, detail="Slider not found")
    
    slider.is_active = False  # Soft delete
    await db.commit()
    return {"message": "Slider deactivated"}


# Hospital endpoints
@router.post("/hospitals", response_model=schemas.HospitalResponse)
async def create_hospital(
    hospital: schemas.HospitalCreate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    db_hospital = models.Hospital(**hospital.model_dump())
    db.add(db_hospital)
    await db.commit()
    # Fetch fresh copy to get the generated ID without triggering relationships
    result = await db.execute(select(models.Hospital).where(models.Hospital.id == db_hospital.id))
    fresh_hospital = result.scalar_one()
    return hospital_to_dict(fresh_hospital)


@router.get("/hospitals", response_model=List[schemas.HospitalResponse])
async def get_hospitals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(models.Hospital)
    
    filters = []
    if search:
        filters.append(or_(
            models.Hospital.name.ilike(f"%{search}%"),
            models.Hospital.description.ilike(f"%{search}%")
        ))
    if location:
        filters.append(models.Hospital.location.ilike(f"%{location}%"))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(models.Hospital.created_at.desc())
    
    result = await db.execute(query)
    hospitals = result.scalars().all()
    
    # Load images and FAQs for each hospital within the session
    hospital_dicts = []
    for hospital in hospitals:
        # Load images within session
        images_result = await db.execute(
            select(models.Image).where(
                and_(
                    models.Image.owner_id == hospital.id,
                    models.Image.owner_type == 'hospital'
                )
            ).order_by(models.Image.position)
        )
        images = images_result.scalars().all()
        
        # Load FAQs within session
        faqs_result = await db.execute(
            select(models.FAQ).where(
                and_(
                    models.FAQ.owner_id == hospital.id,
                    models.FAQ.owner_type == 'hospital',
                    models.FAQ.is_active == True
                )
            ).order_by(models.FAQ.position)
        )
        faqs = faqs_result.scalars().all()
        
        hospital_dict = hospital_to_dict(hospital)
        hospital_dict['images'] = [
            {
                "id": img.id,
                "url": img.url,
                "is_primary": img.is_primary,
                "position": img.position,
                "uploaded_at": img.uploaded_at
            } for img in images
        ]
        hospital_dict['faqs'] = [
            {
                "id": faq.id,
                "owner_type": faq.owner_type,
                "owner_id": faq.owner_id,
                "question": faq.question,
                "answer": faq.answer,
                "position": faq.position,
                "is_active": faq.is_active,
                "created_at": faq.created_at,
                "updated_at": faq.updated_at
            } for faq in faqs
        ]
        hospital_dicts.append(hospital_dict)
    
    return hospital_dicts


@router.get("/hospitals/{hospital_id}", response_model=schemas.HospitalResponse)
async def get_hospital(hospital_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Hospital).where(models.Hospital.id == hospital_id))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    # Load images for the hospital within the session
    images_result = await db.execute(
        select(models.Image).where(
            and_(
                models.Image.owner_id == hospital.id,
                models.Image.owner_type == 'hospital'
            )
        ).order_by(models.Image.position)
    )
    images = images_result.scalars().all()
    
    # Load FAQs for the hospital
    faqs_result = await db.execute(
        select(models.FAQ).where(
            and_(
                models.FAQ.owner_id == hospital.id,
                models.FAQ.owner_type == 'hospital',
                models.FAQ.is_active == True
            )
        ).order_by(models.FAQ.position)
    )
    faqs = faqs_result.scalars().all()
    
    hospital_dict = hospital_to_dict(hospital)
    hospital_dict['images'] = [
        {
            "id": img.id,
            "url": img.url,
            "is_primary": img.is_primary,
            "position": img.position,
            "uploaded_at": img.uploaded_at
        } for img in images
    ]
    hospital_dict['faqs'] = [
        {
            "id": faq.id,
            "owner_type": faq.owner_type,
            "owner_id": faq.owner_id,
            "question": faq.question,
            "answer": faq.answer,
            "position": faq.position,
            "is_active": faq.is_active,
            "created_at": faq.created_at,
            "updated_at": faq.updated_at
        } for faq in faqs
    ]
    
    return hospital_dict


@router.put("/hospitals/{hospital_id}", response_model=schemas.HospitalResponse)
async def update_hospital(
    hospital_id: int,
    hospital_update: schemas.HospitalUpdate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Hospital).where(models.Hospital.id == hospital_id))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    update_data = hospital_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(hospital, field, value)
    
    await db.commit()
    await db.refresh(hospital)
    return hospital_to_dict(hospital)


@router.delete("/hospitals/{hospital_id}")
async def delete_hospital(
    hospital_id: int, 
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Hospital).where(models.Hospital.id == hospital_id))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    await db.delete(hospital)
    await db.commit()
    return {"message": "Hospital deleted"}


# Doctor endpoints
@router.post("/doctors", response_model=schemas.DoctorResponse)
async def create_doctor(
    doctor: schemas.DoctorCreate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    db_doctor = models.Doctor(**doctor.model_dump())
    db.add(db_doctor)
    await db.commit()
    # Fetch fresh copy to get the generated ID without triggering relationships  
    result = await db.execute(select(models.Doctor).where(models.Doctor.id == db_doctor.id))
    fresh_doctor = result.scalar_one()
    return doctor_to_dict(fresh_doctor)


@router.get("/doctors", response_model=List[schemas.DoctorResponse])
async def get_doctors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    hospital_id: Optional[int] = Query(None),
    specialization: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(models.Doctor)
    
    filters = []
    if search:
        filters.append(or_(
            models.Doctor.name.ilike(f"%{search}%"),
            models.Doctor.designation.ilike(f"%{search}%"),
            models.Doctor.short_description.ilike(f"%{search}%"),
            models.Doctor.long_description.ilike(f"%{search}%"),
            models.Doctor.specialization.ilike(f"%{search}%"),
            models.Doctor.qualification.ilike(f"%{search}%"),
            models.Doctor.location.ilike(f"%{search}%")
        ))
    if hospital_id:
        filters.append(models.Doctor.hospital_id == hospital_id)
    if specialization:
        filters.append(models.Doctor.skills.ilike(f"%{specialization}%"))
    if location:
        filters.append(models.Doctor.location.ilike(f"%{location}%"))
    
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(models.Doctor.created_at.desc())
    
    result = await db.execute(query)
    doctors = result.scalars().all()
    
    # Load images and FAQs for each doctor within the session
    doctor_dicts = []
    for doctor in doctors:
        # Load images within session
        images_result = await db.execute(
            select(models.Image).where(
                and_(
                    models.Image.owner_id == doctor.id,
                    models.Image.owner_type == 'doctor'
                )
            ).order_by(models.Image.position)
        )
        images = images_result.scalars().all()
        
        # Load FAQs within session
        faqs_result = await db.execute(
            select(models.FAQ).where(
                and_(
                    models.FAQ.owner_id == doctor.id,
                    models.FAQ.owner_type == 'doctor',
                    models.FAQ.is_active == True
                )
            ).order_by(models.FAQ.position)
        )
        faqs = faqs_result.scalars().all()
        
        doctor_dict = doctor_to_dict(doctor)
        doctor_dict['images'] = [
            {
                "id": img.id,
                "url": img.url,
                "is_primary": img.is_primary,
                "position": img.position,
                "uploaded_at": img.uploaded_at
            } for img in images
        ]
        doctor_dict['faqs'] = [
            {
                "id": faq.id,
                "owner_type": faq.owner_type,
                "owner_id": faq.owner_id,
                "question": faq.question,
                "answer": faq.answer,
                "position": faq.position,
                "is_active": faq.is_active,
                "created_at": faq.created_at,
                "updated_at": faq.updated_at
            } for faq in faqs
        ]
        # Load associated hospitals for this doctor
        hospitals_result = await db.execute(
            select(models.Hospital)
            .join(models.doctor_hospital_association, models.doctor_hospital_association.c.hospital_id == models.Hospital.id)
            .where(models.doctor_hospital_association.c.doctor_id == doctor.id)
        )
        associated_hospitals = hospitals_result.scalars().all()
        # Only expose minimal hospital info for associated_hospitals: id and name
        doctor_dict['associated_hospitals'] = [{"id": h.id, "name": h.name} for h in associated_hospitals]
        doctor_dicts.append(doctor_dict)
    
    return doctor_dicts


@router.get("/doctors/{doctor_id}/debug")
async def debug_doctor_faqs(doctor_id: int, db: AsyncSession = Depends(get_db)):
    """Debug endpoint to check doctor FAQ data"""
    result = await db.execute(select(models.Doctor).where(models.Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Check FAQ table data
    faqs_result = await db.execute(
        select(models.FAQ).where(
            and_(
                models.FAQ.owner_id == doctor.id,
                models.FAQ.owner_type == 'doctor'
            )
        )
    )
    faq_table_data = faqs_result.scalars().all()
    
    return {
        "doctor_id": doctor.id,
        "doctor_name": doctor.name,
        "faq_table_count": len(faq_table_data),
        "faq_table_data": [
            {
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer,
                "is_active": faq.is_active
            } for faq in faq_table_data
        ],
        "direct_faq_fields": {
            "faq1_question": doctor.faq1_question,
            "faq1_answer": doctor.faq1_answer,
            "faq2_question": doctor.faq2_question,
            "faq2_answer": doctor.faq2_answer,
            "faq3_question": doctor.faq3_question,
            "faq3_answer": doctor.faq3_answer,
            "faq4_question": doctor.faq4_question,
            "faq4_answer": doctor.faq4_answer,
            "faq5_question": doctor.faq5_question,
            "faq5_answer": doctor.faq5_answer
        }
    }


@router.get("/doctors/{doctor_id}", response_model=schemas.DoctorResponse)
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Doctor).where(models.Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Load images for the doctor within the session
    images_result = await db.execute(
        select(models.Image).where(
            and_(
                models.Image.owner_id == doctor.id,
                models.Image.owner_type == 'doctor'
            )
        ).order_by(models.Image.position)
    )
    images = images_result.scalars().all()
    
    # Load FAQs for the doctor
    faqs_result = await db.execute(
        select(models.FAQ).where(
            and_(
                models.FAQ.owner_id == doctor.id,
                models.FAQ.owner_type == 'doctor',
                models.FAQ.is_active == True
            )
        ).order_by(models.FAQ.position)
    )
    faqs = faqs_result.scalars().all()
    
    doctor_dict = doctor_to_dict(doctor)
    doctor_dict['images'] = [
        {
            "id": img.id,
            "url": img.url,
            "is_primary": img.is_primary,
            "position": img.position,
            "uploaded_at": img.uploaded_at
        } for img in images
    ]
    doctor_dict['faqs'] = [
        {
            "id": faq.id,
            "owner_type": faq.owner_type,
            "owner_id": faq.owner_id,
            "question": faq.question,
            "answer": faq.answer,
            "position": faq.position,
            "is_active": faq.is_active,
            "created_at": faq.created_at,
            "updated_at": faq.updated_at
        } for faq in faqs
    ]
    # Load associated hospitals for this doctor
    hospitals_result = await db.execute(
        select(models.Hospital)
        .join(models.doctor_hospital_association, models.doctor_hospital_association.c.hospital_id == models.Hospital.id)
        .where(models.doctor_hospital_association.c.doctor_id == doctor.id)
    )
    associated_hospitals = hospitals_result.scalars().all()
    # Only expose minimal hospital info for associated_hospitals: id and name
    doctor_dict['associated_hospitals'] = [{"id": h.id, "name": h.name} for h in associated_hospitals]
    
    return doctor_dict


@router.put("/doctors/{doctor_id}", response_model=schemas.DoctorResponse)
async def update_doctor(
    doctor_id: int,
    doctor_update: schemas.DoctorUpdate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Doctor).where(models.Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    update_data = doctor_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doctor, field, value)
    
    await db.commit()
    await db.refresh(doctor)
    return doctor_to_dict(doctor)


@router.delete("/doctors/{doctor_id}")
async def delete_doctor(
    doctor_id: int, 
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Doctor).where(models.Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    await db.delete(doctor)
    await db.commit()
    return {"message": "Doctor deleted"}


# Global Search endpoint
@router.get("/search")
async def global_search(
    query: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results per category"),
    db: AsyncSession = Depends(get_db)
):
    """
    Global search across doctors, treatments, and hospitals
    Returns results from all three categories based on the search query
    """
    if len(query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters long")
    
    search_term = f"%{query.strip()}%"
    
    # Search Doctors
    doctors_query = select(models.Doctor).where(
        or_(
            models.Doctor.name.ilike(search_term),
            models.Doctor.designation.ilike(search_term),
            models.Doctor.specialization.ilike(search_term),
            models.Doctor.qualification.ilike(search_term),
            models.Doctor.skills.ilike(search_term),
            models.Doctor.location.ilike(search_term),
            models.Doctor.short_description.ilike(search_term),
            models.Doctor.long_description.ilike(search_term)
        )
    ).where(models.Doctor.is_active == True).limit(limit)
    
    # Search Treatments
    treatments_query = select(models.Treatment).where(
        or_(
            models.Treatment.name.ilike(search_term),
            models.Treatment.treatment_type.ilike(search_term),
            models.Treatment.short_description.ilike(search_term),
            models.Treatment.long_description.ilike(search_term),
            models.Treatment.location.ilike(search_term),
            models.Treatment.features.ilike(search_term)
        )
    ).limit(limit)
    
    # Search Hospitals
    hospitals_query = select(models.Hospital).where(
        or_(
            models.Hospital.name.ilike(search_term),
            models.Hospital.description.ilike(search_term),
            models.Hospital.location.ilike(search_term),
            models.Hospital.specializations.ilike(search_term),
            models.Hospital.features.ilike(search_term),
            models.Hospital.facilities.ilike(search_term)
        )
    ).where(models.Hospital.is_active == True).limit(limit)
    
    # Execute all queries
    doctors_result = await db.execute(doctors_query)
    treatments_result = await db.execute(treatments_query)
    hospitals_result = await db.execute(hospitals_query)
    
    doctors = doctors_result.scalars().all()
    treatments = treatments_result.scalars().all()
    hospitals = hospitals_result.scalars().all()
    
    # Load images and FAQs for doctors
    doctor_results = []
    for doctor in doctors:
        # Load images within session
        images_result = await db.execute(
            select(models.Image).where(
                and_(
                    models.Image.owner_id == doctor.id,
                    models.Image.owner_type == "doctor"
                )
            ).order_by(models.Image.position)
        )
        images = images_result.scalars().all()
        
        # Load FAQs within session
        faqs_result = await db.execute(
            select(models.FAQ).where(
                and_(
                    models.FAQ.owner_id == doctor.id,
                    models.FAQ.owner_type == "doctor",
                    models.FAQ.is_active == True
                )
            ).order_by(models.FAQ.position)
        )
        faqs = faqs_result.scalars().all()
        
        doctor_dict = doctor_to_dict(doctor)
        doctor_dict['images'] = [
            {
                "id": img.id,
                "url": img.url,
                "is_primary": img.is_primary,
                "position": img.position,
                "uploaded_at": img.uploaded_at
            } for img in images
        ]
        doctor_dict['faqs'] = [
            {
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer,
                "position": faq.position,
                "is_active": faq.is_active
            } for faq in faqs
        ]
        doctor_results.append(doctor_dict)
    
    # Load images and FAQs for treatments
    treatment_results = []
    for treatment in treatments:
        # Load images within session
        images_result = await db.execute(
            select(models.Image).where(
                and_(
                    models.Image.owner_id == treatment.id,
                    models.Image.owner_type == "treatment"
                )
            ).order_by(models.Image.position)
        )
        images = images_result.scalars().all()
        
        # Load FAQs within session
        faqs_result = await db.execute(
            select(models.FAQ).where(
                and_(
                    models.FAQ.owner_id == treatment.id,
                    models.FAQ.owner_type == "treatment",
                    models.FAQ.is_active == True
                )
            ).order_by(models.FAQ.position)
        )
        faqs = faqs_result.scalars().all()
        
        treatment_dict = treatment_to_dict(treatment)
        treatment_dict['images'] = [
            {
                "id": img.id,
                "url": img.url,
                "is_primary": img.is_primary,
                "position": img.position,
                "uploaded_at": img.uploaded_at
            } for img in images
        ]
        treatment_dict['faqs'] = [
            {
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer,
                "position": faq.position,
                "is_active": faq.is_active
            } for faq in faqs
        ]
        treatment_results.append(treatment_dict)
    
    # Load images and FAQs for hospitals
    hospital_results = []
    for hospital in hospitals:
        # Load images within session
        images_result = await db.execute(
            select(models.Image).where(
                and_(
                    models.Image.owner_id == hospital.id,
                    models.Image.owner_type == "hospital"
                )
            ).order_by(models.Image.position)
        )
        images = images_result.scalars().all()
        
        # Load FAQs within session
        faqs_result = await db.execute(
            select(models.FAQ).where(
                and_(
                    models.FAQ.owner_id == hospital.id,
                    models.FAQ.owner_type == "hospital",
                    models.FAQ.is_active == True
                )
            ).order_by(models.FAQ.position)
        )
        faqs = faqs_result.scalars().all()
        
        hospital_dict = hospital_to_dict(hospital)
        hospital_dict['images'] = [
            {
                "id": img.id,
                "url": img.url,
                "is_primary": img.is_primary,
                "position": img.position,
                "uploaded_at": img.uploaded_at
            } for img in images
        ]
        hospital_dict['faqs'] = [
            {
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer,
                "position": faq.position,
                "is_active": faq.is_active
            } for faq in faqs
        ]
        hospital_results.append(hospital_dict)
    
    return {
        "query": query,
        "total_results": len(doctors) + len(treatments) + len(hospitals),
        "results": {
            "doctors": {
                "count": len(doctors),
                "data": doctor_results
            },
            "treatments": {
                "count": len(treatments),
                "data": treatment_results
            },
            "hospitals": {
                "count": len(hospitals),
                "data": hospital_results
            }
        }
    }


# User Authentication endpoints
@router.post("/auth/signup", response_model=schemas.TokenResponse)
async def user_signup(
    user_data: schemas.UserSignUp,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """User registration with email verification"""
    from app.auth_utils import hash_password, generate_verification_token, send_verification_email, create_access_token, user_to_dict
    from datetime import datetime, timedelta
    
    # Check if user already exists
    existing_user = await db.execute(
        select(models.User).where(models.User.email == user_data.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    verification_token = generate_verification_token()
    verification_expires = datetime.utcnow() + timedelta(hours=24)
    
    db_user = models.User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hash_password(user_data.password),
        email_verification_token=verification_token,
        email_verification_expires=verification_expires
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Send verification email
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    send_verification_email(user_data.email, verification_token, user_data.name, base_url)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(db_user.id), "type": "user"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_to_dict(db_user)
    }

@router.post("/auth/login", response_model=schemas.TokenResponse)
async def user_login(
    user_credentials: schemas.UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """User login"""
    from app.auth_utils import verify_password, create_access_token, user_to_dict
    from datetime import datetime
    
    # Get user by email
    result = await db.execute(
        select(models.User).where(models.User.email == user_credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "type": "user"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_to_dict(user)
    }

@router.post("/auth/verify-email")
async def verify_email(
    verification_data: schemas.VerifyEmail,
    db: AsyncSession = Depends(get_db)
):
    """Verify user email with token"""
    from datetime import datetime
    
    # Find user with verification token
    result = await db.execute(
        select(models.User).where(
            models.User.email_verification_token == verification_data.token
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    if user.email_verification_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )
    
    # Mark email as verified
    user.is_email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    await db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/auth/resend-verification")
async def resend_verification(
    resend_data: schemas.ResendVerification,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Resend email verification"""
    from app.auth_utils import generate_verification_token, send_verification_email
    from datetime import datetime, timedelta
    
    # Get user by email
    result = await db.execute(
        select(models.User).where(models.User.email == resend_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Generate new verification token
    verification_token = generate_verification_token()
    verification_expires = datetime.utcnow() + timedelta(hours=24)
    
    user.email_verification_token = verification_token
    user.email_verification_expires = verification_expires
    await db.commit()
    
    # Send verification email
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    send_verification_email(user.email, verification_token, user.name, base_url)
    
    return {"message": "Verification email sent successfully"}

@router.post("/auth/forgot-password")
async def forgot_password(
    forgot_data: schemas.ForgotPassword,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Send password reset email"""
    from app.auth_utils import generate_verification_token, send_password_reset_email
    from datetime import datetime, timedelta
    
    # Get user by email
    result = await db.execute(
        select(models.User).where(models.User.email == forgot_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate password reset token
    reset_token = generate_verification_token()
    reset_expires = datetime.utcnow() + timedelta(hours=1)
    
    user.password_reset_token = reset_token
    user.password_reset_expires = reset_expires
    await db.commit()
    
    # Send password reset email
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    send_password_reset_email(user.email, reset_token, user.name, base_url)
    
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/auth/reset-password")
async def reset_password(
    reset_data: schemas.ResetPassword,
    db: AsyncSession = Depends(get_db)
):
    """Reset password with token"""
    from app.auth_utils import hash_password
    from datetime import datetime
    
    # Find user with reset token
    result = await db.execute(
        select(models.User).where(
            models.User.password_reset_token == reset_data.token
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    if user.password_reset_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Update password
    user.password_hash = hash_password(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.commit()
    
    return {"message": "Password reset successfully"}

# Frontend verification endpoints (for email links)
@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Handle email verification from email link"""
    from app.auth_utils import get_user_by_email
    from datetime import datetime
    
    # Get base URL for home link
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    try:
        # Find user by verification token
        result = await db.execute(
            select(models.User).where(
                and_(
                    models.User.email_verification_token == token,
                    models.User.email_verification_expires > datetime.utcnow()
                )
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Return error page
            return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Verification Failed - Medi-tour</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
                    .error {{ color: #e74c3c; }}
                    .btn {{ display: inline-block; padding: 12px 24px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                    .btn:hover {{ background-color: #2980b9; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="error">❌ Verification Failed</h1>
                    <p>The verification token is invalid or has expired.</p>
                    <p>Please request a new verification email or contact support.</p>
                    <a href="http://165.22.223.163:8090/login" class="btn">Go to Login</a>
                </div>
            </body>
            </html>
            """
        
        # Verify the user
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verification_expires = None
        await db.commit()
        
        # Return success page
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verified - Medi-tour</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
                .success {{ color: #27ae60; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #27ae60; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .btn:hover {{ background-color: #229954; }}
                .email {{ color: #7f8c8d; font-style: italic; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="success">✅ Email Verified Successfully!</h1>
                <p>Your email address <span class="email">{user.email}</span> has been verified.</p>
                <p>You can now access all features of Medi-tour.</p>
                <a href="http://165.22.223.163:8090/login" class="btn">Go to Login</a>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        # Return generic error page
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error - Medi-tour</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
                .error {{ color: #e74c3c; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .btn:hover {{ background-color: #2980b9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">❌ Something went wrong</h1>
                <p>An error occurred while verifying your email. Please try again later.</p>
                <a href="http://165.22.223.163:8090/login" class="btn">Go to Login</a>
            </div>
        </body>
        </html>
        """

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Handle password reset page from email link"""
    from datetime import datetime
    
    # Get base URL for API calls
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    try:
        # Find user by reset token
        result = await db.execute(
            select(models.User).where(
                and_(
                    models.User.password_reset_token == token,
                    models.User.password_reset_expires > datetime.utcnow()
                )
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Return error page
            return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Reset Failed - Medi-tour</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
                    .error {{ color: #e74c3c; }}
                    .btn {{ display: inline-block; padding: 12px 24px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                    .btn:hover {{ background-color: #2980b9; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="error">❌ Reset Link Expired</h1>
                    <p>The password reset token is invalid or has expired.</p>
                    <p>Please request a new password reset email.</p>
                    <a href="http://165.22.223.163:8090/login" class="btn">Go to Login</a>
                </div>
            </body>
            </html>
            """
        
        # Return password reset form
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Password - Medi-tour</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .title {{ color: #2c3e50; text-align: center; margin-bottom: 30px; }}
                .form-group {{ margin-bottom: 20px; }}
                .form-group label {{ display: block; margin-bottom: 5px; color: #34495e; font-weight: bold; }}
                .form-group input {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; box-sizing: border-box; }}
                .btn {{ width: 100%; padding: 12px; background-color: #e74c3c; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin-top: 10px; }}
                .btn:hover {{ background-color: #c0392b; }}
                .btn:disabled {{ background-color: #95a5a6; cursor: not-allowed; }}
                .message {{ padding: 10px; border-radius: 5px; margin-bottom: 20px; text-align: center; }}
                .success {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .error {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                .email {{ color: #7f8c8d; font-style: italic; text-align: center; margin-bottom: 20px; }}
                .back-link {{ text-align: center; margin-top: 20px; }}
                .back-link a {{ color: #3498db; text-decoration: none; }}
                .back-link a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="title">🔐 Reset Your Password</h1>
                <p class="email">Resetting password for: {user.email}</p>
                
                <div id="message" class="message" style="display: none;"></div>
                
                <form id="resetForm">
                    <div class="form-group">
                        <label for="password">New Password:</label>
                        <input type="password" id="password" name="password" required minlength="6" placeholder="Enter your new password">
                    </div>
                    
                    <div class="form-group">
                        <label for="confirmPassword">Confirm Password:</label>
                        <input type="password" id="confirmPassword" name="confirmPassword" required minlength="6" placeholder="Confirm your new password">
                    </div>
                    
                    <button type="submit" class="btn" id="submitBtn">Reset Password</button>
                </form>
                
                <div class="back-link">
                    <a href="http://165.22.223.163:8090/login">← Back to Login</a>
                </div>
            </div>
            
            <script>
                document.getElementById('resetForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const password = document.getElementById('password').value;
                    const confirmPassword = document.getElementById('confirmPassword').value;
                    const messageDiv = document.getElementById('message');
                    const submitBtn = document.getElementById('submitBtn');
                    
                    // Clear previous messages
                    messageDiv.style.display = 'none';
                    
                    // Validate passwords match
                    if (password !== confirmPassword) {{
                        messageDiv.className = 'message error';
                        messageDiv.textContent = 'Passwords do not match!';
                        messageDiv.style.display = 'block';
                        return;
                    }}
                    
                    // Validate password length
                    if (password.length < 6) {{
                        messageDiv.className = 'message error';
                        messageDiv.textContent = 'Password must be at least 6 characters long!';
                        messageDiv.style.display = 'block';
                        return;
                    }}
                    
                    // Disable submit button
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Resetting...';
                    
                    try {{
                        const response = await fetch('{base_url}/api/v1/auth/reset-password', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                token: '{token}',
                                new_password: password
                            }})
                        }});
                        
                        const data = await response.json();
                        
                        if (response.ok) {{
                            messageDiv.className = 'message success';
                            messageDiv.textContent = 'Password reset successfully! Redirecting to login...';
                            messageDiv.style.display = 'block';
                            
                            // Redirect to login after 2 seconds
                            setTimeout(() => {{
                                window.location.href = 'http://165.22.223.163:8090/login';
                            }}, 2000);
                        }} else {{
                            messageDiv.className = 'message error';
                            messageDiv.textContent = data.detail || 'Failed to reset password. Please try again.';
                            messageDiv.style.display = 'block';
                        }}
                    }} catch (error) {{
                        messageDiv.className = 'message error';
                        messageDiv.textContent = 'Network error. Please check your connection and try again.';
                        messageDiv.style.display = 'block';
                    }} finally {{
                        // Re-enable submit button
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Reset Password';
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        # Return generic error page
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error - Medi-tour</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
                .error {{ color: #e74c3c; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .btn:hover {{ background-color: #2980b9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">❌ Something went wrong</h1>
                <p>An error occurred while processing your password reset. Please try again later.</p>
                <a href="http://165.22.223.163:8090/login" class="btn">Go to Login</a>
            </div>
        </body>
        </html>
        """

@router.get("/auth/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """Get current user information"""
    from app.auth_utils import user_to_dict
    return user_to_dict(current_user)


# Treatment endpoints
@router.post("/treatments", response_model=schemas.TreatmentResponse)
async def create_treatment(
    treatment: schemas.TreatmentCreate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    db_treatment = models.Treatment(**treatment.model_dump())
    db.add(db_treatment)
    await db.commit()
    # Fetch fresh copy to get the generated ID without triggering relationships
    result = await db.execute(select(models.Treatment).where(models.Treatment.id == db_treatment.id))
    fresh_treatment = result.scalar_one()
    return treatment_to_dict(fresh_treatment)


@router.get("/treatments", response_model=List[schemas.TreatmentResponse])
async def get_treatments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    treatment_type: Optional[str] = Query(None),
    hospital_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    price_min: Optional[float] = Query(None),
    price_max: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(models.Treatment)
    
    filters = []
    if search:
        filters.append(or_(
            models.Treatment.name.ilike(f"%{search}%"),
            models.Treatment.short_description.ilike(f"%{search}%"),
            models.Treatment.long_description.ilike(f"%{search}%"),
            models.Treatment.features.ilike(f"%{search}%")
        ))
    if location:
        filters.append(models.Treatment.location.ilike(f"%{location}%"))
    if treatment_type:
        filters.append(models.Treatment.treatment_type.ilike(f"%{treatment_type}%"))
    if hospital_id:
        filters.append(models.Treatment.hospital_id == hospital_id)
    if doctor_id:
        filters.append(models.Treatment.doctor_id == doctor_id)
    if price_min is not None:
        filters.append(or_(
            models.Treatment.price_exact >= price_min,
            models.Treatment.price_min >= price_min
        ))
    if price_max is not None:
        filters.append(or_(
            models.Treatment.price_exact <= price_max,
            models.Treatment.price_max <= price_max
        ))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(models.Treatment.created_at.desc())
    
    result = await db.execute(query)
    treatments = result.scalars().all()
    
    # Load images and FAQs for each treatment within the session
    treatment_dicts = []
    for treatment in treatments:
        # Load images within session
        images_result = await db.execute(
            select(models.Image).where(
                and_(
                    models.Image.owner_id == treatment.id,
                    models.Image.owner_type == 'treatment'
                )
            ).order_by(models.Image.position)
        )
        images = images_result.scalars().all()
        
        # Load FAQs within session
        faqs_result = await db.execute(
            select(models.FAQ).where(
                and_(
                    models.FAQ.owner_id == treatment.id,
                    models.FAQ.owner_type == 'treatment',
                    models.FAQ.is_active == True
                )
            ).order_by(models.FAQ.position)
        )
        faqs = faqs_result.scalars().all()
        
        treatment_dict = treatment_to_dict(treatment)
        treatment_dict['images'] = [
            {
                "id": img.id,
                "url": img.url,
                "is_primary": img.is_primary,
                "position": img.position,
                "uploaded_at": img.uploaded_at
            } for img in images
        ]
        treatment_dict['faqs'] = [
            {
                "id": faq.id,
                "owner_type": faq.owner_type,
                "owner_id": faq.owner_id,
                "question": faq.question,
                "answer": faq.answer,
                "position": faq.position,
                "is_active": faq.is_active,
                "created_at": faq.created_at,
                "updated_at": faq.updated_at
            } for faq in faqs
        ]
        treatment_dicts.append(treatment_dict)
    
    return treatment_dicts


@router.get("/treatments/{treatment_id}", response_model=schemas.TreatmentResponse)
async def get_treatment(treatment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Treatment).where(models.Treatment.id == treatment_id))
    treatment = result.scalar_one_or_none()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    # Load images for the treatment within the session
    images_result = await db.execute(
        select(models.Image).where(
            and_(
                models.Image.owner_id == treatment.id,
                models.Image.owner_type == 'treatment'
            )
        ).order_by(models.Image.position)
    )
    images = images_result.scalars().all()
    
    # Load FAQs for the treatment
    faqs_result = await db.execute(
        select(models.FAQ).where(
            and_(
                models.FAQ.owner_id == treatment.id,
                models.FAQ.owner_type == 'treatment',
                models.FAQ.is_active == True
            )
        ).order_by(models.FAQ.position)
    )
    faqs = faqs_result.scalars().all()
    
    treatment_dict = treatment_to_dict(treatment)
    treatment_dict['images'] = [
        {
            "id": img.id,
            "url": img.url,
            "is_primary": img.is_primary,
            "position": img.position,
            "uploaded_at": img.uploaded_at
        } for img in images
    ]
    treatment_dict['faqs'] = [
        {
            "id": faq.id,
            "owner_type": faq.owner_type,
            "owner_id": faq.owner_id,
            "question": faq.question,
            "answer": faq.answer,
            "position": faq.position,
            "is_active": faq.is_active,
            "created_at": faq.created_at,
            "updated_at": faq.updated_at
        } for faq in faqs
    ]
    
    return treatment_dict


@router.put("/treatments/{treatment_id}", response_model=schemas.TreatmentResponse)
async def update_treatment(
    treatment_id: int,
    treatment_update: schemas.TreatmentUpdate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Treatment).where(models.Treatment.id == treatment_id))
    treatment = result.scalar_one_or_none()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    update_data = treatment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(treatment, field, value)
    
    await db.commit()
    await db.refresh(treatment)
    return treatment_to_dict(treatment)


@router.delete("/treatments/{treatment_id}")
async def delete_treatment(
    treatment_id: int, 
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Treatment).where(models.Treatment.id == treatment_id))
    treatment = result.scalar_one_or_none()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    
    await db.delete(treatment)
    await db.commit()
    return {"message": "Treatment deleted"}


# Package Booking endpoints
@router.post(
    "/bookings", 
    response_model=schemas.PackageBookingResponse,
    summary="Create Booking with File Upload",
    description="""
    Create a new booking with optional medical file upload.
    
    **IMPORTANT:** This endpoint requires `multipart/form-data` for file uploads.
    For JSON-only requests (no files), use `/bookings/json` instead.
    
    **Content-Type:** multipart/form-data
    **Supported File Types:** PDF, JPG, PNG, TXT, DOC, DOCX
    **Max File Size:** 10MB
    
    **✅ Correct JavaScript Example:**
    ```javascript
    const formData = new FormData();
    formData.append('first_name', 'John');
    formData.append('last_name', 'Doe');
    formData.append('email', 'john@example.com');
    formData.append('mobile_no', '+1234567890');
    formData.append('treatment_id', '1'); // Optional
    formData.append('medical_history_file', fileInput.files[0]); // File object
    
    fetch('/api/v1/bookings', {
        method: 'POST',
        body: formData // NO Content-Type header needed
    });
    ```
    
    **❌ Wrong - Don't send JSON to this endpoint:**
    ```javascript
    // This will fail - use /bookings/json instead
    fetch('/api/v1/bookings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({...}) // This will fail
    });
    ```
    
    **Example using curl:**
    ```bash
    curl -X POST "http://localhost:8001/api/v1/bookings" \\
         -F "first_name=John" \\
         -F "last_name=Doe" \\
         -F "email=john@example.com" \\
         -F "mobile_no=+1234567890" \\
         -F "medical_history_file=@/path/to/medical_file.pdf"
    ```
    """,
    tags=["bookings", "file-upload"]
)
async def create_booking(
    first_name: str = Form(..., description="Patient's first name"),
    last_name: str = Form(..., description="Patient's last name"),
    email: str = Form(..., description="Patient's email address"),
    mobile_no: str = Form(..., description="Patient's mobile number"),
    treatment_id: Optional[int] = Form(None, description="Selected treatment ID (optional)"),
    budget: Optional[str] = Form(None, description="Budget range (e.g., '10k-20k')"),
    doctor_preference: Optional[str] = Form(None, description="Preferred doctor name"),
    hospital_preference: Optional[str] = Form(None, description="Preferred hospital name"),
    user_query: Optional[str] = Form(None, description="Additional queries or requirements"),
    travel_assistant: Optional[bool] = Form(False, description="Request travel assistance"),
    stay_assistant: Optional[bool] = Form(False, description="Request accommodation assistance"),
    personal_assistant: Optional[bool] = Form(False, description="Request personal assistant"),
    medical_history_file: Optional[UploadFile] = File(
        None, 
        description="📁 Upload medical history file (PDF, JPG, PNG, TXT, DOC, DOCX - Max 10MB)"
    ),
    db: AsyncSession = Depends(get_db)
):
    """Create a new booking with optional medical file upload"""
    
    medical_file_path = None
    
    # Handle medical file upload if provided
    if medical_history_file and medical_history_file.filename and medical_history_file.size > 0:
        # Validate file type
        allowed_types = {
            'application/pdf': 'pdf',
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/jpg': 'jpg',
            'text/plain': 'txt',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx'
        }
        
        # Check content type
        if medical_history_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type '{medical_history_file.content_type}' not allowed. Supported types: {', '.join(allowed_types.values())}"
            )
        
        # Check file size (max 10MB) using the size attribute first
        if medical_history_file.size and medical_history_file.size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File size too large. Maximum size is 10MB")
        
        # Read file content
        content = await medical_history_file.read()
        
        # Double-check file size after reading
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File size too large. Maximum size is 10MB")
        
        # Ensure we have actual content
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("media/medical")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = allowed_types[medical_history_file.content_type]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file using the already read content
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        medical_file_path = str(file_path)
        print(f"✅ File uploaded successfully: {medical_file_path} ({len(content)} bytes)")
    
    # Create booking object
    booking_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "mobile_no": mobile_no,
        "treatment_id": treatment_id,
        "budget": budget,
        "medical_history_file": medical_file_path,
        "doctor_preference": doctor_preference,
        "hospital_preference": hospital_preference,
        "user_query": user_query,
        "travel_assistant": travel_assistant,
        "stay_assistant": stay_assistant,
        "personal_assistant": personal_assistant
    }
    
    db_booking = models.PackageBooking(**booking_data)
    db.add(db_booking)
    await db.commit()
    await db.refresh(db_booking)
    return db_booking


@router.post(
    "/bookings/json", 
    response_model=schemas.PackageBookingResponse,
    summary="Create Booking (JSON Only)",
    description="""
    Create a new booking using JSON data (no file upload support).
    This is a fallback endpoint for legacy clients that send JSON.
    
    **Content-Type:** application/json
    
    **For new implementations, use `/bookings` with multipart/form-data for file upload support.**
    """,
    tags=["bookings", "json", "legacy"]
)
async def create_booking_json(
    booking: schemas.PackageBookingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new booking using JSON data (no file upload)"""
    
    # Convert Pydantic model to dict
    booking_data = booking.model_dump()
    
    # Create booking object
    db_booking = models.PackageBooking(**booking_data)
    db.add(db_booking)
    await db.commit()
    await db.refresh(db_booking)
    return db_booking


@router.get("/bookings", response_model=List[schemas.PackageBookingResponse])
async def get_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(models.PackageBooking)
    
    if service_type:
        query = query.where(models.PackageBooking.service_type == service_type)
    
    query = query.offset(skip).limit(limit).order_by(models.PackageBooking.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/bookings/{booking_id}", response_model=schemas.PackageBookingResponse)
async def get_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.PackageBooking).where(models.PackageBooking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.get("/bookings/{booking_id}/medical-file")
async def download_booking_medical_file(
    booking_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download medical file for a booking"""
    result = await db.execute(select(models.PackageBooking).where(models.PackageBooking.id == booking_id))
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if not booking.medical_history_file:
        raise HTTPException(status_code=404, detail="No medical file found for this booking")
    
    file_path = Path(booking.medical_history_file)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Medical file not found on server")
    
    # Get original filename or generate one
    filename = f"booking_{booking_id}_medical_file{file_path.suffix}"
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )


# Dropdown/Filter Data Endpoints
@router.get("/filters/locations", response_model=List[str])
async def get_locations(db: AsyncSession = Depends(get_db)):
    """Get all unique locations from hospitals, treatments, and doctors for dropdown"""
    # Get locations from hospitals
    hospital_result = await db.execute(
        select(models.Hospital.location).distinct().where(models.Hospital.location.isnot(None))
    )
    hospital_locations = hospital_result.scalars().all()
    
    # Get locations from treatments  
    treatment_result = await db.execute(
        select(models.Treatment.location).distinct().where(models.Treatment.location.isnot(None))
    )
    treatment_locations = treatment_result.scalars().all()
    
    # Get locations from doctors
    doctor_result = await db.execute(
        select(models.Doctor.location).distinct().where(models.Doctor.location.isnot(None))
    )
    doctor_locations = doctor_result.scalars().all()
    
    # Combine and clean locations
    all_locations = set()
    for location in hospital_locations + treatment_locations + doctor_locations:
        if location and location.strip():
            # Extract city name (everything before the first comma)
            city = location.split(',')[0].strip()
            if city:
                all_locations.add(city)
    
    return sorted(list(all_locations))


@router.get("/doctor-filters/locations", response_model=List[str])
async def get_doctor_locations(db: AsyncSession = Depends(get_db)):
    """Get all unique locations from doctors for dropdown"""
    # Get locations from doctors
    doctor_result = await db.execute(
        select(models.Doctor.location).distinct().where(models.Doctor.location.isnot(None))
    )
    doctor_locations = doctor_result.scalars().all()
    
    # Combine and clean locations
    all_locations = set()
    for location in doctor_locations:
        if location and location.strip():
            # Extract city name (everything before the first comma)
            city = location.split(',')[0].strip()
            if city:
                all_locations.add(city)
    
    return sorted(list(all_locations))

@router.get("/doctor-filters/locations", response_model=List[str])
async def get_doctor_locations(db: AsyncSession = Depends(get_db)):
    """Get all unique locations from doctors for dropdown"""
    # Get locations from doctors
    doctor_result = await db.execute(
        select(models.Doctor.location).distinct().where(models.Doctor.location.isnot(None))
    )
    doctor_locations = doctor_result.scalars().all()
    
    # Combine and clean locations
    all_locations = set()
    for location in doctor_locations:
        if location and location.strip():
            # Extract city name (everything before the first comma)
            city = location.split(',')[0].strip()
            if city:
                all_locations.add(city)
    
    return sorted(list(all_locations))


@router.get("/filters/treatment-types", response_model=List[str])
async def get_treatment_types(db: AsyncSession = Depends(get_db)):
    """Get all unique treatment types for dropdown (categories only, not individual treatment names)"""
    # Debug: Let's see what the raw query returns
    result = await db.execute(
        select(models.Treatment.treatment_type)
        .distinct()
        .where(models.Treatment.treatment_type.isnot(None))
        .where(models.Treatment.treatment_type != "")
    )
    treatment_types = result.scalars().all()
    
    # Debug logging (you can remove this later)
    print(f"Raw treatment_types from DB: {treatment_types}")
    
    # Filter out empty values, clean whitespace, and ensure uniqueness
    valid_types = set()
    for t in treatment_types:
        if t and t.strip():
            # Clean and standardize the type name
            clean_type = t.strip()
            valid_types.add(clean_type)
            print(f"Added clean_type: {clean_type}")
    
    final_result = sorted(list(valid_types))
    print(f"Final result: {final_result}")
    
    return final_result

@router.get("/debug/treatment-types")
async def debug_treatment_types(db: AsyncSession = Depends(get_db)):
    """Debug endpoint to see all treatment names and types"""
    result = await db.execute(
        select(models.Treatment.id, models.Treatment.name, models.Treatment.treatment_type)
        .order_by(models.Treatment.id)
    )
    treatments = result.all()
    
    return {
        "total_treatments": len(treatments),
        "treatments": [
            {
                "id": t.id,
                "name": t.name,
                "treatment_type": t.treatment_type
            } for t in treatments
        ],
        "unique_treatment_types": list(set([t.treatment_type for t in treatments if t.treatment_type])),
        "treatment_types_count": len(set([t.treatment_type for t in treatments if t.treatment_type]))
    }


@router.get("/filters/specializations", response_model=List[str])
async def get_specializations(db: AsyncSession = Depends(get_db)):
    """Get all unique specializations/skills from doctors for dropdown"""
    result = await db.execute(
        select(models.Doctor.specialization).distinct().where(models.Doctor.specialization.isnot(None))
    )
    skills_list = result.scalars().all()
    
    # Parse comma-separated skills and create unique list
    all_specializations = set()
    for skills in skills_list:
        if skills and skills.strip():
            # Split by comma and clean each skill
            for skill in skills.split(','):
                skill = skill.strip()
                if skill:
                    all_specializations.add(skill)
    
    return sorted(list(all_specializations))


# FAQ endpoints
@router.get("/faqs/{owner_type}/{owner_id}", response_model=List[schemas.FAQResponse])
async def get_faqs(
    owner_type: str,
    owner_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all FAQs for a specific entity (doctor, hospital, or treatment)"""
    if owner_type not in ["doctor", "hospital", "treatment"]:
        raise HTTPException(status_code=400, detail="Invalid owner_type. Must be 'doctor', 'hospital', or 'treatment'")
    
    result = await db.execute(
        select(models.FAQ)
        .where(models.FAQ.owner_type == owner_type)
        .where(models.FAQ.owner_id == owner_id)
        .where(models.FAQ.is_active == True)
        .order_by(models.FAQ.position)
    )
    return result.scalars().all()


@router.post("/faqs", response_model=schemas.FAQResponse)
async def create_faq(
    faq: schemas.FAQCreate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new FAQ"""
    if faq.owner_type not in ["doctor", "hospital", "treatment"]:
        raise HTTPException(status_code=400, detail="Invalid owner_type. Must be 'doctor', 'hospital', or 'treatment'")
    
    db_faq = models.FAQ(**faq.model_dump())
    db.add(db_faq)
    await db.commit()
    await db.refresh(db_faq)
    return db_faq


@router.put("/faqs/{faq_id}", response_model=schemas.FAQResponse)
async def update_faq(
    faq_id: int,
    faq_update: schemas.FAQUpdate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing FAQ"""
    result = await db.execute(select(models.FAQ).where(models.FAQ.id == faq_id))
    faq = result.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    update_data = faq_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(faq, field, value)
    
    await db.commit()
    await db.refresh(faq)
    return faq


@router.delete("/faqs/{faq_id}")
async def delete_faq(
    faq_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete an FAQ (soft delete by setting is_active=False)"""
    result = await db.execute(select(models.FAQ).where(models.FAQ.id == faq_id))
    faq = result.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    faq.is_active = False
    await db.commit()
    return {"message": "FAQ deleted successfully"}


# ================================
# IMAGE ENDPOINTS
# ================================

@router.post("/images", response_model=schemas.ImageResponse)
async def create_image(
    image: schemas.ImageCreate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new image record (admin only)"""
    db_image = models.Image(**image.model_dump())
    db.add(db_image)
    await db.commit()
    await db.refresh(db_image)
    return db_image


@router.get("/images", response_model=List[schemas.ImageResponse])
async def get_images(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    owner_type: Optional[str] = Query(None),
    owner_id: Optional[int] = Query(None),
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all images with filtering (admin only)"""
    query = select(models.Image)
    
    filters = []
    if owner_type:
        filters.append(models.Image.owner_type == owner_type)
    if owner_id:
        filters.append(models.Image.owner_id == owner_id)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(models.Image.position, models.Image.uploaded_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/images/{image_id}", response_model=schemas.ImageResponse)
async def get_image(
    image_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific image by ID (admin only)"""
    result = await db.execute(select(models.Image).where(models.Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.put("/images/{image_id}", response_model=schemas.ImageResponse)
async def update_image(
    image_id: int,
    image_update: schemas.ImageBase,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing image (admin only)"""
    result = await db.execute(select(models.Image).where(models.Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    update_data = image_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(image, field, value)
    
    await db.commit()
    await db.refresh(image)
    return image


@router.delete("/images/{image_id}")
async def delete_image(
    image_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete an image (admin only)"""
    result = await db.execute(select(models.Image).where(models.Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    await db.delete(image)
    await db.commit()
    return {"message": "Image deleted successfully"}


# Blog endpoints
@router.get("/blogs", response_model=List[schemas.BlogResponse])
async def get_blogs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    published_only: bool = Query(True),
    featured_only: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get all blogs with filtering and pagination"""
    query = select(models.Blog)
    
    filters = []
    if search:
        filters.append(or_(
            models.Blog.title.ilike(f"%{search}%"),
            models.Blog.content.ilike(f"%{search}%"),
            models.Blog.excerpt.ilike(f"%{search}%")
        ))
    if category:
        filters.append(models.Blog.category.ilike(f"%{category}%"))
    if tags:
        filters.append(models.Blog.tags.ilike(f"%{tags}%"))
    if published_only:
        filters.append(models.Blog.is_published == True)
    if featured_only:
        filters.append(models.Blog.is_featured == True)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(models.Blog.created_at.desc())
    
    result = await db.execute(query)
    blogs = result.scalars().all()
    
    # Load images for each blog within the session
    blog_dicts = []
    for blog in blogs:
        # Load images within session
        images_result = await db.execute(
            select(models.Image).where(
                and_(
                    models.Image.owner_id == blog.id,
                    models.Image.owner_type == 'blog'
                )
            ).order_by(models.Image.position)
        )
        images = images_result.scalars().all()
        
        blog_dict = blog_to_dict(blog)
        blog_dict['images'] = [
            {
                "id": img.id,
                "url": img.url,
                "is_primary": img.is_primary,
                "position": img.position,
                "uploaded_at": img.uploaded_at
            } for img in images
        ]
        blog_dicts.append(blog_dict)
    
    return blog_dicts


@router.get("/blogs/{blog_id}", response_model=schemas.BlogResponse)
async def get_blog(blog_id: int, db: AsyncSession = Depends(get_db)):
    """Get blog details by ID"""
    result = await db.execute(select(models.Blog).where(models.Blog.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Load images for the blog within the session
    images_result = await db.execute(
        select(models.Image).where(
            and_(
                models.Image.owner_id == blog.id,
                models.Image.owner_type == 'blog'
            )
        ).order_by(models.Image.position)
    )
    images = images_result.scalars().all()
    
    blog_dict = blog_to_dict(blog)
    blog_dict['images'] = [
        {
            "id": img.id,
            "url": img.url,
            "is_primary": img.is_primary,
            "position": img.position,
            "uploaded_at": img.uploaded_at
        } for img in images
    ]
    
    # Increment view count
    blog.view_count += 1
    await db.commit()
    blog_dict['view_count'] = blog.view_count
    
    return blog_dict


@router.get("/blogs/slug/{slug}", response_model=schemas.BlogResponse)
async def get_blog_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Get blog details by slug"""
    result = await db.execute(select(models.Blog).where(models.Blog.slug == slug))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Load images for the blog within the session
    images_result = await db.execute(
        select(models.Image).where(
            and_(
                models.Image.owner_id == blog.id,
                models.Image.owner_type == 'blog'
            )
        ).order_by(models.Image.position)
    )
    images = images_result.scalars().all()
    
    blog_dict = blog_to_dict(blog)
    blog_dict['images'] = [
        {
            "id": img.id,
            "url": img.url,
            "is_primary": img.is_primary,
            "position": img.position,
            "uploaded_at": img.uploaded_at
        } for img in images
    ]
    
    # Increment view count
    blog.view_count += 1
    await db.commit()
    blog_dict['view_count'] = blog.view_count
    
    return blog_dict


@router.post("/blogs", response_model=schemas.BlogResponse)
async def create_blog(
    blog: schemas.BlogCreate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new blog (admin only)"""
    # Generate unique slug from title
    import re
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', blog.title.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    
    # Ensure slug is unique
    base_slug = slug
    counter = 1
    while True:
        result = await db.execute(select(models.Blog).where(models.Blog.slug == slug))
        existing = result.scalar_one_or_none()
        if not existing:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    db_blog = models.Blog(**blog.model_dump(), slug=slug)
    db.add(db_blog)
    await db.commit()
    
    # Fetch fresh copy to get the generated ID without triggering relationships
    result = await db.execute(select(models.Blog).where(models.Blog.id == db_blog.id))
    fresh_blog = result.scalar_one()
    return blog_to_dict(fresh_blog)


@router.put("/blogs/{blog_id}", response_model=schemas.BlogResponse)
async def update_blog(
    blog_id: int,
    blog_update: schemas.BlogUpdate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing blog (admin only)"""
    result = await db.execute(select(models.Blog).where(models.Blog.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    update_data = blog_update.model_dump(exclude_unset=True)
    
    # If title is being updated, regenerate slug
    if 'title' in update_data:
        import re
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', update_data['title'].lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        
        # Ensure slug is unique (excluding current blog)
        base_slug = slug
        counter = 1
        while True:
            result = await db.execute(
                select(models.Blog).where(
                    and_(models.Blog.slug == slug, models.Blog.id != blog_id)
                )
            )
            existing = result.scalar_one_or_none()
            if not existing:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        update_data['slug'] = slug
    
    for field, value in update_data.items():
        setattr(blog, field, value)
    
    await db.commit()
    await db.refresh(blog)
    return blog_to_dict(blog)


@router.delete("/blogs/{blog_id}")
async def delete_blog(
    blog_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a blog (admin only)"""
    result = await db.execute(select(models.Blog).where(models.Blog.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    await db.delete(blog)
    await db.commit()
    return {"message": "Blog deleted successfully"}


# Blog filter endpoints
@router.get("/filters/blog-categories", response_model=List[str])
async def get_blog_categories(db: AsyncSession = Depends(get_db)):
    """Get all unique blog categories for dropdown"""
    result = await db.execute(
        select(models.Blog.category).distinct().where(models.Blog.category.isnot(None))
    )
    categories = result.scalars().all()
    
    # Filter out empty values and sort
    valid_categories = [c.strip() for c in categories if c and c.strip()]
    return sorted(valid_categories)


@router.get("/filters/blog-tags", response_model=List[str])
async def get_blog_tags(db: AsyncSession = Depends(get_db)):
    """Get all unique blog tags for dropdown"""
    result = await db.execute(
        select(models.Blog.tags).distinct().where(models.Blog.tags.isnot(None))
    )
    tags_list = result.scalars().all()
    
    # Parse comma-separated tags and create unique list
    all_tags = set()
    for tags in tags_list:
        if tags and tags.strip():
            # Split by comma and clean each tag
            for tag in tags.split(','):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)
    
    return sorted(list(all_tags))


# ================================
# BANNER ENDPOINTS
# ================================

@router.post("/banners", response_model=schemas.BannerResponse)
async def create_banner(
    banner: schemas.BannerCreate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new banner (admin only)"""
    db_banner = models.Banner(**banner.model_dump())
    db.add(db_banner)
    await db.commit()
    await db.refresh(db_banner)
    return db_banner


@router.get("/banners", response_model=List[schemas.BannerResponse])
async def get_banners(
    active_only: bool = Query(True, description="Get only active banners"),
    db: AsyncSession = Depends(get_db)
):
    """Get all banners for frontend display"""
    query = select(models.Banner).order_by(models.Banner.position, models.Banner.created_at.desc())
    
    if active_only:
        query = query.where(models.Banner.is_active == True)
    
    result = await db.execute(query)
    banners = result.scalars().all()
    
    return banners


@router.get("/banners/{banner_id}", response_model=schemas.BannerResponse)
async def get_banner(banner_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific banner by ID"""
    result = await db.execute(select(models.Banner).where(models.Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    return banner


@router.put("/banners/{banner_id}", response_model=schemas.BannerResponse)
async def update_banner(
    banner_id: int,
    banner_update: schemas.BannerUpdate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing banner (admin only)"""
    result = await db.execute(select(models.Banner).where(models.Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    update_data = banner_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(banner, field, value)
    
    await db.commit()
    await db.refresh(banner)
    return banner


@router.delete("/banners/{banner_id}")
async def delete_banner(
    banner_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a banner (admin only)"""
    result = await db.execute(select(models.Banner).where(models.Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    await db.delete(banner)
    await db.commit()
    return {"message": "Banner deleted successfully"}


# ================================
# PARTNER HOSPITAL ENDPOINTS
# ================================

@router.post("/partners", response_model=schemas.PartnerHospitalResponse)
async def create_partner(
    partner: schemas.PartnerHospitalCreate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new partner hospital (admin only)"""
    db_partner = models.PartnerHospital(**partner.model_dump())
    db.add(db_partner)
    await db.commit()
    await db.refresh(db_partner)
    return db_partner


@router.get("/partners", response_model=List[schemas.PartnerHospitalResponse])
async def get_partners(
    active_only: bool = Query(True, description="Get only active partners"),
    db: AsyncSession = Depends(get_db)
):
    """Get all partner hospitals for frontend display"""
    query = select(models.PartnerHospital).order_by(models.PartnerHospital.position, models.PartnerHospital.created_at.desc())
    
    if active_only:
        query = query.where(models.PartnerHospital.is_active == True)
    
    result = await db.execute(query)
    partners = result.scalars().all()
    
    return partners


@router.get("/partners/{partner_id}", response_model=schemas.PartnerHospitalResponse)
async def get_partner(partner_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific partner hospital by ID"""
    result = await db.execute(select(models.PartnerHospital).where(models.PartnerHospital.id == partner_id))
    partner = result.scalar_one_or_none()
    
    if not partner:
        raise HTTPException(status_code=404, detail="Partner hospital not found")
    
    return partner


@router.put("/partners/{partner_id}", response_model=schemas.PartnerHospitalResponse)
async def update_partner(
    partner_id: int,
    partner_update: schemas.PartnerHospitalUpdate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing partner hospital (admin only)"""
    result = await db.execute(select(models.PartnerHospital).where(models.PartnerHospital.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner hospital not found")
    
    update_data = partner_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(partner, field, value)
    
    await db.commit()
    await db.refresh(partner)
    return partner


@router.delete("/partners/{partner_id}")
async def delete_partner(
    partner_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a partner hospital (admin only)"""
    result = await db.execute(select(models.PartnerHospital).where(models.PartnerHospital.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner hospital not found")
    
    await db.delete(partner)
    await db.commit()
    return {"message": "Partner hospital deleted successfully"}


# ================================
# PATIENT STORY ENDPOINTS
# ================================

@router.post("/stories", response_model=schemas.PatientStoryResponse)
async def create_patient_story(
    story: schemas.PatientStoryCreate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new patient story (admin only)"""
    db_story = models.PatientStory(**story.model_dump())
    db.add(db_story)
    await db.commit()
    await db.refresh(db_story)
    return db_story


@router.get("/stories", response_model=List[schemas.PatientStoryResponse])
async def get_patient_stories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True, description="Get only active stories"),
    featured_only: bool = Query(False, description="Get only featured stories"),
    treatment_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get patient stories for frontend display"""
    query = select(models.PatientStory)
    
    filters = []
    if active_only:
        filters.append(models.PatientStory.is_active == True)
    if featured_only:
        filters.append(models.PatientStory.is_featured == True)
    if treatment_type:
        filters.append(models.PatientStory.treatment_type.ilike(f"%{treatment_type}%"))
    if location:
        filters.append(models.PatientStory.location.ilike(f"%{location}%"))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(models.PatientStory.position, models.PatientStory.created_at.desc())
    
    result = await db.execute(query)
    stories = result.scalars().all()
    
    return stories


@router.get("/stories/{story_id}", response_model=schemas.PatientStoryResponse)
async def get_patient_story(story_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific patient story by ID"""
    result = await db.execute(select(models.PatientStory).where(models.PatientStory.id == story_id))
    story = result.scalar_one_or_none()
    
    if not story:
        raise HTTPException(status_code=404, detail="Patient story not found")
    
    return story


@router.put("/stories/{story_id}", response_model=schemas.PatientStoryResponse)
async def update_patient_story(
    story_id: int,
    story_update: schemas.PatientStoryUpdate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing patient story (admin only)"""
    result = await db.execute(select(models.PatientStory).where(models.PatientStory.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Patient story not found")
    
    update_data = story_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(story, field, value)
    
    await db.commit()
    await db.refresh(story)
    return story


@router.delete("/stories/{story_id}")
async def delete_patient_story(
    story_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a patient story (admin only)"""
    result = await db.execute(select(models.PatientStory).where(models.PatientStory.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Patient story not found")
    
    await db.delete(story)
    await db.commit()
    return {"message": "Patient story deleted successfully"}


@router.get("/stories/featured", response_model=List[schemas.PatientStoryResponse])
async def get_featured_stories(
    limit: int = Query(5, ge=1, le=20, description="Number of featured stories to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get featured patient stories for homepage/highlights"""
    query = select(models.PatientStory).where(
        and_(
            models.PatientStory.is_active == True,
            models.PatientStory.is_featured == True
        )
    ).order_by(models.PatientStory.position, models.PatientStory.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    stories = result.scalars().all()
    
    return stories


# ================================
# CONTACT US ENDPOINTS
# ================================

@router.post("/contact", response_model=schemas.ContactUsResponse)
async def create_contact(
    contact: schemas.ContactUsCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new contact us message"""
    db_contact = models.ContactUs(**contact.model_dump())
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    return db_contact


@router.get("/contacts", response_model=List[schemas.ContactUsResponse])
async def get_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service_type: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all contact messages (admin only)"""
    query = select(models.ContactUs)
    
    filters = []
    if service_type:
        filters.append(models.ContactUs.service_type == service_type)
    if is_read is not None:
        filters.append(models.ContactUs.is_read == is_read)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(models.ContactUs.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/contacts/{contact_id}", response_model=schemas.ContactUsResponse)
async def get_contact(
    contact_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific contact message by ID (admin only)"""
    result = await db.execute(select(models.ContactUs).where(models.ContactUs.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact message not found")
    return contact


@router.put("/contacts/{contact_id}", response_model=schemas.ContactUsResponse)
async def update_contact(
    contact_id: int,
    contact_update: schemas.ContactUsUpdate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a contact message (admin only) - mark as read or add response"""
    from datetime import datetime
    
    result = await db.execute(select(models.ContactUs).where(models.ContactUs.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact message not found")
    
    update_data = contact_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
    
    # Set responded_at timestamp if admin_response is provided
    if 'admin_response' in update_data and update_data['admin_response']:
        contact.responded_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a contact message (admin only)"""
    result = await db.execute(select(models.ContactUs).where(models.ContactUs.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact message not found")
    
    await db.delete(contact)
    await db.commit()
    return {"message": "Contact message deleted successfully"}


# ================================
# OFFER ENDPOINTS
# ================================

@router.post("/offers", response_model=schemas.OfferResponse)
async def create_offer(
    offer: schemas.OfferCreate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new offer (admin only)"""
    db_offer = models.Offer(**offer.model_dump())
    db.add(db_offer)
    await db.commit()
    await db.refresh(db_offer)
    return db_offer


@router.get("/offers", response_model=List[schemas.OfferResponse])
async def get_offers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    current_only: bool = Query(False, description="Get only currently active offers"),
    treatment_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all offers with filtering"""
    from datetime import datetime
    
    query = select(models.Offer)
    
    filters = []
    if active_only:
        filters.append(models.Offer.is_active == True)
    if current_only:
        now = datetime.utcnow()
        filters.append(and_(
            models.Offer.start_date <= now,
            models.Offer.end_date >= now,
            models.Offer.is_active == True
        ))
    if treatment_type:
        filters.append(models.Offer.treatment_type.ilike(f"%{treatment_type}%"))
    if location:
        filters.append(models.Offer.location.ilike(f"%{location}%"))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(models.Offer.start_date.desc())
    
    result = await db.execute(query)
    offers = result.scalars().all()
    
    # Load images for each offer within the session
    offer_results = []
    for offer in offers:
        images_result = await db.execute(
            select(models.Image).where(
                and_(
                    models.Image.owner_id == offer.id,
                    models.Image.owner_type == 'offer'
                )
            ).order_by(models.Image.position)
        )
        images = images_result.scalars().all()
        
        offer_dict = {
            "id": offer.id,
            "name": offer.name,
            "description": offer.description,
            "treatment_type": offer.treatment_type,
            "location": offer.location,
            "start_date": offer.start_date,
            "end_date": offer.end_date,
            "discount_percentage": offer.discount_percentage,
            "is_free_camp": offer.is_free_camp,
            "treatment_id": offer.treatment_id,
            "is_active": offer.is_active,
            "created_at": offer.created_at,
            "updated_at": offer.updated_at,
            "images": [
                {
                    "id": img.id,
                    "url": img.url,
                    "is_primary": img.is_primary,
                    "position": img.position,
                    "uploaded_at": img.uploaded_at
                } for img in images
            ]
        }
        offer_results.append(offer_dict)
    
    return offer_results


@router.get("/offers/{offer_id}", response_model=schemas.OfferResponse)
async def get_offer(offer_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific offer by ID"""
    result = await db.execute(select(models.Offer).where(models.Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Load images for the offer within the session
    images_result = await db.execute(
        select(models.Image).where(
            and_(
                models.Image.owner_id == offer.id,
                models.Image.owner_type == 'offer'
            )
        ).order_by(models.Image.position)
    )
    images = images_result.scalars().all()
    
    return {
        "id": offer.id,
        "name": offer.name,
        "description": offer.description,
        "treatment_type": offer.treatment_type,
        "location": offer.location,
        "start_date": offer.start_date,
        "end_date": offer.end_date,
        "discount_percentage": offer.discount_percentage,
        "is_free_camp": offer.is_free_camp,
        "treatment_id": offer.treatment_id,
        "is_active": offer.is_active,
        "created_at": offer.created_at,
        "updated_at": offer.updated_at,
        "images": [
            {
                "id": img.id,
                "url": img.url,
                "is_primary": img.is_primary,
                "position": img.position,
                "uploaded_at": img.uploaded_at
            } for img in images
        ]
    }


@router.put("/offers/{offer_id}", response_model=schemas.OfferResponse)
async def update_offer(
    offer_id: int,
    offer_update: schemas.OfferUpdate,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing offer (admin only)"""
    result = await db.execute(select(models.Offer).where(models.Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    update_data = offer_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(offer, field, value)
    
    await db.commit()
    await db.refresh(offer)
    return offer


@router.delete("/offers/{offer_id}")
async def delete_offer(
    offer_id: int,
    current_admin: models.Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete an offer (admin only)"""
    result = await db.execute(select(models.Offer).where(models.Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    await db.delete(offer)
    await db.commit()
    return {"message": "Offer deleted successfully"}


# ================================
# FILTER ENDPOINTS FOR NEW MODELS
# ================================

@router.get("/filters/treatment-types", response_model=List[str])
async def get_treatment_types(db: AsyncSession = Depends(get_db)):
    """Get all unique treatment types from patient stories"""
    result = await db.execute(
        select(models.PatientStory.treatment_type).distinct().where(
            and_(
                models.PatientStory.treatment_type.isnot(None),
                models.PatientStory.is_active == True
            )
        )
    )
    treatment_types = result.scalars().all()
    
    # Filter out empty values and sort
    valid_types = [t.strip() for t in treatment_types if t and t.strip()]
    return sorted(valid_types)


@router.get("/filters/story-hospitals", response_model=List[str])
async def get_story_hospitals(db: AsyncSession = Depends(get_db)):
    """Get all unique hospital names from patient stories"""
    result = await db.execute(
        select(models.PatientStory.hospital_name).distinct().where(
            and_(
                models.PatientStory.hospital_name.isnot(None),
                models.PatientStory.is_active == True
            )
        )
    )
    hospitals = result.scalars().all()
    
    # Filter out empty values and sort
    valid_hospitals = [h.strip() for h in hospitals if h and h.strip()]
    return sorted(valid_hospitals)


@router.get("/filters/offer-locations", response_model=List[str])
async def get_offer_locations(db: AsyncSession = Depends(get_db)):
    """Get all unique locations from offers"""
    result = await db.execute(
        select(models.Offer.location).distinct().where(
            and_(
                models.Offer.location.isnot(None),
                models.Offer.is_active == True
            )
        )
    )
    locations = result.scalars().all()
    
    # Filter out empty values and sort
    valid_locations = [l.strip() for l in locations if l and l.strip()]
    return sorted(valid_locations)


@router.get("/filters/offer-treatment-types", response_model=List[str])
async def get_offer_treatment_types(db: AsyncSession = Depends(get_db)):
    """Get all unique treatment types from offers"""
    result = await db.execute(
        select(models.Offer.treatment_type).distinct().where(
            and_(
                models.Offer.treatment_type.isnot(None),
                models.Offer.is_active == True
            )
        )
    )
    treatment_types = result.scalars().all()
    
    # Filter out empty values and sort
    valid_types = [t.strip() for t in treatment_types if t and t.strip()]
    return sorted(valid_types)


@router.get("/filters/treatment-features", response_model=List[str])
async def get_treatment_features(db: AsyncSession = Depends(get_db)):
    """Get all unique features from treatments"""
    result = await db.execute(
        select(models.Treatment.features).distinct().where(models.Treatment.features.isnot(None))
    )
    features_list = result.scalars().all()
    
    # Parse comma-separated features and create unique list
    all_features = set()
    for features in features_list:
        if features and features.strip():
            feature_items = [f.strip() for f in features.split(",") if f.strip()]
            all_features.update(feature_items)
    
    return sorted(list(all_features))