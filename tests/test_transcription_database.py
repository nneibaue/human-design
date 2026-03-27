"""Tests for transcription service DynamoDB operations."""

import os
from uuid import UUID, uuid4

import boto3
import pytest
from moto import mock_aws

from transcription_service import database


@pytest.fixture
def dynamodb_table():
    """Create a mock DynamoDB table for testing."""
    with mock_aws():
        # Override environment variables
        os.environ["DYNAMODB_TABLE"] = "test-transcription-service"
        os.environ["AWS_REGION"] = "us-east-1"

        # Create DynamoDB table
        dynamodb_client = boto3.client("dynamodb", region_name="us-east-1")
        dynamodb_client.create_table(
            TableName="test-transcription-service",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "job_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "job_id-index",
                    "KeySchema": [{"AttributeName": "job_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Reinitialize database module's client
        database.dynamodb = dynamodb_client
        database.DYNAMODB_TABLE = "test-transcription-service"

        yield dynamodb_client


# ==================== User Operations Tests ====================


def test_create_user(dynamodb_table):
    """Test creating a new user."""
    email = "test@example.com"
    password_hash = "hashed_password_123"
    display_name = "Test User"

    database.create_user(email, password_hash, display_name)

    # Verify user was created
    user = database.get_user_by_email(email)
    assert user is not None
    assert user["email"] == email
    assert user["password_hash"] == password_hash
    assert user["display_name"] == display_name
    assert "created_at" in user


def test_create_user_without_display_name(dynamodb_table):
    """Test creating a user without display name."""
    email = "test2@example.com"
    password_hash = "hashed_password_456"

    database.create_user(email, password_hash)

    user = database.get_user_by_email(email)
    assert user is not None
    assert user["email"] == email
    assert user["password_hash"] == password_hash
    assert "display_name" not in user


def test_create_user_duplicate_email(dynamodb_table):
    """Test that creating duplicate user raises error."""
    email = "duplicate@example.com"
    password_hash = "password"

    database.create_user(email, password_hash)

    with pytest.raises(ValueError, match="already exists"):
        database.create_user(email, "different_hash")


def test_get_user_by_email_not_found(dynamodb_table):
    """Test getting non-existent user returns None."""
    user = database.get_user_by_email("nonexistent@example.com")
    assert user is None


# ==================== Job Operations Tests ====================


def test_create_job(dynamodb_table):
    """Test creating a new job."""
    email = "user@example.com"
    database.create_user(email, "hash")

    job_id = database.create_job(email, "upload")

    assert isinstance(job_id, UUID)

    # Verify job was created
    job = database.get_job(job_id)
    assert job is not None
    assert job["job_id"] == str(job_id)
    assert job["email"] == email
    assert job["status"] == "queued"
    assert job["job_type"] == "upload"
    assert job["total_files"] == 0
    assert job["completed_files"] == 0
    assert job["failed_files"] == 0
    assert "created_at" in job
    assert "updated_at" in job


def test_get_job_not_found(dynamodb_table):
    """Test getting non-existent job returns None."""
    job = database.get_job(uuid4())
    assert job is None


def test_list_jobs_for_user(dynamodb_table):
    """Test listing jobs for a user."""
    email = "user@example.com"
    database.create_user(email, "hash")

    # Create multiple jobs
    job_id1 = database.create_job(email, "upload")
    job_id2 = database.create_job(email, "youtube")
    job_id3 = database.create_job(email, "upload")

    jobs = database.list_jobs_for_user(email)

    assert len(jobs) == 3
    # Should be ordered newest first
    assert jobs[0]["job_id"] == str(job_id3)
    assert jobs[1]["job_id"] == str(job_id2)
    assert jobs[2]["job_id"] == str(job_id1)


def test_list_jobs_for_user_with_pagination(dynamodb_table):
    """Test listing jobs with limit and offset."""
    email = "user@example.com"
    database.create_user(email, "hash")

    # Create 5 jobs
    job_ids = [database.create_job(email, "upload") for _ in range(5)]

    # Get first 2 jobs
    jobs = database.list_jobs_for_user(email, limit=2, offset=0)
    assert len(jobs) == 2
    assert jobs[0]["job_id"] == str(job_ids[4])  # Newest first
    assert jobs[1]["job_id"] == str(job_ids[3])

    # Get next 2 jobs
    jobs = database.list_jobs_for_user(email, limit=2, offset=2)
    assert len(jobs) == 2
    assert jobs[0]["job_id"] == str(job_ids[2])
    assert jobs[1]["job_id"] == str(job_ids[1])


def test_list_jobs_for_user_empty(dynamodb_table):
    """Test listing jobs for user with no jobs."""
    email = "user@example.com"
    database.create_user(email, "hash")

    jobs = database.list_jobs_for_user(email)
    assert jobs == []


def test_update_job_status(dynamodb_table):
    """Test updating job status."""
    email = "user@example.com"
    database.create_user(email, "hash")
    job_id = database.create_job(email, "upload")

    database.update_job_status(job_id, "running", completed_files=2, failed_files=1)

    job = database.get_job(job_id)
    assert job["status"] == "running"
    assert job["completed_files"] == 2
    assert job["failed_files"] == 1


def test_update_job_status_partial(dynamodb_table):
    """Test updating only status without file counts."""
    email = "user@example.com"
    database.create_user(email, "hash")
    job_id = database.create_job(email, "upload")

    database.update_job_status(job_id, "completed")

    job = database.get_job(job_id)
    assert job["status"] == "completed"
    assert job["completed_files"] == 0  # Should remain unchanged
    assert job["failed_files"] == 0


def test_delete_job(dynamodb_table):
    """Test deleting a job and its files."""
    email = "user@example.com"
    database.create_user(email, "hash")
    job_id = database.create_job(email, "upload")

    # Add some files
    file_id1 = uuid4()
    file_id2 = uuid4()
    database.create_file(job_id, file_id1, "file1.mp3", "s3://bucket/file1.mp3")
    database.create_file(job_id, file_id2, "file2.mp3", "s3://bucket/file2.mp3")

    # Delete job
    database.delete_job(job_id)

    # Verify job is deleted
    assert database.get_job(job_id) is None
    assert database.list_files_for_job(job_id) == []
    assert database.list_jobs_for_user(email) == []


def test_delete_job_not_found(dynamodb_table):
    """Test deleting non-existent job doesn't raise error."""
    database.delete_job(uuid4())  # Should not raise


# ==================== File Operations Tests ====================


def test_create_file(dynamodb_table):
    """Test creating a new file."""
    email = "user@example.com"
    database.create_user(email, "hash")
    job_id = database.create_job(email, "upload")

    file_id = uuid4()
    filename = "test.mp3"
    s3_key = "user@example.com/job123/file123/test.mp3"

    database.create_file(job_id, file_id, filename, s3_key, status="uploaded")

    # Verify file was created
    files = database.list_files_for_job(job_id)
    assert len(files) == 1
    assert files[0]["file_id"] == str(file_id)
    assert files[0]["filename"] == filename
    assert files[0]["audio_s3_key"] == s3_key
    assert files[0]["status"] == "uploaded"
    assert "created_at" in files[0]

    # Verify total_files was incremented
    job = database.get_job(job_id)
    assert job["total_files"] == 1


def test_create_file_default_status(dynamodb_table):
    """Test creating file with default status."""
    email = "user@example.com"
    database.create_user(email, "hash")
    job_id = database.create_job(email, "upload")

    file_id = uuid4()
    database.create_file(job_id, file_id, "test.mp3", "s3://key")

    files = database.list_files_for_job(job_id)
    assert files[0]["status"] == "pending_upload"


def test_list_files_for_job_empty(dynamodb_table):
    """Test listing files for job with no files."""
    email = "user@example.com"
    database.create_user(email, "hash")
    job_id = database.create_job(email, "upload")

    files = database.list_files_for_job(job_id)
    assert files == []


def test_list_files_for_job_multiple(dynamodb_table):
    """Test listing multiple files for a job."""
    email = "user@example.com"
    database.create_user(email, "hash")
    job_id = database.create_job(email, "upload")

    file_id1 = uuid4()
    file_id2 = uuid4()
    file_id3 = uuid4()

    database.create_file(job_id, file_id1, "file1.mp3", "s3://key1")
    database.create_file(job_id, file_id2, "file2.mp3", "s3://key2")
    database.create_file(job_id, file_id3, "file3.mp3", "s3://key3")

    files = database.list_files_for_job(job_id)
    assert len(files) == 3

    file_ids = {f["file_id"] for f in files}
    assert file_ids == {str(file_id1), str(file_id2), str(file_id3)}


def test_update_file_status(dynamodb_table):
    """Test updating file status."""
    email = "user@example.com"
    database.create_user(email, "hash")
    job_id = database.create_job(email, "upload")

    file_id = uuid4()
    database.create_file(job_id, file_id, "test.mp3", "s3://input/key")

    # Update to completed with transcription
    trans_key = "s3://output/trans.json"
    duration = 123.45
    database.update_file_status(
        file_id, job_id, "completed", transcription_s3_key=trans_key, duration_seconds=duration
    )

    files = database.list_files_for_job(job_id)
    assert files[0]["status"] == "completed"
    assert files[0]["transcription_s3_key"] == trans_key
    assert files[0]["duration_seconds"] == duration


def test_update_file_status_partial(dynamodb_table):
    """Test updating only file status without optional fields."""
    email = "user@example.com"
    database.create_user(email, "hash")
    job_id = database.create_job(email, "upload")

    file_id = uuid4()
    database.create_file(job_id, file_id, "test.mp3", "s3://input/key")

    database.update_file_status(file_id, job_id, "transcribing")

    files = database.list_files_for_job(job_id)
    assert files[0]["status"] == "transcribing"
    assert "transcription_s3_key" not in files[0]
    assert "duration_seconds" not in files[0]


def test_update_file_status_failed(dynamodb_table):
    """Test updating file to failed status."""
    email = "user@example.com"
    database.create_user(email, "hash")
    job_id = database.create_job(email, "upload")

    file_id = uuid4()
    database.create_file(job_id, file_id, "test.mp3", "s3://input/key")

    database.update_file_status(file_id, job_id, "failed")

    files = database.list_files_for_job(job_id)
    assert files[0]["status"] == "failed"


# ==================== Integration Tests ====================


def test_complete_workflow(dynamodb_table):
    """Test complete workflow: create user, job, files, update status."""
    # Create user
    email = "workflow@example.com"
    database.create_user(email, "password_hash", "Workflow User")

    # Create job
    job_id = database.create_job(email, "upload")

    # Add files
    file1_id = uuid4()
    file2_id = uuid4()
    database.create_file(job_id, file1_id, "audio1.mp3", "s3://input/audio1.mp3", "uploaded")
    database.create_file(job_id, file2_id, "audio2.mp3", "s3://input/audio2.mp3", "uploaded")

    # Verify job has 2 files
    job = database.get_job(job_id)
    assert job["total_files"] == 2
    assert job["completed_files"] == 0

    # Update file 1 to completed
    database.update_file_status(
        file1_id,
        job_id,
        "completed",
        transcription_s3_key="s3://output/trans1.json",
        duration_seconds=60.5,
    )

    # Update job status
    database.update_job_status(job_id, "running", completed_files=1)

    # Verify updates
    job = database.get_job(job_id)
    assert job["status"] == "running"
    assert job["completed_files"] == 1

    files = database.list_files_for_job(job_id)
    completed = [f for f in files if f["status"] == "completed"]
    assert len(completed) == 1
    assert completed[0]["file_id"] == str(file1_id)

    # Complete second file
    database.update_file_status(
        file2_id,
        job_id,
        "completed",
        transcription_s3_key="s3://output/trans2.json",
        duration_seconds=45.2,
    )

    database.update_job_status(job_id, "completed", completed_files=2)

    # Verify final state
    job = database.get_job(job_id)
    assert job["status"] == "completed"
    assert job["completed_files"] == 2
    assert job["failed_files"] == 0

    files = database.list_files_for_job(job_id)
    assert all(f["status"] == "completed" for f in files)


def test_user_isolation(dynamodb_table):
    """Test that users only see their own jobs."""
    # Create two users
    user1 = "user1@example.com"
    user2 = "user2@example.com"
    database.create_user(user1, "hash1")
    database.create_user(user2, "hash2")

    # Create jobs for each user
    job1_id = database.create_job(user1, "upload")
    job2_id = database.create_job(user2, "youtube")

    # Verify user1 only sees their job
    user1_jobs = database.list_jobs_for_user(user1)
    assert len(user1_jobs) == 1
    assert user1_jobs[0]["job_id"] == str(job1_id)

    # Verify user2 only sees their job
    user2_jobs = database.list_jobs_for_user(user2)
    assert len(user2_jobs) == 1
    assert user2_jobs[0]["job_id"] == str(job2_id)
