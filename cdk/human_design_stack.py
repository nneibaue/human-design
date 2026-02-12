"""CDK stack for Human Design web application infrastructure."""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct


class HumanDesignStack(Stack):
    """AWS infrastructure for Human Design web application"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Secrets Manager - Import existing secrets
        self.secrets = secretsmanager.Secret.from_secret_name_v2(
            self,
            "HDCredentials",
            secret_name="hd-api-credentials"
        )

        self.webapp_password_secret = secretsmanager.Secret.from_secret_name_v2(
            self,
            "WebappPassword",
            secret_name="hd-webapp-password"
        )

        # 2. S3 Bucket for JSON data storage
        data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name="hd-app-data",
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    noncurrent_version_expiration=Duration.days(90)
                )
            ],
        )

        # 3. Lambda function for FastAPI (container image)
        fastapi_lambda = lambda_.DockerImageFunction(
            self,
            "FastAPILambda",
            code=lambda_.DockerImageCode.from_image_asset(
                "../",
                file="Dockerfile",
                target="runtime",
            ),
            memory_size=512,
            timeout=Duration.seconds(30),
            environment={
                "SECRET_NAME": self.secrets.secret_name,
                "WEBAPP_PASSWORD_SECRET": self.webapp_password_secret.secret_name,
                "SESSION_SECRET_KEY": "human-design-session-secret",
                "DATA_BUCKET": data_bucket.bucket_name,
            },
        )

        # Grant Lambda access to secrets and S3
        self.secrets.grant_read(fastapi_lambda)
        self.webapp_password_secret.grant_read(fastapi_lambda)
        data_bucket.grant_read_write(fastapi_lambda)

        # 4. API Gateway HTTP API
        api = apigw.HttpApi(
            self,
            "HDAPI",
            api_name="human-design-api",
            default_integration=integrations.HttpLambdaIntegration(
                "FastAPIIntegration", fastapi_lambda
            ),
        )

        # Outputs
        CfnOutput(
            self,
            "SecretArnOutput",
            value=self.secrets.secret_arn,
            export_name="hd-secret-arn"
        )
        CfnOutput(
            self,
            "ApiUrlOutput",
            value=api.url or "",
            description="FastAPI base URL"
        )
        CfnOutput(
            self,
            "DataBucketOutput",
            value=data_bucket.bucket_name
        )

        # 5. GitHub Actions OIDC federation for CI/CD deployments
        gh_oidc_provider = iam.OpenIdConnectProvider(
            self,
            "GitHubOIDCProvider",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )

        deploy_role = iam.Role(
            self,
            "GitHubActionsDeployRole",
            role_name="github-actions-cdk-deploy",
            assumed_by=iam.FederatedPrincipal(
                gh_oidc_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": "repo:nneibaue/human-design:ref:refs/heads/main",
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess"),
            ],
        )

        CfnOutput(
            self,
            "GHADeployRoleArn",
            value=deploy_role.role_arn,
            description="GitHub Actions deploy role ARN — add as AWS_ROLE_ARN repo secret",
        )
