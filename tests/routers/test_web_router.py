"""Tests for web UI endpoints.

Tests cover:
    - GET /: Landing/login page (unauthenticated, authenticated redirect)
    - GET /dashboard: Dashboard page (authenticated, unauthenticated redirect)
    - GET /jobs/{job_id}: Job detail page (authenticated, forbidden, not found)
    - Cookie-based authentication
    - Proper redirects and error responses

Note: These tests call the endpoint functions directly rather than using TestClient
due to httpx/starlette version compatibility issues.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse

from transcription_service.routers.web import dashboard, index, job_detail


@pytest.fixture
def mock_request():
    """Mock FastAPI Request object."""
    request = MagicMock()
    request.url.path = "/"
    return request


@pytest.fixture
def mock_user():
    """Sample user data for tests."""
    return {
        "email": "test@example.com",
        "password_hash": "$2b$12$abcdefghijklmnopqrstuvwxyz",
        "created_at": "2026-03-26T10:00:00+00:00",
        "display_name": "Test User",
    }


@pytest.fixture
def mock_job():
    """Sample job data for tests."""
    return {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "test@example.com",
        "status": "running",
        "created_at": "2026-03-26T10:00:00+00:00",
        "total_files": 2,
        "completed_files": 1,
    }


# ==================== GET / (Index) Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.web.get_user_from_cookie")
@patch("transcription_service.routers.web.templates.TemplateResponse")
async def test_index_unauthenticated(mock_template_response, mock_get_user, mock_request):
    """Test index page renders login form when not authenticated."""
    # No user authenticated
    mock_get_user.return_value = None

    # Call endpoint
    result = await index(mock_request, access_token=None)

    # Verify template response called
    mock_template_response.assert_called_once()
    call_args = mock_template_response.call_args[0]
    assert call_args[0] == "index.html"
    assert call_args[1]["request"] == mock_request
    assert call_args[1]["user"] is None


@pytest.mark.anyio
@patch("transcription_service.routers.web.get_user_from_cookie")
async def test_index_authenticated_redirect(mock_get_user, mock_request, mock_user):
    """Test index page redirects to dashboard when already authenticated."""
    # User is authenticated
    mock_get_user.return_value = mock_user

    # Call endpoint
    result = await index(mock_request, access_token="valid_token")

    # Verify redirect to dashboard
    assert isinstance(result, RedirectResponse)
    assert result.status_code == status.HTTP_302_FOUND
    assert "/dashboard" in str(result.headers["location"])


@pytest.mark.anyio
@patch("transcription_service.routers.web.get_user_from_cookie")
@patch("transcription_service.routers.web.templates.TemplateResponse")
async def test_index_invalid_token(mock_template_response, mock_get_user, mock_request):
    """Test index page renders login when token is invalid."""
    # Invalid token returns None
    mock_get_user.return_value = None

    # Call endpoint with invalid token
    result = await index(mock_request, access_token="invalid_token")

    # Verify template response (not redirect)
    mock_template_response.assert_called_once()
    call_args = mock_template_response.call_args[0]
    assert call_args[0] == "index.html"
    assert call_args[1]["user"] is None


# ==================== GET /dashboard Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.web.get_user_from_cookie")
@patch("transcription_service.routers.web.templates.TemplateResponse")
async def test_dashboard_authenticated(mock_template_response, mock_get_user, mock_request, mock_user):
    """Test dashboard renders when authenticated."""
    # User is authenticated
    mock_get_user.return_value = mock_user

    # Call endpoint
    result = await dashboard(mock_request, access_token="valid_token")

    # Verify template response called
    mock_template_response.assert_called_once()
    call_args = mock_template_response.call_args[0]
    assert call_args[0] == "dashboard.html"
    assert call_args[1]["request"] == mock_request
    assert call_args[1]["user"] == mock_user


@pytest.mark.anyio
@patch("transcription_service.routers.web.get_user_from_cookie")
async def test_dashboard_unauthenticated_redirect(mock_get_user, mock_request):
    """Test dashboard redirects to index when not authenticated."""
    # No user authenticated
    mock_get_user.return_value = None

    # Call endpoint
    result = await dashboard(mock_request, access_token=None)

    # Verify redirect to index
    assert isinstance(result, RedirectResponse)
    assert result.status_code == status.HTTP_302_FOUND
    assert "/" in str(result.headers["location"])


@pytest.mark.anyio
@patch("transcription_service.routers.web.get_user_from_cookie")
async def test_dashboard_expired_token_redirect(mock_get_user, mock_request):
    """Test dashboard redirects when token is expired."""
    # Expired token returns None
    mock_get_user.return_value = None

    # Call endpoint with expired token
    result = await dashboard(mock_request, access_token="expired_token")

    # Verify redirect to index
    assert isinstance(result, RedirectResponse)
    assert result.status_code == status.HTTP_302_FOUND


# ==================== GET /jobs/{job_id} Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.web.get_user_from_cookie")
@patch("transcription_service.routers.web.get_job")
@patch("transcription_service.routers.web.templates.TemplateResponse")
async def test_job_detail_authenticated(
    mock_template_response, mock_get_job, mock_get_user, mock_request, mock_user, mock_job
):
    """Test job detail page renders when authenticated and job belongs to user."""
    # User is authenticated
    mock_get_user.return_value = mock_user

    # Job exists and belongs to user
    mock_get_job.return_value = mock_job

    # Call endpoint
    result = await job_detail(mock_request, job_id=mock_job["job_id"], access_token="valid_token")

    # Verify template response called
    mock_template_response.assert_called_once()
    call_args = mock_template_response.call_args[0]
    assert call_args[0] == "job_detail.html"
    assert call_args[1]["request"] == mock_request
    assert call_args[1]["user"] == mock_user
    assert call_args[1]["job"] == mock_job

    # Verify get_job called with correct job_id
    mock_get_job.assert_called_once_with(mock_job["job_id"])


@pytest.mark.anyio
@patch("transcription_service.routers.web.get_user_from_cookie")
async def test_job_detail_unauthenticated_redirect(mock_get_user, mock_request):
    """Test job detail redirects to index when not authenticated."""
    # No user authenticated
    mock_get_user.return_value = None

    # Call endpoint
    result = await job_detail(
        mock_request, job_id="123e4567-e89b-12d3-a456-426614174000", access_token=None
    )

    # Verify redirect to index
    assert isinstance(result, RedirectResponse)
    assert result.status_code == status.HTTP_302_FOUND


@pytest.mark.anyio
@patch("transcription_service.routers.web.get_user_from_cookie")
@patch("transcription_service.routers.web.get_job")
async def test_job_detail_not_found(mock_get_job, mock_get_user, mock_request, mock_user):
    """Test job detail returns 404 when job does not exist."""
    # User is authenticated
    mock_get_user.return_value = mock_user

    # Job does not exist
    mock_get_job.return_value = None

    # Call endpoint and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await job_detail(
            mock_request, job_id="nonexistent-job-id", access_token="valid_token"
        )

    # Verify 404 error
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in exc_info.value.detail.lower()


@pytest.mark.anyio
@patch("transcription_service.routers.web.get_user_from_cookie")
@patch("transcription_service.routers.web.get_job")
async def test_job_detail_forbidden(mock_get_job, mock_get_user, mock_request, mock_user, mock_job):
    """Test job detail returns 403 when job belongs to different user."""
    # User is authenticated
    mock_get_user.return_value = mock_user

    # Job exists but belongs to different user
    other_user_job = mock_job.copy()
    other_user_job["email"] = "other@example.com"
    mock_get_job.return_value = other_user_job

    # Call endpoint and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await job_detail(
            mock_request, job_id=mock_job["job_id"], access_token="valid_token"
        )

    # Verify 403 error
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in exc_info.value.detail.lower()


@pytest.mark.anyio
@patch("transcription_service.routers.web.get_user_from_cookie")
@patch("transcription_service.routers.web.get_job")
async def test_job_detail_invalid_uuid(mock_get_job, mock_get_user, mock_request, mock_user):
    """Test job detail returns 404 when job_id is not a valid UUID."""
    # User is authenticated
    mock_get_user.return_value = mock_user

    # get_job raises ValueError for invalid UUID
    mock_get_job.side_effect = ValueError("Invalid UUID format")

    # Call endpoint and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await job_detail(
            mock_request, job_id="not-a-uuid", access_token="valid_token"
        )

    # Verify 404 error
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


# ==================== Cookie Helper Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.web.verify_jwt_token")
@patch("transcription_service.routers.web.get_user_by_email")
async def test_get_user_from_cookie_valid(mock_get_user_by_email, mock_verify_jwt, mock_user):
    """Test get_user_from_cookie returns user for valid token."""
    from transcription_service.routers.web import get_user_from_cookie

    # Mock token verification
    mock_verify_jwt.return_value = "test@example.com"
    mock_get_user_by_email.return_value = mock_user

    # Call helper
    result = get_user_from_cookie("valid_token")

    # Assertions
    assert result == mock_user
    mock_verify_jwt.assert_called_once_with("valid_token")
    mock_get_user_by_email.assert_called_once_with("test@example.com")


@pytest.mark.anyio
@patch("transcription_service.routers.web.verify_jwt_token")
async def test_get_user_from_cookie_no_token(mock_verify_jwt):
    """Test get_user_from_cookie returns None when no token provided."""
    from transcription_service.routers.web import get_user_from_cookie

    # Call helper with no token
    result = get_user_from_cookie(None)

    # Assertions
    assert result is None
    mock_verify_jwt.assert_not_called()


@pytest.mark.anyio
@patch("transcription_service.routers.web.verify_jwt_token")
async def test_get_user_from_cookie_invalid_token(mock_verify_jwt):
    """Test get_user_from_cookie returns None for invalid token."""
    from transcription_service.routers.web import get_user_from_cookie

    # Token verification fails
    mock_verify_jwt.return_value = None

    # Call helper
    result = get_user_from_cookie("invalid_token")

    # Assertions
    assert result is None
    mock_verify_jwt.assert_called_once_with("invalid_token")


@pytest.mark.anyio
@patch("transcription_service.routers.web.verify_jwt_token")
@patch("transcription_service.routers.web.get_user_by_email")
async def test_get_user_from_cookie_user_not_found(mock_get_user_by_email, mock_verify_jwt):
    """Test get_user_from_cookie returns None when user not in database."""
    from transcription_service.routers.web import get_user_from_cookie

    # Token is valid but user not found
    mock_verify_jwt.return_value = "test@example.com"
    mock_get_user_by_email.return_value = None

    # Call helper
    result = get_user_from_cookie("valid_token")

    # Assertions
    assert result is None
