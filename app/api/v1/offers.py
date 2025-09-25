"""
Public API endpoints for Offers
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from app.dependencies import get_db
from app.models import Offer, Treatment, Image
from app.schemas import OfferResponse

router = APIRouter(prefix="/api/v1/offers", tags=["offers"])


@router.get("", response_model=List[OfferResponse])
async def get_offers(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of offers to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of offers to return"),
    treatment_type: Optional[str] = Query(None, description="Filter by treatment type"),
    location: Optional[str] = Query(None, description="Filter by location"),
    is_active: bool = Query(True, description="Filter by active status"),
    include_expired: bool = Query(False, description="Include expired offers"),
    search: Optional[str] = Query(None, description="Search in name and description")
):
    """
    Get list of offers with optional filtering
    
    - **skip**: Number of offers to skip (for pagination)
    - **limit**: Maximum number of offers to return
    - **treatment_type**: Filter by specific treatment type
    - **location**: Filter by location (case-insensitive)
    - **is_active**: Whether to include only active offers
    - **include_expired**: Whether to include expired offers
    - **search**: Search term for name and description
    """
    
    # Build query
    query = select(Offer).options(
        selectinload(Offer.treatment),
        selectinload(Offer.images)
    )
    
    # Apply filters
    conditions = []
    
    if is_active:
        conditions.append(Offer.is_active == True)
    
    if not include_expired:
        now = datetime.utcnow()
        conditions.append(Offer.end_date > now)
    
    if treatment_type:
        conditions.append(Offer.treatment_type.ilike(f"%{treatment_type}%"))
    
    if location:
        conditions.append(Offer.location.ilike(f"%{location}%"))
    
    if search:
        search_term = f"%{search}%"
        conditions.append(
            (Offer.name.ilike(search_term)) | 
            (Offer.description.ilike(search_term))
        )
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Order by creation date (newest first)
    query = query.order_by(desc(Offer.created_at))
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    offers = result.scalars().all()
    
    return offers


@router.get("/{offer_id}", response_model=OfferResponse)
async def get_offer(
    offer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific offer by ID
    """
    query = select(Offer).options(
        selectinload(Offer.treatment),
        selectinload(Offer.images)
    ).where(Offer.id == offer_id)
    
    result = await db.execute(query)
    offer = result.scalar_one_or_none()
    
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Check if offer is accessible (active and not expired)
    if not offer.is_active:
        raise HTTPException(status_code=404, detail="Offer not available")
    
    if offer.end_date and offer.end_date < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Offer has expired")
    
    return offer


@router.get("/treatment-types/list")
async def get_treatment_types(db: AsyncSession = Depends(get_db)):
    """
    Get all available treatment types from offers
    """
    query = select(Offer.treatment_type).distinct().where(
        and_(
            Offer.treatment_type.isnot(None),
            Offer.is_active == True,
            Offer.end_date > datetime.utcnow()
        )
    )
    
    result = await db.execute(query)
    treatment_types = [row[0] for row in result.fetchall() if row[0]]
    
    return {"treatment_types": sorted(treatment_types)}


@router.get("/locations/list")
async def get_locations(db: AsyncSession = Depends(get_db)):
    """
    Get all available locations from offers
    """
    query = select(Offer.location).distinct().where(
        and_(
            Offer.location.isnot(None),
            Offer.is_active == True,
            Offer.end_date > datetime.utcnow()
        )
    )
    
    result = await db.execute(query)
    locations = [row[0] for row in result.fetchall() if row[0]]
    
    return {"locations": sorted(locations)}


@router.get("/active/count")
async def get_active_offers_count(db: AsyncSession = Depends(get_db)):
    """
    Get count of currently active offers
    """
    now = datetime.utcnow()
    
    query = select(Offer).where(
        and_(
            Offer.is_active == True,
            Offer.start_date <= now,
            Offer.end_date > now
        )
    )
    
    result = await db.execute(query)
    active_offers = result.scalars().all()
    
    # Categorize offers
    free_camps = len([o for o in active_offers if o.is_free_camp])
    discount_offers = len([o for o in active_offers if o.discount_percentage and o.discount_percentage > 0])
    
    return {
        "total_active": len(active_offers),
        "free_camps": free_camps,
        "discount_offers": discount_offers,
        "other_offers": len(active_offers) - free_camps - discount_offers
    }