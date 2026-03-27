"""Tests for authentication endpoints.

Tests cover:
    - User registration (success, duplicate email)
    - User login (success, invalid credentials)
    - Get current user profile (authenticated, unauthenticated)

Note: These tests call the endpoint functions directly rather than using TestClient
due to httpx/starlette version compatibility issues.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

from transcription_service.models import UserLogin, UserRegister
from transcription_service.routers.auth import get_current_user_profile, login, register


@pytest.fixture
def mock_user():
    """Sample user data for tests."""
    return {
        "email": "test@example.com",
        "password_hash": "$2b$12$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKL",
        "created_at": "2026-03-26T10:00:00+00:00",
        "display_name": "Test User",
    }


# ==================== Registration Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.auth.get_user_by_email")
@patch("transcription_service.routers.auth.create_user")
@patch("transcription_service.routers.auth.hash_password")
@patch("transcription_service.routers.auth.create_jwt_token")
async def test_register_success(
    mock_create_jwt, mock_hash_password, mock_create_user, mock_get_user
):
    """Test successful user registration with auto-login."""
    # Setup mocks
    mock_get_user.return_value = None  # User does not exist
    mock_hash_password.return_value = "hashed_password_123"
    mock_create_jwt.return_value = "mock_jwt_token_abc"
    mock_create_user.return_value = None

    # Create request
    user = UserRegister(
        email="newuser@example.com", password="securepass123", display_name="New User"
    )

    # Call endpoint function
    response = await register(user)

    # Assertions
    assert response.access_token == "mock_jwt_token_abc"
    assert response.token_type == "bearer"

    # Verify mocks called correctly
    mock_get_user.assert_called_once_with("newuser@example.com")
    mock_hash_password.assert_called_once_with("securepass123")
    mock_create_user.assert_called_once_with(
        email="newuser@example.com", password_hash="hashed_password_123", display_name="New User"
    )
    mock_create_jwt.assert_called_once_with("newuser@example.com")


@pytest.mark.anyio
@patch("transcription_service.routers.auth.get_user_by_email")
async def test_register_duplicate_email(mock_get_user, mock_user):
    """Test registration fails when email already exists."""
    # User already exists
    mock_get_user.return_value = mock_user

    # Create request
    user = UserRegister(email="test@example.com", password="securepass123")

    # Call endpoint function and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await register(user)

    # Assertions
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in exc_info.value.detail.lower()
    mock_get_user.assert_called_once_with("test@example.com")


@pytest.mark.anyio
@patch("transcription_service.routers.auth.get_user_by_email")
@patch("transcription_service.routers.auth.hash_password")
@patch("transcription_service.routers.auth.create_user")
async def test_register_race_condition(mock_create_user, mock_hash_password, mock_get_user):
    """Test registration handles race condition (user created between check and insert)."""
    # First check passes, but create_user fails due to race condition
    mock_get_user.return_value = None
    mock_hash_password.return_value = "hashed_password"
    mock_create_user.side_effect = ValueError("User with email test@example.com already exists")

    # Create request
    user = UserRegister(email="test@example.com", password="securepass123")

    # Call endpoint function and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await register(user)

    # Assertions
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in exc_info.value.detail.lower()


def test_register_invalid_email():
    """Test registration fails with invalid email format."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        UserRegister(email="not-an-email", password="securepass123")


def test_register_short_password():
    """Test registration fails when password is too short."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        UserRegister(email="test@example.com", password="short")


# ==================== Login Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.auth.get_user_by_email")
@patch("transcription_service.routers.auth.verify_password")
@patch("transcription_service.routers.auth.create_jwt_token")
async def test_login_success(mock_create_jwt, mock_verify_password, mock_get_user, mock_user):
    """Test successful login with valid credentials."""
    # Setup mocks
    mock_get_user.return_value = mock_user
    mock_verify_password.return_value = True
    mock_create_jwt.return_value = "mock_jwt_token_xyz"

    # Create request
    credentials = UserLogin(email="test@example.com", password="correctpassword")

    # Call endpoint function
    response = await login(credentials)

    # Assertions
    assert response.access_token == "mock_jwt_token_xyz"
    assert response.token_type == "bearer"

    # Verify mocks
    mock_get_user.assert_called_once_with("test@example.com")
    mock_verify_password.assert_called_once_with("correctpassword", mock_user["password_hash"])
    mock_create_jwt.assert_called_once_with("test@example.com")


@pytest.mark.anyio
@patch("transcription_service.routers.auth.get_user_by_email")
async def test_login_user_not_found(mock_get_user):
    """Test login fails when user does not exist."""
    mock_get_user.return_value = None

    # Create request
    credentials = UserLogin(email="nonexistent@example.com", password="somepassword")

    # Call endpoint function and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await login(credentials)

    # Assertions
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid email or password" in exc_info.value.detail.lower()
    mock_get_user.assert_called_once_with("nonexistent@example.com")


@pytest.mark.anyio
@patch("transcription_service.routers.auth.get_user_by_email")
@patch("transcription_service.routers.auth.verify_password")
async def test_login_wrong_password(mock_verify_password, mock_get_user, mock_user):
    """Test login fails with incorrect password."""
    mock_get_user.return_value = mock_user
    mock_verify_password.return_value = False  # Password does not match

    # Create request
    credentials = UserLogin(email="test@example.com", password="wrongpassword")

    # Call endpoint function and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await login(credentials)

    # Assertions
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid email or password" in exc_info.value.detail.lower()


def test_login_invalid_email_format():
    """Test login with invalid email format."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        UserLogin(email="not-an-email", password="somepassword")


