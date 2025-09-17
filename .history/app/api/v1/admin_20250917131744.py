"""
Admin authentication and management endpoints
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db import get_db
from app import models, schemas
from app.auth import verify_password, create_admin_token
from app.dependencies import get_current_admin, get_current_super_admin

router = APIRouter()


@router.post("/login", response_model=schemas.AdminToken)
async def admin_login(
    admin_data: schemas.AdminLogin,
    db: AsyncSession = Depends(get_db)
):
    """Admin login endpoint"""
    
    # Find admin by username
    result = await db.execute(
        select(models.Admin).where(models.Admin.username == admin_data.username)
    )
    admin = result.scalar_one_or_none()
    
    if not admin or not verify_password(admin_data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account is inactive"
        )
    
    # Update last login
    admin.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token = create_admin_token(
        admin_username=admin.username,
        admin_id=admin.id,
        is_super_admin=admin.is_super_admin
    )
    
    # Convert admin to dict for safe serialization
    admin_dict = {
        "id": admin.id,
        "username": admin.username,
        "email": admin.email,
        "is_active": admin.is_active,
        "is_super_admin": admin.is_super_admin,
        "created_at": admin.created_at,
        "last_login": admin.last_login
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": admin_dict
    }


@router.get("/me", response_model=schemas.AdminResponse)
async def get_current_admin_info(
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Get current admin information"""
    return {
        "id": current_admin.id,
        "username": current_admin.username,
        "email": current_admin.email,
        "is_active": current_admin.is_active,
        "is_super_admin": current_admin.is_super_admin,
        "created_at": current_admin.created_at,
        "last_login": current_admin.last_login
    }


@router.get("/admins", response_model=List[schemas.AdminResponse])
async def list_admins(
    current_admin: models.Admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all admins (super admin only)"""
    result = await db.execute(select(models.Admin).order_by(models.Admin.created_at.desc()))
    admins = result.scalars().all()
    
    return [
        {
            "id": admin.id,
            "username": admin.username,
            "email": admin.email,
            "is_active": admin.is_active,
            "is_super_admin": admin.is_super_admin,
            "created_at": admin.created_at,
            "last_login": admin.last_login
        }
        for admin in admins
    ]


@router.post("/admins", response_model=schemas.AdminResponse)
async def create_admin(
    admin_data: schemas.AdminCreate,
    current_admin: models.Admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new admin (super admin only)"""
    from app.auth import get_password_hash
    
    # Check if username already exists
    result = await db.execute(
        select(models.Admin).where(models.Admin.username == admin_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    result = await db.execute(
        select(models.Admin).where(models.Admin.email == admin_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Create new admin
    hashed_password = get_password_hash(admin_data.password)
    db_admin = models.Admin(
        username=admin_data.username,
        email=admin_data.email,
        password_hash=hashed_password,
        is_super_admin=admin_data.is_super_admin
    )
    
    db.add(db_admin)
    await db.commit()
    await db.refresh(db_admin)
    
    return {
        "id": db_admin.id,
        "username": db_admin.username,
        "email": db_admin.email,
        "is_active": db_admin.is_active,
        "is_super_admin": db_admin.is_super_admin,
        "created_at": db_admin.created_at,
        "last_login": db_admin.last_login
    }


@router.put("/admins/{admin_id}/toggle-active")
async def toggle_admin_active(
    admin_id: int,
    current_admin: models.Admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Toggle admin active status (super admin only)"""
    
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    result = await db.execute(select(models.Admin).where(models.Admin.id == admin_id))
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    admin.is_active = not admin.is_active
    await db.commit()
    
    return {"message": f"Admin {'activated' if admin.is_active else 'deactivated'} successfully"}