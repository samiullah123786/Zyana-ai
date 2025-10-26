"""Main FastAPI application entry point for Zyana backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
import traceback

from config import settings
from routers import webhook, finance, calendar, memory, agent, profile, invoice, client, notification, admin, feedback

# Configure logging - INFO level with selective DEBUG for our code
logging.basicConfig(
    level=logging.INFO,  # INFO for most things
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Reduce noise from third-party libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("hpack").setLevel(logging.WARNING)
logging.getLogger("h2").setLevel(logging.WARNING)

# Keep our code at INFO for important events
logging.getLogger("clients.openai_client").setLevel(logging.INFO)
logging.getLogger("agents.intent_router").setLevel(logging.INFO)
logging.getLogger("routers.webhook").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Global exception handler to catch EVERYTHING (even silent exceptions)
def log_unhandled_exceptions(exc_type, exc_value, exc_traceback):
    """Catch and log ALL unhandled exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    print("=" * 100)
    print("🔥🔥🔥 UNHANDLED EXCEPTION CAUGHT BY GLOBAL HANDLER 🔥🔥🔥")
    print("=" * 100)
    logger.critical("🔥 Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    print("Exception Type:", exc_type)
    print("Exception Value:", exc_value)
    print("Traceback:")
    traceback.print_tb(exc_traceback)
    print("=" * 100)

sys.excepthook = log_unhandled_exceptions
logger.info("✅ Global exception handler installed")

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
    try:
        logger.info("="*60)
        logger.info("🚀 Starting Zyana AI Backend...")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Backend URL: http://{settings.backend_host}:{settings.backend_port}")
        logger.info("="*60)
        
        # Test critical imports
        try:
            from agents.finance import finance_agent
            from agents.calendar import calendar_agent
            from agents.router import main_agent
            logger.info("✅ All agents imported successfully")
        except Exception as e:
            logger.error(f"❌ Agent import failed: {e}", exc_info=True)
        
        # Initialize agent self-description
        try:
            from startup.agent_self_describe import agent_self_describe
            await agent_self_describe.initialize()
        except Exception as e:
            logger.error(f"❌ Agent self-describe failed: {e}", exc_info=True)
        
        # Set up Telegram webhook ALWAYS (not just production)
        if settings.webhook_url:
            from services.telegram_bot import set_telegram_webhook
            try:
                webhook_url = f"{settings.webhook_url}/webhook/telegram"
                logger.info(f"🔗 Setting webhook: {webhook_url}")
                result = await set_telegram_webhook(webhook_url)
                logger.info(f"✅ Telegram webhook set: {result}")
            except Exception as e:
                logger.error(f"❌ Failed to set Telegram webhook: {e}", exc_info=True)
        else:
            logger.warning("⚠️  No WEBHOOK_URL configured - bot won't receive messages!")
        
        logger.info("="*60)
        logger.info("✅ Backend started successfully!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ CRITICAL: Startup failed: {e}", exc_info=True)
        # Don't crash - allow server to start for debugging


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
    """Health check endpoint for monitoring - checks all critical services."""
    from datetime import datetime
    from clients.supabase_client import supabase_client
    from clients.qdrant_client import qdrant_client
    from agents.calendar import calendar_agent
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Check Supabase (database)
    try:
        result = supabase_client.admin.table("users").select("id").limit(1).execute()
        health_status["services"]["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Qdrant (vector database)
    try:
        collections = qdrant_client.client.get_collections()
        health_status["services"]["qdrant"] = "ok"
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        health_status["services"]["qdrant"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Google Calendar OAuth
    try:
        if calendar_agent.credentials:
            health_status["services"]["google_calendar"] = "connected"
        else:
            health_status["services"]["google_calendar"] = "not_authenticated"
    except Exception as e:
        logger.error(f"Google Calendar health check failed: {e}")
        health_status["services"]["google_calendar"] = f"error: {str(e)}"
    
    # Check Fal AI (non-critical, no actual call)
    health_status["services"]["fal_ai"] = "available"
    
    return health_status


# Include routers
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
app.include_router(finance.router, prefix="/finance", tags=["Finance"])
app.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
app.include_router(memory.router, prefix="/memory", tags=["Memory"])
app.include_router(agent.router, prefix="/agent", tags=["Agent"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(invoice.router, prefix="/invoice", tags=["Invoice"])
app.include_router(client.router, prefix="/client", tags=["Client"])
app.include_router(notification.router, prefix="/notification", tags=["Notification"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])


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

