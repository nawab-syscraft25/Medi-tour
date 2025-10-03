#!/usr/bin/env python3
"""
Check what tables exist in the database
"""

import sqlite3
import os

def check_tables():
    # Try different database paths
    db_paths = ["meditour.db", "medi_tour.db"]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print(f"No database found! Tried: {db_paths}")
        return
    
    print(f"Using database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
            
        # Check if we have any treatment-related tables
        for table in tables:
            table_name = table[0]
            if 'treatment' in table_name.lower() or 'hospital' in table_name.lower() or 'doctor' in table_name.lower():
                print(f"\nColumns in {table_name}:")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_tables()
