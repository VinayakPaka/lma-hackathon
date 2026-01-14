"""
GreenGuard ESG Platform - Main Application Entry Point
"""
import os
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth, file_upload, esg_extract, ai_esg_extract, compliance, kpi_benchmark, use_of_proceeds, kpi_evaluation, kpi_benchmarking, report_chat



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting GreenGuard ESG Platform...")
    
    # Reset provider exhaustion flags on startup (in case API keys were changed)
    try:
        from app.agents.base_agent import reset_provider_flags
        reset_provider_flags()
        logger.info("Provider exhaustion flags reset for fresh API key state")
    except Exception as e:
        logger.warning(f"Could not reset provider flags: {e}")
    
    # Check configuration
    from app.middleware.config_check import check_configuration
    config_ok = check_configuration()
    if not config_ok:
        logger.warning("=" * 80)
        logger.warning("⚠️  APPLICATION STARTED WITH CONFIGURATION ISSUES")
        logger.warning("See CONFIGURATION_GUIDE.md for setup instructions")
        logger.warning("=" * 80)
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    await init_db()
    logger.info("Database initialized successfully")
    yield
    logger.info("Shutting down GreenGuard ESG Platform...")
    await close_db()
    logger.info("Database connection closed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for GreenGuard ESG Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()}
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error", "message": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    logger.error(f"Unexpected error: {str(exc)}\n{error_trace}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "message": str(exc)}
    )


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(file_upload.router, prefix="/upload", tags=["File Upload"])
app.include_router(esg_extract.router, prefix="/extract", tags=["ESG Extraction"])
app.include_router(ai_esg_extract.router, prefix="/ai-extract", tags=["AI ESG Extraction"])
app.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
app.include_router(kpi_benchmark.router, prefix="/kpi", tags=["KPI Benchmarking"])
app.include_router(use_of_proceeds.router, prefix="/use-of-proceeds", tags=["Use of Proceeds"])
app.include_router(kpi_evaluation.router, prefix="/kpi", tags=["KPI Evaluation"])
app.include_router(kpi_benchmarking.router)  # KPI Benchmarking Engine (uses /kpi-benchmark prefix)
app.include_router(report_chat.router)


@app.get("/", tags=["Health"])
async def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "status": "healthy"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "database": "connected"}
