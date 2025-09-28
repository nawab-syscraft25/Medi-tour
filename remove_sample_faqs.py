#!/usr/bin/env python3

import sqlite3

def remove_sample_faqs():
    """Remove the sample FAQs I added for Hospital 15"""
    try:
        conn = sqlite3.connect('meditour.db')
        cursor = conn.cursor()
        
        # Remove the sample FAQs for Hospital 15
        cursor.execute("DELETE FROM faqs WHERE owner_type='hospital' AND owner_id=15")
        rows_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ Removed {rows_deleted} sample FAQs from Hospital 15")
        print("Now you can add your own custom FAQs through the form!")
        
    except Exception as e:
        print(f"Error removing FAQs: {e}")

if __name__ == "__main__":
    remove_sample_faqs()