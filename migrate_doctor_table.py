#!/usr/bin/env python3
"""
Migration script to update doctor table with new fields:
- Split description into short_description and long_description
- Add consultancy_fee field
"""

import sqlite3
import os
from datetime import datetime

def migrate_doctor_table():
    """Migrate doctor table to add new fields"""
    
    db_path = "meditour.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    print(f"Using database: {db_path}")
    
    # Create backup
    backup_path = f"doctor_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        # Create backup
        print("Creating database backup...")
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current table structure
        cursor.execute("PRAGMA table_info(doctors)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"Current columns: {column_names}")
        
        # Check if migration is needed
        if 'short_description' in column_names and 'consultancy_fee' in column_names:
            print("✅ Migration already completed!")
            conn.close()
            return True
        
        print("Starting doctor table migration...")
        
        # Step 1: Add new columns
        if 'short_description' not in column_names:
            cursor.execute("ALTER TABLE doctors ADD COLUMN short_description VARCHAR(500)")
            print("✅ Added short_description column")
        
        if 'long_description' not in column_names:
            cursor.execute("ALTER TABLE doctors ADD COLUMN long_description TEXT")
            print("✅ Added long_description column")
        
        if 'consultancy_fee' not in column_names:
            cursor.execute("ALTER TABLE doctors ADD COLUMN consultancy_fee FLOAT")
            print("✅ Added consultancy_fee column")
        
        if 'specialization' not in column_names:
            cursor.execute("ALTER TABLE doctors ADD COLUMN specialization VARCHAR(200)")
            print("✅ Added specialization column")
        
        if 'qualification' not in column_names:
            cursor.execute("ALTER TABLE doctors ADD COLUMN qualification VARCHAR(500)")
            print("✅ Added qualification column")
        
        # Step 2: Migrate existing description data
        if 'description' in column_names:
            cursor.execute("SELECT id, description FROM doctors WHERE description IS NOT NULL")
            doctors_with_desc = cursor.fetchall()
            
            print(f"Migrating description data for {len(doctors_with_desc)} doctors...")
            
            for doctor_id, description in doctors_with_desc:
                if description:
                    # If description is long, split it
                    if len(description) > 300:
                        short_desc = description[:300] + "..."
                        long_desc = description
                    else:
                        short_desc = description
                        long_desc = description
                    
                    cursor.execute("""
                        UPDATE doctors 
                        SET short_description = ?, long_description = ? 
                        WHERE id = ?
                    """, (short_desc, long_desc, doctor_id))
            
            print("✅ Migrated existing description data")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Doctor table migration completed successfully!")
        print(f"Backup saved as: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        if os.path.exists(backup_path):
            print(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, db_path)
        return False

if __name__ == "__main__":
    success = migrate_doctor_table()
    if success:
        print("\n🎉 Doctor table migration completed!")
        print("New fields added:")
        print("- short_description (VARCHAR(500))")
        print("- long_description (TEXT)")
        print("- consultancy_fee (FLOAT)")
        print("- specialization (VARCHAR(200))")
        print("- qualification (VARCHAR(500))")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above.")
