#!/usr/bin/env python3
"""
Fix contact_us table structure
"""
import sqlite3

def fix_contact_table():
    """Add missing columns to contact_us table"""
    conn = sqlite3.connect("./meditour.db")
    cursor = conn.cursor()
    
    try:
        # Add missing columns to contact_us table
        try:
            cursor.execute("ALTER TABLE contact_us ADD COLUMN is_read BOOLEAN DEFAULT 0")
            print("✅ Added is_read column")
        except:
            print("📝 is_read column already exists")
            
        try:
            cursor.execute("ALTER TABLE contact_us ADD COLUMN responded_at DATETIME")
            print("✅ Added responded_at column")
        except:
            print("📝 responded_at column already exists")
            
        conn.commit()
        print("✅ Contact table structure updated!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Fixing contact_us table structure...")
    fix_contact_table()