"""DynamoDB operations for transcription service using single-table design.

Single-table design:
    Users:
        PK: USER#<email>
        SK: METADATA

    Jobs (owned by user):
        PK: USER#<email>
        SK: JOB#<timestamp>#<uuid>
        Attributes: job_id (for GSI lookup)

    Job Metadata:
        PK: JOB#<job_id>
        SK: #METADATA

    Files (belonging to job):
        PK: JOB#<job_id>
        SK: FILE#<file_id>

    GSI for job lookup:
        Index: job_id-index
        GSI1PK: job_id
"""

import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import boto3
from botocore.exceptions import ClientError


# Configuration
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "transcription-service")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Initialize boto3 client
dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)


def _now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _dict_to_item(data: dict[str, Any]) -> dict[str, Any]:
    """Convert Python dict to DynamoDB item format."""
    item = {}
    for key, value in data.items():
        if value is None:
            continue
        elif isinstance(value, str):
            item[key] = {"S": value}
        elif isinstance(value, int):
            item[key] = {"N": str(value)}
        elif isinstance(value, float):
            item[key] = {"N": str(value)}
        elif isinstance(value, list):
            item[key] = {"L": [_dict_to_item({"v": v})["v"] for v in value]}
        elif isinstance(value, bool):
            item[key] = {"BOOL": value}
        else:
            item[key] = {"S": str(value)}
    return item


def _item_to_dict(item: dict[str, Any]) -> dict[str, Any]:
    """Convert DynamoDB item format to Python dict."""
    result = {}
    for key, value in item.items():
        if "S" in value:
            result[key] = value["S"]
        elif "N" in value:
            # Try int first, fallback to float
            try:
                result[key] = int(value["N"])
            except ValueError:
                result[key] = float(value["N"])
        elif "BOOL" in value:
            result[key] = value["BOOL"]
        elif "L" in value:
            result[key] = [_item_to_dict({"v": v})["v"] for v in value["L"]]
        elif "NULL" in value:
            result[key] = None
    return result


# ==================== User Operations ====================


def create_user(email: str, password_hash: str, display_name: str | None = None) -> None:
    """Create a new user.

    Args:
        email: User's email address (unique identifier)
        password_hash: Bcrypt password hash
        display_name: Optional display name

    Raises:
        ClientError: If user already exists or DynamoDB operation fails
    """
    now = _now_iso()
    item = {
        "PK": {"S": f"USER#{email}"},
        "SK": {"S": "METADATA"},
        "email": {"S": email},
        "password_hash": {"S": password_hash},
        "created_at": {"S": now},
    }
    if display_name:
        item["display_name"] = {"S": display_name}

    try:
        dynamodb.put_item(
            TableName=DYNAMODB_TABLE,
            Item=item,
            ConditionExpression="attribute_not_exists(PK)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ValueError(f"User with email {email} already exists") from e
        raise


def get_user_by_email(email: str) -> dict | None:
    """Get user by email address.

    Args:
        email: User's email address

    Returns:
        User dict with keys: email, password_hash, created_at, display_name (optional)
        None if user not found
    """
    try:
        response = dynamodb.get_item(
            TableName=DYNAMODB_TABLE,
            Key={
                "PK": {"S": f"USER#{email}"},
                "SK": {"S": "METADATA"},
            },
        )
        if "Item" not in response:
            return None
        return _item_to_dict(response["Item"])
    except ClientError:
        return None


# ==================== Job Operations ====================


def create_job(email: str, job_type: str) -> UUID:
    """Create a new transcription job.

    Args:
        email: User's email address
        job_type: Type of job ("upload" or "youtube")

    Returns:
        UUID of the newly created job

    Raises:
        ClientError: If DynamoDB operation fails
    """
    job_id = uuid4()
    now = _now_iso()

    # Create job record owned by user
    user_job_item = {
        "PK": {"S": f"USER#{email}"},
        "SK": {"S": f"JOB#{now}#{job_id}"},
        "job_id": {"S": str(job_id)},
        "status": {"S": "queued"},
        "created_at": {"S": now},
        "updated_at": {"S": now},
        "total_files": {"N": "0"},
        "completed_files": {"N": "0"},
        "failed_files": {"N": "0"},
        "job_type": {"S": job_type},
    }

    # Create job metadata record for file lookups
    job_metadata_item = {
        "PK": {"S": f"JOB#{job_id}"},
        "SK": {"S": "#METADATA"},
        "job_id": {"S": str(job_id)},
        "email": {"S": email},
        "status": {"S": "queued"},
        "created_at": {"S": now},
        "updated_at": {"S": now},
        "total_files": {"N": "0"},
        "completed_files": {"N": "0"},
        "failed_files": {"N": "0"},
        "job_type": {"S": job_type},
    }

    # Write both items
    dynamodb.put_item(TableName=DYNAMODB_TABLE, Item=user_job_item)
    dynamodb.put_item(TableName=DYNAMODB_TABLE, Item=job_metadata_item)

    return job_id


def get_job(job_id: UUID) -> dict | None:
    """Get job by job_id.

    Args:
        job_id: Job UUID

    Returns:
        Job dict with keys: job_id, email, status, created_at, updated_at,
        total_files, completed_files, failed_files, job_type
        None if job not found
    """
    try:
        response = dynamodb.get_item(
            TableName=DYNAMODB_TABLE,
            Key={
                "PK": {"S": f"JOB#{job_id}"},
                "SK": {"S": "#METADATA"},
            },
        )
        if "Item" not in response:
            return None
        return _item_to_dict(response["Item"])
    except ClientError:
        return None


def list_jobs_for_user(email: str, limit: int = 20, offset: int = 0) -> list[dict]:
    """List all jobs for a user.

    Args:
        email: User's email address
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip (for pagination)

    Returns:
        List of job dicts, ordered by creation time (newest first)
    """
    try:
        response = dynamodb.query(
            TableName=DYNAMODB_TABLE,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"USER#{email}"},
                ":sk_prefix": {"S": "JOB#"},
            },
            ScanIndexForward=False,  # Newest first
            Limit=limit + offset,
        )

        items = [_item_to_dict(item) for item in response.get("Items", [])]

        # Manual offset handling (DynamoDB doesn't support offset directly)
        return items[offset : offset + limit]

    except ClientError:
        return []


