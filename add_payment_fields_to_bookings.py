"""
Migration script to add payment fields to package_bookings table
Run this script to add Razorpay payment integration fields
"""
from sqlalchemy import create_engine, Column, Float, String, DateTime
from sqlalchemy.orm import sessionmaker
import os

# Database URL - update this with your actual database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

def add_payment_columns():
    """Add payment-related columns to package_bookings table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add amount column
            conn.execute("ALTER TABLE package_bookings ADD COLUMN amount FLOAT")
            print("✅ Added 'amount' column")
        except Exception as e:
            print(f"⚠️ 'amount' column may already exist: {e}")
        
        try:
            # Add payment_status column
            conn.execute("ALTER TABLE package_bookings ADD COLUMN payment_status VARCHAR(50) DEFAULT 'pending'")
            print("✅ Added 'payment_status' column")
        except Exception as e:
            print(f"⚠️ 'payment_status' column may already exist: {e}")
        
        try:
            # Add razorpay_order_id column
            conn.execute("ALTER TABLE package_bookings ADD COLUMN razorpay_order_id VARCHAR(100)")
            print("✅ Added 'razorpay_order_id' column")
        except Exception as e:
            print(f"⚠️ 'razorpay_order_id' column may already exist: {e}")
        
        try:
            # Add razorpay_payment_id column
            conn.execute("ALTER TABLE package_bookings ADD COLUMN razorpay_payment_id VARCHAR(100)")
            print("✅ Added 'razorpay_payment_id' column")
        except Exception as e:
            print(f"⚠️ 'razorpay_payment_id' column may already exist: {e}")
        
        try:
            # Add razorpay_signature column
            conn.execute("ALTER TABLE package_bookings ADD COLUMN razorpay_signature VARCHAR(200)")
            print("✅ Added 'razorpay_signature' column")
        except Exception as e:
            print(f"⚠️ 'razorpay_signature' column may already exist: {e}")
        
        try:
            # Add payment_date column
            conn.execute("ALTER TABLE package_bookings ADD COLUMN payment_date DATETIME")
            print("✅ Added 'payment_date' column")
        except Exception as e:
            print(f"⚠️ 'payment_date' column may already exist: {e}")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    add_payment_columns()
