from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from config.logging_config import setup_logging, get_logger
from .routers import personalization_router
from .services.ai_service import model as gemini_model

# Setup logging
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="CDP Personalization API",
    description="AI-powered customer personalization using RAG (Retrieve-Augment-Generate)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (allow browser access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(personalization_router)
app.include_router(graph_router)

@app.get("/")
async def root():
    """API health check and info."""
    return {
        "service": "CDP Personalization API",
        "status": "running",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "gemini_enabled": gemini_model is not None,
        "endpoints": {
            "personalize": "/api/personalize/{profile_id}",
            "profile_summary": "/api/profile/{profile_id}",
            "graph_cluster": "/api/graph/cluster/{profile_id}",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("=" * 60)
    logger.info("CDP Personalization API Starting")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Host: {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"MongoDB: {settings.MONGO_HOST}:{settings.MONGO_PORT}")
    logger.info(f"Gemini API: {'Enabled' if settings.GEMINI_API_KEY else 'Disabled (using mocks)'}")
    logger.info(f"Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information."""
    logger.info("CDP Personalization API shutting down")


def main():
    """Run the API server."""
    import uvicorn
    
    if not settings.GEMINI_API_KEY:
        logger.warning("⚠️  GEMINI_API_KEY not set!")
        logger.warning("   Set it in .env file or export GEMINI_API_KEY='your-key-here'")
        logger.warning("   Get a key at: https://aistudio.google.com/app/apikey")
        logger.warning("   API will use mock responses for now.")
    
    uvicorn.run(
        "src.python.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        workers=settings.API_WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()
