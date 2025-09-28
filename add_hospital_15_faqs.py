#!/usr/bin/env python3

import asyncio
import sqlite3
from datetime import datetime

async def add_hospital_15_faqs():
    """Add sample FAQs to Hospital 15 for testing"""
    
    # Use regular sqlite3 for simplicity
    conn = sqlite3.connect('meditour.db')
    cursor = conn.cursor()
    
    # Sample FAQs for Hospital 15
    sample_faqs = [
        {
            'question': 'What are your visiting hours?',
            'answer': 'Our visiting hours are from 9:00 AM to 8:00 PM daily.\nWe allow 2 visitors per patient at a time.'
        },
        {
            'question': 'Do you accept insurance?',
            'answer': 'Yes, we accept most major insurance plans.\nPlease contact our billing department for specific coverage details.'
        },
        {
            'question': 'What emergency services do you provide?',
            'answer': 'We provide 24/7 emergency care including:\n- Trauma care\n- Cardiac emergencies\n- Stroke treatment\n- Surgical emergencies'
        }
    ]
    
    # Add FAQs
    now = datetime.now().isoformat()
    for i, faq in enumerate(sample_faqs):
        cursor.execute("""
            INSERT INTO faqs (owner_type, owner_id, question, answer, position, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'hospital',
            15,
            faq['question'],
            faq['answer'],
            i,
            1,  # is_active = True
            now,
            now
        ))
    
    conn.commit()
    
    # Verify the FAQs were added
    cursor.execute("SELECT id, question FROM faqs WHERE owner_type='hospital' AND owner_id=15")
    results = cursor.fetchall()
    
    print(f"✅ Added {len(sample_faqs)} FAQs to Hospital 15:")
    for result in results:
        print(f"  FAQ {result[0]}: {result[1]}")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(add_hospital_15_faqs())