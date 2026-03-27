"""S3 helper functions for file operations"""

import os
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError


def _get_s3_client():
    """Get S3 client (lazy initialization for testability)"""
    return boto3.client("s3")


def get_input_bucket() -> str:
    """Get input S3 bucket name from environment

    Returns:
        Bucket name for audio file uploads

    Raises:
        KeyError: If INPUT_BUCKET environment variable not set
    """
    return os.environ.get("S3_INPUT_BUCKET", "transcription-input")


def get_output_bucket() -> str:
    """Get output S3 bucket name from environment

    Returns:
        Bucket name for transcription results

    Raises:
        KeyError: If OUTPUT_BUCKET environment variable not set
    """
    return os.environ.get("S3_OUTPUT_BUCKET", "transcription-output")


def upload_file_to_s3(file_obj: BinaryIO, bucket: str, key: str) -> None:
    """Upload file to S3 using streaming upload for memory efficiency

    Args:
        file_obj: File-like object to upload (must be opened in binary mode)
        bucket: S3 bucket name
        key: S3 object key (path within bucket)

    Raises:
        ClientError: If S3 upload fails

    Example:
        >>> with open("audio.mp3", "rb") as f:
        ...     upload_file_to_s3(f, "my-bucket", "user/job123/audio.mp3")
    """
    try:
        s3 = _get_s3_client()
        s3.upload_fileobj(file_obj, bucket, key)
    except ClientError as e:
        raise RuntimeError(f"Failed to upload file to S3: {e}") from e


def download_file_from_s3(bucket: str, key: str, dest_path: Path) -> None:
    """Download file from S3 to local filesystem

    Args:
        bucket: S3 bucket name
        key: S3 object key to download
        dest_path: Local filesystem path to save file

    Raises:
        ClientError: If S3 download fails
        FileNotFoundError: If S3 object does not exist

    Example:
        >>> download_file_from_s3("my-bucket", "results/transcript.json", Path("/tmp/output.json"))
    """
    try:
        # Ensure parent directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Download file
        s3 = _get_s3_client()
        s3.download_file(bucket, key, str(dest_path))
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in ("404", "NoSuchKey"):
            raise FileNotFoundError(f"S3 object not found: s3://{bucket}/{key}") from e
        raise RuntimeError(f"Failed to download file from S3: {e}") from e


def generate_presigned_upload_url(bucket: str, key: str, expiration: int = 900) -> str:
    """Generate pre-signed URL for uploading to S3 (PUT operation)

    Pre-signed URLs allow clients to upload directly to S3 without AWS credentials.
    Default expiration is 15 minutes (900 seconds).

    Args:
        bucket: S3 bucket name
        key: S3 object key for the upload
        expiration: URL expiration time in seconds (default: 900 = 15 minutes)

    Returns:
        Pre-signed URL for PUT operation

    Raises:
        ClientError: If URL generation fails

    Example:
        >>> url = generate_presigned_upload_url("my-bucket", "uploads/file.mp3")
        >>> # Client can now PUT to this URL: requests.put(url, data=file_data)
    """
    try:
        s3 = _get_s3_client()
        url = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiration,
        )
        return url
    except ClientError as e:
        raise RuntimeError(f"Failed to generate presigned upload URL: {e}") from e


def generate_presigned_download_url(bucket: str, key: str, expiration: int = 3600) -> str:
    """Generate pre-signed URL for downloading from S3 (GET operation)

    Pre-signed URLs allow clients to download directly from S3 without AWS credentials.
    Default expiration is 1 hour (3600 seconds).

    Args:
        bucket: S3 bucket name
        key: S3 object key to download
        expiration: URL expiration time in seconds (default: 3600 = 1 hour)

    Returns:
        Pre-signed URL for GET operation

    Raises:
        ClientError: If URL generation fails

    Example:
        >>> url = generate_presigned_download_url("my-bucket", "results/transcript.json")
        >>> # Client can now GET from this URL: requests.get(url)
    """
    try:
        s3 = _get_s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiration,
        )
        return url
    except ClientError as e:
        raise RuntimeError(f"Failed to generate presigned download URL: {e}") from e


def check_file_exists(bucket: str, key: str) -> bool:
    """Check if file exists in S3 using HEAD request

    This is efficient as it only fetches metadata, not the file contents.

    Args:
        bucket: S3 bucket name
        key: S3 object key to check

    Returns:
        True if file exists, False otherwise

    Example:
        >>> if check_file_exists("my-bucket", "audio/file.mp3"):
        ...     print("File exists!")
    """
    try:
        s3 = _get_s3_client()
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in ("404", "NoSuchKey"):
            return False
        # For other errors (permissions, network), still return False
        # but we could also raise in production
        return False


def delete_file(bucket: str, key: str) -> None:
    """Delete file from S3

    Args:
        bucket: S3 bucket name
        key: S3 object key to delete

    Raises:
        ClientError: If S3 deletion fails

    Example:
        >>> delete_file("my-bucket", "temp/old-file.mp3")
    """
    try:
        s3 = _get_s3_client()
        s3.delete_object(Bucket=bucket, Key=key)
    except ClientError as e:
        raise RuntimeError(f"Failed to delete file from S3: {e}") from e


def delete_files_with_prefix(bucket: str, prefix: str) -> None:
    """Delete all files in S3 with given prefix (batch deletion)

    This is useful for cleaning up all files in a job directory.

    Args:
        bucket: S3 bucket name
        prefix: S3 key prefix (e.g., "user@example.com/job-123/")

    Raises:
        ClientError: If S3 operations fail

    Example:
        >>> delete_files_with_prefix("my-bucket", "user@example.com/job-123/")
    """
    try:
        s3 = _get_s3_client()
        # List all objects with prefix
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        objects = response.get("Contents", [])

        if not objects:
            return

        # Batch delete (max 1000 objects per request)
        delete_keys = [{"Key": obj["Key"]} for obj in objects]
        s3.delete_objects(
            Bucket=bucket,
            Delete={"Objects": delete_keys},
        )
    except ClientError as e:
        raise RuntimeError(f"Failed to delete files with prefix from S3: {e}") from e
