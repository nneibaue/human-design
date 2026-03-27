"""CDK stack for Transcription Service API (Lambda + API Gateway + DynamoDB)."""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    Fn,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    aws_ecr as ecr,
    aws_s3 as s3,
    CfnOutput,
)
from constructs import Construct


class TranscriptionApiStack(Stack):
    """FastAPI Lambda + API Gateway HTTP API for transcription service.

    This stack creates:
    - DynamoDB table for user accounts and job tracking
    - JWT secret in Secrets Manager
    - Lambda function running FastAPI with Mangum handler
    - API Gateway HTTP API with Lambda proxy integration
    - IAM permissions for S3, DynamoDB, Batch, and Secrets Manager

    Cross-stack dependencies:
    - Imports S3 bucket names from TranscribeStack
    - Imports Batch job definition and queue from TranscribeStack
    - Imports HD credentials secret from HumanDesignStack
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ===================================================================
        # 1. DynamoDB Table
        # ===================================================================

        table = dynamodb.Table(
            self,
            "TranscriptionTable",
            table_name="transcription-service",
            partition_key=dynamodb.Attribute(
                name="PK",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="SK",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            # Enable encryption at rest (default is AWS owned key, free)
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

        # ===================================================================
        # 2. JWT Secret (Secrets Manager)
        # ===================================================================

        jwt_secret = secretsmanager.Secret(
            self,
            "JwtSecret",
            secret_name="transcription-service/jwt-secret",
            description="JWT signing secret for transcription service API",
            # Auto-generate a 64-character random secret
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template="{}",
                generate_string_key="secret",
                password_length=64,
                exclude_characters='"\\',  # Avoid JSON escaping issues
            ),
        )

        # ===================================================================
        # 3. Import Cross-Stack Resources
        # ===================================================================

        # Import S3 buckets from TranscribeStack
        input_bucket_name = Fn.import_value("input-bucket")
        output_bucket_name = Fn.import_value("output-bucket")

        input_bucket = s3.Bucket.from_bucket_name(
            self, "InputBucket", input_bucket_name
        )
        output_bucket = s3.Bucket.from_bucket_name(
            self, "OutputBucket", output_bucket_name
        )

        # Import Batch resources from TranscribeStack
        job_queue_name = Fn.import_value("job-queue")
        job_definition_name = Fn.import_value("job-definition")

        # Import HD credentials secret from HumanDesignStack
        hd_secret_arn = Fn.import_value("hd-secret-arn")
        hd_secret = secretsmanager.Secret.from_secret_complete_arn(
            self, "HdSecret", hd_secret_arn
        )

        # Import ECR repo for Lambda container image
        ecr_repo_uri = Fn.import_value("ecr-repo")
        # Extract repo name from URI (format: account.dkr.ecr.region.amazonaws.com/repo-name)
        ecr_repo = ecr.Repository.from_repository_name(
            self, "EcrRepo", "ra-transcribe"
        )

        # ===================================================================
        # 4. Lambda IAM Role
        # ===================================================================

        lambda_role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Execution role for transcription API Lambda",
        )

        # CloudWatch Logs permissions (basic Lambda logging)
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        # DynamoDB permissions (full access to our table)
        table.grant_read_write_data(lambda_role)

        # S3 permissions (read/write to both buckets)
        input_bucket.grant_read_write(lambda_role)
        output_bucket.grant_read_write(lambda_role)

        # Secrets Manager permissions (read JWT secret and HD credentials)
        jwt_secret.grant_read(lambda_role)
        hd_secret.grant_read(lambda_role)

        # AWS Batch permissions (submit jobs)
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "batch:SubmitJob",
                    "batch:DescribeJobs",
                    "batch:ListJobs",
                    "batch:TerminateJob",
                ],
                resources=[
                    f"arn:aws:batch:{self.region}:{self.account}:job-queue/{job_queue_name}",
                    f"arn:aws:batch:{self.region}:{self.account}:job-definition/{job_definition_name}:*",
                    f"arn:aws:batch:{self.region}:{self.account}:job/*",
                ],
            )
        )

        # ===================================================================
        # 5. Lambda Function (Docker Image from ECR)
        # ===================================================================

        # Note: We use the same ECR repo as the Batch job (ra-transcribe)
        # but could create a separate transcription-api repo if images diverge

        lambda_function = lambda_.DockerImageFunction(
            self,
            "ApiFunction",
            function_name="transcription-api",
            code=lambda_.DockerImageCode.from_ecr(
                repository=ecr_repo,
                tag_or_digest="latest",
            ),
            memory_size=1024,  # 1 GB RAM
            timeout=Duration.seconds(30),  # API Gateway max
            role=lambda_role,
            description="FastAPI transcription service with Mangum handler",
            environment={
                "DYNAMODB_TABLE": table.table_name,
                "S3_INPUT_BUCKET": input_bucket_name,
                "S3_OUTPUT_BUCKET": output_bucket_name,
                "JWT_SECRET_NAME": jwt_secret.secret_name,
                "HD_SECRET_NAME": "hd-api-credentials",
                "BATCH_JOB_DEFINITION": job_definition_name,
                "BATCH_JOB_QUEUE": job_queue_name,
                "AWS_REGION": self.region,
                # FastAPI/Mangum configuration
                "STAGE": "prod",
            },
        )

        # ===================================================================
        # 6. API Gateway HTTP API
        # ===================================================================

        # Create Lambda integration
        lambda_integration = integrations.HttpLambdaIntegration(
            "LambdaIntegration",
            handler=lambda_function,
            payload_format_version=apigwv2.PayloadFormatVersion.VERSION_2_0,
        )

        # Create HTTP API
        http_api = apigwv2.HttpApi(
            self,
            "HttpApi",
            api_name="TranscriptionServiceAPI",
            description="HTTP API for transcription service",
            # CORS configuration (allow all for friends/dev usage)
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.PUT,
                    apigwv2.CorsHttpMethod.DELETE,
                    apigwv2.CorsHttpMethod.OPTIONS,
                ],
                allow_headers=["*"],
                allow_credentials=True,
                max_age=Duration.hours(1),
            ),
            # Default integration (proxy all requests to Lambda)
            default_integration=lambda_integration,
        )

        # ===================================================================
        # 7. Stack Outputs
        # ===================================================================

        CfnOutput(
            self,
            "ApiEndpoint",
            value=http_api.url or "not-deployed",
            description="Transcription API endpoint URL",
            export_name="transcription-api-endpoint",
        )

        CfnOutput(
            self,
            "DynamoDbTable",
            value=table.table_name,
            description="DynamoDB table for user accounts and jobs",
            export_name="transcription-api-table",
        )

        CfnOutput(
            self,
            "LambdaFunctionArn",
            value=lambda_function.function_arn,
            description="Lambda function ARN",
            export_name="transcription-api-lambda-arn",
        )

        CfnOutput(
            self,
            "JwtSecretArn",
            value=jwt_secret.secret_arn,
            description="JWT secret ARN in Secrets Manager",
            export_name="transcription-api-jwt-secret-arn",
        )
