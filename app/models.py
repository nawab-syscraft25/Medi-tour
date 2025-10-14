# app/models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Table, and_
from sqlalchemy.orm import relationship, declarative_base, foreign

Base = declarative_base()

# Association table for many-to-many relationship between Doctor and Hospital
doctor_hospital_association = Table('doctor_hospital_association', Base.metadata,
    Column('doctor_id', Integer, ForeignKey('doctors.id'), primary_key=True),
    Column('hospital_id', Integer, ForeignKey('hospitals.id'), primary_key=True)
)

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    owner_type = Column(String(50), nullable=False)  # "hospital","doctor","treatment","slider","offer","blog"
    owner_id = Column(Integer, nullable=False)
    url = Column(String(1000), nullable=False)
    is_primary = Column(Boolean, default=False)
    position = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class FAQ(Base):
    __tablename__ = "faqs"
    id = Column(Integer, primary_key=True, index=True)
    owner_type = Column(String(50), nullable=False)  # "hospital","doctor","treatment"
    owner_id = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    position = Column(Integer, default=0)  # For ordering FAQs
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Slider(Base):
    __tablename__ = "sliders"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(250), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(1000), nullable=True)   # convenience primary URL
    link = Column(String(1000), nullable=True)
    tags = Column(String(500), nullable=True)         # comma-separated
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Hospital(Base):
    __tablename__ = "hospitals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(80), nullable=True)
    email = Column(String(300), nullable=True)
    website = Column(String(500), nullable=True)
    established_year = Column(Integer, nullable=True)
    bed_count = Column(Integer, nullable=True)
    specializations = Column(Text, nullable=True)  # comma-separated
    rating = Column(Float, nullable=True)
    features = Column(Text, nullable=True)    # comma-separated one-liners
    facilities = Column(Text, nullable=True)  # comma-separated keywords
    # Simple FAQ fields
    faq1_question = Column(Text, nullable=True)
    faq1_answer = Column(Text, nullable=True)
    faq2_question = Column(Text, nullable=True)
    faq2_answer = Column(Text, nullable=True)
    faq3_question = Column(Text, nullable=True)
    faq3_answer = Column(Text, nullable=True)
    faq4_question = Column(Text, nullable=True)
    faq4_answer = Column(Text, nullable=True)
    faq5_question = Column(Text, nullable=True)
    faq5_answer = Column(Text, nullable=True)
    is_featured = Column(Boolean, default=False, index=True)  # featured on homepage
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    doctors = relationship("Doctor", secondary=doctor_hospital_association, back_populates="hospitals", lazy="noload")
    tours = relationship("Treatment", back_populates="hospital", lazy="noload")
    images = relationship("Image", 
                         primaryjoin="and_(Hospital.id == foreign(Image.owner_id), Image.owner_type == 'hospital')",
                         lazy="select", viewonly=True)
    faqs = relationship("FAQ", 
                       primaryjoin="and_(Hospital.id == foreign(FAQ.owner_id), FAQ.owner_type == 'hospital')",
                       lazy="select", viewonly=True)

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(250), nullable=False, index=True)
    profile_photo = Column(String(1000), nullable=True)
    short_description = Column(String(500), nullable=True)  # Brief description for cards/listings
    long_description = Column(Text, nullable=True)  # Detailed description for profile page
    designation = Column(String(200), nullable=True)
    specialization = Column(String(200), nullable=True)  # single main specialization
    qualification = Column(String(500), nullable=True)   # main qualification
    experience_years = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    consultancy_fee = Column(Float, nullable=True)  # Consultation fee
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True)  # primary hospital
    location = Column(String(500), nullable=True)  # Doctor's practice location
    gender = Column(String(20), nullable=True)
    skills = Column(Text, nullable=True)           # comma-separated
    qualifications = Column(Text, nullable=True)   # detailed qualifications
    highlights = Column(Text, nullable=True)
    awards = Column(Text, nullable=True)
    # Simple FAQ fields
    faq1_question = Column(Text, nullable=True)
    faq1_answer = Column(Text, nullable=True)
    faq2_question = Column(Text, nullable=True)
    faq2_answer = Column(Text, nullable=True)
    faq3_question = Column(Text, nullable=True)
    faq3_answer = Column(Text, nullable=True)
    faq4_question = Column(Text, nullable=True)
    faq4_answer = Column(Text, nullable=True)
    faq5_question = Column(Text, nullable=True)
    faq5_answer = Column(Text, nullable=True)
    is_featured = Column(Boolean, default=False, index=True)  # featured on homepage
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    hospital = relationship("Hospital", foreign_keys=[hospital_id], lazy="noload")  # primary hospital
    hospitals = relationship("Hospital", secondary=doctor_hospital_association, back_populates="doctors", lazy="noload")  # all associated hospitals
    appointments = relationship("Appointment", back_populates="doctor", lazy="noload")
    images = relationship("Image",
                         primaryjoin="and_(Doctor.id == foreign(Image.owner_id), Image.owner_type == 'doctor')",
                         lazy="select", viewonly=True)
    faqs = relationship("FAQ", 
                       primaryjoin="and_(Doctor.id == foreign(FAQ.owner_id), FAQ.owner_type == 'doctor')",
                       lazy="select", viewonly=True)
    
    @property
    def description(self) -> str:
        """Backward compatibility property for templates"""
        return self.short_description or self.long_description or ""

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String(250), nullable=True)
    patient_contact = Column(String(80), nullable=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)
    hospital_preference = Column(String(300), nullable=True) 
    scheduled_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="scheduled")
    # Payment fields for Razorpay integration
    consultation_fees = Column(Float, nullable=True)  # Consultation fees
    payment_status = Column(String(50), default="pending")  # pending, completed, failed, refunded
    payment_id = Column(String(255), nullable=True)  # Razorpay payment ID
    payment_order_id = Column(String(255), nullable=True)  # Razorpay order ID
    payment_signature = Column(String(255), nullable=True)  # Razorpay signature for verification
    created_at = Column(DateTime, default=datetime.utcnow)
    doctor = relationship("Doctor", back_populates="appointments", lazy="noload")

class Treatment(Base):
    __tablename__ = "treatments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False, index=True)
    short_description = Column(String(500), nullable=True)
    long_description = Column(Text, nullable=True)
    treatment_type = Column(String(100), nullable=True, index=True)  # admin-defined
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)
    price_exact = Column(Float, nullable=True)
    rating = Column(Float, nullable=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True)
    other_hospital_name = Column(String(300), nullable=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)
    other_doctor_name = Column(String(300), nullable=True)
    location = Column(String(500), nullable=True)
    features = Column(Text, nullable=True)  # comma-separated treatment features
    # Simple FAQ fields
    faq1_question = Column(Text, nullable=True)
    faq1_answer = Column(Text, nullable=True)
    faq2_question = Column(Text, nullable=True)
    faq2_answer = Column(Text, nullable=True)
    faq3_question = Column(Text, nullable=True)
    faq3_answer = Column(Text, nullable=True)
    faq4_question = Column(Text, nullable=True)
    faq4_answer = Column(Text, nullable=True)
    faq5_question = Column(Text, nullable=True)
    faq5_answer = Column(Text, nullable=True)
    is_featured = Column(Boolean, default=False, index=True)  # featured on homepage
    created_at = Column(DateTime, default=datetime.utcnow)
    hospital = relationship("Hospital", back_populates="tours", lazy="noload")
    doctor = relationship("Doctor", lazy="noload")
    images = relationship("Image", 
                         primaryjoin="and_(Treatment.id == foreign(Image.owner_id), Image.owner_type == 'treatment')",
                         lazy="select", viewonly=True)
    faqs = relationship("FAQ", 
                       primaryjoin="and_(Treatment.id == foreign(FAQ.owner_id), FAQ.owner_type == 'treatment')",
                       lazy="select", viewonly=True)

