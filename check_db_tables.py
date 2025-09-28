#!/usr/bin/env python3

import sqlite3

def check_database():
    """Check if FAQ table exists and show database structure"""
    # Check both possible database files
    db_files = ['medi_tour.db', 'meditour.db']
    
    for db_file in db_files:
        print(f"\n=== Checking {db_file} ===")
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Check if FAQs table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='faqs'")
            result = cursor.fetchone()
            
            if result:
                print("✅ FAQs table exists!")
                
                # Count total FAQs
                cursor.execute('SELECT COUNT(*) FROM faqs')
                count = cursor.fetchone()[0]
                print(f"Total FAQs in database: {count}")
                
                if count > 0:
                    # Show FAQs by entity type
                    cursor.execute('SELECT owner_type, owner_id, COUNT(*) FROM faqs GROUP BY owner_type, owner_id ORDER BY owner_type, owner_id')
                    groups = cursor.fetchall()
                    print("\nFAQs by entity:")
                    for group in groups:
                        print(f"  {group[0]} {group[1]}: {group[2]} FAQs")
                    
                    # Show specific hospital 15 FAQs
                    cursor.execute("SELECT id, question, is_active FROM faqs WHERE owner_type='hospital' AND owner_id=15")
                    hospital_15_faqs = cursor.fetchall()
                    print(f"\nHospital 15 FAQs: {len(hospital_15_faqs)} found")
                    for faq in hospital_15_faqs:
                        print(f"  FAQ {faq[0]}: {faq[1][:50]}... (Active: {faq[2]})")
            else:
                print("❌ FAQs table does NOT exist!")
                
                # Show all available tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"\nAvailable tables: {len(tables)} found")
                for table in tables:
                    print(f"  - {table[0]}")
            
            conn.close()
            
        except Exception as e:
            print(f"Error checking {db_file}: {e}")

if __name__ == "__main__":
    check_database()