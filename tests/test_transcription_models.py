"""Tests for transcription service Pydantic models"""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from transcription_service.models import (
    FileResponse,
    FileUploadMetadata,
    JobDetailResponse,
    JobResponse,
    PresignedUpload,
    PresignedUploadRequest,
    PresignedUploadResponse,
    TokenResponse,
    UploadCompleteRequest,
    UserLogin,
    UserRegister,
    UserResponse,
    YouTubeRequest,
)


# ============================================================================
# Auth Models Tests
# ============================================================================


def test_user_register_valid():
    """Test valid user registration"""
    user = UserRegister(
        email="test@example.com", password="password123", display_name="Test User"
    )
    assert user.email == "test@example.com"
    assert user.password == "password123"
    assert user.display_name == "Test User"


def test_user_register_invalid_email():
    """Test user registration with invalid email"""
    with pytest.raises(ValidationError):
        UserRegister(email="not-an-email", password="password123")


def test_user_register_short_password():
    """Test user registration with password too short"""
    with pytest.raises(ValidationError):
        UserRegister(email="test@example.com", password="short")


def test_user_login_valid():
    """Test valid user login"""
    login = UserLogin(email="test@example.com", password="password123")
    assert login.email == "test@example.com"
    assert login.password == "password123"


def test_token_response():
    """Test token response model"""
    token = TokenResponse(access_token="abc123xyz")
    assert token.access_token == "abc123xyz"
    assert token.token_type == "bearer"


def test_user_response():
    """Test user response model"""
    now = datetime.now(timezone.utc)
    user = UserResponse(email="test@example.com", created_at=now, display_name="Test")
    assert user.email == "test@example.com"
    assert user.created_at == now
    assert user.display_name == "Test"


# ============================================================================
# Job Models Tests
# ============================================================================


def test_file_upload_metadata_valid():
    """Test valid file upload metadata"""
    metadata = FileUploadMetadata(
        filename="lecture.mp3", content_type="audio/mpeg", size_bytes=15728640
    )
    assert metadata.filename == "lecture.mp3"
    assert metadata.content_type == "audio/mpeg"
    assert metadata.size_bytes == 15728640


def test_file_upload_metadata_empty_filename():
    """Test file upload metadata with empty filename"""
    with pytest.raises(ValidationError):
        FileUploadMetadata(filename="", content_type="audio/mpeg", size_bytes=1000)


def test_file_upload_metadata_long_filename():
    """Test file upload metadata with filename too long"""
    with pytest.raises(ValidationError):
        FileUploadMetadata(filename="x" * 256, content_type="audio/mpeg", size_bytes=1000)


def test_file_upload_metadata_invalid_content_type():
    """Test file upload metadata with invalid content type"""
    with pytest.raises(ValidationError):
        FileUploadMetadata(filename="test.txt", content_type="text/plain", size_bytes=1000)


def test_file_upload_metadata_zero_size():
    """Test file upload metadata with zero size"""
    with pytest.raises(ValidationError):
        FileUploadMetadata(filename="test.mp3", content_type="audio/mpeg", size_bytes=0)


def test_presigned_upload_request_valid():
    """Test valid presigned upload request"""
    request = PresignedUploadRequest(
        files=[
            FileUploadMetadata(
                filename="lecture.mp3", content_type="audio/mpeg", size_bytes=15728640
            )
        ]
    )
    assert len(request.files) == 1
    assert request.files[0].filename == "lecture.mp3"


def test_presigned_upload_request_empty():
    """Test presigned upload request with no files"""
    with pytest.raises(ValidationError):
        PresignedUploadRequest(files=[])


def test_presigned_upload_valid():
    """Test valid presigned upload"""
    file_id = uuid.uuid4()
    upload = PresignedUpload(
        file_id=file_id, filename="lecture.mp3", upload_url="https://s3.amazonaws.com/..."
    )
    assert upload.file_id == file_id
    assert upload.filename == "lecture.mp3"
    assert upload.upload_url == "https://s3.amazonaws.com/..."


def test_presigned_upload_invalid_uuid():
    """Test presigned upload with invalid UUID"""
    with pytest.raises(ValidationError):
        PresignedUpload(
            file_id="not-a-uuid",
            filename="lecture.mp3",
            upload_url="https://s3.amazonaws.com/...",
        )


