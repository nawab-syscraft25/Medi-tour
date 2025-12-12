from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models
from app.utils.static_files import CachedStaticFiles, MediaStaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting CureOn Medical Tourism API...")
    
    # Create media directory for local uploads
    if settings.debug:
        os.makedirs("media/uploads", exist_ok=True)
        print("📁 Created media upload directory")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down CureOn Medical Tourism API...")


# Create FastAPI application
app = FastAPI(
    title="CureOn Medical Tourism API",
    description="A comprehensive REST API for medical tourism platform",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    if settings.debug:
        # In debug mode, show detailed error
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "traceback": traceback.format_exc() if settings.debug else None
            }
        )
    else:
        # In production, show generic error
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "debug": settings.debug
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - redirects to admin panel"""
    return RedirectResponse(url="/admin")


# Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Add a route for the booking page
@app.get("/book", response_class=HTMLResponse)
async def book_appointment(request: Request, db: AsyncSession = Depends(get_db)):
    """Serve the appointment booking page"""
    # Get all doctors
    result = await db.execute(select(models.Doctor).order_by(models.Doctor.name))
    doctors = result.scalars().all()
    
    return templates.TemplateResponse("book_appointment.html", {
        "request": request,
        "doctors": doctors
    })


# Include API routes
from app.api.v1 import api_router

app.include_router(
    api_router,
    prefix="/api/v1"
)

# Add filter endpoints directly for frontend compatibility
from app.api.v1.routes import get_locations, get_treatment_types, get_specializations

app.add_api_route("/api/filters/locations", get_locations, methods=["GET"])
app.add_api_route("/api/filters/treatment-types", get_treatment_types, methods=["GET"])
app.add_api_route("/api/filters/specializations", get_specializations, methods=["GET"])

# Include admin web interface routes
from app.admin_web import router as admin_router

app.include_router(admin_router)

# Mount static files with caching
app.mount("/static", CachedStaticFiles(directory="static"), name="static")
print("📂 Mounted static files at /static with caching enabled")

# Mount media directory for serving uploaded files with aggressive caching
# Note: Media files benefit from long cache times since they're typically
# immutable (identified by unique filenames/UUIDs)
app.mount("/media", MediaStaticFiles(directory="media"), name="media")
print("📂 Mounted media files at /media with caching enabled (1 year TTL)")


# Additional middleware for request logging (debug mode only)
if settings.debug:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log requests in debug mode"""
        print(f"📝 {request.method} {request.url}")
        response = await call_next(request)
        print(f"📤 {response.status_code}")
        return response


# Startup message
if __name__ == "__main__":
    import uvicorn
    
    print(f"""
    🏥 CureOn Medical Tourism API Server
    
    Environment: {settings.environment}
    Debug Mode: {settings.debug}
    Database: {settings.database_url.split('://')[0]}
    
    Starting server on http://0.0.0.0:8000
    API Documentation: http://0.0.0.0:8000/docs
    """)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )