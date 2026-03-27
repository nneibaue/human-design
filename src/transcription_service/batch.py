"""AWS Batch job submission for transcription"""

import os
from uuid import UUID

import boto3


def _get_batch_client():
    """Get boto3 Batch client (lazy initialization for testing)"""
    return boto3.client("batch", region_name=os.environ.get("AWS_REGION", "us-east-1"))


def get_job_queue() -> str:
    """Get Batch job queue name from environment"""
    return os.environ["BATCH_JOB_QUEUE"]


def get_job_definition() -> str:
    """Get Batch job definition name from environment"""
    return os.environ["BATCH_JOB_DEFINITION"]


def get_dynamodb_table() -> str:
    """Get DynamoDB table name from environment"""
    return os.environ["DYNAMODB_TABLE"]


def submit_transcription_job(
    job_id: UUID,
    file_id: UUID,
    input_s3_uri: str,
    output_s3_uri: str,
    model_name: str = "large-v3",
) -> str:
    """Submit transcription job to AWS Batch

    Args:
        job_id: UUID of the parent job
        file_id: UUID of the file to transcribe
        input_s3_uri: S3 URI of the input audio file (e.g., s3://bucket/key)
        output_s3_uri: S3 URI prefix for output files (e.g., s3://bucket/job_id)
        model_name: Whisper model to use (default: large-v3)

    Returns:
        AWS Batch job ID (string)

    Raises:
        KeyError: If required environment variables are missing
        ClientError: If AWS Batch API call fails

    Example:
        >>> batch_job_id = submit_transcription_job(
        ...     job_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        ...     file_id=UUID("123e4567-e89b-12d3-a456-426614174001"),
        ...     input_s3_uri="s3://my-bucket/audio.mp3",
        ...     output_s3_uri="s3://my-bucket/output/job-123",
        ...     model_name="large-v3"
        ... )
        >>> print(batch_job_id)
        'abc123-def456-...'
    """
    job_name = f"transcribe-{file_id}"
    job_queue = get_job_queue()
    job_definition = get_job_definition()
    dynamodb_table = get_dynamodb_table()

    # Convert UUIDs to strings for command line
    job_id_str = str(job_id)
    file_id_str = str(file_id)

    # Build command for parallel_transcribe.py
    # Format: python /workspace/parallel_transcribe.py <input_s3_uri> <output_s3_uri> <job_id> <file_id> <model>
    command = [
        "python",
        "/workspace/parallel_transcribe.py",
        input_s3_uri,
        output_s3_uri,
        job_id_str,
        file_id_str,
        model_name,
    ]

    # Submit job to AWS Batch
    batch_client = _get_batch_client()
    response = batch_client.submit_job(
        jobName=job_name,
        jobQueue=job_queue,
        jobDefinition=job_definition,
        containerOverrides={
            "command": command,
            "environment": [
                {"name": "JOB_ID", "value": job_id_str},
                {"name": "FILE_ID", "value": file_id_str},
                {"name": "DYNAMODB_TABLE", "value": dynamodb_table},
            ],
        },
    )

    return response["jobId"]


def get_job_status(batch_job_id: str) -> dict:
    """Get AWS Batch job status

    Args:
        batch_job_id: AWS Batch job ID to query

    Returns:
        Dictionary containing job status information:
        - jobId: Batch job ID
        - jobName: Job name
        - status: Job status (SUBMITTED, PENDING, RUNNABLE, STARTING, RUNNING, SUCCEEDED, FAILED)
        - statusReason: Optional reason for current status
        - createdAt: Job creation timestamp
        - startedAt: Job start timestamp (if started)
        - stoppedAt: Job stop timestamp (if stopped)

    Raises:
        ClientError: If AWS Batch API call fails or job not found

    Example:
        >>> status = get_job_status("abc123-def456-...")
        >>> print(status["status"])
        'RUNNING'
    """
    batch_client = _get_batch_client()
    response = batch_client.describe_jobs(jobs=[batch_job_id])

    if not response.get("jobs"):
        raise ValueError(f"Batch job not found: {batch_job_id}")

    job = response["jobs"][0]

    return {
        "jobId": job["jobId"],
        "jobName": job["jobName"],
        "status": job["status"],
        "statusReason": job.get("statusReason"),
        "createdAt": job.get("createdAt"),
        "startedAt": job.get("startedAt"),
        "stoppedAt": job.get("stoppedAt"),
    }
