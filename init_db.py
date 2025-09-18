#!/usr/bin/env python3
"""
Database initialization script
Creates all tables manually if Alembic fails
"""
import asyncio
import sqlite3
from pathlib import Path

# Database path
DB_PATH = "./meditour.db"

def create_tables():
    """Create all tables manually"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create images table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_type VARCHAR(50) NOT NULL,
            owner_id INTEGER NOT NULL,
            url VARCHAR(1000) NOT NULL,
            is_primary BOOLEAN DEFAULT 0,
            position INTEGER,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create sliders table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sliders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(250),
            description TEXT,
            image_url VARCHAR(1000),
            link VARCHAR(1000),
            tags VARCHAR(500),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create hospitals table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            location VARCHAR(500),
            phone VARCHAR(20),
            features VARCHAR(1000),
            facilities VARCHAR(1000),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create doctors table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            specialty VARCHAR(200),
            description TEXT,
            qualifications TEXT,
            experience_years INTEGER,
            phone VARCHAR(20),
            email VARCHAR(100),
            skills VARCHAR(1000),
            hospital_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        )
        """)
        
        # Create treatments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(100),
            price REAL,
            duration_days INTEGER,
            success_rate REAL,
            hospital_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        )
        """)
        
        # Create package_bookings table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS package_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name VARCHAR(200) NOT NULL,
            patient_email VARCHAR(100) NOT NULL,
            patient_phone VARCHAR(20),
            treatment_id INTEGER,
            hospital_id INTEGER,
            doctor_id INTEGER,
            booking_date DATETIME,
            arrival_date DATETIME,
            departure_date DATETIME,
            number_of_guests INTEGER DEFAULT 1,
            special_requirements TEXT,
            total_cost REAL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (treatment_id) REFERENCES treatments(id),
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
        """)
        
        # Create admins table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            is_super_admin BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
        """)
        
        # Create contact_us table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contact_us (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            subject VARCHAR(200),
            message TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'new',
            admin_response TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create alembic_version table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        )
        """)
        
        # Insert the latest migration version
        cursor.execute("DELETE FROM alembic_version")
        cursor.execute("INSERT INTO alembic_version VALUES ('3d415c3faa09')")
        
        conn.commit()
        print("✅ All tables created successfully!")
        
        # Show created tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\n📋 Created tables:")
        for table in tables:
            print(f"  - {table[0]}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Creating database tables...")
    create_tables()