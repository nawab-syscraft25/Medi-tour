#!/usr/bin/env python3
"""
Database initialization script
Creates all tables with complete schema matching SQLAlchemy models
Only recreates if schema is incorrect or missing
"""
import asyncio
import sqlite3
from pathlib import Path

# Database path
DB_PATH = "./meditour.db"

def check_database_schema():
    """Check if database exists and has correct schema"""
    if not Path(DB_PATH).exists():
        print("📄 Database file doesn't exist")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if all required tables exist
        required_tables = [
            'images', 'sliders', 'hospitals', 'doctors', 'appointments',
            'treatments', 'package_bookings', 'admins', 'contact_us'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        missing_tables = set(required_tables) - set(existing_tables)
        if missing_tables:
            print(f"📋 Missing tables: {', '.join(missing_tables)}")
            return False
        
        # Check if key columns exist in critical tables
        schema_checks = {
            'doctors': ['profile_photo', 'highlights', 'awards'],
            'treatments': ['short_description', 'treatment_type', 'price_exact'],
            'package_bookings': ['service_type', 'budget_range', 'travel_assistant'],
            'contact_us': ['is_read', 'responded_at']
        }
        
        for table, required_columns in schema_checks.items():
            cursor.execute(f"PRAGMA table_info({table})")
            existing_columns = [col[1] for col in cursor.fetchall()]
            missing_columns = set(required_columns) - set(existing_columns)
            if missing_columns:
                print(f"📋 Table {table} missing columns: {', '.join(missing_columns)}")
                return False
        
        conn.close()
        print("✅ Database schema is correct and up-to-date")
        return True
        
    except Exception as e:
        print(f"❌ Error checking database schema: {e}")
        return False

def create_tables():
    """Create all tables with complete schema matching models.py"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("🔧 Creating database tables with complete schema...")
        
        # Drop existing tables to ensure clean schema
        print("🗑️  Dropping existing tables...")
        tables_to_drop = [
            "package_bookings", "contact_us", "admins", "appointments", 
            "treatments", "doctors", "hospitals", "sliders", "images", "alembic_version"
        ]
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        # Create images table
        cursor.execute("""
        CREATE TABLE images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_type VARCHAR(50) NOT NULL,
            owner_id INTEGER NOT NULL,
            url VARCHAR(1000) NOT NULL,
            is_primary BOOLEAN DEFAULT 0,
            position INTEGER,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("   ✅ Created images table")
        
        # Create sliders table
        cursor.execute("""
        CREATE TABLE sliders (
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
        print("   ✅ Created sliders table")
        
        # Create hospitals table
        cursor.execute("""
        CREATE TABLE hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(300) NOT NULL,
            description TEXT,
            location VARCHAR(500),
            phone VARCHAR(80),
            features TEXT,
            facilities TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("   ✅ Created hospitals table")
        
        # Create doctors table with ALL columns from model
        cursor.execute("""
        CREATE TABLE doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(250) NOT NULL,
            profile_photo VARCHAR(1000),
            description TEXT,
            designation VARCHAR(200),
            experience_years INTEGER,
            hospital_id INTEGER,
            gender VARCHAR(20),
            skills TEXT,
            qualifications TEXT,
            highlights TEXT,
            awards TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE SET NULL
        )
        """)
        print("   ✅ Created doctors table")
        
        # Create appointments table
        cursor.execute("""
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name VARCHAR(250),
            patient_contact VARCHAR(80),
            doctor_id INTEGER,
            scheduled_at DATETIME,
            notes TEXT,
            status VARCHAR(50) DEFAULT 'scheduled',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
        )
        """)
        print("   ✅ Created appointments table")
        
        # Create treatments table with ALL columns from model
        cursor.execute("""
        CREATE TABLE treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(300) NOT NULL,
            short_description VARCHAR(500),
            long_description TEXT,
            treatment_type VARCHAR(100),
            price_min REAL,
            price_max REAL,
            price_exact REAL,
            hospital_id INTEGER,
            other_hospital_name VARCHAR(300),
            doctor_id INTEGER,
            other_doctor_name VARCHAR(300),
            location VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE SET NULL,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
        )
        """)
        print("   ✅ Created treatments table")
        
        # Create package_bookings table with ALL columns from model
        cursor.execute("""
        CREATE TABLE package_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(250) NOT NULL,
            email VARCHAR(300) NOT NULL,
            phone VARCHAR(80) NOT NULL,
            service_type VARCHAR(100),
            service_ref VARCHAR(300),
            budget_range VARCHAR(100),
            medical_history_file VARCHAR(1000),
            user_query TEXT,
            travel_assistant BOOLEAN DEFAULT 0,
            stay_assistant BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("   ✅ Created package_bookings table")
        
        # Create admins table
        cursor.execute("""
        CREATE TABLE admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(300) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            is_super_admin BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
        """)
        print("   ✅ Created admins table")
        
        # Create contact_us table with ALL columns from model
        cursor.execute("""
        CREATE TABLE contact_us (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(250) NOT NULL,
            email VARCHAR(300) NOT NULL,
            phone VARCHAR(80),
            subject VARCHAR(500),
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            admin_response TEXT,
            responded_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("   ✅ Created contact_us table")
        
        # Create alembic_version table
        cursor.execute("""
        CREATE TABLE alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        )
        """)
        print("   ✅ Created alembic_version table")
        
        # Insert the latest migration version
        cursor.execute("INSERT INTO alembic_version VALUES ('3d415c3faa09')")
        print("   ✅ Set migration version")
        
        # Create indexes for better performance
        print("📊 Creating indexes...")
        indexes = [
            "CREATE INDEX ix_images_id ON images(id)",
            "CREATE INDEX ix_hospitals_id ON hospitals(id)",
            "CREATE INDEX ix_hospitals_name ON hospitals(name)",
            "CREATE INDEX ix_doctors_id ON doctors(id)",
            "CREATE INDEX ix_doctors_name ON doctors(name)",
            "CREATE INDEX ix_treatments_id ON treatments(id)",
            "CREATE INDEX ix_treatments_name ON treatments(name)",
            "CREATE INDEX ix_treatments_treatment_type ON treatments(treatment_type)",
            "CREATE INDEX ix_package_bookings_id ON package_bookings(id)",
            "CREATE INDEX ix_package_bookings_email ON package_bookings(email)",
            "CREATE INDEX ix_admins_id ON admins(id)",
            "CREATE INDEX ix_admins_username ON admins(username)",
            "CREATE INDEX ix_admins_email ON admins(email)",
            "CREATE INDEX ix_contact_us_id ON contact_us(id)",
            "CREATE INDEX ix_contact_us_email ON contact_us(email)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        print("\n🎉 Database created successfully with complete schema!")
        
        # Show created tables with column count
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"\n📋 Created {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"  - {table_name} ({len(columns)} columns)")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def ensure_admin_exists():
    """Ensure default admin user exists"""
    try:
        from app.auth import get_password_hash
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if admin already exists
        cursor.execute("SELECT id FROM admins WHERE username = 'admin'")
        if cursor.fetchone():
            print("   ✅ Default admin user exists")
            return
        
        # Create admin user
        password_hash = get_password_hash("password123")
        cursor.execute("""
            INSERT INTO admins (username, email, password_hash, is_active, is_super_admin, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, ("admin", "admin@example.com", password_hash, True, True))
        
        conn.commit()
        print("   ✅ Created default admin user (username: admin, password: password123)")
        
    except Exception as e:
        print(f"   ⚠️  Could not create admin user: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Checking Medi-Tour Database...")
    
    if check_database_schema():
        print("📊 Database is ready! No changes needed.")
        ensure_admin_exists()
    else:
        print("🔧 Database needs initialization...")
        create_tables()
        ensure_admin_exists()
    
    print("\n🎯 Database ready! You can now start the API server.")
    print("   📚 API Documentation: http://localhost:8000/docs")
    print("   🔐 Admin Login: username=admin, password=password123")