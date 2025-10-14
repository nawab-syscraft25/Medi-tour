#!/usr/bin/env python3
"""
Migration script to add time_slots column to doctors table
"""

import sqlite3
import os
from datetime import datetime

def migrate_doctor_time_slots():
    """Add time_slots column to doctors table"""
    
    db_path = "meditour.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    print(f"Using database: {db_path}")
    
    # Create backup
    backup_path = f"doctor_time_slots_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        # Create backup
        print("Creating database backup...")
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if time_slots column already exists
        cursor.execute("PRAGMA table_info(doctors)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'time_slots' in column_names:
            print("Column 'time_slots' already exists in doctors table")
            return True
        
        # Add time_slots column
        print("Adding time_slots column to doctors table...")
        cursor.execute("ALTER TABLE doctors ADD COLUMN time_slots TEXT")
        conn.commit()
        print("✅ Successfully added time_slots column to doctors table")
        
        return True
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = migrate_doctor_time_slots()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now use the time_slots field for doctors.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above.")