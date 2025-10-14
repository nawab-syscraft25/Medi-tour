import sqlite3
import json

# Test time slots functionality
def test_time_slots():
    # Connect to database
    conn = sqlite3.connect('meditour.db')
    cursor = conn.cursor()
    
    # Create a sample time slots JSON
    time_slots = {
        "Monday": "9:00 AM - 5:00 PM",
        "Tuesday": "9:00 AM - 5:00 PM",
        "Wednesday": "Off",
        "Thursday": "9:00 AM - 5:00 PM",
        "Friday": "9:00 AM - 5:00 PM",
        "Saturday": "10:00 AM - 2:00 PM",
        "Sunday": "Off"
    }
    
    time_slots_json = json.dumps(time_slots)
    print(f"Time slots JSON: {time_slots_json}")
    
    # Test inserting a doctor with time slots
    cursor.execute("""
        INSERT INTO doctors (
            name, profile_photo, description, designation, experience_years, 
            hospital_id, gender, skills, qualifications, highlights, awards, 
            created_at, specialization, qualification, rating, is_active, 
            is_featured, short_description, long_description, consultancy_fee, 
            location, faq1_question, faq1_answer, faq2_question, faq2_answer, 
            faq3_question, faq3_answer, faq4_question, faq4_answer, 
            faq5_question, faq5_answer, time_slots
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Dr. Test Doctor", None, None, "Test Designation", 10, 
        None, "Male", None, None, None, None, 
        "2023-01-01 00:00:00", "Test Specialization", "Test Qualification", 4.5, 1, 
        1, "Test short description", "Test long description", 500.0, 
        "Test Location", None, None, None, None, 
        None, None, None, None, 
        None, None, time_slots_json
    ))
    
    doctor_id = cursor.lastrowid
    conn.commit()
    
    print(f"Inserted doctor with ID: {doctor_id}")
    
    # Retrieve the doctor and check time slots
    cursor.execute("SELECT time_slots FROM doctors WHERE id = ?", (doctor_id,))
    result = cursor.fetchone()
    
    if result:
        retrieved_time_slots = result[0]
        print(f"Retrieved time slots: {retrieved_time_slots}")
        
        # Parse and display
        if retrieved_time_slots:
            try:
                parsed_slots = json.loads(retrieved_time_slots)
                print("Parsed time slots:")
                for day, hours in parsed_slots.items():
                    print(f"  {day}: {hours}")
            except json.JSONDecodeError as e:
                print(f"Error parsing time slots: {e}")
        else:
            print("No time slots found")
    
    # Clean up - delete the test doctor
    cursor.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
    conn.commit()
    print(f"Deleted test doctor with ID: {doctor_id}")
    
    conn.close()

if __name__ == "__main__":
    test_time_slots()