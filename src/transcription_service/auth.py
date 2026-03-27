"""JWT and password utilities for transcription service authentication

This module provides JWT token creation and verification, password hashing with bcrypt,
and FastAPI dependency functions for extracting the current user from request headers.
"""

import os
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import HTTPException, Request, status

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-DO-NOT-USE-IN-PRODUCTION-CHANGE-ME")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7

# bcrypt Configuration
BCRYPT_ROUNDS = 12


def create_jwt_token(email: str) -> str:
    """Create a JWT token for the given email with 7-day expiration.

    Args:
        email: User email address to encode in the token

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_jwt_token("user@example.com")
        >>> print(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    payload = {
        "sub": email,
        "exp": datetime.now(UTC) + timedelta(days=JWT_EXPIRATION_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> str | None:
    """Verify a JWT token and return the email if valid.

    Args:
        token: JWT token string to verify

    Returns:
        Email address from token if valid, None if invalid or expired

    Example:
        >>> token = create_jwt_token("user@example.com")
        >>> email = verify_jwt_token(token)
        >>> print(email)
        'user@example.com'
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str | None = payload.get("sub")
        return email if email else None
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidTokenError:
        # Token is invalid (malformed, wrong signature, etc.)
        return None


def get_current_user(request: Request) -> str:
    """FastAPI dependency to extract and verify user email from Authorization header.

    Extracts the JWT token from the Authorization header (Bearer scheme),
    verifies it, and returns the user email. Raises 401 if token is missing,
    invalid, or expired.

    Args:
        request: FastAPI Request object

    Returns:
        User email address from verified JWT token

    Raises:
        HTTPException: 401 Unauthorized if token is missing, invalid, or expired

    Example:
        >>> from fastapi import Depends
        >>> @app.get("/protected")
        >>> async def protected_route(user_email: str = Depends(get_current_user)):
        ...     return {"user": user_email}
    """
    # Extract Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate Bearer scheme
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    token = parts[1]
    email = verify_jwt_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return email


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with 12 rounds.

    Args:
        password: Plain text password to hash

    Returns:
        bcrypt hash string (UTF-8 decoded)

    Example:
        >>> hashed = hash_password("mysecretpassword")
        >>> print(hashed)
        '$2b$12$...'
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain text password against a bcrypt hash.

    Args:
        plain: Plain text password to verify
        hashed: bcrypt hash string to verify against

    Returns:
        True if password matches hash, False otherwise

    Example:
        >>> hashed = hash_password("mysecretpassword")
        >>> verify_password("mysecretpassword", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    password_bytes = plain.encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)
