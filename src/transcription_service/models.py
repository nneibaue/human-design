"""Pydantic v2 models for transcription service API

This module defines all request and response models for the transcription service,
using Pydantic v2 for validation and serialization.
"""

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============================================================================
# Auth Models
# ============================================================================


class UserRegister(BaseModel):
    """User registration request"""

    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    display_name: Optional[str] = Field(None, description="Optional display name for the user")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepass123",
                "display_name": "John Doe",
            }
        }
    )


class UserLogin(BaseModel):
    """User login request"""

    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "user@example.com", "password": "securepass123"}}
    )


class TokenResponse(BaseModel):
    """JWT token response"""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User profile response"""

    email: EmailStr
    created_at: datetime
    display_name: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "created_at": "2026-03-26T10:00:00Z",
                "display_name": "John Doe",
            }
        }
    )


# ============================================================================
# Job Models
# ============================================================================

# Job and file status literals
JobStatus = Literal["queued", "running", "completed", "failed"]
JobType = Literal["upload", "youtube"]
FileStatus = Literal["pending_upload", "uploaded", "queued", "transcribing", "completed", "failed"]


class FileUploadMetadata(BaseModel):
    """Metadata for a file to be uploaded via presigned URL"""

    filename: str
    content_type: str
    size_bytes: int = Field(gt=0, description="File size in bytes, must be positive")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"filename": "lecture.mp3", "content_type": "audio/mpeg", "size_bytes": 15728640}
        }
    )


class PresignedUploadRequest(BaseModel):
    """Request for presigned upload URLs (for files >10MB)"""

    files: list[FileUploadMetadata] = Field(min_length=1, description="List of files to upload")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "files": [
                    {"filename": "lecture1.mp3", "content_type": "audio/mpeg", "size_bytes": 15728640},
                    {"filename": "lecture2.mp3", "content_type": "audio/mpeg", "size_bytes": 20971520},
                ]
            }
        }
    )


class PresignedUploadResponse(BaseModel):
    """Response with presigned upload URLs"""

    job_id: str
    uploads: list[dict[str, Any]]  # List of {file_id, filename, upload_url}

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "uploads": [
                    {
                        "file_id": "abc123",
                        "filename": "lecture1.mp3",
                        "upload_url": "https://s3.amazonaws.com/...",
                    }
                ],
            }
        }
    )


class UploadCompleteRequest(BaseModel):
    """Request to confirm presigned uploads are complete"""

    job_id: str
    file_ids: list[str] = Field(min_length=1, description="List of file IDs that were uploaded")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"job_id": "123e4567-e89b-12d3-a456-426614174000", "file_ids": ["abc123", "def456"]}
        }
    )


class YouTubeRequest(BaseModel):
    """Request to transcribe YouTube videos"""

    urls: list[str] = Field(min_length=1, description="List of YouTube URLs to transcribe")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "urls": [
                    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "https://youtu.be/dQw4w9WgXcQ",
                ]
            }
        }
    )


class JobResponse(BaseModel):
    """Job summary response"""

    job_id: str
    user_email: EmailStr
    status: JobStatus
    created_at: datetime
    total_files: int = Field(ge=0, description="Total number of files in the job")
    completed_files: int = Field(default=0, ge=0, description="Number of completed files")
    failed_files: int = Field(default=0, ge=0, description="Number of failed files")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_email": "user@example.com",
                "status": "running",
                "created_at": "2026-03-26T10:00:00Z",
                "total_files": 3,
                "completed_files": 1,
                "failed_files": 0,
            }
        }
    )


class FileResponse(BaseModel):
    """File response with transcription status"""

    file_id: str
    filename: str
    status: FileStatus
    created_at: datetime
    duration_seconds: Optional[float] = Field(None, ge=0, description="Audio duration in seconds")
    download_url: Optional[str] = Field(None, description="Pre-signed S3 URL for transcription download")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "abc123",
                "filename": "lecture1.mp3",
                "status": "completed",
                "created_at": "2026-03-26T10:00:00Z",
                "duration_seconds": 3600.5,
                "download_url": "https://s3.amazonaws.com/...",
            }
        }
    )


class JobDetailResponse(BaseModel):
    """Detailed job response with file list"""

    job_id: str
    user_email: EmailStr
    status: JobStatus
    total_files: int = Field(ge=0)
    completed_files: int = Field(ge=0)
    files: list[FileResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_email": "user@example.com",
                "status": "running",
                "total_files": 2,
                "completed_files": 1,
                "files": [
                    {
                        "file_id": "abc123",
                        "filename": "lecture1.mp3",
                        "status": "completed",
                        "created_at": "2026-03-26T10:00:00Z",
                        "duration_seconds": 3600.5,
                        "download_url": "https://s3.amazonaws.com/...",
                    },
                    {
                        "file_id": "def456",
                        "filename": "lecture2.mp3",
                        "status": "transcribing",
                        "created_at": "2026-03-26T10:05:00Z",
                        "duration_seconds": None,
                        "download_url": None,
                    },
                ],
            }
        }
    )
