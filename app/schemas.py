from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, validator, ConfigDict
from pydantic import Field


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


# FAQ schemas
class FAQBase(BaseModel):
    question: str
    answer: str
    position: int = 0
    is_active: bool = True


class FAQCreate(FAQBase):
    owner_type: str  # "doctor", "hospital", "treatment"
    owner_id: int


class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    position: Optional[int] = None
    is_active: Optional[bool] = None


class FAQResponse(BaseSchema):
    id: int
    owner_type: str
    owner_id: int
    question: str
    answer: str
    position: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


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
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    established_year: Optional[int] = None
    bed_count: Optional[int] = None
    specializations: Optional[str] = None
    rating: Optional[float] = None
    features: Optional[str] = None  # comma-separated
    facilities: Optional[str] = None  # comma-separated
    is_featured: Optional[bool] = False
    is_active: Optional[bool] = True
    
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
    is_featured: Optional[bool] = None
    
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
    faqs: List[FAQResponse] = []
    # Direct FAQ fields from model
    faq1_question: Optional[str] = None
    faq1_answer: Optional[str] = None
    faq2_question: Optional[str] = None
    faq2_answer: Optional[str] = None
    faq3_question: Optional[str] = None
    faq3_answer: Optional[str] = None
    faq4_question: Optional[str] = None
    faq4_answer: Optional[str] = None
    faq5_question: Optional[str] = None
    faq5_answer: Optional[str] = None
    
    @property
    def features_list(self) -> List[str]:
        return [f.strip() for f in (self.features or "").split(",") if f.strip()]
    
    @property
    def facilities_list(self) -> List[str]:
        return [f.strip() for f in (self.facilities or "").split(",") if f.strip()]
    
    @property
    def specializations_list(self) -> List[str]:
        return [s.strip() for s in (self.specializations or "").split(",") if s.strip()]


# Doctor schemas
class DoctorBase(BaseModel):
    name: str
    profile_photo: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    designation: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    rating: Optional[float] = None
    consultancy_fee: Optional[float] = None
    hospital_id: Optional[int] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    skills: Optional[str] = None  # comma-separated
    qualifications: Optional[str] = None
    highlights: Optional[str] = None
    awards: Optional[str] = None
    time_slots: Optional[str] = None  # JSON string containing availability for each day of the week
    is_featured: bool = False
    is_active: bool = True
    
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
    
    @validator('consultancy_fee', pre=True, always=True)
    def validate_consultancy_fee(cls, v):
        if v is not None and v != "":
            try:
                v = float(v)
                if v < 0:
                    raise ValueError('Consultancy fee must be a positive number')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Consultancy fee must be a valid number')
        return None


class DoctorCreate(DoctorBase):
    associated_hospitals: Optional[List[int]] = None


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    profile_photo: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    designation: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    rating: Optional[float] = None
    consultancy_fee: Optional[float] = None
    hospital_id: Optional[int] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    skills: Optional[str] = None
    qualifications: Optional[str] = None
    highlights: Optional[str] = None
    awards: Optional[str] = None
    time_slots: Optional[str] = None  # JSON string containing availability for each day of the week
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    associated_hospitals: Optional[List[int]] = None
    
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
    
    @validator('consultancy_fee', pre=True, always=True)
    def validate_consultancy_fee(cls, v):
        if v is not None and v != "":
            try:
                v = float(v)
                if v < 0:
                    raise ValueError('Consultancy fee must be a positive number')
                return v
            except (ValueError, TypeError):
                if v == "":  # Empty string should be converted to None
                    return None
                raise ValueError('Consultancy fee must be a valid number')
        return None


class DoctorResponse(BaseSchema):
    id: int
    name: str
    profile_photo: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    designation: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    rating: Optional[float] = None
    consultancy_fee: Optional[float] = None
    hospital_id: Optional[int] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    skills: Optional[str] = None
    qualifications: Optional[str] = None
    highlights: Optional[str] = None
    awards: Optional[str] = None
    time_slots: Optional[Dict[str, Any]] = None  # Parsed JSON dict of availability per day
    is_featured: bool = False
    is_active: bool = True
    created_at: datetime
    images: List[ImageResponse] = []
    faqs: List[FAQResponse] = []
    # Direct FAQ fields from model
    faq1_question: Optional[str] = None
    faq1_answer: Optional[str] = None
    faq2_question: Optional[str] = None
    faq2_answer: Optional[str] = None
    faq3_question: Optional[str] = None
    faq3_answer: Optional[str] = None
    faq4_question: Optional[str] = None
    faq4_answer: Optional[str] = None
    faq5_question: Optional[str] = None
    faq5_answer: Optional[str] = None
    # Associated hospitals
    associated_hospitals: Optional[List[dict]] = None
    
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
    features: Optional[str] = None  # comma-separated features
    is_ayushman: bool = False
    Includes: Optional[str] = None
    excludes: Optional[str] = None
    is_featured: bool = False
    
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
    features: Optional[str] = None
    is_ayushman: Optional[bool] = None
    Includes: Optional[str] = None
    excludes: Optional[str] = None
    is_featured: Optional[bool] = None
    
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
    features: Optional[str] = None
    is_ayushman: bool = False
    Includes: Optional[str] = None
    excludes: Optional[str] = None
    is_featured: bool = False
    created_at: datetime
    images: List[ImageResponse] = []
    faqs: List[FAQResponse] = []
    # Direct FAQ fields from model
    faq1_question: Optional[str] = None
    faq1_answer: Optional[str] = None
    faq2_question: Optional[str] = None
    faq2_answer: Optional[str] = None
    faq3_question: Optional[str] = None
    faq3_answer: Optional[str] = None
    faq4_question: Optional[str] = None
    faq4_answer: Optional[str] = None
    faq5_question: Optional[str] = None
    faq5_answer: Optional[str] = None
    
    @property
    def features_list(self) -> List[str]:
        return [f.strip() for f in (self.features or "").split(",") if f.strip()]


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
    preferred_time_slot: Optional[str] = None
    user_query: Optional[str] = None
    travel_assistant: bool = False
    stay_assistant: bool = False
    personal_assistant: bool = False


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
    preferred_time_slot: Optional[str] = None
    user_query: Optional[str] = None
    travel_assistant: Optional[bool] = None
    stay_assistant: Optional[bool] = None
    personal_assistant: Optional[bool] = None


