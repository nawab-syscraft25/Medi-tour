from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.api.v1 import routes, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Medi-Tour API...")
    
    # Create media directory for local uploads
    if settings.debug:
        os.makedirs("media/uploads", exist_ok=True)
        print("📁 Created media upload directory")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down Medi-Tour API...")


# Create FastAPI application
app = FastAPI(
    title="Medi-Tour API",
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
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Medi-Tour API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health"
    }


# Include API routes
app.include_router(
    routes.router,
    prefix="/api/v1",
    tags=["main"]
)

app.include_router(
    uploads.router,
    prefix="/api/v1/uploads",
    tags=["uploads"]
)


# Serve static files for local development
if settings.debug:
    # Mount media directory for serving uploaded files
    app.mount("/media", StaticFiles(directory="media"), name="media")
    print("📂 Mounted media files at /media")


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
    🏥 Medi-Tour API Server
    
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