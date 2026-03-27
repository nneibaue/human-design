"""Web UI endpoints for serving HTML templates.

This module provides browser-facing endpoints that render HTML templates:
    - GET /: Landing/login page
    - GET /dashboard: Dashboard with job list and upload form
    - GET /jobs/{job_id}: Job detail page

All HTML pages use Jinja2 templates with JavaScript for interactivity.
Protected pages require JWT authentication via cookie.
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from transcription_service.auth import verify_jwt_token
from transcription_service.database import get_job, get_user_by_email

# Initialize Jinja2 templates
# Templates are located in src/transcription_service/templates/
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["web"])


def get_user_from_cookie(access_token: str | None) -> dict | None:
    """Extract and verify user from JWT cookie.

    Args:
        access_token: JWT token from cookie (may be None)

    Returns:
        User dict with email, display_name, etc. if authenticated
        None if not authenticated or token invalid

    Note:
        This is a helper function, not a FastAPI dependency.
        It returns None instead of raising exceptions to allow
        graceful handling in route handlers.
    """
    if not access_token:
        return None

    # Verify JWT and extract email
    email = verify_jwt_token(access_token)
    if not email:
        return None

    # Get user from database
    user = get_user_by_email(email)
    return user


@router.get("/")
async def index(
    request: Request,
    access_token: Annotated[str | None, Cookie()] = None,
):
    """Render landing/login page.

    If user is already authenticated (valid JWT cookie), redirects to dashboard.
    Otherwise, renders the login/register page with form toggle.

    Args:
        request: FastAPI Request object
        access_token: JWT token from cookie (optional)

    Returns:
        HTMLResponse with login page or RedirectResponse to /dashboard

    Example:
        >>> GET /
        >>> (Renders index.html with login/register forms)

        >>> GET / (with valid JWT cookie)
        >>> 302 Redirect to /dashboard
    """
    # Check if user is already authenticated
    user = get_user_from_cookie(access_token)
    if user:
        # Already logged in, redirect to dashboard
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    # Not authenticated, show login page
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": None,  # Not authenticated
        },
    )


@router.get("/dashboard")
async def dashboard(
    request: Request,
    access_token: Annotated[str | None, Cookie()] = None,
):
    """Render dashboard with job list and upload form.

    Requires authentication. If not authenticated, redirects to landing page.
    Dashboard includes file upload, YouTube URL submission, and job list.

    Args:
        request: FastAPI Request object
        access_token: JWT token from cookie (optional)

    Returns:
        HTMLResponse with dashboard or RedirectResponse to /

    Raises:
        RedirectResponse: 302 redirect to / if not authenticated

    Example:
        >>> GET /dashboard (with valid JWT cookie)
        >>> (Renders dashboard.html with user info)

        >>> GET /dashboard (without cookie or invalid token)
        >>> 302 Redirect to /
    """
    # Check authentication
    user = get_user_from_cookie(access_token)
    if not user:
        # Not authenticated, redirect to login
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    # Render dashboard with user info
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,  # Pass full user object for display_name
        },
    )


@router.get("/jobs/{job_id}")
async def job_detail(
    request: Request,
    job_id: str,
    access_token: Annotated[str | None, Cookie()] = None,
):
    """Render job detail page with files and status.

    Requires authentication and job ownership verification.
    Shows job metadata, progress, error messages, and file list.

    Args:
        request: FastAPI Request object
        job_id: UUID of the job to display
        access_token: JWT token from cookie (optional)

    Returns:
        HTMLResponse with job details, RedirectResponse, or HTTPException

    Raises:
        RedirectResponse: 302 redirect to / if not authenticated
        HTTPException 404: Job not found
        HTTPException 403: Job does not belong to user

    Example:
        >>> GET /jobs/123e4567-e89b-12d3-a456-426614174000
        >>> (Renders job_detail.html with job info)

        >>> GET /jobs/nonexistent-job
        >>> 404 Not Found

        >>> GET /jobs/{other_user_job}
        >>> 403 Forbidden
    """
    # Check authentication
    user = get_user_from_cookie(access_token)
    if not user:
        # Not authenticated, redirect to login
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    # Get job from database
    try:
        job = get_job(job_id)
    except ValueError:
        # Invalid UUID format
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        ) from None

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    # Verify job belongs to user
    if job["email"] != user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job",
        )

    # Render job detail page
    # Note: JavaScript will fetch full job details via API
    # We only need to pass job_id and user context
    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "user": user,
            "job": job,  # Pass job for initial render
        },
    )
