"""
API v1 router
"""

from fastapi import APIRouter
from app.api.v1 import routes, uploads, admin, contact

api_router = APIRouter()

# Include routers
api_router.include_router(routes.router, tags=["main"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(contact.router, tags=["contact"])
