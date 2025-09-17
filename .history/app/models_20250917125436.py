# app/models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Table
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    owner_type = Column(String(50), nullable=False)  # "hospital","doctor","treatment","slider"
    owner_id = Column(Integer, nullable=False)
    url = Column(String(1000), nullable=False)
    is_primary = Column(Boolean, default=False)
    position = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

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
    phone = Column(String(80), nullable=True)
    features = Column(Text, nullable=True)    # comma-separated one-liners
    facilities = Column(Text, nullable=True)  # comma-separated keywords
    created_at = Column(DateTime, default=datetime.utcnow)
    doctors = relationship("Doctor", back_populates="hospital", lazy="noload")
    tours = relationship("Treatment", back_populates="hospital", lazy="noload")

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(250), nullable=False, index=True)
    profile_photo = Column(String(1000), nullable=True)
    description = Column(Text, nullable=True)
    designation = Column(String(200), nullable=True)
    experience_years = Column(Integer, nullable=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True)
    gender = Column(String(20), nullable=True)
    skills = Column(Text, nullable=True)           # comma-separated
    qualifications = Column(Text, nullable=True)
    highlights = Column(Text, nullable=True)
    awards = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    hospital = relationship("Hospital", back_populates="doctors", lazy="noload")
    appointments = relationship("Appointment", back_populates="doctor", lazy="noload")

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String(250), nullable=True)
    patient_contact = Column(String(80), nullable=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="scheduled")
    created_at = Column(DateTime, default=datetime.utcnow)
    doctor = relationship("Doctor", back_populates="appointments")

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
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True)
    other_hospital_name = Column(String(300), nullable=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)
    other_doctor_name = Column(String(300), nullable=True)
    location = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    hospital = relationship("Hospital", back_populates="tours")
    doctor = relationship("Doctor", lazy="joined")

class PackageBooking(Base):
    __tablename__ = "package_bookings"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(250), nullable=False)
    email = Column(String(300), nullable=False, index=True)
    phone = Column(String(80), nullable=False)
    service_type = Column(String(100), nullable=True)      # "hospital","doctor","treatment","other"
    service_ref = Column(String(300), nullable=True)       # referenced id or name string
    budget_range = Column(String(100), nullable=True)      # e.g., "5k-10k"
    medical_history_file = Column(String(1000), nullable=True)
    user_query = Column(Text, nullable=True)
    travel_assistant = Column(Boolean, default=False)
    stay_assistant = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)