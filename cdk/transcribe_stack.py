"""CDK stack for Ra transcription AWS Batch infrastructure."""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    Size,
    Fn,
    aws_s3 as s3,
    aws_ecr as ecr,
    aws_batch as batch,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class TranscribeStack(Stack):
    """AWS Batch infrastructure for parallel audio transcription."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket for input audio files (temporary storage)
        input_bucket = s3.Bucket(
            self,
            "InputBucket",
            bucket_name="hd-transcribe-input",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteAfter7Days",
                    enabled=True,
                    expiration=Duration.days(7),
                )
            ],
        )

        # S3 bucket for output transcriptions (permanent storage)
        output_bucket = s3.Bucket(
            self,
            "OutputBucket",
            bucket_name="hd-transcribe-output",
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True,
        )

        # ECR repository for Docker image
        ecr_repo = ecr.Repository(
            self,
            "TranscribeRepo",
            repository_name="ra-transcribe",
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True,
            image_scan_on_push=True,
        )

        # IAM role for ECS task execution (pull image, write logs)
        execution_role = iam.Role(
            self,
            "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )

        # IAM role for Batch job (S3 access)
        job_role = iam.Role(
            self,
            "JobRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        # Grant S3 permissions to job role
        input_bucket.grant_read(job_role)
        output_bucket.grant_read_write(job_role)

        # Import shared secrets (cross-stack reference)
        secret_arn = Fn.import_value("hd-secret-arn")
        secret = secretsmanager.Secret.from_secret_complete_arn(
            self, "ImportedSecret", secret_arn
        )

        # Grant Batch job access to secrets
        secret.grant_read(job_role)

        # Use default VPC (simpler than creating new one)
        vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)

        # Batch compute environment (On-Demand for reliability)
        compute_environment = batch.ManagedEc2EcsComputeEnvironment(
            self,
            "ComputeEnvironment",
            compute_environment_name="transcribe-compute",
            vpc=vpc,
            spot=False,  # Use on-demand instances
            instance_types=[
                ec2.InstanceType("m5.large"),  # 2 vCPU, 8 GB RAM, ~$0.096/hour on-demand
                ec2.InstanceType("m5.xlarge"),  # 4 vCPU, 16 GB RAM, ~$0.192/hour on-demand
            ],
            minv_cpus=2,  # Keep 1 m5.large running (min 2 vCPUs) to avoid startup delays
            maxv_cpus=32,  # Max 16 m5.large or 8 m5.xlarge
            enabled=True,
        )

        # Batch job queue
        job_queue = batch.JobQueue(
            self,
            "JobQueue",
            job_queue_name="transcribe-queue",
            priority=1,
            compute_environments=[
                batch.OrderedComputeEnvironment(
                    compute_environment=compute_environment,
                    order=1,
                )
            ],
        )

        # Batch job definition
        job_definition = batch.EcsJobDefinition(
            self,
            "JobDefinition",
            job_definition_name="transcribe-job",
            container=batch.EcsEc2ContainerDefinition(
                self,
                "Container",
                image=ecs.ContainerImage.from_ecr_repository(ecr_repo, "latest"),
                cpu=2,
                memory=Size.mebibytes(4096),  # 4 GB
                job_role=job_role,
                execution_role=execution_role,
                logging=ecs.LogDriver.aws_logs(stream_prefix="transcribe"),
                environment={
                    "SECRET_NAME": "hd-api-credentials",
                },
                # Command will be overridden per job
                command=[
                    "python",
                    "/workspace/parallel_transcribe.py",
                ],
            ),
            retry_attempts=2,
            timeout=Duration.hours(4),  # Max 4 hours per job
        )

        # Stack outputs
        self.add_outputs(
            input_bucket=input_bucket.bucket_name,
            output_bucket=output_bucket.bucket_name,
            ecr_repo=ecr_repo.repository_uri,
            job_queue=job_queue.job_queue_name,
            job_definition=job_definition.job_definition_name,
        )

    def add_outputs(self, **kwargs):
        """Add CloudFormation outputs for easy reference."""
        from aws_cdk import CfnOutput

        for key, value in kwargs.items():
            # Replace underscores with hyphens for CloudFormation export names
            export_name = key.replace("_", "-")
            CfnOutput(self, f"{key}Output", value=value, export_name=export_name)
