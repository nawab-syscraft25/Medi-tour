#!/usr/bin/env python3
"""
Comprehensive script to fix all remaining FAQ issues in admin_web.py
"""

def fix_all_faq_issues():
    # Read the file
    with open('app/admin_web.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove all debug lines that reference old faq_questions/faq_answers
    debug_lines_to_remove = [
        'print(f"DEBUG DOCTOR: FAQ Questions received: {faq_questions}")',
        'print(f"DEBUG DOCTOR: FAQ Answers received: {faq_answers}")',
        'print(f"DEBUG DOCTOR: Questions count: {len(faq_questions)}, Answers count: {len(faq_answers)}")',
        'logger.debug(f"[DEBUG] Received FAQ questions Nawab: {faq_questions}")',
        'logger.debug(f"[DEBUG] Received FAQ answers: {faq_answers}")',
        'print(f"[DEBUG] Received FAQ questions: {faq_questions}")',
        'print(f"[DEBUG] Received FAQ answers: {faq_answers}")'
    ]
    
    for debug_line in debug_lines_to_remove:
        if debug_line in content:
            content = content.replace(debug_line, '# Debug line removed')
            print(f"✓ Removed debug line: {debug_line[:50]}...")
    
    # Remove any remaining references to faq_questions and faq_answers in hospital update
    old_hospital_faq_handling = """        # Normalize to list if only one FAQ is present
        if isinstance(faq_questions, str):
            faq_questions = [faq_questions]
        if isinstance(faq_answers, str):
            faq_answers = [faq_answers]

        # Add new FAQs, skipping duplicates
        seen_faqs = set()
        faq_list = []
        for question, answer in zip(faq_questions, faq_answers):
            q = question.strip()
            a = answer.strip()
            if q and a:"""
    
    if old_hospital_faq_handling in content:
        content = content.replace(old_hospital_faq_handling, '        # FAQ handling removed - using direct model fields now')
        print("✓ Removed old hospital FAQ handling")
    
    # Write the file back
    with open('app/admin_web.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ All FAQ issue fixes applied!")

if __name__ == "__main__":
    fix_all_faq_issues()