def update_job_status(
    job_id: UUID,
    status: str,
    completed_files: int | None = None,
    failed_files: int | None = None,
) -> None:
    """Update job status and file counts.

    Args:
        job_id: Job UUID
        status: New status ("queued" | "running" | "completed" | "failed")
        completed_files: Number of completed files (if updating)
        failed_files: Number of failed files (if updating)

    Raises:
        ClientError: If DynamoDB operation fails
    """
    now = _now_iso()

    # Build update expression dynamically
    update_parts = ["#status = :status", "updated_at = :updated_at"]
    attr_names = {"#status": "status"}
    attr_values = {
        ":status": {"S": status},
        ":updated_at": {"S": now},
    }

    if completed_files is not None:
        update_parts.append("completed_files = :completed")
        attr_values[":completed"] = {"N": str(completed_files)}

    if failed_files is not None:
        update_parts.append("failed_files = :failed")
        attr_values[":failed"] = {"N": str(failed_files)}

    update_expression = "SET " + ", ".join(update_parts)

    # Update job metadata record
    dynamodb.update_item(
        TableName=DYNAMODB_TABLE,
        Key={
            "PK": {"S": f"JOB#{job_id}"},
            "SK": {"S": "#METADATA"},
        },
        UpdateExpression=update_expression,
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
    )

    # Also update user's job record (find it via query)
    job = get_job(job_id)
    if job and "email" in job:
        email = job["email"]
        # Query for the user's job record
        response = dynamodb.query(
            TableName=DYNAMODB_TABLE,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            FilterExpression="job_id = :job_id",
            ExpressionAttributeValues={
                ":pk": {"S": f"USER#{email}"},
                ":sk_prefix": {"S": "JOB#"},
                ":job_id": {"S": str(job_id)},
            },
            Limit=1,
        )

        if response.get("Items"):
            user_job_item = response["Items"][0]
            dynamodb.update_item(
                TableName=DYNAMODB_TABLE,
                Key={
                    "PK": user_job_item["PK"],
                    "SK": user_job_item["SK"],
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=attr_names,
                ExpressionAttributeValues=attr_values,
            )


def delete_job(job_id: UUID) -> None:
    """Delete a job and all associated files.

    Args:
        job_id: Job UUID

    Raises:
        ClientError: If DynamoDB operation fails
    """
    # Get job to find user email
    job = get_job(job_id)
    if not job:
        return

    email = job.get("email")

    # Delete all files for this job
    files = list_files_for_job(job_id)
    for file in files:
        dynamodb.delete_item(
            TableName=DYNAMODB_TABLE,
            Key={
                "PK": {"S": f"JOB#{job_id}"},
                "SK": {"S": f"FILE#{file['file_id']}"},
            },
        )

    # Delete job metadata record
    dynamodb.delete_item(
        TableName=DYNAMODB_TABLE,
        Key={
            "PK": {"S": f"JOB#{job_id}"},
            "SK": {"S": "#METADATA"},
        },
    )

    # Delete user's job record (find it via query)
    if email:
        response = dynamodb.query(
            TableName=DYNAMODB_TABLE,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            FilterExpression="job_id = :job_id",
            ExpressionAttributeValues={
                ":pk": {"S": f"USER#{email}"},
                ":sk_prefix": {"S": "JOB#"},
                ":job_id": {"S": str(job_id)},
            },
            Limit=1,
        )

        if response.get("Items"):
            user_job_item = response["Items"][0]
            dynamodb.delete_item(
                TableName=DYNAMODB_TABLE,
                Key={
                    "PK": user_job_item["PK"],
                    "SK": user_job_item["SK"],
                },
            )


# ==================== File Operations ====================


def create_file(
    job_id: UUID,
    file_id: UUID,
    filename: str,
    s3_key: str,
    status: str = "pending_upload",
) -> None:
    """Create a new file record for a job.

    Args:
        job_id: Job UUID this file belongs to
        file_id: Unique file UUID
        filename: Original filename
        s3_key: S3 key where audio is stored
        status: Initial status (default: "pending_upload")

    Raises:
        ClientError: If DynamoDB operation fails
    """
    now = _now_iso()
    item = {
        "PK": {"S": f"JOB#{job_id}"},
        "SK": {"S": f"FILE#{file_id}"},
        "file_id": {"S": str(file_id)},
        "filename": {"S": filename},
        "audio_s3_key": {"S": s3_key},
        "status": {"S": status},
        "created_at": {"S": now},
    }

    dynamodb.put_item(TableName=DYNAMODB_TABLE, Item=item)

    # Increment total_files count in job
    dynamodb.update_item(
        TableName=DYNAMODB_TABLE,
        Key={
            "PK": {"S": f"JOB#{job_id}"},
            "SK": {"S": "#METADATA"},
        },
        UpdateExpression="SET total_files = total_files + :inc, updated_at = :updated_at",
        ExpressionAttributeValues={
            ":inc": {"N": "1"},
            ":updated_at": {"S": now},
        },
    )


def list_files_for_job(job_id: UUID) -> list[dict]:
    """List all files for a job.

    Args:
        job_id: Job UUID

    Returns:
        List of file dicts with keys: file_id, filename, audio_s3_key,
        transcription_s3_key (optional), status, duration_seconds (optional),
        created_at
    """
    try:
        response = dynamodb.query(
            TableName=DYNAMODB_TABLE,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"JOB#{job_id}"},
                ":sk_prefix": {"S": "FILE#"},
            },
        )
        return [_item_to_dict(item) for item in response.get("Items", [])]
    except ClientError:
        return []


