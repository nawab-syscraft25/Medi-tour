#!/usr/bin/env python3
"""
JSON export/import utilities for small datasets
"""
import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app import models


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


async def export_to_json(output_file: str = "meditour_data.json") -> None:
    """Export all data to JSON file"""
    async with AsyncSessionLocal() as db:
        data = {}
        
        # Export sliders
        result = await db.execute(select(models.Slider))
        sliders = result.scalars().all()
        data['sliders'] = [
            {
                'id': s.id,
                'title': s.title,
                'description': s.description,
                'image_url': s.image_url,
                'link': s.link,
                'tags': s.tags,
                'is_active': s.is_active,
                'created_at': s.created_at
            } for s in sliders
        ]
        
        # Export hospitals
        result = await db.execute(select(models.Hospital))
        hospitals = result.scalars().all()
        data['hospitals'] = [
            {
                'id': h.id,
                'name': h.name,
                'description': h.description,
                'location': h.location,
                'phone': h.phone,
                'features': h.features,
                'facilities': h.facilities,
                'created_at': h.created_at
            } for h in hospitals
        ]
        
        # Export doctors
        result = await db.execute(select(models.Doctor))
        doctors = result.scalars().all()
        data['doctors'] = [
            {
                'id': d.id,
                'name': d.name,
                'profile_photo': d.profile_photo,
                'description': d.description,
                'designation': d.designation,
                'experience_years': d.experience_years,
                'hospital_id': d.hospital_id,
                'gender': d.gender,
                'skills': d.skills,
                'qualifications': d.qualifications,
                'highlights': d.highlights,
                'awards': d.awards,
                'created_at': d.created_at
            } for d in doctors
        ]
        
        # Export treatments
        result = await db.execute(select(models.Treatment))
        treatments = result.scalars().all()
        data['treatments'] = [
            {
                'id': t.id,
                'name': t.name,
                'short_description': t.short_description,
                'long_description': t.long_description,
                'treatment_type': t.treatment_type,
                'price_min': t.price_min,
                'price_max': t.price_max,
                'price_exact': t.price_exact,
                'hospital_id': t.hospital_id,
                'other_hospital_name': t.other_hospital_name,
                'doctor_id': t.doctor_id,
                'other_doctor_name': t.other_doctor_name,
                'location': t.location,
                'created_at': t.created_at
            } for t in treatments
        ]
        
        # Export package bookings
        result = await db.execute(select(models.PackageBooking))
        bookings = result.scalars().all()
        data['package_bookings'] = [
            {
                'id': b.id,
                'name': b.name,
                'email': b.email,
                'phone': b.phone,
                'service_type': b.service_type,
                'service_ref': b.service_ref,
                'budget_range': b.budget_range,
                'medical_history_file': b.medical_history_file,
                'user_query': b.user_query,
                'travel_assistant': b.travel_assistant,
                'stay_assistant': b.stay_assistant,
                'created_at': b.created_at
            } for b in bookings
        ]
        
        # Export appointments
        result = await db.execute(select(models.Appointment))
        appointments = result.scalars().all()
        data['appointments'] = [
            {
                'id': a.id,
                'patient_name': a.patient_name,
                'patient_contact': a.patient_contact,
                'doctor_id': a.doctor_id,
                'scheduled_at': a.scheduled_at,
                'notes': a.notes,
                'status': a.status,
                'created_at': a.created_at
            } for a in appointments
        ]
        
        # Export images
        result = await db.execute(select(models.Image))
        images = result.scalars().all()
        data['images'] = [
            {
                'id': i.id,
                'owner_type': i.owner_type,
                'owner_id': i.owner_id,
                'url': i.url,
                'is_primary': i.is_primary,
                'position': i.position,
                'uploaded_at': i.uploaded_at
            } for i in images
        ]
        
        # Add metadata
        data['export_metadata'] = {
            'timestamp': datetime.utcnow(),
            'total_records': sum(len(data[key]) for key in data if key != 'export_metadata')
        }
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=DateTimeEncoder, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {data['export_metadata']['total_records']} records to {output_file}")


