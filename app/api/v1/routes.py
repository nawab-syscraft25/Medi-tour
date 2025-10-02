from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from app.db import get_db
from app import models, schemas
from app.dependencies import get_current_admin


def hospital_to_dict(hospital: models.Hospital) -> dict:
    """Convert Hospital model to dict for safe serialization"""
    return {
        "id": hospital.id,
        "name": hospital.name,
        "description": hospital.description,
        "location": hospital.location,
        "phone": hospital.phone,
        "features": hospital.features,
        "facilities": hospital.facilities,
        "rating": hospital.rating,
        "created_at": hospital.created_at,
        "images": []  # Will be populated separately
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
        "created_at": doctor.created_at,
        "images": []  # Will be populated separately
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
        "other_doctor_name": treatment.other_doctor_name,
        "location": treatment.location,
        "rating": treatment.rating,
        "created_at": treatment.created_at,
        "images": []  # Will be populated separately
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
    
    # Load images for each hospital within the session
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
    
    # Load images for each doctor within the session
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
        doctor_dicts.append(doctor_dict)
    
    return doctor_dicts


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
            models.Treatment.long_description.ilike(f"%{search}%")
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
    
    # Load images for each treatment within the session
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
@router.post("/bookings", response_model=schemas.PackageBookingResponse)
async def create_booking(
    booking: schemas.PackageBookingCreate,
    db: AsyncSession = Depends(get_db)
):
    db_booking = models.PackageBooking(**booking.model_dump())
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
    """Get all unique treatment types for dropdown"""
    result = await db.execute(
        select(models.Treatment.treatment_type).distinct().where(models.Treatment.treatment_type.isnot(None))
    )
    treatment_types = result.scalars().all()
    
    # Filter out empty values and sort
    valid_types = [t.strip() for t in treatment_types if t and t.strip()]
    return sorted(valid_types)


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

@router.get("/banners", response_model=List[dict])
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
    
    return [
        {
            "id": banner.id,
            "name": banner.name,
            "title": banner.title,
            "subtitle": banner.subtitle,
            "description": banner.description,
            "image_url": banner.image_url,
            "link_url": banner.link_url,
            "button_text": banner.button_text,
            "position": banner.position,
            "is_active": banner.is_active,
            "created_at": banner.created_at
        }
        for banner in banners
    ]


@router.get("/banners/{banner_id}", response_model=dict)
async def get_banner(banner_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific banner by ID"""
    result = await db.execute(select(models.Banner).where(models.Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    return {
        "id": banner.id,
        "name": banner.name,
        "title": banner.title,
        "subtitle": banner.subtitle,
        "description": banner.description,
        "image_url": banner.image_url,
        "link_url": banner.link_url,
        "button_text": banner.button_text,
        "position": banner.position,
        "is_active": banner.is_active,
        "created_at": banner.created_at
    }


# ================================
# PARTNER HOSPITAL ENDPOINTS
# ================================

@router.get("/partners", response_model=List[dict])
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
    
    return [
        {
            "id": partner.id,
            "name": partner.name,
            "description": partner.description,
            "logo_url": partner.logo_url,
            "website_url": partner.website_url,
            "location": partner.location,
            "position": partner.position,
            "is_active": partner.is_active,
            "created_at": partner.created_at
        }
        for partner in partners
    ]


@router.get("/partners/{partner_id}", response_model=dict)
async def get_partner(partner_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific partner hospital by ID"""
    result = await db.execute(select(models.PartnerHospital).where(models.PartnerHospital.id == partner_id))
    partner = result.scalar_one_or_none()
    
    if not partner:
        raise HTTPException(status_code=404, detail="Partner hospital not found")
    
    return {
        "id": partner.id,
        "name": partner.name,
        "description": partner.description,
        "logo_url": partner.logo_url,
        "website_url": partner.website_url,
        "location": partner.location,
        "position": partner.position,
        "is_active": partner.is_active,
        "created_at": partner.created_at
    }


# ================================
# PATIENT STORY ENDPOINTS
# ================================

@router.get("/stories", response_model=List[dict])
async def get_patient_stories(
    active_only: bool = Query(True, description="Get only active stories"),
    featured_only: bool = Query(False, description="Get only featured stories"),
    limit: int = Query(10, ge=1, le=50, description="Number of stories to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get patient stories for frontend display"""
    query = select(models.PatientStory).order_by(models.PatientStory.position, models.PatientStory.created_at.desc())
    
    if active_only:
        query = query.where(models.PatientStory.is_active == True)
    
    if featured_only:
        query = query.where(models.PatientStory.is_featured == True)
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    stories = result.scalars().all()
    
    return [
        {
            "id": story.id,
            "patient_name": story.patient_name,
            "description": story.description,
            "rating": story.rating,
            "profile_photo": story.profile_photo,
            "treatment_type": story.treatment_type,
            "hospital_name": story.hospital_name,
            "location": story.location,
            "position": story.position,
            "is_featured": story.is_featured,
            "is_active": story.is_active,
            "created_at": story.created_at
        }
        for story in stories
    ]


@router.get("/stories/{story_id}", response_model=dict)
async def get_patient_story(story_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific patient story by ID"""
    result = await db.execute(select(models.PatientStory).where(models.PatientStory.id == story_id))
    story = result.scalar_one_or_none()
    
    if not story:
        raise HTTPException(status_code=404, detail="Patient story not found")
    
    return {
        "id": story.id,
        "patient_name": story.patient_name,
        "description": story.description,
        "rating": story.rating,
        "profile_photo": story.profile_photo,
        "treatment_type": story.treatment_type,
        "hospital_name": story.hospital_name,
        "location": story.location,
        "position": story.position,
        "is_featured": story.is_featured,
        "is_active": story.is_active,
        "created_at": story.created_at
    }


@router.get("/stories/featured", response_model=List[dict])
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
    
    return [
        {
            "id": story.id,
            "patient_name": story.patient_name,
            "description": story.description,
            "rating": story.rating,
            "profile_photo": story.profile_photo,
            "treatment_type": story.treatment_type,
            "hospital_name": story.hospital_name,
            "location": story.location,
            "position": story.position,
            "is_featured": story.is_featured,
            "is_active": story.is_active,
            "created_at": story.created_at
        }
        for story in stories
    ]


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