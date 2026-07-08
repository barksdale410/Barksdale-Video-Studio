from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.routes import auth, directors, analysis, generation

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered video storyboard generator with director style profiles",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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
    """Global exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else None
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(directors.router)
app.include_router(analysis.router)
app.include_router(generation.router)


# Health check
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/api/v1/health", tags=["Health"])
async def health_check_v1():
    """Health check endpoint v1."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "Welcome to Barksdale Video Studio API",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": "/api/v1/auth",
            "directors": "/api/v1/directors",
            "analyze": "/api/v1/analyze",
            "generate": "/api/v1/generate",
            "jobs": "/api/v1/jobs"
        }
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    # Ensure static directories exist
    os.makedirs("static", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"📚 API docs available at: /docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print(f"👋 {settings.APP_NAME} shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        workers=1
    )
