#!/usr/bin/env python3
"""
Simple script to fix doctor FAQ handling in admin_web.py
"""

def fix_doctor_faq():
    # Read the file
    with open('app/admin_web.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace doctor creation FAQ parameters
    old_create_params = """    faq_questions: List[str] = Form(default=[]),
    faq_answers: List[str] = Form(default=[]),"""
    
    new_create_params = """    faq1_question: str = Form(""),
    faq1_answer: str = Form(""),
    faq2_question: str = Form(""),
    faq2_answer: str = Form(""),
    faq3_question: str = Form(""),
    faq3_answer: str = Form(""),
    faq4_question: str = Form(""),
    faq4_answer: str = Form(""),
    faq5_question: str = Form(""),
    faq5_answer: str = Form(""),"""
    
    # Replace in doctor creation function
    if old_create_params in content:
        content = content.replace(old_create_params, new_create_params, 1)
        print("✓ Updated doctor creation parameters")
    else:
        print("✗ Could not find doctor creation parameters to replace")
    
    # Replace doctor creation FAQ handling
    old_create_handling = """        # Handle FAQ creation
        for question, answer in zip(faq_questions, faq_answers):
            if question.strip() and answer.strip():  # Only create FAQ if both fields have content
                faq = FAQ(
                    owner_type="doctor",
                    owner_id=doctor.id,
                    question=question.strip(),
                    answer=answer.strip()
                )
                db.add(faq)"""
    
    new_create_handling = """        # Set FAQ fields directly on doctor model
        doctor.faq1_question = faq1_question.strip() if faq1_question else None
        doctor.faq1_answer = faq1_answer.strip() if faq1_answer else None
        doctor.faq2_question = faq2_question.strip() if faq2_question else None
        doctor.faq2_answer = faq2_answer.strip() if faq2_answer else None
        doctor.faq3_question = faq3_question.strip() if faq3_question else None
        doctor.faq3_answer = faq3_answer.strip() if faq3_answer else None
        doctor.faq4_question = faq4_question.strip() if faq4_question else None
        doctor.faq4_answer = faq4_answer.strip() if faq4_answer else None
        doctor.faq5_question = faq5_question.strip() if faq5_question else None
        doctor.faq5_answer = faq5_answer.strip() if faq5_answer else None"""
    
    if old_create_handling in content:
        content = content.replace(old_create_handling, new_create_handling, 1)
        print("✓ Updated doctor creation FAQ handling")
    else:
        print("✗ Could not find doctor creation FAQ handling to replace")
    
    # Write the file back
    with open('app/admin_web.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Doctor FAQ backend fixes applied!")

if __name__ == "__main__":
    fix_doctor_faq()
