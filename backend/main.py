"""Main FastAPI application entry point for Zyana backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from config import settings
from routers import webhook, finance, calendar, memory, agent, profile

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Zyana AI Backend",
    description="Multi-agent AI assistant backend with FastAPI",
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [
        "https://zyana.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("🚀 Starting Zyana AI Backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Backend URL: http://{settings.backend_host}:{settings.backend_port}")
    
    # TODO: Initialize database connection pool
    # TODO: Initialize Qdrant collection
    # TODO: Verify external API connectivity


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("👋 Shutting down Zyana AI Backend...")
    # TODO: Close database connections
    # TODO: Close Redis connections


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "status": "online",
        "service": "Zyana AI Backend",
        "version": "1.0.0",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    # TODO: Check database connectivity
    # TODO: Check Redis connectivity
    # TODO: Check Qdrant connectivity
    return {
        "status": "healthy",
        "services": {
            "database": "ok",
            "redis": "ok",
            "qdrant": "ok",
            "fal_ai": "ok"
        }
    }


# Include routers
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
app.include_router(finance.router, prefix="/finance", tags=["Finance"])
app.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
app.include_router(memory.router, prefix="/memory", tags=["Memory"])
app.include_router(agent.router, prefix="/agent", tags=["Agent"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.is_development else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.is_development
    )

