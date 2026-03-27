"""FastAPI application for transcription service.

This module provides the main FastAPI application that orchestrates
the transcription service API. It includes:
- CORS middleware for web UI access
- Static file serving for CSS and JavaScript
- Health check endpoint
- Web UI, authentication, and job management routers
- Mangum handler for AWS Lambda deployment

The application is designed to run as a Lambda function behind API Gateway,
with minimal operational costs suitable for personal use with friends.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from mangum import Mangum

from transcription_service.routers import auth, jobs, web

# Create FastAPI application
app = FastAPI(
    title="Transcription Service API",
    version="1.0.0",
    description=(
        "Audio transcription service with user authentication. "
        "Supports direct file uploads, presigned S3 uploads for large files, "
        "and YouTube URL transcription using AWS Batch."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware for web UI access
# Note: In production, restrict allow_origins to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (development/friends usage)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files for CSS and JavaScript
# Static files are located in src/transcription_service/static/
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register routers
# Web router must be registered LAST so / goes to the HTML landing page
app.include_router(auth.router)
app.include_router(jobs.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint.

    Returns a simple status message indicating the service is running.
    Useful for monitoring, load balancers, and API Gateway health checks.

    Note: The root path (/) now serves the web UI landing page.
    Use /health for programmatic health checks.

    Returns:
        Dictionary with status and service name
    """
    return {
        "status": "ok",
        "service": "transcription-api",
        "version": "1.0.0",
    }


@app.get("/api", tags=["health"])
async def api_info() -> dict[str, str]:
    """API information endpoint.

    Provides service metadata and version information.
    Use /health for health checks or /docs for API documentation.

    Returns:
        Dictionary with service information
    """
    return {
        "status": "ok",
        "service": "transcription-api",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Register web router LAST so it doesn't shadow /health
app.include_router(web.router)


# Mangum handler for AWS Lambda
# This wraps the FastAPI app for Lambda execution via API Gateway
handler = Mangum(app, lifespan="off")
