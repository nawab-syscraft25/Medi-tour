"""
Migration script to add payment fields to the appointments table
"""
from sqlalchemy import text
from meditour.db import get_db_sync
from app.models import Base

def upgrade():
    """Add payment fields to appointments table"""
    engine = get_db_sync()
    
    # Add new columns to appointments table
    with engine.connect() as conn:
        # Add consultation_fees column
        try:
            conn.execute(text("ALTER TABLE appointments ADD COLUMN consultation_fees FLOAT"))
            print("Added consultation_fees column")
        except Exception as e:
            print(f"Column consultation_fees may already exist: {e}")
        
        # Add payment_status column with default value
        try:
            conn.execute(text("ALTER TABLE appointments ADD COLUMN payment_status VARCHAR(50) DEFAULT 'pending'"))
            print("Added payment_status column")
        except Exception as e:
            print(f"Column payment_status may already exist: {e}")
        
        # Add payment_id column
        try:
            conn.execute(text("ALTER TABLE appointments ADD COLUMN payment_id VARCHAR(255)"))
            print("Added payment_id column")
        except Exception as e:
            print(f"Column payment_id may already exist: {e}")
        
        # Add payment_order_id column
        try:
            conn.execute(text("ALTER TABLE appointments ADD COLUMN payment_order_id VARCHAR(255)"))
            print("Added payment_order_id column")
        except Exception as e:
            print(f"Column payment_order_id may already exist: {e}")
        
        # Add payment_signature column
        try:
            conn.execute(text("ALTER TABLE appointments ADD COLUMN payment_signature VARCHAR(255)"))
            print("Added payment_signature column")
        except Exception as e:
            print(f"Column payment_signature may already exist: {e}")
        
        conn.commit()
    
    print("Migration completed successfully")

def downgrade():
    """Remove payment fields from appointments table"""
    engine = get_db_sync()
    
    # Remove columns from appointments table
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE appointments DROP COLUMN payment_signature"))
            print("Dropped payment_signature column")
        except Exception as e:
            print(f"Error dropping payment_signature column: {e}")
        
        try:
            conn.execute(text("ALTER TABLE appointments DROP COLUMN payment_order_id"))
            print("Dropped payment_order_id column")
        except Exception as e:
            print(f"Error dropping payment_order_id column: {e}")
        
        try:
            conn.execute(text("ALTER TABLE appointments DROP COLUMN payment_id"))
            print("Dropped payment_id column")
        except Exception as e:
            print(f"Error dropping payment_id column: {e}")
        
        try:
            conn.execute(text("ALTER TABLE appointments DROP COLUMN payment_status"))
            print("Dropped payment_status column")
        except Exception as e:
            print(f"Error dropping payment_status column: {e}")
        
        try:
            conn.execute(text("ALTER TABLE appointments DROP COLUMN consultation_fees"))
            print("Dropped consultation_fees column")
        except Exception as e:
            print(f"Error dropping consultation_fees column: {e}")
        
        conn.commit()
    
    print("Downgrade completed successfully")

if __name__ == "__main__":
    upgrade()