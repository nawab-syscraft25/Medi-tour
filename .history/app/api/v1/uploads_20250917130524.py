import os
import uuid
import aiofiles
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError

from app.db import get_db
from app import models, schemas
from app.core.config import settings

router = APIRouter()


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension"""
    if not filename:
        return False
    ext = filename.lower().split('.')[-1]
    return ext in allowed_extensions


def validate_file_size(file_size: int) -> bool:
    """Validate file size"""
    return file_size <= settings.max_upload_size


async def count_existing_images(db: AsyncSession, owner_type: str, owner_id: int) -> int:
    """Count existing images for an owner"""
    result = await db.execute(
        select(models.Image).where(
            and_(
                models.Image.owner_type == owner_type,
                models.Image.owner_id == owner_id
            )
        )
    )
    return len(result.scalars().all())


async def set_primary_image(db: AsyncSession, owner_type: str, owner_id: int, new_primary_id: int):
    """Set a new primary image and unset others"""
    # Unset all existing primary flags
    result = await db.execute(
        select(models.Image).where(
            and_(
                models.Image.owner_type == owner_type,
                models.Image.owner_id == owner_id,
                models.Image.is_primary == True
            )
        )
    )
    existing_primaries = result.scalars().all()
    for img in existing_primaries:
        img.is_primary = False
    
    # Set new primary
    result = await db.execute(
        select(models.Image).where(models.Image.id == new_primary_id)
    )
    new_primary = result.scalar_one_or_none()
    if new_primary:
        new_primary.is_primary = True
    
    await db.commit()


# Local development upload endpoint
@router.post("/image")
async def upload_image_local(
    owner_type: str = Form(...),
    owner_id: int = Form(...),
    is_primary: bool = Form(False),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload images locally for development"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Local upload only available in development mode")
    
    # Validate owner_type
    valid_owner_types = ["hospital", "doctor", "treatment", "slider"]
    if owner_type not in valid_owner_types:
        raise HTTPException(status_code=400, detail=f"Invalid owner_type. Must be one of: {valid_owner_types}")
    
    # Check file count limits
    existing_count = await count_existing_images(db, owner_type, owner_id)
    if existing_count + len(files) > settings.max_images_per_owner:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum {settings.max_images_per_owner} images allowed per owner"
        )
    
    uploaded_images = []
    
    # Create upload directory organized by owner type
    upload_dir = f"media/{owner_type}"
    os.makedirs(upload_dir, exist_ok=True)
    
    for i, file in enumerate(files):
        # Validate file extension
        if not validate_file_extension(file.filename, settings.allowed_image_ext_list):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_image_ext_list)}"
            )
        
        # Validate file size
        content = await file.read()
        if not validate_file_size(len(content)):
            raise HTTPException(status_code=400, detail="File size exceeds maximum limit")
        
        # Generate unique filename
        file_ext = file.filename.split('.')[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create image record with organized URL path
        image_url = f"/media/{owner_type}/{unique_filename}"
        db_image = models.Image(
            owner_type=owner_type,
            owner_id=owner_id,
            url=image_url,
            is_primary=is_primary and i == 0,  # Only first file can be primary
            position=existing_count + i
        )
        db.add(db_image)
        await db.flush()
        uploaded_images.append(db_image)
    
    await db.commit()
    
    # Handle primary image setting
    if is_primary and uploaded_images:
        await set_primary_image(db, owner_type, owner_id, uploaded_images[0].id)
    
    return {
        "message": f"Uploaded {len(uploaded_images)} images successfully",
        "images": [schemas.ImageResponse.model_validate(img) for img in uploaded_images]
    }


# S3 presigned upload endpoint
@router.post("/presign", response_model=schemas.PresignedUploadResponse)
async def create_presigned_upload(
    request: schemas.PresignedUploadRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create presigned S3 upload URL"""
    if settings.debug:
        raise HTTPException(status_code=403, detail="Use local upload endpoint in development mode")
    
    # Validate S3 configuration
    if not all([settings.aws_access_key_id, settings.aws_secret_access_key, settings.s3_bucket_name]):
        raise HTTPException(status_code=500, detail="S3 configuration incomplete")
    
    # Validate owner_type
    valid_owner_types = ["hospital", "doctor", "treatment", "slider", "booking"]
    if request.owner_type not in valid_owner_types:
        raise HTTPException(status_code=400, detail=f"Invalid owner_type. Must be one of: {valid_owner_types}")
    
    # Check file count limits
    existing_count = await count_existing_images(db, request.owner_type, request.owner_id)
    if existing_count >= settings.max_images_per_owner:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum {settings.max_images_per_owner} images allowed per owner"
        )
    
    # Validate file extension
    allowed_extensions = settings.allowed_image_ext_list
    if request.owner_type == "booking":  # Allow documents for bookings
        allowed_extensions.extend(settings.allowed_doc_ext_list)
    
    if not validate_file_extension(request.filename, allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate S3 key
    file_ext = request.filename.split('.')[-1].lower()
    unique_key = f"{request.owner_type}/{request.owner_id}/{uuid.uuid4()}.{file_ext}"
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.s3_region
        )
        
        # Generate presigned POST
        presigned_post = s3_client.generate_presigned_post(
            Bucket=settings.s3_bucket_name,
            Key=unique_key,
            Fields={
                "Content-Type": f"image/{file_ext}" if file_ext in settings.allowed_image_ext_list else f"application/{file_ext}"
            },
            Conditions=[
                {"Content-Type": f"image/{file_ext}" if file_ext in settings.allowed_image_ext_list else f"application/{file_ext}"},
                ["content-length-range", 1, settings.max_upload_size]
            ],
            ExpiresIn=3600  # 1 hour
        )
        
        return schemas.PresignedUploadResponse(
            upload_url=presigned_post['url'],
            fields=presigned_post['fields'],
            key=unique_key
        )
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to create presigned URL: {str(e)}")


