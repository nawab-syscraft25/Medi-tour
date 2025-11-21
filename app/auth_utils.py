import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models
import os

# Configuration - Import from settings
from app.core.config import settings

# JWT Configuration
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Email Configuration
SMTP_SERVER = settings.smtp_server
SMTP_PORT = settings.smtp_port
SMTP_USERNAME = settings.smtp_username
SMTP_PASSWORD = settings.smtp_password
FROM_EMAIL = settings.from_email or settings.smtp_username

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_verification_token() -> str:
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    """Get user by email"""
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalar_one_or_none()

def send_email(to_email: str, subject: str, body: str, is_html: bool = False):
    """Send email using SMTP"""
    try:
        # Validate email configuration
        if not SMTP_SERVER or not SMTP_USERNAME or not SMTP_PASSWORD:
            print(f"❌ Email configuration missing: SMTP_SERVER={SMTP_SERVER}, SMTP_USERNAME={SMTP_USERNAME}, SMTP_PASSWORD={'***' if SMTP_PASSWORD else 'None'}")
            return False
        
        print(f"📧 Attempting to send email to {to_email}")
        print(f"📧 Using SMTP: {SMTP_SERVER}:{SMTP_PORT}")
        print(f"📧 From: {FROM_EMAIL}")
        
        msg = MIMEMultipart()
        msg['From'] = f"CureOn Medical Tourism <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Use SMTP_SSL for port 465, SMTP with starttls for port 587
        if SMTP_PORT == 465:
            # SSL/TLS connection (recommended for port 465)
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        else:
            # STARTTLS connection (for port 587)
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
        
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(FROM_EMAIL, to_email, text)
        server.quit()
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

def send_verification_email(to_email: str, token: str, user_name: str, base_url: str = None):
    """Send email verification email"""
    subject = "Verify Your Email - CureOn Medical Tourism"
    
    # Use current domain or fallback to localhost
    
    base_url = "https://portal.cureonmedicaltourism.com"
    
    verification_url = f"{base_url}/api/v1/verify-email?token={token}"
    
    body = f"""
    Hi {user_name},
    
    Thank you for signing up with CureOn Medical Tourism!
    
    Please click the link below to verify your email address:
    {verification_url}
    
    This link will expire in 24 hours.
    
    If you didn't create an account with us, please ignore this email.
    
    Best regards,
    CureOn Medical Tourism Team
    """
    
    return send_email(to_email, subject, body)

def send_password_reset_email(to_email: str, token: str, user_name: str, base_url: str = None):
    """Send password reset email"""
    subject = "Reset Your Password - CureOn Medical Tourism"
    
    # Use current domain or fallback to localhost
    base_url = "https://portal.cureonmedicaltourism.com"
    
    reset_url = f"{base_url}/api/v1/reset-password?token={token}"
    
    body = f"""
    Hi {user_name},
    
    You requested to reset your password for your CureOn Medical Tourism account.
    
    Please click the link below to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request a password reset, please ignore this email.
    
    Best regards,
    CureOn Medical Tourism Team
    """
    
    return send_email(to_email, subject, body)

def user_to_dict(user: models.User) -> dict:
    """Convert User model to dict for safe serialization"""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "is_email_verified": user.is_email_verified,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "last_login": user.last_login
    }
