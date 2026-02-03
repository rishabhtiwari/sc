"""
Asset Service - Main Application
FastAPI application for asset management with MinIO storage
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from datetime import datetime
from config.settings import settings
from routes import asset_routes, audio_library_routes, project_routes, image_library_routes, video_library_routes

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Custom JSON encoder for MongoDB ObjectId
def custom_jsonable_encoder(obj, **kwargs):
    """Custom JSON encoder that handles MongoDB ObjectId"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return jsonable_encoder(obj, custom_encoder={
        ObjectId: str,
        datetime: lambda dt: dt.isoformat()
    }, **kwargs)


# Monkey patch FastAPI's jsonable_encoder
import fastapi.encoders
original_jsonable_encoder = fastapi.encoders.jsonable_encoder


def patched_jsonable_encoder(obj, **kwargs):
    """Patched jsonable_encoder that handles ObjectId"""
    # Add custom encoders for ObjectId and datetime
    custom_encoder = kwargs.get('custom_encoder', {})
    custom_encoder[ObjectId] = str
    if datetime not in custom_encoder:
        custom_encoder[datetime] = lambda dt: dt.isoformat()
    kwargs['custom_encoder'] = custom_encoder
    return original_jsonable_encoder(obj, **kwargs)


fastapi.encoders.jsonable_encoder = patched_jsonable_encoder


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Asset Management Service with MinIO Storage",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


# Include routers
app.include_router(
    asset_routes.router,
    prefix="/api/assets",
    tags=["Assets"]
)

app.include_router(
    audio_library_routes.router,
    prefix="/api/audio-studio",
    tags=["Audio Studio"]
)

app.include_router(
    image_library_routes.router,
    prefix="/api/image-library",
    tags=["Image Library"]
)

app.include_router(
    video_library_routes.router,
    prefix="/api/video-library",
    tags=["Video Library"]
)

app.include_router(
    project_routes.router,
    prefix="/api",
    tags=["Projects"]
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"MinIO endpoint: {settings.MINIO_ENDPOINT}")
    logger.info(f"MongoDB: {settings.MONGODB_URL}")
    
    # Test connections
    try:
        from services.storage_service import storage_service
        from services.database_service import db_service
        
        logger.info("✅ Storage service initialized")
        logger.info("✅ Database service initialized")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info(f"Shutting down {settings.APP_NAME}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

