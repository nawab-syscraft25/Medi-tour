#!/usr/bin/env python3
"""
Create contact_us table with the correct schema (first_name, last_name)
"""

import sqlite3
import os
from datetime import datetime

def create_contact_table():
    """Create contact_us table with correct schema"""
    
    # Try to find the database file
    possible_db_paths = ["app.db", "medi_tour.db", "meditour.db"]
    db_path = None
    
    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print(f"Database file not found! Tried: {possible_db_paths}")
        return False
    
    print(f"Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if contact_us table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contact_us'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ contact_us table already exists!")
            
            # Check current schema
            cursor.execute("PRAGMA table_info(contact_us)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'first_name' in column_names and 'last_name' in column_names:
                print("✅ Table already has correct schema with first_name and last_name!")
                conn.close()
                return True
            else:
                print("❌ Table exists but has incorrect schema")
                print(f"Current columns: {column_names}")
                conn.close()
                return False
        
        print("Creating contact_us table with correct schema...")
        
        # Create the table with the correct schema
        cursor.execute('''
            CREATE TABLE contact_us (
                id INTEGER NOT NULL PRIMARY KEY,
                first_name VARCHAR(150) NOT NULL,
                last_name VARCHAR(150) NOT NULL,
                email VARCHAR(300) NOT NULL,
                phone VARCHAR(80),
                subject VARCHAR(500),
                message TEXT NOT NULL,
                service_type VARCHAR(100),
                is_read BOOLEAN DEFAULT 0,
                admin_response TEXT,
                responded_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute("CREATE INDEX ix_contact_us_id ON contact_us (id)")
        cursor.execute("CREATE INDEX ix_contact_us_email ON contact_us (email)")
        cursor.execute("CREATE INDEX ix_contact_us_service_type ON contact_us (service_type)")
        
        conn.commit()
        conn.close()
        
        print("✅ contact_us table created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_contact_table()
    if success:
        print("\n🎉 Contact table is ready!")
        print("You can now use the contact API endpoints.")
    else:
        print("\n❌ Failed to create contact table!")