async def import_from_json(input_file: str) -> None:
    """Import data from JSON file"""
    if not Path(input_file).exists():
        print(f"❌ File {input_file} not found")
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    async with AsyncSessionLocal() as db:
        imported_counts = {}
        
        # Import hospitals first (referenced by doctors and treatments)
        if 'hospitals' in data:
            for hospital_data in data['hospitals']:
                # Remove id to let DB assign new ones
                hospital_data.pop('id', None)
                # Convert datetime string back to datetime
                if 'created_at' in hospital_data and isinstance(hospital_data['created_at'], str):
                    hospital_data['created_at'] = datetime.fromisoformat(hospital_data['created_at'])
                
                hospital = models.Hospital(**hospital_data)
                db.add(hospital)
            await db.commit()
            imported_counts['hospitals'] = len(data['hospitals'])
        
        # Import doctors
        if 'doctors' in data:
            for doctor_data in data['doctors']:
                doctor_data.pop('id', None)
                if 'created_at' in doctor_data and isinstance(doctor_data['created_at'], str):
                    doctor_data['created_at'] = datetime.fromisoformat(doctor_data['created_at'])
                
                doctor = models.Doctor(**doctor_data)
                db.add(doctor)
            await db.commit()
            imported_counts['doctors'] = len(data['doctors'])
        
        # Import treatments
        if 'treatments' in data:
            for treatment_data in data['treatments']:
                treatment_data.pop('id', None)
                if 'created_at' in treatment_data and isinstance(treatment_data['created_at'], str):
                    treatment_data['created_at'] = datetime.fromisoformat(treatment_data['created_at'])
                
                treatment = models.Treatment(**treatment_data)
                db.add(treatment)
            await db.commit()
            imported_counts['treatments'] = len(data['treatments'])
        
        # Import sliders
        if 'sliders' in data:
            for slider_data in data['sliders']:
                slider_data.pop('id', None)
                if 'created_at' in slider_data and isinstance(slider_data['created_at'], str):
                    slider_data['created_at'] = datetime.fromisoformat(slider_data['created_at'])
                
                slider = models.Slider(**slider_data)
                db.add(slider)
            await db.commit()
            imported_counts['sliders'] = len(data['sliders'])
        
        # Import appointments
        if 'appointments' in data:
            for appointment_data in data['appointments']:
                appointment_data.pop('id', None)
                if 'created_at' in appointment_data and isinstance(appointment_data['created_at'], str):
                    appointment_data['created_at'] = datetime.fromisoformat(appointment_data['created_at'])
                if 'scheduled_at' in appointment_data and isinstance(appointment_data['scheduled_at'], str):
                    appointment_data['scheduled_at'] = datetime.fromisoformat(appointment_data['scheduled_at'])
                
                appointment = models.Appointment(**appointment_data)
                db.add(appointment)
            await db.commit()
            imported_counts['appointments'] = len(data['appointments'])
        
        # Import package bookings
        if 'package_bookings' in data:
            for booking_data in data['package_bookings']:
                booking_data.pop('id', None)
                if 'created_at' in booking_data and isinstance(booking_data['created_at'], str):
                    booking_data['created_at'] = datetime.fromisoformat(booking_data['created_at'])
                
                booking = models.PackageBooking(**booking_data)
                db.add(booking)
            await db.commit()
            imported_counts['package_bookings'] = len(data['package_bookings'])
        
        # Import images
        if 'images' in data:
            for image_data in data['images']:
                image_data.pop('id', None)
                if 'uploaded_at' in image_data and isinstance(image_data['uploaded_at'], str):
                    image_data['uploaded_at'] = datetime.fromisoformat(image_data['uploaded_at'])
                
                image = models.Image(**image_data)
                db.add(image)
            await db.commit()
            imported_counts['images'] = len(data['images'])
        
        total_imported = sum(imported_counts.values())
        print(f"✅ Imported {total_imported} records:")
        for table, count in imported_counts.items():
            print(f"   {table}: {count}")


async def clear_all_data() -> None:
    """Clear all data from database (use with caution!)"""
    async with AsyncSessionLocal() as db:
        # Delete in order to respect foreign key constraints
        tables = [
            models.Image,
            models.Appointment,
            models.Treatment,
            models.Doctor,
            models.Hospital,
            models.PackageBooking,
            models.Slider
        ]
        
        for table in tables:
            result = await db.execute(select(table))
            records = result.scalars().all()
            for record in records:
                await db.delete(record)
        
        await db.commit()
        print("✅ All data cleared from database")


async def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python export_import.py export [filename]")
        print("  python export_import.py import <filename>")
        print("  python export_import.py clear")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'export':
        filename = sys.argv[2] if len(sys.argv) > 2 else "meditour_data.json"
        await export_to_json(filename)
    
    elif command == 'import':
        if len(sys.argv) < 3:
            print("❌ Please specify input filename")
            return
        filename = sys.argv[2]
        await import_from_json(filename)
    
    elif command == 'clear':
        confirm = input("⚠️  This will delete ALL data. Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            await clear_all_data()
        else:
            print("Operation cancelled")
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())