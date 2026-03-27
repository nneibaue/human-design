"""Tests for AWS Batch submission module"""

import os
from uuid import UUID, uuid4

import pytest
from moto import mock_aws

from src.transcription_service import batch


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for moto"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_REGION"] = "us-east-1"


@pytest.fixture
def batch_env_vars():
    """Set up required environment variables"""
    os.environ["BATCH_JOB_QUEUE"] = "test-queue"
    os.environ["BATCH_JOB_DEFINITION"] = "test-job-def"
    os.environ["DYNAMODB_TABLE"] = "test-table"
    yield
    # Cleanup
    for key in ["BATCH_JOB_QUEUE", "BATCH_JOB_DEFINITION", "DYNAMODB_TABLE"]:
        os.environ.pop(key, None)


@pytest.fixture
def batch_infrastructure(aws_credentials):
    """Create mock AWS Batch infrastructure"""
    with mock_aws():
        import boto3
        from botocore.exceptions import ClientError

        # Create EC2 resources (required for Batch compute environment)
        ec2 = boto3.resource("ec2", region_name="us-east-1")
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        subnet = vpc.create_subnet(CidrBlock="10.0.0.0/24")
        security_group = ec2.create_security_group(
            GroupName="test-sg", Description="Test SG", VpcId=vpc.id
        )

        # Create IAM role (required for Batch)
        iam = boto3.client("iam", region_name="us-east-1")
        iam.create_role(
            RoleName="test-batch-role",
            AssumeRolePolicyDocument='{"Version": "2012-10-17", "Statement": []}',
        )
        role_arn = iam.get_role(RoleName="test-batch-role")["Role"]["Arn"]

        # Create compute environment (UNMANAGED for simpler testing)
        batch_client = boto3.client("batch", region_name="us-east-1")
        batch_client.create_compute_environment(
            computeEnvironmentName="test-compute-env",
            type="UNMANAGED",
            serviceRole=role_arn,
        )

        # Create job queue
        batch_client.create_job_queue(
            jobQueueName="test-queue",
            state="ENABLED",
            priority=1,
            computeEnvironmentOrder=[
                {"order": 1, "computeEnvironment": "test-compute-env"}
            ],
        )

        # Create job definition
        batch_client.register_job_definition(
            jobDefinitionName="test-job-def",
            type="container",
            containerProperties={
                "image": "test-image:latest",
                "vcpus": 2,
                "memory": 2048,
            },
        )

        yield batch_client


def test_get_job_queue(batch_env_vars):
    """Test getting job queue from environment"""
    assert batch.get_job_queue() == "test-queue"


def test_get_job_definition(batch_env_vars):
    """Test getting job definition from environment"""
    assert batch.get_job_definition() == "test-job-def"


def test_get_dynamodb_table(batch_env_vars):
    """Test getting DynamoDB table from environment"""
    assert batch.get_dynamodb_table() == "test-table"


def test_submit_transcription_job_success(batch_infrastructure, batch_env_vars):
    """Test successful job submission"""
    job_id = uuid4()
    file_id = uuid4()
    input_uri = "s3://input-bucket/audio.mp3"
    output_uri = "s3://output-bucket/results"

    # Submit job
    batch_job_id = batch.submit_transcription_job(
        job_id=job_id,
        file_id=file_id,
        input_s3_uri=input_uri,
        output_s3_uri=output_uri,
        model_name="large-v3",
    )

    # Verify job was created
    assert batch_job_id is not None
    assert isinstance(batch_job_id, str)
    assert len(batch_job_id) > 0

    # Verify job details
    response = batch_infrastructure.describe_jobs(jobs=[batch_job_id])
    assert len(response["jobs"]) == 1

    job = response["jobs"][0]
    assert job["jobName"] == f"transcribe-{file_id}"
    assert "test-queue" in job["jobQueue"]  # May be ARN or name
    assert "test-job-def" in job["jobDefinition"]  # May include revision

    # Verify command
    container = job["container"]
    expected_command = [
        "python",
        "/workspace/parallel_transcribe.py",
        input_uri,
        output_uri,
        str(job_id),
        str(file_id),
        "large-v3",
    ]
    assert container["command"] == expected_command

    # Verify environment variables
    env_dict = {e["name"]: e["value"] for e in container["environment"]}
    assert env_dict["JOB_ID"] == str(job_id)
    assert env_dict["FILE_ID"] == str(file_id)
    assert env_dict["DYNAMODB_TABLE"] == "test-table"


