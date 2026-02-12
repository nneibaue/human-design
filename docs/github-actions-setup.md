# GitHub Actions CI/CD Setup

Automated CDK deployments on push to `main` using GitHub Actions with AWS OIDC federation (no long-lived keys).

## Prerequisites

- AWS CLI configured with admin access
- CDK bootstrapped in target account/region: `cdk bootstrap aws://863355752029/us-east-1`

## One-Time Bootstrap

The OIDC provider and deploy role are defined in the CDK stack itself, so they must be created with a manual deploy before GitHub Actions can use them.

### 1. Deploy the stack manually

```bash
cd cdk
cdk deploy HumanDesignStack --require-approval=never
```

### 2. Copy the role ARN from the output

Look for `GHADeployRoleArn` in the deploy output:

```
HumanDesignStack.GHADeployRoleArn = arn:aws:iam::863355752029:role/github-actions-cdk-deploy
```

### 3. Add GitHub repo secrets

Go to https://github.com/nneibaue/human-design/settings/secrets/actions and add:

| Secret | Value |
|--------|-------|
| `AWS_ROLE_ARN` | The role ARN from step 2 |
| `AWS_ACCOUNT_ID` | `863355752029` |

### 4. Push to main

The workflow triggers on pushes to `main` that touch `cdk/**`, `src/**`, `lambda/**`, `Dockerfile`, or `pyproject.toml`. You can also trigger it manually via the "Run workflow" button on the Actions tab.

## How It Works

1. GitHub Actions requests a short-lived OIDC token scoped to the repo and branch
2. `aws-actions/configure-aws-credentials` exchanges the token for temporary AWS credentials via `sts:AssumeRoleWithWebIdentity`
3. The `github-actions-cdk-deploy` role is trusted only for `repo:nneibaue/human-design:ref:refs/heads/main`
4. CDK runs `diff` then `deploy --all` for both `HumanDesignStack` and `RaTranscribeStack`

## Troubleshooting

### OIDC provider already exists

If you get `EntityAlreadyExistsException` for the OIDC provider, another stack or manual setup already created it. Import the existing provider by ARN instead of creating a new one:

```python
gh_oidc_provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
    self, "GitHubOIDCProvider",
    "arn:aws:iam::863355752029:oidc-provider/token.actions.githubusercontent.com"
)
```

### Docker build failures in CI

The Lambda container image build runs during `cdk deploy`. `ubuntu-latest` runners have Docker pre-installed, so this should work. If builds fail with memory issues, the runner's 7 GB RAM is likely sufficient but check the Dockerfile for expensive build steps.

### VPC context drift (TranscribeStack)

`TranscribeStack` looks up the default VPC at synth time. The VPC context is cached in `cdk/cdk.context.json` (committed to the repo). If the VPC changes, update the context locally:

```bash
cd cdk
cdk context --clear
cdk synth
# Commit the updated cdk.context.json
```

### Permission errors during deploy

The deploy role uses `AdministratorAccess`. If you see access denied errors, verify:
- The `AWS_ROLE_ARN` secret matches the deployed role
- The trust policy subject condition matches the branch (`refs/heads/main`)

## References

- [Configuring OpenID Connect in AWS](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [aws-actions/configure-aws-credentials](https://github.com/aws-actions/configure-aws-credentials)
- [AWS CDK Deploy Action Patterns](https://docs.aws.amazon.com/cdk/v2/guide/cdk_pipeline.html)
