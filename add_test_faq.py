#!/usr/bin/env python3

import sqlite3
from datetime import datetime

def add_test_faq():
    """Add a test FAQ directly to the database to verify the form will display it"""
    
    conn = sqlite3.connect('meditour.db')
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Add a test FAQ for Hospital 15
    cursor.execute("""
        INSERT INTO faqs (owner_type, owner_id, question, answer, position, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'hospital',
        15,
        'What facilities are available?',
        'We have state-of-the-art medical equipment and modern facilities.\nOur services include 24/7 emergency care and specialized departments.',
        0,
        1,  # is_active = True
        now,
        now
    ))
    
    conn.commit()
    
    # Verify it was added
    cursor.execute("SELECT id, question FROM faqs WHERE owner_type='hospital' AND owner_id=15")
    results = cursor.fetchall()
    
    print(f"✅ Added test FAQ to Hospital 15:")
    for result in results:
        print(f"  FAQ {result[0]}: {result[1]}")
    
    conn.close()

if __name__ == "__main__":
    add_test_faq()