class PackageBookingResponse(PackageBookingBase, BaseSchema):
    id: int
    created_at: datetime


# Appointment schemas
class AppointmentBase(BaseModel):
    patient_name: Optional[str] = None
    patient_contact: Optional[str] = None
    doctor_id: Optional[int] = None
    hospital_preference: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    status: str = "scheduled"
    consultation_fees: Optional[float] = None
    payment_status: str = "pending"
    payment_id: Optional[str] = None
    payment_order_id: Optional[str] = None
    payment_signature: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    patient_name: Optional[str] = None
    patient_contact: Optional[str] = None
    doctor_id: Optional[int] = None
    hospital_preference: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    consultation_fees: Optional[float] = None
    payment_status: Optional[str] = None
    payment_id: Optional[str] = None
    payment_order_id: Optional[str] = None
    payment_signature: Optional[str] = None


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
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: Optional[str] = None
    message: str
    service_type: Optional[str] = None


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


# User Authentication schemas
class UserSignUp(BaseModel):
    name: str = Field(..., min_length=2, max_length=250)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=80)
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseSchema):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    is_email_verified: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)

class VerifyEmail(BaseModel):
    token: str

class ResendVerification(BaseModel):
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Banner schemas
class BannerBase(BaseModel):
    name: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    button_text: Optional[str] = None
    position: int = 0
    is_active: bool = True


class BannerCreate(BannerBase):
    pass


class BannerUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    button_text: Optional[str] = None
    position: Optional[int] = None
    is_active: Optional[bool] = None


class BannerResponse(BannerBase, BaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime


# Partner Hospital schemas
class PartnerHospitalBase(BaseModel):
    name: str
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    position: int = 0
    is_active: bool = True
    hospital_id: Optional[int] = None


class PartnerHospitalCreate(PartnerHospitalBase):
    pass


class PartnerHospitalUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    position: Optional[int] = None
    is_active: Optional[bool] = None
    hospital_id: Optional[int] = None


class PartnerHospitalResponse(PartnerHospitalBase, BaseSchema):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    hospital: Optional["HospitalResponse"] = None


# Patient Story schemas
class PatientStoryBase(BaseModel):
    patient_name: str
    description: str
    rating: int = Field(..., ge=1, le=5)
    profile_photo: Optional[str] = None
    treatment_type: Optional[str] = None
    hospital_name: Optional[str] = None
    location: Optional[str] = None
    date_of_treatment: Optional[datetime] = None
    position: int = 0
    is_featured: bool = False
    is_active: bool = True
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v


class PatientStoryCreate(PatientStoryBase):
    pass


class PatientStoryUpdate(BaseModel):
    patient_name: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    profile_photo: Optional[str] = None
    treatment_type: Optional[str] = None
    hospital_name: Optional[str] = None
    location: Optional[str] = None
    date_of_treatment: Optional[datetime] = None
    position: Optional[int] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v


class PatientStoryResponse(PatientStoryBase, BaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime


# Update forward references
DoctorResponse.model_rebuild()
HospitalResponse.model_rebuild()
TreatmentResponse.model_rebuild()
AppointmentResponse.model_rebuild()
BlogResponse.model_rebuild()
BannerResponse.model_rebuild()
PartnerHospitalResponse.model_rebuild()
PatientStoryResponse.model_rebuild()


# AboutUs / FeaturedCard / ContactUsPage schemas
class FeaturedCardResponse(BaseSchema):
    id: int
    about_us_id: int
    heading: str
    description: Optional[str] = None
    position: int
    created_at: datetime


class AboutUsBase(BaseModel):
    heading: str
    description: Optional[str] = None
    vision_heading: Optional[str] = None
    vision_desc: Optional[str] = None
    vision: Optional[str] = None
    mission: Optional[str] = None
    bottom_heading: Optional[str] = None
    bottom_desc: Optional[str] = None
    bottom_list: Optional[str] = None
    feature_title: Optional[str] = None
    feature_desc: Optional[str] = None


class AboutUsResponse(AboutUsBase, BaseSchema):
    id: int
    position: int
    is_featured: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    featured_cards: List[FeaturedCardResponse] = []


class ContactUsPageResponse(BaseSchema):
    id: int
    heading: Optional[str] = None
    description: Optional[str] = None
    phone_no: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


AboutUsResponse.model_rebuild()
FeaturedCardResponse.model_rebuild()
ContactUsPageResponse.model_rebuild()