class PackageBooking(Base):
    __tablename__ = "package_bookings"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    email = Column(String(300), nullable=False, index=True)
    mobile_no = Column(String(80), nullable=False)
    treatment_id = Column(Integer, ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True, index=True)  # Selected treatment with ID
    budget = Column(String(100), nullable=True)            # Budget as string (e.g., "10k-20k", "Under 50k")
    medical_history_file = Column(String(1000), nullable=True)  # PDF or image file path
    doctor_preference = Column(String(300), nullable=True)  # Doctor preference input string
    hospital_preference = Column(String(300), nullable=True)  # Hospital preference string
    user_query = Column(Text, nullable=True)
    travel_assistant = Column(Boolean, default=False)
    stay_assistant = Column(Boolean, default=False)
    personal_assistant = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    treatment = relationship("Treatment", lazy="noload")


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(300), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # bcrypt hashed password
    is_active = Column(Boolean, default=True)
    is_super_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(250), nullable=False)
    email = Column(String(300), unique=True, index=True, nullable=False)
    phone = Column(String(80), nullable=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hashed password
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class ContactUs(Base):
    __tablename__ = "contact_us"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    email = Column(String(300), nullable=False, index=True)
    phone = Column(String(80), nullable=True)
    subject = Column(String(500), nullable=True)
    message = Column(Text, nullable=False)
    service_type = Column(String(100), nullable=True, index=True)  # Service type field
    is_read = Column(Boolean, default=False)
    admin_response = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @property
    def full_name(self) -> str:
        """Get full name for display purposes (backward compatibility)"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def name(self) -> str:
        """Backward compatibility property for templates"""
        return self.full_name


class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False, index=True)  # Offer Name/Title
    description = Column(Text, nullable=False)  # Full Description
    treatment_type = Column(String(100), nullable=True, index=True)  # Type of Treatment
    location = Column(String(500), nullable=True, index=True)  # Location (city or hospital/clinic)
    start_date = Column(DateTime, nullable=False, index=True)  # Start Date
    end_date = Column(DateTime, nullable=False, index=True)  # End Date
    discount_percentage = Column(Float, nullable=True)  # Discount Percentage (0-100)
    is_free_camp = Column(Boolean, default=False)  # Free Camp Flag
    treatment_id = Column(Integer, ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True)  # Link to treatment
    is_active = Column(Boolean, default=True)  # Active status
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    treatment = relationship("Treatment", lazy="noload")
    images = relationship("Image", 
                         primaryjoin="and_(Offer.id == foreign(Image.owner_id), Image.owner_type == 'offer')",
                         lazy="select", viewonly=True)


class Blog(Base):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    subtitle = Column(String(1000), nullable=True)
    slug = Column(String(600), nullable=False, unique=True, index=True)  # URL-friendly version of title
    content = Column(Text, nullable=False)  # Rich HTML content from text editor
    excerpt = Column(Text, nullable=True)  # Short summary/preview
    featured_image = Column(String(1000), nullable=True)  # Main blog image
    meta_description = Column(String(500), nullable=True)  # SEO meta description
    tags = Column(String(1000), nullable=True)  # comma-separated tags
    category = Column(String(200), nullable=True, index=True)  # blog category
    author_name = Column(String(200), nullable=True)  # author name
    reading_time = Column(Integer, nullable=True)  # estimated reading time in minutes
    view_count = Column(Integer, default=0)  # number of views
    is_published = Column(Boolean, default=False, index=True)  # published status
    is_featured = Column(Boolean, default=False, index=True)  # featured on homepage
    published_at = Column(DateTime, nullable=True, index=True)  # publication date
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = relationship("Image", 
                         primaryjoin="and_(Blog.id == foreign(Image.owner_id), Image.owner_type == 'blog')",
                         lazy="select", viewonly=True)


class Banner(Base):
    __tablename__ = "banners"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)  # Banner name (e.g., "Home Page Banner", "About Us Banner")
    title = Column(String(500), nullable=True)  # Banner title text
    subtitle = Column(String(1000), nullable=True)  # Banner subtitle text
    description = Column(Text, nullable=True)  # Banner description
    image_url = Column(String(1000), nullable=True)  # Banner image URL
    link_url = Column(String(1000), nullable=True)  # Optional link URL
    button_text = Column(String(100), nullable=True)  # Button text if link exists
    position = Column(Integer, default=0)  # For ordering banners
    is_active = Column(Boolean, default=True)  # Active status
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PartnerHospital(Base):
    __tablename__ = "partner_hospitals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False, index=True)  # Hospital name
    logo_url = Column(String(1000), nullable=True)  # Hospital logo URL
    website_url = Column(String(1000), nullable=True)  # Hospital website
    description = Column(Text, nullable=True)  # Brief description
    location = Column(String(500), nullable=True)  # Hospital location
    position = Column(Integer, default=0)  # For ordering partners
    is_active = Column(Boolean, default=True)  # Active status
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PatientStory(Base):
    __tablename__ = "patient_stories"
    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String(200), nullable=False, index=True)  # Patient name
    description = Column(Text, nullable=False)  # Patient story/testimonial
    rating = Column(Integer, nullable=False)  # Rating 1-5
    profile_photo = Column(String(1000), nullable=True)  # Patient profile photo URL
    treatment_type = Column(String(200), nullable=True)  # Type of treatment received
    hospital_name = Column(String(300), nullable=True)  # Hospital where treated
    location = Column(String(500), nullable=True)  # Patient location
    date_of_treatment = Column(DateTime, nullable=True)  # When treatment was received
    position = Column(Integer, default=0)  # For ordering stories
    is_featured = Column(Boolean, default=False)  # Featured on homepage
    is_active = Column(Boolean, default=True)  # Active status
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)