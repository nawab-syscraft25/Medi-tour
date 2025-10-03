#!/usr/bin/env python3
"""
Simple migration script to add FAQ columns to Hospital, Doctor, and Treatment tables
"""

import sqlite3
import os

def add_faq_columns():
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
        # Add FAQ columns to hospitals table
        print("Adding FAQ columns to hospitals table...")
        faq_columns = [
            "faq1_question TEXT",
            "faq1_answer TEXT", 
            "faq2_question TEXT",
            "faq2_answer TEXT",
            "faq3_question TEXT", 
            "faq3_answer TEXT",
            "faq4_question TEXT",
            "faq4_answer TEXT",
            "faq5_question TEXT",
            "faq5_answer TEXT"
        ]
        
        for column in faq_columns:
            try:
                cursor.execute(f"ALTER TABLE hospitals ADD COLUMN {column}")
                print(f"  Added {column.split()[0]} to hospitals")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"  Column {column.split()[0]} already exists in hospitals")
                else:
                    raise
        
        # Add FAQ columns to doctors table
        print("Adding FAQ columns to doctors table...")
        for column in faq_columns:
            try:
                cursor.execute(f"ALTER TABLE doctors ADD COLUMN {column}")
                print(f"  Added {column.split()[0]} to doctors")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"  Column {column.split()[0]} already exists in doctors")
                else:
                    raise
        
        # Add FAQ columns to treatments table
        print("Adding FAQ columns to treatments table...")
        for column in faq_columns:
            try:
                cursor.execute(f"ALTER TABLE treatments ADD COLUMN {column}")
                print(f"  Added {column.split()[0]} to treatments")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"  Column {column.split()[0]} already exists in treatments")
                else:
                    raise
        
        conn.commit()
        print("Successfully added FAQ columns to all tables!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_faq_columns()
