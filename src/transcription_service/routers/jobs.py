"""Job management endpoints for transcription service

This module provides REST API endpoints for managing transcription jobs:
- Upload audio files (<= 10MB direct upload)
- Request presigned URLs for large files (> 10MB)
- Confirm presigned uploads
- Submit YouTube URLs for transcription
- List and retrieve job details
- Delete jobs and associated files
"""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from transcription_service.auth import get_current_user
from transcription_service.batch import submit_transcription_job
from transcription_service.database import (
    create_file,
    create_job,
    delete_job as db_delete_job,
    get_job,
    list_files_for_job,
    list_jobs_for_user,
    update_file_status,
    update_job_status,
)
from transcription_service.models import (
    FileResponse,
    JobDetailResponse,
    JobResponse,
    PresignedUpload,
    PresignedUploadRequest,
    PresignedUploadResponse,
    UploadCompleteRequest,
    YouTubeRequest,
)
from transcription_service.s3 import (
    check_file_exists,
    delete_files_with_prefix,
    generate_presigned_download_url,
    generate_presigned_upload_url,
    get_input_bucket,
    get_output_bucket,
    upload_file_to_s3,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    limit: int = 20,
    offset: int = 0,
    user_email: str = Depends(get_current_user),
) -> list[JobResponse]:
    """List all jobs for the authenticated user.

    Returns jobs in reverse chronological order (newest first).
    Supports pagination via limit and offset parameters.

    Args:
        limit: Maximum number of jobs to return (default: 20)
        offset: Number of jobs to skip for pagination (default: 0)
        user_email: User email from JWT token (injected by dependency)

    Returns:
        List of JobResponse objects containing job summaries

    Example:
        >>> GET /jobs?limit=10&offset=0
        >>> [
        ...     {
        ...         "job_id": "123e4567-e89b-12d3-a456-426614174000",
        ...         "user_email": "user@example.com",
        ...         "status": "completed",
        ...         "created_at": "2026-03-26T10:00:00Z",
        ...         "total_files": 3,
        ...         "completed_files": 3,
        ...         "failed_files": 0
        ...     }
        ... ]
    """
    jobs = list_jobs_for_user(user_email, limit=limit, offset=offset)

    return [
        JobResponse(
            job_id=UUID(job["job_id"]),
            user_email=user_email,
            status=job["status"],
            created_at=job["created_at"],
            total_files=job.get("total_files", 0),
            completed_files=job.get("completed_files", 0),
            failed_files=job.get("failed_files", 0),
        )
        for job in jobs
    ]


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job_details(
    job_id: UUID,
    user_email: str = Depends(get_current_user),
) -> JobDetailResponse:
    """Get detailed information about a specific job.

    Includes job metadata and list of all files with their statuses.
    Generates presigned download URLs for completed transcription files.

    Args:
        job_id: UUID of the job to retrieve
        user_email: User email from JWT token (injected by dependency)

    Returns:
        JobDetailResponse with job details and file list

    Raises:
        HTTPException 404: Job not found
        HTTPException 403: Job does not belong to user

    Example:
        >>> GET /jobs/123e4567-e89b-12d3-a456-426614174000
        >>> {
        ...     "job_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "user_email": "user@example.com",
        ...     "status": "running",
        ...     "total_files": 2,
        ...     "completed_files": 1,
        ...     "files": [...]
        ... }
    """
    # Get job from database
    job = get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    # Verify job belongs to user
    if job["email"] != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job",
        )

    # Get all files for the job
    files = list_files_for_job(job_id)
    output_bucket = get_output_bucket()

    # Build file responses with download URLs for completed files
    file_responses = []
    for file in files:
        download_url = None
        if file["status"] == "completed" and "transcription_s3_key" in file:
            # Generate presigned download URL (1 hour expiration)
            download_url = generate_presigned_download_url(
                output_bucket,
                file["transcription_s3_key"],
                expiration=3600,
            )

        file_responses.append(
            FileResponse(
                file_id=UUID(file["file_id"]),
                filename=file["filename"],
                status=file["status"],
                created_at=file["created_at"],
                duration_seconds=file.get("duration_seconds"),
                download_url=download_url,
            )
        )

    return JobDetailResponse(
        job_id=job_id,
        user_email=user_email,
        status=job["status"],
        total_files=job.get("total_files", 0),
        completed_files=job.get("completed_files", 0),
        files=file_responses,
    )


