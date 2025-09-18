#!/usr/bin/env python3
"""
Fix database table structure to match SQLAlchemy models
"""
import sqlite3

DB_PATH = "./meditour.db"

def update_database_schema():
    """Update database tables to match current models"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("🔧 Updating database schema...")
        
        # Fix doctors table - add missing columns
        print("📋 Updating doctors table...")
        missing_doctor_columns = [
            "ALTER TABLE doctors ADD COLUMN profile_photo VARCHAR(1000)",
            "ALTER TABLE doctors ADD COLUMN description TEXT", 
            "ALTER TABLE doctors ADD COLUMN highlights TEXT",
            "ALTER TABLE doctors ADD COLUMN awards TEXT"
        ]
        
        for sql in missing_doctor_columns:
            try:
                cursor.execute(sql)
                print(f"   ✅ Added column: {sql.split('ADD COLUMN')[1].strip()}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"   ⏭️  Column already exists: {sql.split('ADD COLUMN')[1].strip()}")
                else:
                    print(f"   ❌ Error: {e}")
        
        # Fix treatments table - add missing columns
        print("📋 Updating treatments table...")
        missing_treatment_columns = [
            "ALTER TABLE treatments ADD COLUMN short_description TEXT",
            "ALTER TABLE treatments ADD COLUMN long_description TEXT",
            "ALTER TABLE treatments ADD COLUMN treatment_type VARCHAR(100)",
            "ALTER TABLE treatments ADD COLUMN price_exact REAL",
            "ALTER TABLE treatments ADD COLUMN other_hospital_name VARCHAR(200)",
            "ALTER TABLE treatments ADD COLUMN doctor_id INTEGER",
            "ALTER TABLE treatments ADD COLUMN other_doctor_name VARCHAR(200)",
            "ALTER TABLE treatments ADD COLUMN location VARCHAR(500)"
        ]
        
        for sql in missing_treatment_columns:
            try:
                cursor.execute(sql)
                print(f"   ✅ Added column: {sql.split('ADD COLUMN')[1].strip()}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"   ⏭️  Column already exists: {sql.split('ADD COLUMN')[1].strip()}")
                else:
                    print(f"   ❌ Error: {e}")
        
        # Fix package_bookings table - add missing columns
        print("📋 Updating package_bookings table...")
        missing_booking_columns = [
            "ALTER TABLE package_bookings ADD COLUMN name VARCHAR(200)",
            "ALTER TABLE package_bookings ADD COLUMN service_type VARCHAR(50)",
            "ALTER TABLE package_bookings ADD COLUMN service_ref VARCHAR(200)",
            "ALTER TABLE package_bookings ADD COLUMN budget_range VARCHAR(50)",
            "ALTER TABLE package_bookings ADD COLUMN medical_history_file VARCHAR(1000)",
            "ALTER TABLE package_bookings ADD COLUMN user_query TEXT",
            "ALTER TABLE package_bookings ADD COLUMN travel_assistant BOOLEAN DEFAULT 0",
            "ALTER TABLE package_bookings ADD COLUMN stay_assistant BOOLEAN DEFAULT 0"
        ]
        
        for sql in missing_booking_columns:
            try:
                cursor.execute(sql)
                print(f"   ✅ Added column: {sql.split('ADD COLUMN')[1].strip()}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"   ⏭️  Column already exists: {sql.split('ADD COLUMN')[1].strip()}")
                else:
                    print(f"   ❌ Error: {e}")
        
        # Rename columns in package_bookings to match model
        print("📋 Updating column names...")
        try:
            # Check if patient_name exists and name doesn't
            cursor.execute("PRAGMA table_info(package_bookings)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'patient_name' in columns and 'name' not in columns:
                cursor.execute("ALTER TABLE package_bookings RENAME COLUMN patient_name TO name")
                print("   ✅ Renamed patient_name to name")
            if 'patient_email' in columns and 'email' not in columns:
                cursor.execute("ALTER TABLE package_bookings RENAME COLUMN patient_email TO email")
                print("   ✅ Renamed patient_email to email")
            if 'patient_phone' in columns and 'phone' not in columns:
                cursor.execute("ALTER TABLE package_bookings RENAME COLUMN patient_phone TO phone")
                print("   ✅ Renamed patient_phone to phone")
                
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  Column rename issue: {e}")
        
        conn.commit()
        print("\n✅ Database schema updated successfully!")
        
        # Show current table structures
        print("\n📊 Current table structures:")
        tables = ['doctors', 'treatments', 'package_bookings']
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\n{table}:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
                
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_schema()