# ==================== Get Current User Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.auth.get_user_by_email")
async def test_get_me_success(mock_get_user, mock_user):
    """Test getting current user profile with valid token."""
    # Setup mocks
    mock_get_user.return_value = mock_user

    # Call endpoint function (user_email injected by dependency)
    response = await get_current_user_profile(user_email="test@example.com")

    # Assertions
    assert response.email == "test@example.com"
    assert response.display_name == "Test User"
    assert response.created_at is not None

    # Verify mocks
    mock_get_user.assert_called_once_with("test@example.com")


@pytest.mark.anyio
@patch("transcription_service.routers.auth.get_user_by_email")
async def test_get_me_no_display_name(mock_get_user):
    """Test getting current user profile when display_name is not set."""
    # User without display_name
    user_data = {
        "email": "test@example.com",
        "password_hash": "hashed",
        "created_at": "2026-03-26T10:00:00+00:00",
    }
    mock_get_user.return_value = user_data

    # Call endpoint function
    response = await get_current_user_profile(user_email="test@example.com")

    # Assertions
    assert response.email == "test@example.com"
    assert response.display_name is None


@pytest.mark.anyio
@patch("transcription_service.routers.auth.get_user_by_email")
async def test_get_me_user_not_found_in_db(mock_get_user):
    """Test /auth/me handles case where user is deleted after token issued."""
    mock_get_user.return_value = None  # User not found

    # Call endpoint function and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_profile(user_email="test@example.com")

    # Should return 404 (edge case: user deleted after token creation)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "user not found" in exc_info.value.detail.lower()


# ==================== Auth Dependency Tests ====================


@patch("transcription_service.auth.verify_jwt_token")
def test_get_current_user_missing_header(mock_verify_jwt):
    """Test get_current_user dependency when Authorization header is missing."""
    from transcription_service.auth import get_current_user

    # Create mock request without Authorization header
    mock_request = MagicMock()
    mock_request.headers.get.return_value = None

    # Call dependency
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(mock_request)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "missing authorization header" in exc_info.value.detail.lower()


@patch("transcription_service.auth.verify_jwt_token")
def test_get_current_user_invalid_format(mock_verify_jwt):
    """Test get_current_user dependency with malformed Authorization header."""
    from transcription_service.auth import get_current_user

    # Create mock request with invalid Authorization header
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "InvalidFormat"

    # Call dependency
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(mock_request)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid authorization header format" in exc_info.value.detail.lower()


@patch("transcription_service.auth.verify_jwt_token")
def test_get_current_user_invalid_token(mock_verify_jwt):
    """Test get_current_user dependency with invalid/expired token."""
    from transcription_service.auth import get_current_user

    mock_verify_jwt.return_value = None  # Token verification fails

    # Create mock request with Bearer token
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "Bearer invalid_token"

    # Call dependency
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(mock_request)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid or expired token" in exc_info.value.detail.lower()


@patch("transcription_service.auth.verify_jwt_token")
def test_get_current_user_success(mock_verify_jwt):
    """Test get_current_user dependency with valid token."""
    from transcription_service.auth import get_current_user

    mock_verify_jwt.return_value = "test@example.com"

    # Create mock request with valid Bearer token
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "Bearer valid_token_123"

    # Call dependency
    email = get_current_user(mock_request)

    assert email == "test@example.com"
    mock_verify_jwt.assert_called_once_with("valid_token_123")


# ==================== End-to-End Flow Test ====================


@pytest.mark.anyio
@patch("transcription_service.routers.auth.get_user_by_email")
@patch("transcription_service.routers.auth.create_user")
@patch("transcription_service.routers.auth.hash_password")
@patch("transcription_service.routers.auth.verify_password")
@patch("transcription_service.routers.auth.create_jwt_token")
async def test_register_login_get_me_flow(
    mock_create_jwt, mock_verify_password, mock_hash_password, mock_create_user, mock_get_user
):
    """Test complete flow: register → login → get profile."""
    # Step 1: Register new user
    mock_get_user.return_value = None  # No existing user
    mock_hash_password.return_value = "hashed_pass"
    mock_create_jwt.return_value = "token_from_register"

    user_reg = UserRegister(
        email="flow@example.com", password="password123", display_name="Flow User"
    )
    register_response = await register(user_reg)
    assert register_response.access_token == "token_from_register"

    # Step 2: Login with same credentials
    mock_get_user.return_value = {
        "email": "flow@example.com",
        "password_hash": "hashed_pass",
        "created_at": "2026-03-26T10:00:00+00:00",
        "display_name": "Flow User",
    }
    mock_verify_password.return_value = True
    mock_create_jwt.return_value = "token_from_login"

    credentials = UserLogin(email="flow@example.com", password="password123")
    login_response = await login(credentials)
    assert login_response.access_token == "token_from_login"

    # Step 3: Get user profile
    me_response = await get_current_user_profile(user_email="flow@example.com")
    assert me_response.email == "flow@example.com"
    assert me_response.display_name == "Flow User"