def update_file_status(
    file_id: UUID,
    job_id: UUID,
    status: str,
    transcription_s3_key: str | None = None,
    duration_seconds: float | None = None,
) -> None:
    """Update file status and transcription details.

    Args:
        file_id: File UUID
        job_id: Job UUID this file belongs to
        status: New status ("pending_upload" | "uploaded" | "queued" |
                "transcribing" | "completed" | "failed")
        transcription_s3_key: S3 key for transcription output (if completed)
        duration_seconds: Audio duration in seconds (if completed)

    Raises:
        ClientError: If DynamoDB operation fails
    """
    update_parts = ["#status = :status"]
    attr_names = {"#status": "status"}
    attr_values = {":status": {"S": status}}

    if transcription_s3_key is not None:
        update_parts.append("transcription_s3_key = :trans_key")
        attr_values[":trans_key"] = {"S": transcription_s3_key}

    if duration_seconds is not None:
        update_parts.append("duration_seconds = :duration")
        attr_values[":duration"] = {"N": str(duration_seconds)}

    update_expression = "SET " + ", ".join(update_parts)

    dynamodb.update_item(
        TableName=DYNAMODB_TABLE,
        Key={
            "PK": {"S": f"JOB#{job_id}"},
            "SK": {"S": f"FILE#{file_id}"},
        },
        UpdateExpression=update_expression,
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
    )
