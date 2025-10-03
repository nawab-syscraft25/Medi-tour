#!/usr/bin/env python3
"""
Simple script to fix doctor update FAQ handling in admin_web.py
"""

def fix_doctor_update_faq():
    # Read the file
    with open('app/admin_web.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace doctor update FAQ parameters
    old_update_params = """    faq_questions: List[str] = Form(default=[]),
    faq_answers: List[str] = Form(default=[]),"""
    
    new_update_params = """    faq1_question: str = Form(""),
    faq1_answer: str = Form(""),
    faq2_question: str = Form(""),
    faq2_answer: str = Form(""),
    faq3_question: str = Form(""),
    faq3_answer: str = Form(""),
    faq4_question: str = Form(""),
    faq4_answer: str = Form(""),
    faq5_question: str = Form(""),
    faq5_answer: str = Form(""),"""
    
    # Replace in doctor update function (should be the remaining occurrence)
    if old_update_params in content:
        content = content.replace(old_update_params, new_update_params, 1)
        print("✓ Updated doctor update parameters")
    else:
        print("✗ Could not find doctor update parameters to replace")
    
    # Find and replace doctor update FAQ handling
    # Look for the pattern where doctor fields are being updated
    old_update_handling = """        # Handle FAQ updates - remove existing FAQs and create new ones
        print(f"DEBUG DOCTOR: Deleting existing FAQs for doctor {doctor.id}")
        await db.execute(delete(FAQ).where(FAQ.owner_type == "doctor", FAQ.owner_id == doctor.id))

        # Create new FAQs
        for question, answer in zip(faq_questions, faq_answers):
            if question.strip() and answer.strip():  # Only create FAQ if both fields have content
                faq = FAQ(
                    owner_type="doctor",
                    owner_id=doctor.id,
                    question=question.strip(),
                    answer=answer.strip()
                )
                db.add(faq)
                print(f"DEBUG DOCTOR: Created FAQ: {question[:50]}...")"""
    
    new_update_handling = """        # Update FAQ fields directly on doctor model
        doctor.faq1_question = faq1_question.strip() if faq1_question else None
        doctor.faq1_answer = faq1_answer.strip() if faq1_answer else None
        doctor.faq2_question = faq2_question.strip() if faq2_question else None
        doctor.faq2_answer = faq2_answer.strip() if faq2_answer else None
        doctor.faq3_question = faq3_question.strip() if faq3_question else None
        doctor.faq3_answer = faq3_answer.strip() if faq3_answer else None
        doctor.faq4_question = faq4_question.strip() if faq4_question else None
        doctor.faq4_answer = faq4_answer.strip() if faq4_answer else None
        doctor.faq5_question = faq5_question.strip() if faq5_question else None
        doctor.faq5_answer = faq5_answer.strip() if faq5_answer else None
        print(f"DEBUG DOCTOR: Updated FAQ fields for doctor {doctor.id}")"""
    
    if old_update_handling in content:
        content = content.replace(old_update_handling, new_update_handling, 1)
        print("✓ Updated doctor update FAQ handling")
    else:
        print("✗ Could not find doctor update FAQ handling to replace")
        # Try a simpler pattern
        simple_old = """        await db.execute(delete(FAQ).where(FAQ.owner_type == "doctor", FAQ.owner_id == doctor.id))"""
        if simple_old in content:
            # Find the broader context and replace it
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'delete(FAQ).where(FAQ.owner_type == "doctor"' in line:
                    # Find the end of this FAQ handling block
                    start_idx = i
                    end_idx = i
                    # Look for the next major section or commit
                    for j in range(i+1, len(lines)):
                        if 'await db.commit()' in lines[j] or 'except Exception' in lines[j]:
                            end_idx = j
                            break
                        if lines[j].strip() and not lines[j].startswith('        '):
                            end_idx = j
                            break
                    
                    # Replace this section
                    new_lines = [
                        "        # Update FAQ fields directly on doctor model",
                        "        doctor.faq1_question = faq1_question.strip() if faq1_question else None",
                        "        doctor.faq1_answer = faq1_answer.strip() if faq1_answer else None",
                        "        doctor.faq2_question = faq2_question.strip() if faq2_question else None",
                        "        doctor.faq2_answer = faq2_answer.strip() if faq2_answer else None",
                        "        doctor.faq3_question = faq3_question.strip() if faq3_question else None",
                        "        doctor.faq3_answer = faq3_answer.strip() if faq3_answer else None",
                        "        doctor.faq4_question = faq4_question.strip() if faq4_question else None",
                        "        doctor.faq4_answer = faq4_answer.strip() if faq4_answer else None",
                        "        doctor.faq5_question = faq5_question.strip() if faq5_question else None",
                        "        doctor.faq5_answer = faq5_answer.strip() if faq5_answer else None",
                        "        print(f\"DEBUG DOCTOR: Updated FAQ fields for doctor {doctor.id}\")",
                        ""
                    ]
                    
                    # Replace the old FAQ handling lines
                    lines[start_idx:end_idx] = new_lines
                    content = '\n'.join(lines)
                    print("✓ Updated doctor update FAQ handling (simple pattern)")
                    break
    
    # Write the file back
    with open('app/admin_web.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Doctor update FAQ backend fixes applied!")

if __name__ == "__main__":
    fix_doctor_update_faq()
