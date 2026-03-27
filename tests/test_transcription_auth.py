"""Tests for transcription service authentication utilities"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi import HTTPException, Request

from transcription_service.auth import (
    JWT_ALGORITHM,
    JWT_SECRET,
    create_jwt_token,
    get_current_user,
    hash_password,
    verify_jwt_token,
    verify_password,
)


class TestJWT:
    """Tests for JWT token creation and verification"""

    def test_create_jwt_token_returns_string(self) -> None:
        """Test that create_jwt_token returns a non-empty string"""
        token = create_jwt_token("test@example.com")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_jwt_token_is_valid_jwt(self) -> None:
        """Test that created token is a valid JWT"""
        token = create_jwt_token("test@example.com")
        # Should not raise an exception
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert "sub" in payload
        assert "exp" in payload

    def test_create_jwt_token_contains_email(self) -> None:
        """Test that JWT token contains the email in 'sub' claim"""
        email = "user@example.com"
        token = create_jwt_token(email)
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == email

    def test_create_jwt_token_has_7_day_expiration(self) -> None:
        """Test that JWT token expires in 7 days"""
        token = create_jwt_token("test@example.com")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Check expiration is approximately 7 days from now
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=UTC)
        now = datetime.now(UTC)
        delta = exp_datetime - now

        # Allow 1 second tolerance for test execution time
        assert timedelta(days=7) - timedelta(seconds=1) <= delta <= timedelta(days=7)

    def test_verify_jwt_token_returns_email_for_valid_token(self) -> None:
        """Test that verify_jwt_token returns email for valid token"""
        email = "test@example.com"
        token = create_jwt_token(email)
        result = verify_jwt_token(token)
        assert result == email

    def test_verify_jwt_token_returns_none_for_invalid_token(self) -> None:
        """Test that verify_jwt_token returns None for invalid token"""
        result = verify_jwt_token("invalid.token.here")
        assert result is None

    def test_verify_jwt_token_returns_none_for_expired_token(self) -> None:
        """Test that verify_jwt_token returns None for expired token"""
        # Create token that expired 1 hour ago
        payload = {
            "sub": "test@example.com",
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        result = verify_jwt_token(expired_token)
        assert result is None

    def test_verify_jwt_token_returns_none_for_wrong_secret(self) -> None:
        """Test that verify_jwt_token returns None for token signed with wrong secret"""
        payload = {
            "sub": "test@example.com",
            "exp": datetime.now(UTC) + timedelta(days=7),
        }
        wrong_token = jwt.encode(payload, "wrong-secret", algorithm=JWT_ALGORITHM)
        result = verify_jwt_token(wrong_token)
        assert result is None

    def test_verify_jwt_token_returns_none_for_missing_sub(self) -> None:
        """Test that verify_jwt_token returns None when 'sub' claim is missing"""
        payload = {"exp": datetime.now(UTC) + timedelta(days=7)}
        token_without_sub = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        result = verify_jwt_token(token_without_sub)
        assert result is None

    def test_roundtrip_create_and_verify(self) -> None:
        """Test complete roundtrip: create token and verify it"""
        email = "roundtrip@example.com"
        token = create_jwt_token(email)
        verified_email = verify_jwt_token(token)
        assert verified_email == email


class TestPasswordHashing:
    """Tests for password hashing and verification with bcrypt"""

    def test_hash_password_returns_string(self) -> None:
        """Test that hash_password returns a non-empty string"""
        hashed = hash_password("testpassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_returns_bcrypt_format(self) -> None:
        """Test that hash_password returns bcrypt format string ($2b$...)"""
        hashed = hash_password("testpassword")
        assert hashed.startswith("$2b$12$")  # bcrypt with 12 rounds

    def test_hash_password_different_for_same_input(self) -> None:
        """Test that hashing the same password twice produces different hashes (salt)"""
        password = "samepassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # Different due to random salt

    def test_verify_password_returns_true_for_correct_password(self) -> None:
        """Test that verify_password returns True for correct password"""
        password = "correctpassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_returns_false_for_wrong_password(self) -> None:
        """Test that verify_password returns False for wrong password"""
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_with_empty_password(self) -> None:
        """Test that empty password can be hashed and verified"""
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("nonempty", hashed) is False

    def test_verify_password_with_special_characters(self) -> None:
        """Test password hashing and verification with special characters"""
        password = "p@$$w0rd!#%^&*()"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_with_unicode(self) -> None:
        """Test password hashing and verification with unicode characters"""
        password = "パスワード🔒"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_roundtrip_hash_and_verify(self) -> None:
        """Test complete roundtrip: hash password and verify it"""
        password = "mysecretpassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False


class TestGetCurrentUser:
    """Tests for get_current_user FastAPI dependency"""

    def test_get_current_user_returns_email_for_valid_token(self) -> None:
        """Test that get_current_user returns email for valid Authorization header"""
        email = "user@example.com"
        token = create_jwt_token(email)

        # Mock request with valid Authorization header
        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        result = get_current_user(request)
        assert result == email

    def test_get_current_user_raises_401_for_missing_header(self) -> None:
        """Test that get_current_user raises 401 when Authorization header is missing"""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401
        assert "Missing Authorization header" in exc_info.value.detail

    def test_get_current_user_raises_401_for_invalid_format(self) -> None:
        """Test that get_current_user raises 401 for invalid header format"""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = "InvalidFormat"

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401
        assert "Invalid Authorization header format" in exc_info.value.detail

    def test_get_current_user_raises_401_for_wrong_scheme(self) -> None:
        """Test that get_current_user raises 401 for non-Bearer scheme"""
        token = create_jwt_token("user@example.com")
        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Basic {token}"

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401
        assert "Invalid Authorization header format" in exc_info.value.detail

    def test_get_current_user_raises_401_for_invalid_token(self) -> None:
        """Test that get_current_user raises 401 for invalid token"""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = "Bearer invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    def test_get_current_user_raises_401_for_expired_token(self) -> None:
        """Test that get_current_user raises 401 for expired token"""
        # Create expired token
        payload = {
            "sub": "user@example.com",
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {expired_token}"

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    def test_get_current_user_case_insensitive_bearer(self) -> None:
        """Test that get_current_user accepts Bearer/bearer/BEARER"""
        email = "user@example.com"
        token = create_jwt_token(email)

        for scheme in ["Bearer", "bearer", "BEARER"]:
            request = MagicMock(spec=Request)
            request.headers.get.return_value = f"{scheme} {token}"
            result = get_current_user(request)
            assert result == email