def test_submit_transcription_job_custom_model(batch_infrastructure, batch_env_vars):
    """Test job submission with custom model"""
    job_id = uuid4()
    file_id = uuid4()

    batch_job_id = batch.submit_transcription_job(
        job_id=job_id,
        file_id=file_id,
        input_s3_uri="s3://input/file.mp3",
        output_s3_uri="s3://output",
        model_name="base",
    )

    # Verify model parameter
    response = batch_infrastructure.describe_jobs(jobs=[batch_job_id])
    job = response["jobs"][0]
    command = job["container"]["command"]
    assert command[-1] == "base"  # Last arg is model


def test_submit_transcription_job_missing_env_var():
    """Test job submission fails with missing environment variable"""
    job_id = uuid4()
    file_id = uuid4()

    with pytest.raises(KeyError):
        batch.submit_transcription_job(
            job_id=job_id,
            file_id=file_id,
            input_s3_uri="s3://input/file.mp3",
            output_s3_uri="s3://output",
        )


def test_get_job_status_success(batch_infrastructure, batch_env_vars):
    """Test getting job status"""
    job_id = uuid4()
    file_id = uuid4()

    # Submit a job first
    batch_job_id = batch.submit_transcription_job(
        job_id=job_id,
        file_id=file_id,
        input_s3_uri="s3://input/file.mp3",
        output_s3_uri="s3://output",
    )

    # Get job status
    status = batch.get_job_status(batch_job_id)

    # Verify status fields
    assert status["jobId"] == batch_job_id
    assert status["jobName"] == f"transcribe-{file_id}"
    assert status["status"] in [
        "SUBMITTED",
        "PENDING",
        "RUNNABLE",
        "STARTING",
        "RUNNING",
        "SUCCEEDED",
        "FAILED",
    ]
    assert "createdAt" in status


def test_get_job_status_not_found(batch_infrastructure, batch_env_vars):
    """Test getting status of non-existent job"""
    with pytest.raises(ValueError, match="Batch job not found"):
        batch.get_job_status("nonexistent-job-id")


def test_submit_multiple_jobs(batch_infrastructure, batch_env_vars):
    """Test submitting multiple jobs for same parent job"""
    job_id = uuid4()
    file_ids = [uuid4() for _ in range(3)]

    batch_job_ids = []
    for file_id in file_ids:
        batch_job_id = batch.submit_transcription_job(
            job_id=job_id,
            file_id=file_id,
            input_s3_uri=f"s3://input/{file_id}.mp3",
            output_s3_uri="s3://output",
        )
        batch_job_ids.append(batch_job_id)

    # Verify all jobs were created with unique IDs
    assert len(batch_job_ids) == 3
    assert len(set(batch_job_ids)) == 3  # All unique

    # Verify all jobs exist
    for batch_job_id in batch_job_ids:
        status = batch.get_job_status(batch_job_id)
        assert status["jobId"] == batch_job_id


def test_uuid_to_string_conversion(batch_infrastructure, batch_env_vars):
    """Test that UUIDs are properly converted to strings"""
    job_id = UUID("12345678-1234-5678-1234-567812345678")
    file_id = UUID("87654321-4321-8765-4321-876543218765")

    batch_job_id = batch.submit_transcription_job(
        job_id=job_id,
        file_id=file_id,
        input_s3_uri="s3://input/file.mp3",
        output_s3_uri="s3://output",
    )

    # Verify UUIDs were converted to strings in command
    response = batch_infrastructure.describe_jobs(jobs=[batch_job_id])
    job = response["jobs"][0]
    command = job["container"]["command"]

    assert command[3] == "s3://output"
    assert command[4] == "12345678-1234-5678-1234-567812345678"
    assert command[5] == "87654321-4321-8765-4321-876543218765"

    # Verify environment variables
    env_dict = {e["name"]: e["value"] for e in job["container"]["environment"]}
    assert env_dict["JOB_ID"] == "12345678-1234-5678-1234-567812345678"
    assert env_dict["FILE_ID"] == "87654321-4321-8765-4321-876543218765"


def test_s3_uri_formats(batch_infrastructure, batch_env_vars):
    """Test various S3 URI formats are handled correctly"""
    job_id = uuid4()
    file_id = uuid4()

    test_cases = [
        ("s3://bucket/key", "s3://bucket/output"),
        ("s3://bucket/path/to/file.mp3", "s3://bucket/path/to/output"),
        ("s3://my-bucket-123/user@example.com/file.mp3", "s3://my-bucket-123/output"),
    ]

    for input_uri, output_uri in test_cases:
        batch_job_id = batch.submit_transcription_job(
            job_id=job_id,
            file_id=file_id,
            input_s3_uri=input_uri,
            output_s3_uri=output_uri,
        )

        response = batch_infrastructure.describe_jobs(jobs=[batch_job_id])
        command = response["jobs"][0]["container"]["command"]

        assert command[2] == input_uri
        assert command[3] == output_uri
