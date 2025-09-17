from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator


# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# Image schemas
class ImageBase(BaseModel):
    owner_type: str
    owner_id: int
    url: str
    is_primary: bool = False
    position: Optional[int] = None


class ImageCreate(ImageBase):
    pass


class ImageResponse(ImageBase, BaseSchema):
    id: int
    uploaded_at: datetime


# Slider schemas
class SliderBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link: Optional[str] = None
    tags: Optional[str] = None  # comma-separated
    is_active: bool = True


class SliderCreate(SliderBase):
    pass


class SliderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link: Optional[str] = None
    tags: Optional[str] = None
    is_active: Optional[bool] = None


class SliderResponse(SliderBase, BaseSchema):
    id: int
    created_at: datetime
    
    @property
    def tags_list(self) -> List[str]:
        return [tag.strip() for tag in (self.tags or "").split(",") if tag.strip()]


# Hospital schemas
class HospitalBase(BaseModel):
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    features: Optional[str] = None  # comma-separated
    facilities: Optional[str] = None  # comma-separated


class HospitalCreate(HospitalBase):
    pass


class HospitalUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    features: Optional[str] = None
    facilities: Optional[str] = None


class HospitalResponse(HospitalBase, BaseSchema):
    id: int
    created_at: datetime
    
    @property
    def features_list(self) -> List[str]:
        return [f.strip() for f in (self.features or "").split(",") if f.strip()]
    
    @property
    def facilities_list(self) -> List[str]:
        return [f.strip() for f in (self.facilities or "").split(",") if f.strip()]


# Doctor schemas
class DoctorBase(BaseModel):
    name: str
    profile_photo: Optional[str] = None
    description: Optional[str] = None
    designation: Optional[str] = None
    experience_years: Optional[int] = None
    hospital_id: Optional[int] = None
    gender: Optional[str] = None
    skills: Optional[str] = None  # comma-separated
    qualifications: Optional[str] = None
    highlights: Optional[str] = None
    awards: Optional[str] = None


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    profile_photo: Optional[str] = None
    description: Optional[str] = None
    designation: Optional[str] = None
    experience_years: Optional[int] = None
    hospital_id: Optional[int] = None
    gender: Optional[str] = None
    skills: Optional[str] = None
    qualifications: Optional[str] = None
    highlights: Optional[str] = None
    awards: Optional[str] = None


class DoctorResponse(DoctorBase, BaseSchema):
    id: int
    created_at: datetime
    hospital: Optional["HospitalResponse"] = None
    
    @property
    def skills_list(self) -> List[str]:
        return [s.strip() for s in (self.skills or "").split(",") if s.strip()]


# Treatment schemas
class TreatmentBase(BaseModel):
    name: str
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    treatment_type: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_exact: Optional[float] = None
    hospital_id: Optional[int] = None
    other_hospital_name: Optional[str] = None
    doctor_id: Optional[int] = None
    other_doctor_name: Optional[str] = None
    location: Optional[str] = None


class TreatmentCreate(TreatmentBase):
    pass


class TreatmentUpdate(BaseModel):
    name: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    treatment_type: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_exact: Optional[float] = None
    hospital_id: Optional[int] = None
    other_hospital_name: Optional[str] = None
    doctor_id: Optional[int] = None
    other_doctor_name: Optional[str] = None
    location: Optional[str] = None


class TreatmentResponse(TreatmentBase, BaseSchema):
    id: int
    created_at: datetime
    hospital: Optional["HospitalResponse"] = None
    doctor: Optional["DoctorResponse"] = None


# Package Booking schemas
class PackageBookingBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    service_type: Optional[str] = None  # "hospital","doctor","treatment","other"
    service_ref: Optional[str] = None
    budget_range: Optional[str] = None
    medical_history_file: Optional[str] = None
    user_query: Optional[str] = None
    travel_assistant: bool = False
    stay_assistant: bool = False


class PackageBookingCreate(PackageBookingBase):
    pass


class PackageBookingResponse(PackageBookingBase, BaseSchema):
    id: int
    created_at: datetime


# Appointment schemas
class AppointmentBase(BaseModel):
    patient_name: Optional[str] = None
    patient_contact: Optional[str] = None
    doctor_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    status: str = "scheduled"


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    patient_name: Optional[str] = None
    patient_contact: Optional[str] = None
    doctor_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class AppointmentResponse(AppointmentBase, BaseSchema):
    id: int
    created_at: datetime
    doctor: Optional["DoctorResponse"] = None


# Upload schemas
class PresignedUploadRequest(BaseModel):
    owner_type: str
    owner_id: int
    filename: str


class PresignedUploadResponse(BaseModel):
    upload_url: str
    fields: dict
    key: str


class UploadNotifyRequest(BaseModel):
    owner_type: str
    owner_id: int
    key: str
    is_primary: bool = False


# Update forward references
DoctorResponse.model_rebuild()
HospitalResponse.model_rebuild()
TreatmentResponse.model_rebuild()
AppointmentResponse.model_rebuild()