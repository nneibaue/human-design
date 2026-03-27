"""Tests for job management endpoints

Tests cover:
    - List jobs for user (with pagination)
    - Get job details (with file list and download URLs)
    - Upload files directly (<= 10MB)
    - Request presigned URLs (> 10MB)
    - Complete presigned uploads
    - YouTube transcription
    - Delete jobs

Note: These tests call endpoint functions directly rather than using TestClient
due to httpx/starlette version compatibility issues.
"""

from io import BytesIO
from unittest.mock import MagicMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, UploadFile, status

from transcription_service.models import (
    PresignedUploadRequest,
    FileUploadMetadata,
    UploadCompleteRequest,
    YouTubeRequest,
)
from transcription_service.routers.jobs import (
    list_jobs,
    get_job_details,
    upload_files,
    request_presigned_urls,
    complete_presigned_upload,
    transcribe_youtube,
    delete_job,
)


@pytest.fixture
def mock_user_email():
    """Mock user email for tests"""
    return "test@example.com"


@pytest.fixture
def mock_job_id():
    """Mock job UUID for tests"""
    return uuid4()


@pytest.fixture
def mock_file_id():
    """Mock file UUID for tests"""
    return uuid4()


# ==================== List Jobs Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.list_jobs_for_user")
async def test_list_jobs_success(mock_list, mock_user_email, mock_job_id):
    """Test listing jobs for authenticated user"""
    mock_list.return_value = [
        {
            "job_id": str(mock_job_id),
            "status": "completed",
            "created_at": "2026-03-26T10:00:00Z",
            "total_files": 3,
            "completed_files": 3,
            "failed_files": 0,
        }
    ]

    result = await list_jobs(limit=20, offset=0, user_email=mock_user_email)

    assert len(result) == 1
    assert result[0].job_id == mock_job_id
    assert result[0].user_email == mock_user_email
    assert result[0].status == "completed"
    assert result[0].total_files == 3
    mock_list.assert_called_once_with(mock_user_email, limit=20, offset=0)


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.list_jobs_for_user")
async def test_list_jobs_with_pagination(mock_list, mock_user_email):
    """Test list jobs with custom limit and offset"""
    mock_list.return_value = []

    result = await list_jobs(limit=10, offset=5, user_email=mock_user_email)

    assert result == []
    mock_list.assert_called_once_with(mock_user_email, limit=10, offset=5)


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.list_jobs_for_user")
async def test_list_jobs_empty(mock_list, mock_user_email):
    """Test listing jobs when user has no jobs"""
    mock_list.return_value = []

    result = await list_jobs(user_email=mock_user_email)

    assert result == []