def test_presigned_upload_response_valid():
    """Test valid presigned upload response"""
    job_id = uuid.uuid4()
    file_id = uuid.uuid4()
    response = PresignedUploadResponse(
        job_id=job_id,
        uploads=[
            PresignedUpload(
                file_id=file_id,
                filename="lecture.mp3",
                upload_url="https://s3.amazonaws.com/...",
            )
        ],
    )
    assert response.job_id == job_id
    assert len(response.uploads) == 1
    assert response.uploads[0].file_id == file_id


def test_upload_complete_request_valid():
    """Test valid upload complete request"""
    job_id = uuid.uuid4()
    file_id1 = uuid.uuid4()
    file_id2 = uuid.uuid4()
    request = UploadCompleteRequest(job_id=job_id, file_ids=[file_id1, file_id2])
    assert request.job_id == job_id
    assert len(request.file_ids) == 2
    assert file_id1 in request.file_ids
    assert file_id2 in request.file_ids


def test_upload_complete_request_empty():
    """Test upload complete request with no file IDs"""
    job_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        UploadCompleteRequest(job_id=job_id, file_ids=[])


def test_youtube_request_valid():
    """Test valid YouTube request"""
    request = YouTubeRequest(
        urls=[
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
        ]
    )
    assert len(request.urls) == 2
    assert "youtube.com" in request.urls[0]
    assert "youtu.be" in request.urls[1]


def test_youtube_request_invalid_url():
    """Test YouTube request with non-YouTube URL"""
    with pytest.raises(ValidationError, match="Invalid YouTube URL"):
        YouTubeRequest(urls=["https://vimeo.com/123456"])


def test_youtube_request_empty():
    """Test YouTube request with no URLs"""
    with pytest.raises(ValidationError):
        YouTubeRequest(urls=[])


def test_job_response_valid():
    """Test valid job response"""
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    response = JobResponse(
        job_id=job_id,
        user_email="test@example.com",
        status="running",
        created_at=now,
        total_files=3,
        completed_files=1,
        failed_files=0,
    )
    assert response.job_id == job_id
    assert response.user_email == "test@example.com"
    assert response.status == "running"
    assert response.total_files == 3
    assert response.completed_files == 1
    assert response.failed_files == 0


def test_file_response_valid():
    """Test valid file response"""
    file_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    response = FileResponse(
        file_id=file_id,
        filename="lecture.mp3",
        status="completed",
        created_at=now,
        duration_seconds=3600.5,
        download_url="https://s3.amazonaws.com/...",
    )
    assert response.file_id == file_id
    assert response.filename == "lecture.mp3"
    assert response.status == "completed"
    assert response.duration_seconds == 3600.5


def test_file_response_empty_filename():
    """Test file response with empty filename"""
    file_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        FileResponse(
            file_id=file_id,
            filename="",
            status="completed",
            created_at=now,
        )


def test_job_detail_response_valid():
    """Test valid job detail response"""
    job_id = uuid.uuid4()
    file_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    response = JobDetailResponse(
        job_id=job_id,
        user_email="test@example.com",
        status="running",
        total_files=1,
        completed_files=0,
        files=[
            FileResponse(
                file_id=file_id,
                filename="lecture.mp3",
                status="transcribing",
                created_at=now,
            )
        ],
    )
    assert response.job_id == job_id
    assert response.total_files == 1
    assert len(response.files) == 1
    assert response.files[0].file_id == file_id


# ============================================================================
# JSON Serialization Tests
# ============================================================================


def test_user_register_json_roundtrip():
    """Test JSON serialization/deserialization for UserRegister"""
    user = UserRegister(email="test@example.com", password="password123")
    json_data = user.model_dump_json()
    user_restored = UserRegister.model_validate_json(json_data)
    assert user_restored.email == user.email
    assert user_restored.password == user.password


def test_presigned_upload_response_json_roundtrip():
    """Test JSON serialization/deserialization for PresignedUploadResponse"""
    job_id = uuid.uuid4()
    file_id = uuid.uuid4()
    response = PresignedUploadResponse(
        job_id=job_id,
        uploads=[
            PresignedUpload(
                file_id=file_id,
                filename="lecture.mp3",
                upload_url="https://s3.amazonaws.com/...",
            )
        ],
    )
    json_data = response.model_dump_json()
    response_restored = PresignedUploadResponse.model_validate_json(json_data)
    assert response_restored.job_id == response.job_id
    assert response_restored.uploads[0].file_id == response.uploads[0].file_id


def test_youtube_request_json_roundtrip():
    """Test JSON serialization/deserialization for YouTubeRequest"""
    request = YouTubeRequest(urls=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
    json_data = request.model_dump_json()
    request_restored = YouTubeRequest.model_validate_json(json_data)
    assert request_restored.urls == request.urls
