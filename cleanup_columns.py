#!/usr/bin/env python3
"""Script to clean up old columns from PackageBooking table"""
import sqlite3

def cleanup_old_columns():
    """Remove old columns that are no longer needed"""
    conn = sqlite3.connect('meditour.db')
    cursor = conn.cursor()
    
    # First, check if there's any data that needs to be migrated
    cursor.execute("SELECT id, name, phone, budget_range FROM package_bookings WHERE first_name IS NULL OR last_name IS NULL OR mobile_no IS NULL")
    records_to_migrate = cursor.fetchall()
    
    if records_to_migrate:
        print(f"Found {len(records_to_migrate)} records that need data migration")
        
        # Migrate data from old columns to new columns
        for record in records_to_migrate:
            record_id, name, phone, budget_range = record
            
            # Split name into first and last name
            if name and name.strip():
                name_parts = name.strip().split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else 'User'
            else:
                first_name = 'Unknown'
                last_name = 'User'
            
            mobile_no = phone if phone else 'Not provided'
            budget = budget_range if budget_range else None
            
            cursor.execute("""
                UPDATE package_bookings 
                SET first_name = ?, last_name = ?, mobile_no = ?, budget = ?
                WHERE id = ?
            """, (first_name, last_name, mobile_no, budget, record_id))
        
        print("Data migration completed")
    
    # Now create a new table without the old columns
    cursor.execute("""
        CREATE TABLE package_bookings_new (
            id INTEGER PRIMARY KEY,
            email VARCHAR(300) NOT NULL,
            first_name VARCHAR(150) NOT NULL,
            last_name VARCHAR(150) NOT NULL,
            mobile_no VARCHAR(80) NOT NULL,
            treatment_id INTEGER,
            budget VARCHAR(100),
            medical_history_file VARCHAR(1000),
            doctor_preference VARCHAR(300),
            hospital_preference VARCHAR(300),
            user_query TEXT,
            travel_assistant BOOLEAN,
            stay_assistant BOOLEAN,
            created_at DATETIME
        )
    """)
    
    # Copy data from old table to new table
    cursor.execute("""
        INSERT INTO package_bookings_new 
        (id, email, first_name, last_name, mobile_no, treatment_id, budget, 
         medical_history_file, doctor_preference, hospital_preference, 
         user_query, travel_assistant, stay_assistant, created_at)
        SELECT 
            id, email, first_name, last_name, mobile_no, treatment_id, budget, 
            medical_history_file, doctor_preference, hospital_preference, 
            user_query, travel_assistant, stay_assistant, created_at
        FROM package_bookings
    """)
    
    # Drop old table
    cursor.execute("DROP TABLE package_bookings")
    
    # Rename new table
    cursor.execute("ALTER TABLE package_bookings_new RENAME TO package_bookings")
    
    # Create index
    cursor.execute("CREATE INDEX ix_package_bookings_treatment_id ON package_bookings (treatment_id)")
    
    conn.commit()
    conn.close()
    print("Old columns removed successfully")

if __name__ == "__main__":
    cleanup_old_columns()