# S3 upload notification endpoint
@router.post("/notify")
async def notify_upload_complete(
    request: schemas.UploadNotifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Notify server that S3 upload is complete"""
    if settings.debug:
        raise HTTPException(status_code=403, detail="This endpoint is for production S3 uploads only")
    
    # Validate S3 configuration
    if not settings.s3_base_url:
        raise HTTPException(status_code=500, detail="S3 base URL not configured")
    
    # Check if image already exists
    result = await db.execute(
        select(models.Image).where(
            and_(
                models.Image.owner_type == request.owner_type,
                models.Image.owner_id == request.owner_id,
                models.Image.url.endswith(request.key.split('/')[-1])
            )
        )
    )
    existing_image = result.scalar_one_or_none()
    if existing_image:
        raise HTTPException(status_code=400, detail="Image already registered")
    
    # Get current image count for position
    existing_count = await count_existing_images(db, request.owner_type, request.owner_id)
    
    # Create image record
    image_url = f"{settings.s3_base_url}/{request.key}"
    db_image = models.Image(
        owner_type=request.owner_type,
        owner_id=request.owner_id,
        url=image_url,
        is_primary=request.is_primary,
        position=existing_count
    )
    db.add(db_image)
    await db.commit()
    await db.refresh(db_image)
    
    # Handle primary image setting
    if request.is_primary:
        await set_primary_image(db, request.owner_type, request.owner_id, db_image.id)
    
    return {
        "message": "Upload registered successfully",
        "image": schemas.ImageResponse.model_validate(db_image)
    }


# Get images for an owner
@router.get("/images/{owner_type}/{owner_id}", response_model=List[schemas.ImageResponse])
async def get_images(
    owner_type: str,
    owner_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all images for a specific owner"""
    result = await db.execute(
        select(models.Image).where(
            and_(
                models.Image.owner_type == owner_type,
                models.Image.owner_id == owner_id
            )
        ).order_by(models.Image.position, models.Image.uploaded_at)
    )
    return result.scalars().all()


# Delete image
@router.delete("/images/{image_id}")
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an image"""
    result = await db.execute(select(models.Image).where(models.Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete file from local storage if in debug mode
    if settings.debug and image.url.startswith("/media/"):
        # Convert URL path to actual file path
        file_path = image.url.lstrip("/")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                # Log error but don't fail the deletion
                print(f"Warning: Could not delete file {file_path}: {e}")
    
    await db.delete(image)
    await db.commit()
    
    return {"message": "Image deleted successfully"}