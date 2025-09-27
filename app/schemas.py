from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator, ConfigDict


# Base schemas
class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore'  # Ignore extra attributes from SQLAlchemy models
    )


# Image schemas
class ImageBase(BaseModel):
    url: str
    is_primary: bool = False
    position: Optional[int] = None


class ImageCreate(BaseModel):
    owner_type: str
    owner_id: int
    url: str
    is_primary: bool = False
    position: Optional[int] = None


class ImageResponse(BaseSchema):
    id: int
    owner_type: Optional[str] = None
    owner_id: Optional[int] = None
    url: str
    is_primary: bool = False
    position: Optional[int] = None
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
    rating: Optional[float] = None
    features: Optional[str] = None  # comma-separated
    facilities: Optional[str] = None  # comma-separated
    
    @validator('rating', pre=True, always=True)
    def validate_rating(cls, v):
        if v is not None and v != "":
            try:
                v = float(v)
                if v < 1 or v > 5:
                    raise ValueError('Rating must be between 1 and 5')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Rating must be a valid number')
        return None


class HospitalCreate(HospitalBase):
    pass


class HospitalUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[float] = None
    features: Optional[str] = None
    facilities: Optional[str] = None
    
    @validator('rating', pre=True, always=True)
    def validate_rating(cls, v):
        if v is not None and v != "":
            try:
                v = float(v)
                if v < 1 or v > 5:
                    raise ValueError('Rating must be between 1 and 5')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Rating must be a valid number')
        return None


class HospitalResponse(HospitalBase, BaseSchema):
    id: int
    created_at: datetime
    images: List[ImageResponse] = []
    
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
    rating: Optional[float] = None
    hospital_id: Optional[int] = None
    gender: Optional[str] = None
    skills: Optional[str] = None  # comma-separated
    qualifications: Optional[str] = None
    highlights: Optional[str] = None
    awards: Optional[str] = None
    
    @validator('experience_years', pre=True, always=True)
    def validate_experience_years(cls, v):
        if v is not None and v != "":
            try:
                v = int(v)
                if v < 0:
                    raise ValueError('Experience years must be a positive number')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Experience years must be a valid number')
        return None
    
    @validator('rating', pre=True, always=True)
    def validate_rating(cls, v):
        if v is not None and v != "":
            try:
                v = float(v)
                if v < 1 or v > 5:
                    raise ValueError('Rating must be between 1 and 5')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Rating must be a valid number')
        return None


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    profile_photo: Optional[str] = None
    description: Optional[str] = None
    designation: Optional[str] = None
    experience_years: Optional[int] = None
    rating: Optional[float] = None
    hospital_id: Optional[int] = None
    gender: Optional[str] = None
    skills: Optional[str] = None
    qualifications: Optional[str] = None
    highlights: Optional[str] = None
    awards: Optional[str] = None
    
    @validator('experience_years', pre=True, always=True)
    def validate_experience_years(cls, v):
        if v is not None and v != "":
            try:
                v = int(v)
                if v < 0:
                    raise ValueError('Experience years must be a positive number')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Experience years must be a valid number')
        return None
    
    @validator('rating', pre=True, always=True)
    def validate_rating(cls, v):
        if v is not None and v != "":
            try:
                v = float(v)
                if v < 1 or v > 5:
                    raise ValueError('Rating must be between 1 and 5')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Rating must be a valid number')
        return None


class DoctorResponse(BaseSchema):
    id: int
    name: str
    profile_photo: Optional[str] = None
    description: Optional[str] = None
    designation: Optional[str] = None
    experience_years: Optional[int] = None
    rating: Optional[float] = None
    hospital_id: Optional[int] = None
    gender: Optional[str] = None
    skills: Optional[str] = None
    qualifications: Optional[str] = None
    highlights: Optional[str] = None
    awards: Optional[str] = None
    created_at: datetime
    images: List[ImageResponse] = []
    
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
    rating: Optional[float] = None
    hospital_id: Optional[int] = None
    other_hospital_name: Optional[str] = None
    doctor_id: Optional[int] = None
    other_doctor_name: Optional[str] = None
    location: Optional[str] = None
    
    @validator('price_min', 'price_max', 'price_exact', pre=True, always=True)
    def validate_prices(cls, v):
        if v is not None and v != "":
            try:
                v = float(v)
                if v < 0:
                    raise ValueError('Price must be a positive number')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Price must be a valid number')
        return None
    
    @validator('rating', pre=True, always=True)
    def validate_rating(cls, v):
        if v is not None and v != "":
            try:
                v = float(v)
                if v < 1 or v > 5:
                    raise ValueError('Rating must be between 1 and 5')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Rating must be a valid number')
        return None


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
    rating: Optional[float] = None
    hospital_id: Optional[int] = None
    other_hospital_name: Optional[str] = None
    doctor_id: Optional[int] = None
    other_doctor_name: Optional[str] = None
    location: Optional[str] = None
    
    @validator('price_min', 'price_max', 'price_exact', pre=True, always=True)
    def validate_prices(cls, v):
        if v is not None and v != "":
            try:
                v = float(v)
                if v < 0:
                    raise ValueError('Price must be a positive number')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Price must be a valid number')
        return None
    
    @validator('rating', pre=True, always=True)
    def validate_rating(cls, v):
        if v is not None and v != "":
            try:
                v = float(v)
                if v < 1 or v > 5:
                    raise ValueError('Rating must be between 1 and 5')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Rating must be a valid number')
        return None


class TreatmentResponse(BaseSchema):
    id: int
    name: str
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    treatment_type: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_exact: Optional[float] = None
    rating: Optional[float] = None
    hospital_id: Optional[int] = None
    other_hospital_name: Optional[str] = None
    doctor_id: Optional[int] = None
    other_doctor_name: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime
    images: List[ImageResponse] = []


# Package Booking schemas
class PackageBookingBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mobile_no: str
    treatment_id: Optional[int] = None
    budget: Optional[str] = None
    medical_history_file: Optional[str] = None
    doctor_preference: Optional[str] = None
    hospital_preference: Optional[str] = None
    user_query: Optional[str] = None
    travel_assistant: bool = False
    stay_assistant: bool = False


class PackageBookingCreate(PackageBookingBase):
    pass


class PackageBookingUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_no: Optional[str] = None
    treatment_id: Optional[int] = None
    budget: Optional[str] = None
    medical_history_file: Optional[str] = None
    doctor_preference: Optional[str] = None
    hospital_preference: Optional[str] = None
    user_query: Optional[str] = None
    travel_assistant: Optional[bool] = None
    stay_assistant: Optional[bool] = None


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
    # doctor: Optional["DoctorResponse"] = None  # Removed to avoid greenlet issues


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


# Admin schemas
class AdminLogin(BaseModel):
    username: str
    password: str


class AdminBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True
    is_super_admin: bool = False


class AdminCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_super_admin: bool = False


class AdminResponse(AdminBase, BaseSchema):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None


class AdminToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminResponse


# Contact Us schemas
class ContactUsBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: Optional[str] = None
    message: str


class ContactUsCreate(ContactUsBase):
    pass


class ContactUsUpdate(BaseModel):
    is_read: Optional[bool] = None
    admin_response: Optional[str] = None


class ContactUsResponse(ContactUsBase, BaseSchema):
    id: int
    is_read: bool = False
    admin_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime


# Offer schemas (Attractions / Discount Packages)
class OfferBase(BaseModel):
    name: str
    description: str
    treatment_type: Optional[str] = None
    location: Optional[str] = None
    start_date: datetime
    end_date: datetime
    discount_percentage: Optional[float] = None
    is_free_camp: bool = False
    treatment_id: Optional[int] = None
    is_active: bool = True
    
    @validator('discount_percentage', pre=True, always=True)
    def validate_discount_percentage(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError('Discount percentage must be a number')
            if v < 0 or v > 100:
                raise ValueError('Discount percentage must be between 0 and 100')
        return v
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class OfferCreate(OfferBase):
    pass


class OfferUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    treatment_type: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    discount_percentage: Optional[float] = None
    is_free_camp: Optional[bool] = None
    treatment_id: Optional[int] = None
    is_active: Optional[bool] = None
    
    @validator('discount_percentage', pre=True, always=True)
    def validate_discount_percentage(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError('Discount percentage must be a number')
            if v < 0 or v > 100:
                raise ValueError('Discount percentage must be between 0 and 100')
        return v


class OfferResponse(BaseSchema):
    id: int
    name: str
    description: str
    treatment_type: Optional[str] = None
    location: Optional[str] = None
    start_date: datetime
    end_date: datetime
    discount_percentage: Optional[float] = None
    is_free_camp: bool = False
    treatment_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    images: List[ImageResponse] = []
    
    @property
    def is_expired(self) -> bool:
        """Check if the offer has expired"""
        return datetime.utcnow() > self.end_date
    
    @property
    def is_current(self) -> bool:
        """Check if the offer is currently active and not expired"""
        now = datetime.utcnow()
        return self.is_active and self.start_date <= now <= self.end_date
    
    @property
    def days_remaining(self) -> int:
        """Get the number of days remaining for the offer"""
        if self.is_expired:
            return 0
        return (self.end_date - datetime.utcnow()).days


# Blog schemas
class BlogBase(BaseModel):
    title: str
    subtitle: Optional[str] = None
    content: str
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    meta_description: Optional[str] = None
    tags: Optional[str] = None  # comma-separated
    category: Optional[str] = None
    author_name: Optional[str] = None
    reading_time: Optional[int] = None
    is_published: bool = False
    is_featured: bool = False
    published_at: Optional[datetime] = None
    
    @validator('reading_time', pre=True, always=True)
    def validate_reading_time(cls, v):
        if v is not None and v != "":
            try:
                v = int(v)
                if v < 0:
                    raise ValueError('Reading time must be a positive number')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Reading time must be a valid number')
        return None


class BlogCreate(BlogBase):
    pass


class BlogUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    meta_description: Optional[str] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    author_name: Optional[str] = None
    reading_time: Optional[int] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    published_at: Optional[datetime] = None
    
    @validator('reading_time', pre=True, always=True)
    def validate_reading_time(cls, v):
        if v is not None and v != "":
            try:
                v = int(v)
                if v < 0:
                    raise ValueError('Reading time must be a positive number')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Reading time must be a valid number')
        return None


class BlogResponse(BlogBase, BaseSchema):
    id: int
    slug: str
    view_count: int = 0
    created_at: datetime
    updated_at: datetime
    images: List[ImageResponse] = []
    
    @property
    def tags_list(self) -> List[str]:
        return [tag.strip() for tag in (self.tags or "").split(",") if tag.strip()]
    
    @property
    def reading_time_display(self) -> str:
        if self.reading_time:
            return f"{self.reading_time} min read"
        return "Quick read"


# Update forward references
DoctorResponse.model_rebuild()
HospitalResponse.model_rebuild()
TreatmentResponse.model_rebuild()
AppointmentResponse.model_rebuild()
BlogResponse.model_rebuild()