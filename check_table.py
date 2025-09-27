#!/usr/bin/env python3
"""Script to check the structure of PackageBooking table"""
import sqlite3

def check_table_structure():
    """Check the current structure of package_bookings table"""
    conn = sqlite3.connect('meditour.db')
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute("PRAGMA table_info(package_bookings)")
    columns = cursor.fetchall()
    
    print("Current package_bookings table structure:")
    print("=" * 50)
    for col in columns:
        print(f"Column: {col[1]}, Type: {col[2]}, Not Null: {col[3]}, Default: {col[4]}, PK: {col[5]}")
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='package_bookings'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print(f"\nTable exists: {table_exists[0]}")
    else:
        print("Table does not exist")
    
    conn.close()

if __name__ == "__main__":
    check_table_structure()