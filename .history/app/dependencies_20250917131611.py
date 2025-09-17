"""
FastAPI dependencies for admin authentication
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app import models
from app.auth import verify_token

security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> models.Admin:
    """Get current admin from JWT token"""
    
    # Verify token
    payload = verify_token(credentials.credentials)
    
    # Check if user is admin
    if not payload.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get admin from database
    admin_id = payload.get("admin_id")
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    result = await db.execute(select(models.Admin).where(models.Admin.id == admin_id))
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found"
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account is inactive"
        )
    
    return admin


async def get_current_super_admin(
    current_admin: models.Admin = Depends(get_current_admin)
) -> models.Admin:
    """Ensure current admin is a super admin"""
    if not current_admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_admin


def admin_required(func):
    """Decorator to require admin authentication"""
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper