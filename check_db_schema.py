#!/usr/bin/env python3
"""
Check current database schema for contact_us table
"""

import sqlite3
import os

def check_contact_table_schema():
    """Check the current schema of contact_us table"""
    
    # Check the main database file with migrated data
    db_path = "meditour.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    print(f"Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if contact_us table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contact_us'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ contact_us table does not exist!")
            conn.close()
            return
        
        # Get table schema
        cursor.execute("PRAGMA table_info(contact_us)")
        columns = cursor.fetchall()
        
        print("\n📋 Current contact_us table schema:")
        print("-" * 50)
        for col in columns:
            cid, name, type_, notnull, default, pk = col
            nullable = "NOT NULL" if notnull else "NULL"
            primary = "PRIMARY KEY" if pk else ""
            print(f"{name:15} {type_:15} {nullable:10} {primary}")
        
        # Check current data
        cursor.execute("SELECT COUNT(*) FROM contact_us")
        count = cursor.fetchone()[0]
        print(f"\n📊 Total records: {count}")
        
        if count > 0:
            # Show sample data
            cursor.execute("SELECT * FROM contact_us LIMIT 3")
            rows = cursor.fetchall()
            print("\n📝 Sample data (first 3 records):")
            print("-" * 50)
            column_names = [description[0] for description in cursor.description]
            print(" | ".join(f"{name:12}" for name in column_names))
            print("-" * (len(column_names) * 15))
            for row in rows:
                print(" | ".join(f"{str(val)[:12]:12}" for val in row))
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    check_contact_table_schema()
