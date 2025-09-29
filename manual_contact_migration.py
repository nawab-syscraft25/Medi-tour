#!/usr/bin/env python3
"""
Manual migration script to handle contact_us table schema change
from 'name' field to 'first_name' and 'last_name' fields
"""

import sqlite3
import os
from datetime import datetime

def migrate_contact_table():
    """Migrate contact_us table from name to first_name/last_name"""
    
    # Use the database file that has the contact data
    db_path = "meditour.db"  # This one has the existing contact data
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    print(f"Using database: {db_path}")
    
    # Create backup
    backup_path = f"app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        # Create backup
        print("Creating database backup...")
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(contact_us)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'first_name' in columns and 'last_name' in columns:
            print("Migration already completed!")
            conn.close()
            return True
        
        if 'name' not in columns:
            print("Warning: 'name' column not found in contact_us table")
            conn.close()
            return False
        
        print("Starting migration...")
        
        # Step 1: Create new table with updated schema
        cursor.execute('''
            CREATE TABLE contact_us_new (
                id INTEGER PRIMARY KEY,
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
        
        # Step 2: Migrate existing data
        cursor.execute("SELECT * FROM contact_us")
        rows = cursor.fetchall()
        
        print(f"Migrating {len(rows)} contact records...")
        
        for row in rows:
            # Parse the existing data
            id_val, name, email, phone, subject, message, is_read, admin_response, responded_at, created_at = row
            
            # Split name into first_name and last_name
            if name:
                name_parts = name.strip().split(' ', 1)
                first_name = name_parts[0] if name_parts else 'Unknown'
                last_name = name_parts[1] if len(name_parts) > 1 else 'User'
            else:
                first_name = 'Unknown'
                last_name = 'User'
            
            # Insert into new table
            cursor.execute('''
                INSERT INTO contact_us_new 
                (id, first_name, last_name, email, phone, subject, message, service_type, 
                 is_read, admin_response, responded_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id_val, first_name, last_name, email, phone, subject, message, None,
                  is_read, admin_response, responded_at, created_at))
        
        # Step 3: Drop old table and rename new table
        cursor.execute("DROP TABLE contact_us")
        cursor.execute("ALTER TABLE contact_us_new RENAME TO contact_us")
        
        # Step 4: Create index on email
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_contact_us_email ON contact_us (email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_contact_us_service_type ON contact_us (service_type)")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        print(f"Backup saved as: {backup_path}")
        return True
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        if os.path.exists(backup_path):
            print(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, db_path)
        return False

if __name__ == "__main__":
    success = migrate_contact_table()
    if success:
        print("\n✅ Migration completed successfully!")
        print("You can now run your application with the updated schema.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above.")
