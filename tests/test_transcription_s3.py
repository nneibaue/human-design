"""Tests for S3 helper functions using moto for mocking"""

import io
import os

import pytest
from moto import mock_aws

from src.transcription_service.s3 import (
    check_file_exists,
    delete_file,
    delete_files_with_prefix,
    download_file_from_s3,
    generate_presigned_download_url,
    generate_presigned_upload_url,
    get_input_bucket,
    get_output_bucket,
    upload_file_to_s3,
)


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for moto"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def s3_client(aws_credentials):
    """Create mock S3 client and buckets"""
    with mock_aws():
        import boto3

        # Create S3 client
        s3 = boto3.client("s3", region_name="us-east-1")

        # Create test buckets
        s3.create_bucket(Bucket="test-input-bucket")
        s3.create_bucket(Bucket="test-output-bucket")
        s3.create_bucket(Bucket="test-bucket")

        yield s3


@pytest.fixture
def env_vars():
    """Set environment variables for bucket names"""
    os.environ["S3_INPUT_BUCKET"] = "test-input-bucket"
    os.environ["S3_OUTPUT_BUCKET"] = "test-output-bucket"
    yield
    # Cleanup
    os.environ.pop("S3_INPUT_BUCKET", None)
    os.environ.pop("S3_OUTPUT_BUCKET", None)


def test_get_input_bucket_from_env(env_vars):
    """Test getting input bucket from environment variable"""
    assert get_input_bucket() == "test-input-bucket"


def test_get_output_bucket_from_env(env_vars):
    """Test getting output bucket from environment variable"""
    assert get_output_bucket() == "test-output-bucket"


def test_get_input_bucket_default():
    """Test input bucket falls back to default when env var not set"""
    os.environ.pop("S3_INPUT_BUCKET", None)
    assert get_input_bucket() == "transcription-input"


def test_get_output_bucket_default():
    """Test output bucket falls back to default when env var not set"""
    os.environ.pop("S3_OUTPUT_BUCKET", None)
    assert get_output_bucket() == "transcription-output"


def test_upload_file_to_s3(s3_client):
    """Test uploading file to S3 using streaming upload"""
    # Create test file content
    content = b"Test audio file content"
    file_obj = io.BytesIO(content)

    # Upload file
    upload_file_to_s3(file_obj, "test-bucket", "test/audio.mp3")

    # Verify upload
    response = s3_client.get_object(Bucket="test-bucket", Key="test/audio.mp3")
    uploaded_content = response["Body"].read()
    assert uploaded_content == content


def test_upload_file_to_s3_with_nested_path(s3_client):
    """Test uploading file with nested S3 path"""
    content = b"Nested file content"
    file_obj = io.BytesIO(content)

    upload_file_to_s3(file_obj, "test-bucket", "user/job123/file456/audio.mp3")

    response = s3_client.get_object(Bucket="test-bucket", Key="user/job123/file456/audio.mp3")
    assert response["Body"].read() == content


def test_download_file_from_s3(s3_client, tmp_path):
    """Test downloading file from S3 to local filesystem"""
    # Upload test file first
    content = b"Test transcription result"
    s3_client.put_object(Bucket="test-bucket", Key="results/transcript.json", Body=content)

    # Download file
    dest_path = tmp_path / "transcript.json"
    download_file_from_s3("test-bucket", "results/transcript.json", dest_path)

    # Verify download
    assert dest_path.exists()
    assert dest_path.read_bytes() == content


def test_download_file_from_s3_creates_parent_dirs(s3_client, tmp_path):
    """Test that download creates parent directories if they don't exist"""
    content = b"Test content"
    s3_client.put_object(Bucket="test-bucket", Key="data/file.txt", Body=content)

    # Download to nested path that doesn't exist
    dest_path = tmp_path / "nested" / "deep" / "file.txt"
    download_file_from_s3("test-bucket", "data/file.txt", dest_path)

    assert dest_path.exists()
    assert dest_path.read_bytes() == content


def test_download_file_from_s3_not_found(s3_client, tmp_path):
    """Test downloading non-existent file raises FileNotFoundError"""
    dest_path = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError, match="S3 object not found"):
        download_file_from_s3("test-bucket", "missing/file.txt", dest_path)


def test_generate_presigned_upload_url(s3_client):
    """Test generating presigned URL for upload"""
    url = generate_presigned_upload_url("test-bucket", "uploads/file.mp3")

    assert "test-bucket" in url
    assert "uploads/file.mp3" in url
    # Check for signature parameters (moto uses different format than real AWS)
    assert "Signature" in url or "X-Amz-Signature" in url
    assert "Expires" in url or "X-Amz-Expires" in url


def test_generate_presigned_upload_url_custom_expiration(s3_client):
    """Test presigned upload URL with custom expiration"""
    url = generate_presigned_upload_url("test-bucket", "uploads/file.mp3", expiration=300)

    assert "test-bucket" in url
    # Check for expiration parameter (moto format may differ)
    assert "Expires=" in url or "X-Amz-Expires=" in url


def test_generate_presigned_download_url(s3_client):
    """Test generating presigned URL for download"""
    # Upload file first
    s3_client.put_object(Bucket="test-bucket", Key="results/file.json", Body=b"test")

    url = generate_presigned_download_url("test-bucket", "results/file.json")

    assert "test-bucket" in url
    assert "results/file.json" in url
    # Check for signature parameters (moto uses different format than real AWS)
    assert "Signature" in url or "X-Amz-Signature" in url
    assert "Expires" in url or "X-Amz-Expires" in url


