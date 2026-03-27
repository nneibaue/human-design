"""Authentication endpoints for user registration, login, and profile management.

This module provides three endpoints:
    - POST /auth/register: Create new user with auto-login
    - POST /auth/login: Authenticate existing user
    - GET /auth/me: Get current user profile (requires authentication)
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from transcription_service.auth import (
    create_jwt_token,
    get_current_user,
    hash_password,
    verify_password,
)
from transcription_service.database import create_user, get_user_by_email
from transcription_service.models import TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new user account with email and password. "
        "Returns JWT token for immediate login."
    ),
)
async def register(user: UserRegister) -> TokenResponse:
    """Register a new user and return authentication token.

    Creates a new user account with the provided email, password, and optional
    display name. The password is hashed using bcrypt before storage. On successful
    registration, a JWT token is automatically generated and returned, allowing
    the user to immediately access protected endpoints without a separate login.

    Args:
        user: User registration data (email, password, display_name)

    Returns:
        TokenResponse with access_token and token_type

    Raises:
        HTTPException 400: If user with this email already exists

    Example:
        >>> response = client.post("/auth/register", json={
        ...     "email": "user@example.com",
        ...     "password": "securepass123",
        ...     "display_name": "John Doe"
        ... })
        >>> print(response.json())
        {"access_token": "eyJhbGc...", "token_type": "bearer"}
    """
    # Check if user already exists
    existing_user = get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user.email} already exists",
        )

    # Hash password and create user
    password_hash = hash_password(user.password)
    try:
        create_user(
            email=user.email, password_hash=password_hash, display_name=user.display_name
        )
    except ValueError as e:
        # create_user raises ValueError if user already exists (race condition)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # Auto-login: generate JWT token
    access_token = create_jwt_token(user.email)
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description="Authenticate user and return JWT token for accessing protected endpoints.",
)
async def login(credentials: UserLogin) -> TokenResponse:
    """Authenticate user and return JWT token.

    Validates the provided email and password against stored credentials.
    If authentication succeeds, returns a JWT token valid for 7 days.
    The token should be included in the Authorization header as
    "Bearer <token>" for all protected endpoints.

    Args:
        credentials: User login credentials (email, password)

    Returns:
        TokenResponse with access_token and token_type

    Raises:
        HTTPException 401: If email not found or password is incorrect

    Example:
        >>> response = client.post("/auth/login", json={
        ...     "email": "user@example.com",
        ...     "password": "securepass123"
        ... })
        >>> print(response.json())
        {"access_token": "eyJhbGc...", "token_type": "bearer"}
    """
    # Get user from database
    user = get_user_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token
    access_token = create_jwt_token(credentials.email)
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description=(
        "Return profile information for the authenticated user. "
        "Requires valid JWT token in Authorization header."
    ),
)
async def get_current_user_profile(user_email: str = Depends(get_current_user)) -> UserResponse:
    """Get current authenticated user's profile information.

    Extracts user email from the JWT token and retrieves their profile
    from the database. Returns user email, account creation timestamp,
    and optional display name.

    Args:
        user_email: Email extracted from JWT token (injected by dependency)

    Returns:
        UserResponse with email, created_at, and display_name

    Raises:
        HTTPException 401: If token is missing, invalid, or expired
        HTTPException 404: If user not found in database (should not happen)

    Example:
        >>> response = client.get(
        ...     "/auth/me",
        ...     headers={"Authorization": "Bearer eyJhbGc..."}
        ... )
        >>> print(response.json())
        {
            "email": "user@example.com",
            "created_at": "2026-03-26T10:00:00Z",
            "display_name": "John Doe"
        }
    """
    # Get user from database
    user = get_user_by_email(user_email)
    if not user:
        # This should not happen if JWT is valid, but handle it anyway
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found in database"
        )

    # Parse created_at timestamp
    created_at = datetime.fromisoformat(user["created_at"])

    return UserResponse(
        email=user["email"], created_at=created_at, display_name=user.get("display_name")
    )
