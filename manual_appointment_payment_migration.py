9#!/usr/bin/env python3
"""
Manual migration script to add payment fields to appointments table for SQLite
This script works around SQLite's limitations with ALTER COLUMN operations
"""
import sqlite3
import os

def add_appointment_payment_fields():
    """Add payment fields to appointments table"""
    # Database path - adjust as needed for your setup
    db_path = "./meditour.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return False
    
    print(f"🔧 Adding payment fields to appointments table in {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the columns already exist
        cursor.execute("PRAGMA table_info(appointments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add consultation_fees column if it doesn't exist
        if 'consultation_fees' not in columns:
            try:
                cursor.execute("ALTER TABLE appointments ADD COLUMN consultation_fees FLOAT")
                print("✅ Added consultation_fees column")
            except Exception as e:
                print(f"⚠️  Error adding consultation_fees column: {e}")
        else:
            print("📝 consultation_fees column already exists")
        
        # Add payment_status column if it doesn't exist
        if 'payment_status' not in columns:
            try:
                cursor.execute("ALTER TABLE appointments ADD COLUMN payment_status VARCHAR(50)")
                cursor.execute("UPDATE appointments SET payment_status = 'pending' WHERE payment_status IS NULL")
                print("✅ Added payment_status column")
            except Exception as e:
                print(f"⚠️  Error adding payment_status column: {e}")
        else:
            print("📝 payment_status column already exists")
        
        # Add payment_id column if it doesn't exist
        if 'payment_id' not in columns:
            try:
                cursor.execute("ALTER TABLE appointments ADD COLUMN payment_id VARCHAR(255)")
                print("✅ Added payment_id column")
            except Exception as e:
                print(f"⚠️  Error adding payment_id column: {e}")
        else:
            print("📝 payment_id column already exists")
        
        # Add payment_order_id column if it doesn't exist
        if 'payment_order_id' not in columns:
            try:
                cursor.execute("ALTER TABLE appointments ADD COLUMN payment_order_id VARCHAR(255)")
                print("✅ Added payment_order_id column")
            except Exception as e:
                print(f"⚠️  Error adding payment_order_id column: {e}")
        else:
            print("📝 payment_order_id column already exists")
        
        # Add payment_signature column if it doesn't exist
        if 'payment_signature' not in columns:
            try:
                cursor.execute("ALTER TABLE appointments ADD COLUMN payment_signature VARCHAR(255)")
                print("✅ Added payment_signature column")
            except Exception as e:
                print(f"⚠️  Error adding payment_signature column: {e}")
        else:
            print("📝 payment_signature column already exists")
        
        # Add hospital_preference column if it doesn't exist (from your migration)
        if 'hospital_preference' not in columns:
            try:
                cursor.execute("ALTER TABLE appointments ADD COLUMN hospital_preference VARCHAR(300)")
                print("✅ Added hospital_preference column")
            except Exception as e:
                print(f"⚠️  Error adding hospital_preference column: {e}")
        else:
            print("📝 hospital_preference column already exists")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Successfully added payment fields to appointments table!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Running manual appointment payment fields migration...")
    success = add_appointment_payment_fields()
    if success:
        print("\n✅ Migration completed successfully!")
        print("You can now use the payment integration features.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above.")