@router.post("/upload", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def upload_files(
    files: list[UploadFile] = File(..., description="Audio files to transcribe (max 10MB each)"),
    user_email: str = Depends(get_current_user),
) -> JobResponse:
    """Upload audio files directly for transcription (files <= 10MB).

    Accepts multiple audio files via multipart/form-data.
    Files are uploaded to S3 and transcription jobs are queued immediately.

    Args:
        files: List of audio files from multipart form data
        user_email: User email from JWT token (injected by dependency)

    Returns:
        JobResponse with job details

    Raises:
        HTTPException 400: No files provided or file validation failed

    Example:
        >>> POST /jobs/upload
        >>> Content-Type: multipart/form-data
        >>> files[]: audio1.mp3
        >>> files[]: audio2.mp3
        >>> {
        ...     "job_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "user_email": "user@example.com",
        ...     "status": "queued",
        ...     "created_at": "2026-03-26T10:00:00Z",
        ...     "total_files": 2,
        ...     "completed_files": 0,
        ...     "failed_files": 0
        ... }
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )

    # Create job
    job_id = create_job(email=user_email, job_type="upload")
    input_bucket = get_input_bucket()
    output_bucket = get_output_bucket()

    # Process each file
    for upload_file in files:
        file_id = uuid4()
        s3_key = f"{user_email}/{job_id}/{file_id}/{upload_file.filename}"

        # Upload to S3
        try:
            upload_file_to_s3(upload_file.file, input_bucket, s3_key)
        except Exception as e:
            # If upload fails, mark job as failed
            update_job_status(job_id, "failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file {upload_file.filename}: {str(e)}",
            ) from e

        # Create file record
        create_file(
            job_id=job_id,
            file_id=file_id,
            filename=upload_file.filename or "unknown",
            s3_key=s3_key,
            status="uploaded",
        )

        # Submit transcription job to AWS Batch
        try:
            input_s3_uri = f"s3://{input_bucket}/{s3_key}"
            output_s3_uri = f"s3://{output_bucket}/{job_id}"
            submit_transcription_job(
                job_id=job_id,
                file_id=file_id,
                input_s3_uri=input_s3_uri,
                output_s3_uri=output_s3_uri,
            )

            # Update file status to queued
            update_file_status(file_id, job_id, "queued")
        except Exception as e:
            # If batch submission fails, mark file as failed
            update_file_status(file_id, job_id, "failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit transcription job for {upload_file.filename}: {str(e)}",
            ) from e

    # Get updated job info
    job = get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created job",
        )

    return JobResponse(
        job_id=job_id,
        user_email=user_email,
        status=job["status"],
        created_at=job["created_at"],
        total_files=job.get("total_files", 0),
        completed_files=job.get("completed_files", 0),
        failed_files=job.get("failed_files", 0),
    )


@router.post("/upload/presigned", response_model=PresignedUploadResponse)
async def request_presigned_urls(
    request: PresignedUploadRequest,
    user_email: str = Depends(get_current_user),
) -> PresignedUploadResponse:
    """Request presigned S3 URLs for uploading large files (> 10MB).

    Generates presigned URLs that allow clients to upload files directly to S3.
    Files must be uploaded within 15 minutes, then confirmed via /upload/complete.

    Args:
        request: PresignedUploadRequest with file metadata
        user_email: User email from JWT token (injected by dependency)

    Returns:
        PresignedUploadResponse with job_id and presigned URLs

    Example:
        >>> POST /jobs/upload/presigned
        >>> {
        ...     "files": [
        ...         {
        ...             "filename": "lecture.mp3",
        ...             "content_type": "audio/mpeg",
        ...             "size_bytes": 15728640
        ...         }
        ...     ]
        ... }
        >>> {
        ...     "job_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "uploads": [
        ...         {
        ...             "file_id": "abc123...",
        ...             "filename": "lecture.mp3",
        ...             "upload_url": "https://s3.amazonaws.com/..."
        ...         }
        ...     ]
        ... }
    """
    # Create job
    job_id = create_job(email=user_email, job_type="upload")
    input_bucket = get_input_bucket()

    uploads: list[PresignedUpload] = []

    # Generate presigned URL for each file
    for file_metadata in request.files:
        file_id = uuid4()
        s3_key = f"{user_email}/{job_id}/{file_id}/{file_metadata.filename}"

        # Generate presigned upload URL (15 minute expiration)
        upload_url = generate_presigned_upload_url(
            bucket=input_bucket,
            key=s3_key,
            expiration=900,  # 15 minutes
        )

        # Create file record with pending_upload status
        create_file(
            job_id=job_id,
            file_id=file_id,
            filename=file_metadata.filename,
            s3_key=s3_key,
            status="pending_upload",
        )

        uploads.append(
            PresignedUpload(
                file_id=file_id,
                filename=file_metadata.filename,
                upload_url=upload_url,
            )
        )

    return PresignedUploadResponse(job_id=job_id, uploads=uploads)


@router.post("/upload/complete", response_model=JobResponse)
async def complete_presigned_upload(
    request: UploadCompleteRequest,
    user_email: str = Depends(get_current_user),
) -> JobResponse:
    """Confirm that presigned uploads are complete and queue transcription jobs.

    Verifies that files exist in S3, updates their status, and submits
    transcription jobs to AWS Batch.

    Args:
        request: UploadCompleteRequest with job_id and file_ids
        user_email: User email from JWT token (injected by dependency)

    Returns:
        JobResponse with updated job status

    Raises:
        HTTPException 404: Job not found
        HTTPException 403: Job does not belong to user
        HTTPException 400: File not found in S3 or verification failed

    Example:
        >>> POST /jobs/upload/complete
        >>> {
        ...     "job_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "file_ids": ["abc123...", "def456..."]
        ... }
        >>> {
        ...     "job_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "status": "queued",
        ...     ...
        ... }
    """
    job_id = request.job_id

    # Get job and verify ownership
    job = get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    if job["email"] != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job",
        )

    # Get all files for the job
    files = list_files_for_job(job_id)
    file_map = {UUID(f["file_id"]): f for f in files}

    input_bucket = get_input_bucket()
    output_bucket = get_output_bucket()

    # Verify each file exists in S3 and submit transcription jobs
    for file_id in request.file_ids:
        if file_id not in file_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file_id} not found in job {job_id}",
            )

        file = file_map[file_id]
        s3_key = file["audio_s3_key"]

        # Check if file exists in S3
        if not check_file_exists(input_bucket, s3_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file['filename']} not found in S3. Please re-upload.",
            )

        # Update file status to uploaded
        update_file_status(file_id, job_id, "uploaded")

        # Submit transcription job to AWS Batch
        try:
            input_s3_uri = f"s3://{input_bucket}/{s3_key}"
            output_s3_uri = f"s3://{output_bucket}/{job_id}"
            submit_transcription_job(
                job_id=job_id,
                file_id=file_id,
                input_s3_uri=input_s3_uri,
                output_s3_uri=output_s3_uri,
            )

            # Update file status to queued
            update_file_status(file_id, job_id, "queued")
        except Exception as e:
            # If batch submission fails, mark file as failed
            update_file_status(file_id, job_id, "failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit transcription job: {str(e)}",
            ) from e

    # Update job status to queued
    update_job_status(job_id, "queued")

    # Get updated job info
    job = get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job",
        )

    return JobResponse(
        job_id=job_id,
        user_email=user_email,
        status=job["status"],
        created_at=job["created_at"],
        total_files=job.get("total_files", 0),
        completed_files=job.get("completed_files", 0),
        failed_files=job.get("failed_files", 0),
    )


@router.post("/youtube", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def transcribe_youtube(
    request: YouTubeRequest,
    user_email: str = Depends(get_current_user),
) -> JobResponse:
    """Submit YouTube URLs for audio extraction and transcription.

    Downloads audio from YouTube videos using yt-dlp and transcribes them.
    All processing happens asynchronously in AWS Batch.

    Args:
        request: YouTubeRequest with list of YouTube URLs
        user_email: User email from JWT token (injected by dependency)

    Returns:
        JobResponse with job details

    Example:
        >>> POST /jobs/youtube
        >>> {
        ...     "urls": [
        ...         "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ...         "https://youtu.be/dQw4w9WgXcQ"
        ...     ]
        ... }
        >>> {
        ...     "job_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "status": "queued",
        ...     ...
        ... }
    """
    # Create job
    job_id = create_job(email=user_email, job_type="youtube")
    input_bucket = get_input_bucket()
    output_bucket = get_output_bucket()

    # Process each URL
    for url in request.urls:
        file_id = uuid4()

        # Extract video ID from URL for filename
        # Simple extraction - works for youtube.com and youtu.be
        if "youtube.com" in url:
            video_id = url.split("v=")[-1].split("&")[0]
        elif "youtu.be" in url:
            video_id = url.split("/")[-1].split("?")[0]
        else:
            video_id = str(file_id)[:8]

        filename = f"{video_id}.mp3"
        s3_key = f"{user_email}/{job_id}/{file_id}/{filename}"

        # Create file record
        create_file(
            job_id=job_id,
            file_id=file_id,
            filename=filename,
            s3_key=s3_key,
            status="queued",
        )

        # Submit YouTube transcription job to AWS Batch
        # Note: This requires a modified batch job that runs yt-dlp first
        try:
            input_s3_uri = f"s3://{input_bucket}/{s3_key}"
            output_s3_uri = f"s3://{output_bucket}/{job_id}"

            # For YouTube jobs, we pass the URL as input and let the batch job
            # handle downloading with yt-dlp, then uploading to S3
            # The batch job needs to be modified to detect YouTube URLs
            submit_transcription_job(
                job_id=job_id,
                file_id=file_id,
                input_s3_uri=url,  # Pass YouTube URL instead of S3 URI
                output_s3_uri=output_s3_uri,
            )
        except Exception as e:
            # If batch submission fails, mark file as failed
            update_file_status(file_id, job_id, "failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit YouTube transcription job: {str(e)}",
            ) from e

    # Get updated job info
    job = get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created job",
        )

    return JobResponse(
        job_id=job_id,
        user_email=user_email,
        status=job["status"],
        created_at=job["created_at"],
        total_files=job.get("total_files", 0),
        completed_files=job.get("completed_files", 0),
        failed_files=job.get("failed_files", 0),
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    user_email: str = Depends(get_current_user),
) -> None:
    """Delete a job and all associated files from S3 and DynamoDB.

    Permanently removes all audio files, transcription results, and database records.
    This operation cannot be undone.

    Args:
        job_id: UUID of the job to delete
        user_email: User email from JWT token (injected by dependency)

    Returns:
        204 No Content on success

    Raises:
        HTTPException 404: Job not found
        HTTPException 403: Job does not belong to user

    Example:
        >>> DELETE /jobs/123e4567-e89b-12d3-a456-426614174000
        >>> (204 No Content)
    """
    # Get job and verify ownership
    job = get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    if job["email"] != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this job",
        )

    # Delete all files from S3
    input_bucket = get_input_bucket()
    output_bucket = get_output_bucket()
    s3_prefix = f"{user_email}/{job_id}/"

    try:
        # Delete from input bucket
        delete_files_with_prefix(input_bucket, s3_prefix)

        # Delete from output bucket
        delete_files_with_prefix(output_bucket, str(job_id))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete files from S3: {str(e)}",
        ) from e

    # Delete from DynamoDB
    try:
        db_delete_job(job_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job from database: {str(e)}",
        ) from e