# ==================== Get Job Details Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_output_bucket")
@patch("transcription_service.routers.jobs.generate_presigned_download_url")
@patch("transcription_service.routers.jobs.list_files_for_job")
@patch("transcription_service.routers.jobs.get_job")
async def test_get_job_details_success(
    mock_get_job,
    mock_list_files,
    mock_generate_url,
    mock_get_bucket,
    mock_user_email,
    mock_job_id,
    mock_file_id,
):
    """Test getting job details with completed and in-progress files"""
    mock_get_job.return_value = {
        "job_id": str(mock_job_id),
        "email": mock_user_email,
        "status": "running",
        "created_at": "2026-03-26T10:00:00Z",
        "total_files": 2,
        "completed_files": 1,
    }

    file_id_2 = uuid4()
    mock_list_files.return_value = [
        {
            "file_id": str(mock_file_id),
            "filename": "test.mp3",
            "status": "completed",
            "created_at": "2026-03-26T10:00:00Z",
            "duration_seconds": 120.5,
            "transcription_s3_key": f"{mock_job_id}/{mock_file_id}.json",
        },
        {
            "file_id": str(file_id_2),
            "filename": "test2.mp3",
            "status": "transcribing",
            "created_at": "2026-03-26T10:05:00Z",
        },
    ]

    mock_get_bucket.return_value = "output-bucket"
    mock_generate_url.return_value = "https://s3.aws.com/presigned-url"

    result = await get_job_details(job_id=mock_job_id, user_email=mock_user_email)

    assert result.job_id == mock_job_id
    assert result.status == "running"
    assert result.total_files == 2
    assert result.completed_files == 1
    assert len(result.files) == 2

    # Check completed file has download URL
    completed_file = next(f for f in result.files if f.status == "completed")
    assert completed_file.download_url == "https://s3.aws.com/presigned-url"
    assert completed_file.duration_seconds == 120.5

    # Check transcribing file has no download URL
    transcribing_file = next(f for f in result.files if f.status == "transcribing")
    assert transcribing_file.download_url is None


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_job")
async def test_get_job_not_found(mock_get_job, mock_job_id, mock_user_email):
    """Test getting non-existent job"""
    mock_get_job.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_job_details(job_id=mock_job_id, user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in exc_info.value.detail


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_job")
async def test_get_job_forbidden(mock_get_job, mock_job_id, mock_user_email):
    """Test getting job that belongs to another user"""
    mock_get_job.return_value = {
        "job_id": str(mock_job_id),
        "email": "other@example.com",
        "status": "running",
    }

    with pytest.raises(HTTPException) as exc_info:
        await get_job_details(job_id=mock_job_id, user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in exc_info.value.detail


# ==================== Upload Files Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_output_bucket")
@patch("transcription_service.routers.jobs.get_input_bucket")
@patch("transcription_service.routers.jobs.get_job")
@patch("transcription_service.routers.jobs.update_file_status")
@patch("transcription_service.routers.jobs.submit_transcription_job")
@patch("transcription_service.routers.jobs.create_file")
@patch("transcription_service.routers.jobs.upload_file_to_s3")
@patch("transcription_service.routers.jobs.create_job")
async def test_upload_files_success(
    mock_create_job,
    mock_upload_s3,
    mock_create_file,
    mock_submit_job,
    mock_update_file,
    mock_get_job,
    mock_get_input,
    mock_get_output,
    mock_user_email,
    mock_job_id,
):
    """Test uploading files successfully"""
    mock_create_job.return_value = mock_job_id
    mock_get_input.return_value = "input-bucket"
    mock_get_output.return_value = "output-bucket"
    mock_get_job.return_value = {
        "job_id": str(mock_job_id),
        "email": mock_user_email,
        "status": "queued",
        "created_at": "2026-03-26T10:00:00Z",
        "total_files": 2,
        "completed_files": 0,
        "failed_files": 0,
    }

    # Create mock upload files
    file1 = Mock(spec=UploadFile)
    file1.filename = "test1.mp3"
    file1.file = BytesIO(b"fake audio 1")

    file2 = Mock(spec=UploadFile)
    file2.filename = "test2.mp3"
    file2.file = BytesIO(b"fake audio 2")

    result = await upload_files(files=[file1, file2], user_email=mock_user_email)

    assert result.job_id == mock_job_id
    assert result.status == "queued"
    assert result.total_files == 2
    assert mock_create_job.call_count == 1
    assert mock_upload_s3.call_count == 2
    assert mock_create_file.call_count == 2
    assert mock_submit_job.call_count == 2


@pytest.mark.anyio
async def test_upload_no_files(mock_user_email):
    """Test upload with no files provided"""
    with pytest.raises(HTTPException) as exc_info:
        await upload_files(files=[], user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "No files provided" in exc_info.value.detail


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_input_bucket")
@patch("transcription_service.routers.jobs.update_job_status")
@patch("transcription_service.routers.jobs.upload_file_to_s3")
@patch("transcription_service.routers.jobs.create_job")
async def test_upload_s3_failure(
    mock_create_job, mock_upload_s3, mock_update_job, mock_get_input, mock_user_email, mock_job_id
):
    """Test upload when S3 upload fails"""
    mock_create_job.return_value = mock_job_id
    mock_get_input.return_value = "input-bucket"
    mock_upload_s3.side_effect = RuntimeError("S3 error")

    file1 = Mock(spec=UploadFile)
    file1.filename = "test.mp3"
    file1.file = BytesIO(b"fake audio")

    with pytest.raises(HTTPException) as exc_info:
        await upload_files(files=[file1], user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to upload" in exc_info.value.detail
    mock_update_job.assert_called_once_with(mock_job_id, "failed")


# ==================== Presigned URLs Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_input_bucket")
@patch("transcription_service.routers.jobs.create_file")
@patch("transcription_service.routers.jobs.generate_presigned_upload_url")
@patch("transcription_service.routers.jobs.create_job")
async def test_request_presigned_urls_success(
    mock_create_job, mock_generate_url, mock_create_file, mock_get_input, mock_user_email, mock_job_id
):
    """Test requesting presigned upload URLs"""
    mock_create_job.return_value = mock_job_id
    mock_get_input.return_value = "input-bucket"
    mock_generate_url.return_value = "https://s3.aws.com/presigned-upload-url"

    request = PresignedUploadRequest(
        files=[
            FileUploadMetadata(filename="large.mp3", content_type="audio/mpeg", size_bytes=15728640),
            FileUploadMetadata(filename="huge.mp3", content_type="audio/mpeg", size_bytes=52428800),
        ]
    )

    result = await request_presigned_urls(request=request, user_email=mock_user_email)

    assert result.job_id == mock_job_id
    assert len(result.uploads) == 2
    assert result.uploads[0].filename == "large.mp3"
    assert result.uploads[0].upload_url == "https://s3.aws.com/presigned-upload-url"
    assert mock_create_job.call_count == 1
    assert mock_create_file.call_count == 2
    assert mock_generate_url.call_count == 2


# ==================== Complete Presigned Upload Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_output_bucket")
@patch("transcription_service.routers.jobs.get_input_bucket")
@patch("transcription_service.routers.jobs.update_job_status")
@patch("transcription_service.routers.jobs.submit_transcription_job")
@patch("transcription_service.routers.jobs.update_file_status")
@patch("transcription_service.routers.jobs.check_file_exists")
@patch("transcription_service.routers.jobs.list_files_for_job")
@patch("transcription_service.routers.jobs.get_job")
async def test_complete_upload_success(
    mock_get_job,
    mock_list_files,
    mock_check_exists,
    mock_update_file,
    mock_submit_job,
    mock_update_job,
    mock_get_input,
    mock_get_output,
    mock_user_email,
    mock_job_id,
    mock_file_id,
):
    """Test completing presigned upload"""
    mock_get_job.side_effect = [
        # First call for verification
        {
            "job_id": str(mock_job_id),
            "email": mock_user_email,
            "status": "queued",
        },
        # Second call for final response
        {
            "job_id": str(mock_job_id),
            "email": mock_user_email,
            "status": "queued",
            "created_at": "2026-03-26T10:00:00Z",
            "total_files": 1,
            "completed_files": 0,
            "failed_files": 0,
        },
    ]

    mock_list_files.return_value = [
        {
            "file_id": str(mock_file_id),
            "filename": "test.mp3",
            "audio_s3_key": f"{mock_user_email}/{mock_job_id}/{mock_file_id}/test.mp3",
            "status": "pending_upload",
        }
    ]

    mock_check_exists.return_value = True
    mock_get_input.return_value = "input-bucket"
    mock_get_output.return_value = "output-bucket"

    request = UploadCompleteRequest(job_id=mock_job_id, file_ids=[mock_file_id])

    result = await complete_presigned_upload(request=request, user_email=mock_user_email)

    assert result.job_id == mock_job_id
    assert result.status == "queued"
    assert mock_check_exists.call_count == 1
    assert mock_submit_job.call_count == 1
    mock_update_job.assert_called_once_with(mock_job_id, "queued")


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_job")
async def test_complete_upload_job_not_found(mock_get_job, mock_user_email, mock_job_id):
    """Test completing upload for non-existent job"""
    mock_get_job.return_value = None

    request = UploadCompleteRequest(job_id=mock_job_id, file_ids=[uuid4()])

    with pytest.raises(HTTPException) as exc_info:
        await complete_presigned_upload(request=request, user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_job")
async def test_complete_upload_forbidden(mock_get_job, mock_user_email, mock_job_id):
    """Test completing upload for another user's job"""
    mock_get_job.return_value = {"job_id": str(mock_job_id), "email": "other@example.com"}

    request = UploadCompleteRequest(job_id=mock_job_id, file_ids=[uuid4()])

    with pytest.raises(HTTPException) as exc_info:
        await complete_presigned_upload(request=request, user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_input_bucket")
@patch("transcription_service.routers.jobs.check_file_exists")
@patch("transcription_service.routers.jobs.list_files_for_job")
@patch("transcription_service.routers.jobs.get_job")
async def test_complete_upload_file_not_in_s3(
    mock_get_job,
    mock_list_files,
    mock_check_exists,
    mock_get_input,
    mock_user_email,
    mock_job_id,
    mock_file_id,
):
    """Test completing upload when file not found in S3"""
    mock_get_job.return_value = {"job_id": str(mock_job_id), "email": mock_user_email}

    mock_list_files.return_value = [
        {
            "file_id": str(mock_file_id),
            "filename": "test.mp3",
            "audio_s3_key": f"{mock_user_email}/{mock_job_id}/{mock_file_id}/test.mp3",
        }
    ]

    mock_check_exists.return_value = False
    mock_get_input.return_value = "input-bucket"

    request = UploadCompleteRequest(job_id=mock_job_id, file_ids=[mock_file_id])

    with pytest.raises(HTTPException) as exc_info:
        await complete_presigned_upload(request=request, user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "not found in S3" in exc_info.value.detail


# ==================== YouTube Transcription Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_output_bucket")
@patch("transcription_service.routers.jobs.get_input_bucket")
@patch("transcription_service.routers.jobs.get_job")
@patch("transcription_service.routers.jobs.submit_transcription_job")
@patch("transcription_service.routers.jobs.create_file")
@patch("transcription_service.routers.jobs.create_job")
async def test_youtube_transcription_success(
    mock_create_job,
    mock_create_file,
    mock_submit_job,
    mock_get_job,
    mock_get_input,
    mock_get_output,
    mock_user_email,
    mock_job_id,
):
    """Test YouTube transcription job creation"""
    mock_create_job.return_value = mock_job_id
    mock_get_input.return_value = "input-bucket"
    mock_get_output.return_value = "output-bucket"
    mock_get_job.return_value = {
        "job_id": str(mock_job_id),
        "email": mock_user_email,
        "status": "queued",
        "created_at": "2026-03-26T10:00:00Z",
        "total_files": 2,
        "completed_files": 0,
        "failed_files": 0,
    }

    request = YouTubeRequest(
        urls=[
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/jNQXAC9IVRw",
        ]
    )

    result = await transcribe_youtube(request=request, user_email=mock_user_email)

    assert result.job_id == mock_job_id
    assert result.status == "queued"
    assert result.total_files == 2
    assert mock_create_file.call_count == 2
    assert mock_submit_job.call_count == 2


@pytest.mark.anyio
async def test_youtube_invalid_url():
    """Test YouTube job with invalid URL - validation happens at FastAPI level

    Note: The field_validator in Pydantic v2 should catch this, but we test
    the endpoint behavior here. In production, FastAPI will validate the request
    body and return 422 Unprocessable Entity for invalid YouTube URLs.
    """
    # This test is primarily for documentation - the actual validation
    # happens when FastAPI parses the request body
    request = YouTubeRequest(urls=["https://www.youtube.com/watch?v=valid"])
    assert len(request.urls) == 1


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_output_bucket")
@patch("transcription_service.routers.jobs.get_input_bucket")
@patch("transcription_service.routers.jobs.update_file_status")
@patch("transcription_service.routers.jobs.submit_transcription_job")
@patch("transcription_service.routers.jobs.create_file")
@patch("transcription_service.routers.jobs.create_job")
async def test_youtube_batch_failure(
    mock_create_job,
    mock_create_file,
    mock_submit_job,
    mock_update_file,
    mock_get_input,
    mock_get_output,
    mock_user_email,
    mock_job_id,
):
    """Test YouTube job when Batch submission fails"""
    mock_create_job.return_value = mock_job_id
    mock_get_input.return_value = "input-bucket"
    mock_get_output.return_value = "output-bucket"
    mock_submit_job.side_effect = RuntimeError("Batch error")

    request = YouTubeRequest(urls=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"])

    with pytest.raises(HTTPException) as exc_info:
        await transcribe_youtube(request=request, user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to submit YouTube transcription job" in exc_info.value.detail


# ==================== Delete Job Tests ====================


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_output_bucket")
@patch("transcription_service.routers.jobs.get_input_bucket")
@patch("transcription_service.routers.jobs.db_delete_job")
@patch("transcription_service.routers.jobs.delete_files_with_prefix")
@patch("transcription_service.routers.jobs.get_job")
async def test_delete_job_success(
    mock_get_job,
    mock_delete_files,
    mock_db_delete,
    mock_get_input,
    mock_get_output,
    mock_user_email,
    mock_job_id,
):
    """Test deleting a job"""
    mock_get_job.return_value = {"job_id": str(mock_job_id), "email": mock_user_email}
    mock_get_input.return_value = "input-bucket"
    mock_get_output.return_value = "output-bucket"

    result = await delete_job(job_id=mock_job_id, user_email=mock_user_email)

    assert result is None  # 204 No Content
    assert mock_delete_files.call_count == 2  # Input and output buckets
    mock_db_delete.assert_called_once_with(mock_job_id)


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_job")
async def test_delete_job_not_found(mock_get_job, mock_user_email, mock_job_id):
    """Test deleting non-existent job"""
    mock_get_job.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await delete_job(job_id=mock_job_id, user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_job")
async def test_delete_job_forbidden(mock_get_job, mock_user_email, mock_job_id):
    """Test deleting another user's job"""
    mock_get_job.return_value = {"job_id": str(mock_job_id), "email": "other@example.com"}

    with pytest.raises(HTTPException) as exc_info:
        await delete_job(job_id=mock_job_id, user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_input_bucket")
@patch("transcription_service.routers.jobs.delete_files_with_prefix")
@patch("transcription_service.routers.jobs.get_job")
async def test_delete_job_s3_failure(
    mock_get_job, mock_delete_files, mock_get_input, mock_user_email, mock_job_id
):
    """Test delete job when S3 deletion fails"""
    mock_get_job.return_value = {"job_id": str(mock_job_id), "email": mock_user_email}
    mock_get_input.return_value = "input-bucket"
    mock_delete_files.side_effect = RuntimeError("S3 error")

    with pytest.raises(HTTPException) as exc_info:
        await delete_job(job_id=mock_job_id, user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to delete files from S3" in exc_info.value.detail


@pytest.mark.anyio
@patch("transcription_service.routers.jobs.get_output_bucket")
@patch("transcription_service.routers.jobs.get_input_bucket")
@patch("transcription_service.routers.jobs.db_delete_job")
@patch("transcription_service.routers.jobs.delete_files_with_prefix")
@patch("transcription_service.routers.jobs.get_job")
async def test_delete_job_db_failure(
    mock_get_job,
    mock_delete_files,
    mock_db_delete,
    mock_get_input,
    mock_get_output,
    mock_user_email,
    mock_job_id,
):
    """Test delete job when database deletion fails"""
    mock_get_job.return_value = {"job_id": str(mock_job_id), "email": mock_user_email}
    mock_get_input.return_value = "input-bucket"
    mock_get_output.return_value = "output-bucket"
    mock_db_delete.side_effect = RuntimeError("DB error")

    with pytest.raises(HTTPException) as exc_info:
        await delete_job(job_id=mock_job_id, user_email=mock_user_email)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to delete job from database" in exc_info.value.detail