def test_generate_presigned_download_url_custom_expiration(s3_client):
    """Test presigned download URL with custom expiration"""
    s3_client.put_object(Bucket="test-bucket", Key="file.txt", Body=b"test")

    url = generate_presigned_download_url("test-bucket", "file.txt", expiration=7200)

    assert "test-bucket" in url
    # Check for expiration parameter (moto format may differ)
    assert "Expires=" in url or "X-Amz-Expires=" in url


def test_check_file_exists_true(s3_client):
    """Test checking if file exists returns True for existing file"""
    # Upload file
    s3_client.put_object(Bucket="test-bucket", Key="exists.txt", Body=b"content")

    assert check_file_exists("test-bucket", "exists.txt") is True


def test_check_file_exists_false(s3_client):
    """Test checking if file exists returns False for non-existent file"""
    assert check_file_exists("test-bucket", "does-not-exist.txt") is False


def test_check_file_exists_nested_path(s3_client):
    """Test checking file existence with nested path"""
    s3_client.put_object(Bucket="test-bucket", Key="user/job/file.mp3", Body=b"audio")

    assert check_file_exists("test-bucket", "user/job/file.mp3") is True
    assert check_file_exists("test-bucket", "user/job/other.mp3") is False


def test_delete_file(s3_client):
    """Test deleting file from S3"""
    # Upload file first
    s3_client.put_object(Bucket="test-bucket", Key="to-delete.txt", Body=b"temp")

    # Verify file exists
    assert check_file_exists("test-bucket", "to-delete.txt") is True

    # Delete file
    delete_file("test-bucket", "to-delete.txt")

    # Verify file no longer exists
    assert check_file_exists("test-bucket", "to-delete.txt") is False


def test_delete_files_with_prefix(s3_client):
    """Test batch deletion of files with prefix"""
    # Upload multiple files with same prefix
    s3_client.put_object(Bucket="test-bucket", Key="job123/file1.mp3", Body=b"audio1")
    s3_client.put_object(Bucket="test-bucket", Key="job123/file2.mp3", Body=b"audio2")
    s3_client.put_object(Bucket="test-bucket", Key="job123/results/transcript.json", Body=b"result")
    s3_client.put_object(Bucket="test-bucket", Key="job456/other.mp3", Body=b"other")

    # Verify files exist
    assert check_file_exists("test-bucket", "job123/file1.mp3") is True
    assert check_file_exists("test-bucket", "job123/file2.mp3") is True
    assert check_file_exists("test-bucket", "job123/results/transcript.json") is True
    assert check_file_exists("test-bucket", "job456/other.mp3") is True

    # Delete all files with job123 prefix
    delete_files_with_prefix("test-bucket", "job123/")

    # Verify job123 files are gone
    assert check_file_exists("test-bucket", "job123/file1.mp3") is False
    assert check_file_exists("test-bucket", "job123/file2.mp3") is False
    assert check_file_exists("test-bucket", "job123/results/transcript.json") is False

    # Verify job456 file still exists
    assert check_file_exists("test-bucket", "job456/other.mp3") is True


def test_delete_files_with_prefix_no_matches(s3_client):
    """Test deleting files with prefix that doesn't match any files"""
    # Upload files
    s3_client.put_object(Bucket="test-bucket", Key="job123/file.mp3", Body=b"audio")

    # Delete with non-matching prefix (should not raise error)
    delete_files_with_prefix("test-bucket", "job999/")

    # Verify original file still exists
    assert check_file_exists("test-bucket", "job123/file.mp3") is True


def test_delete_files_with_prefix_empty_bucket(s3_client):
    """Test deleting files with prefix from empty bucket"""
    # Should not raise error even if bucket is empty
    delete_files_with_prefix("test-bucket", "any-prefix/")


def test_upload_and_download_roundtrip(s3_client, tmp_path):
    """Test full upload-download roundtrip"""
    # Original content
    original_content = b"Full roundtrip test content with some data"

    # Upload
    file_obj = io.BytesIO(original_content)
    upload_file_to_s3(file_obj, "test-bucket", "roundtrip/test.bin")

    # Download
    dest_path = tmp_path / "downloaded.bin"
    download_file_from_s3("test-bucket", "roundtrip/test.bin", dest_path)

    # Verify content matches
    assert dest_path.read_bytes() == original_content


def test_presigned_url_includes_bucket_and_key(s3_client):
    """Test presigned URLs contain bucket and key information"""
    upload_url = generate_presigned_upload_url("test-bucket", "uploads/file.mp3")
    download_url = generate_presigned_download_url("test-bucket", "downloads/file.json")

    # Upload URL should contain bucket and key
    assert "test-bucket" in upload_url
    assert "uploads/file.mp3" in upload_url

    # Download URL should contain bucket and key
    assert "test-bucket" in download_url
    assert "downloads/file.json" in download_url


def test_large_file_upload(s3_client):
    """Test uploading larger file (simulating streaming behavior)"""
    # Create 1MB test file
    content = b"x" * (1024 * 1024)
    file_obj = io.BytesIO(content)

    upload_file_to_s3(file_obj, "test-bucket", "large/file.bin")

    # Verify upload
    response = s3_client.get_object(Bucket="test-bucket", Key="large/file.bin")
    uploaded_content = response["Body"].read()
    assert len(uploaded_content) == len(content)
    assert uploaded_content == content


def test_upload_with_special_characters_in_key(s3_client):
    """Test uploading file with special characters in key"""
    content = b"Special key test"
    file_obj = io.BytesIO(content)

    # Key with spaces, hyphens, underscores
    key = "user@example.com/job-123/my_file (1).mp3"
    upload_file_to_s3(file_obj, "test-bucket", key)

    # Verify upload
    response = s3_client.get_object(Bucket="test-bucket", Key=key)
    assert response["Body"].read() == content
