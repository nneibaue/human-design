"""FastAPI application for transcription service.

This module provides the main FastAPI application that orchestrates
the transcription service API. It includes:
- CORS middleware for web UI access
- Health check endpoint
- Authentication and job management routers
- Mangum handler for AWS Lambda deployment

The application is designed to run as a Lambda function behind API Gateway,
with minimal operational costs suitable for personal use with friends.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from transcription_service.routers import auth, jobs

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

# Register routers
app.include_router(auth.router)
app.include_router(jobs.router)


@app.get("/", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns a simple status message indicating the service is running.
    Useful for monitoring, load balancers, and API Gateway health checks.

    Returns:
        Dictionary with status and service name

    Example:
        >>> GET /
        >>> {
        ...     "status": "ok",
        ...     "service": "transcription-api",
        ...     "version": "1.0.0"
        ... }
    """
    return {
        "status": "ok",
        "service": "transcription-api",
        "version": "1.0.0",
    }


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Alternative health check endpoint.

    Provides the same functionality as the root endpoint,
    but with a more explicit path for health monitoring tools.

    Returns:
        Dictionary with status and service name
    """
    return {
        "status": "ok",
        "service": "transcription-api",
        "version": "1.0.0",
    }


# Mangum handler for AWS Lambda
# This wraps the FastAPI app for Lambda execution via API Gateway
handler = Mangum(app, lifespan="off")
