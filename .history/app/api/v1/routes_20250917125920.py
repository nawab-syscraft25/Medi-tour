from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from app.db import get_db
from app import models, schemas


def doctor_to_dict(doctor: models.Doctor) -> dict:
    """Convert Doctor model to dict for safe serialization"""
    return {
        "id": doctor.id,
        "name": doctor.name,
        "profile_photo": doctor.profile_photo,
        "description": doctor.description,
        "designation": doctor.designation,
        "experience_years": doctor.experience_years,
        "hospital_id": doctor.hospital_id,
        "gender": doctor.gender,
        "skills": doctor.skills,
        "qualifications": doctor.qualifications,
        "highlights": doctor.highlights,
        "awards": doctor.awards,
        "created_at": doctor.created_at,
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
        "created_at": treatment.created_at,
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
    db: AsyncSession = Depends(get_db)
):
    db_hospital = models.Hospital(**hospital.model_dump())
    db.add(db_hospital)
    await db.commit()
    await db.refresh(db_hospital)
    return db_hospital


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
    return result.scalars().all()


@router.get("/hospitals/{hospital_id}", response_model=schemas.HospitalResponse)
async def get_hospital(hospital_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Hospital).where(models.Hospital.id == hospital_id))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital


@router.put("/hospitals/{hospital_id}", response_model=schemas.HospitalResponse)
async def update_hospital(
    hospital_id: int,
    hospital_update: schemas.HospitalUpdate,
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
    return hospital


@router.delete("/hospitals/{hospital_id}")
async def delete_hospital(hospital_id: int, db: AsyncSession = Depends(get_db)):
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
    db: AsyncSession = Depends(get_db)
):
    query = select(models.Doctor)
    
    filters = []
    if search:
        filters.append(or_(
            models.Doctor.name.ilike(f"%{search}%"),
            models.Doctor.designation.ilike(f"%{search}%"),
            models.Doctor.description.ilike(f"%{search}%")
        ))
    if hospital_id:
        filters.append(models.Doctor.hospital_id == hospital_id)
    if specialization:
        filters.append(models.Doctor.skills.ilike(f"%{specialization}%"))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.offset(skip).limit(limit).order_by(models.Doctor.created_at.desc())
    
    result = await db.execute(query)
    doctors = result.scalars().all()
    return [doctor_to_dict(doctor) for doctor in doctors]


@router.get("/doctors/{doctor_id}", response_model=schemas.DoctorResponse)
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Doctor).where(models.Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor_to_dict(doctor)


@router.put("/doctors/{doctor_id}", response_model=schemas.DoctorResponse)
async def update_doctor(
    doctor_id: int,
    doctor_update: schemas.DoctorUpdate,
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
async def delete_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
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
    db: AsyncSession = Depends(get_db)
):
    db_treatment = models.Treatment(**treatment.model_dump())
    db.add(db_treatment)
    await db.commit()
    await db.refresh(db_treatment)
    return treatment_to_dict(db_treatment)


@router.get("/treatments", response_model=List[schemas.TreatmentResponse])
async def get_treatments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
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
    if treatment_type:
        filters.append(models.Treatment.treatment_type == treatment_type)
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
    return [treatment_to_dict(treatment) for treatment in treatments]


@router.get("/treatments/{treatment_id}", response_model=schemas.TreatmentResponse)
async def get_treatment(treatment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Treatment).where(models.Treatment.id == treatment_id))
    treatment = result.scalar_one_or_none()
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found")
    return treatment_to_dict(treatment)


@router.put("/treatments/{treatment_id}", response_model=schemas.TreatmentResponse)
async def update_treatment(
    treatment_id: int,
    treatment_update: schemas.TreatmentUpdate,
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
async def delete_treatment(treatment_id: int, db: AsyncSession = Depends(get_db)):
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