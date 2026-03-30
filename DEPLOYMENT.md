# Transcription Service - Deployment & Testing Guide

## Prerequisites

- Personal AWS account with admin/deploy permissions
- AWS CLI configured with personal profile
- Docker installed (for building Lambda image)
- CDK CLI installed (`npm install -g aws-cdk`)

## Step 1: Configure AWS Profile

```bash
# Configure personal AWS profile (one-time)
aws configure --profile personal
# Enter Access Key ID
# Enter Secret Access Key
# Region: us-east-1 (NOT us-gov-east-1)
# Output format: json

# Verify it works
AWS_PROFILE=personal aws sts get-caller-identity
```

## Step 2: Bootstrap CDK (First Time Only)

```bash
export AWS_PROFILE=personal
cd cdk
cdk bootstrap aws://ACCOUNT-ID/us-east-1
```

Replace `ACCOUNT-ID` with your AWS account number from step 1.

## Step 3: Build and Push Docker Image

The Lambda function uses a Docker image that needs to be pushed to ECR before deployment.

```bash
export AWS_PROFILE=personal
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 1. Create ECR repository (if it doesn't exist)
aws ecr create-repository --repository-name ra-transcribe --region us-east-1 || true

# 2. Build Docker image
docker build -f Dockerfile.transcribe -t ra-transcribe:latest .

# 3. Tag for ECR
docker tag ra-transcribe:latest ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/ra-transcribe:latest

# 4. Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# 5. Push image
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/ra-transcribe:latest
```

## Step 4: Deploy CDK Stacks

Deploy in order (TranscriptionApiStack depends on the others):

```bash
export AWS_PROFILE=personal
cd cdk

# Check what will be deployed
cdk diff TranscriptionApiStack

# Deploy (will prompt for confirmation)
cdk deploy TranscriptionApiStack

# Or deploy all stacks at once
cdk deploy --all
```

**Note:** If HumanDesignStack or RaTranscribeStack don't exist yet, deploy them first:
```bash
cdk deploy HumanDesignStack
cdk deploy RaTranscribeStack
cdk deploy TranscriptionApiStack
```

## Step 5: Get API Endpoint

After successful deployment, the output will show:
```
TranscriptionApiStack.ApiEndpoint = https://abc123.execute-api.us-east-1.amazonaws.com
```

Save this URL - you'll need it for testing.

## Step 6: Test the API

### Test 1: Health Check

```bash
curl https://YOUR-API-ENDPOINT.execute-api.us-east-1.amazonaws.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Transcription Service API",
  "version": "1.0.0"
}
```

### Test 2: Register a User

```bash
curl -X POST https://YOUR-API-ENDPOINT/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "display_name": "Test User"
  }'
```

Expected response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

Save the `access_token` for subsequent requests.

### Test 3: Get User Profile

```bash
TOKEN="your-access-token-from-step-2"

curl https://YOUR-API-ENDPOINT/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "email": "test@example.com",
  "created_at": "2026-03-28T...",
  "display_name": "Test User"
}
```

### Test 4: Upload Audio File

```bash
TOKEN="your-access-token"

curl -X POST https://YOUR-API-ENDPOINT/jobs/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@/path/to/audio.mp3"
```

Expected response:
```json
{
  "job_id": "uuid-here",
  "user_email": "test@example.com",
  "status": "queued",
  "created_at": "2026-03-28T...",
  "total_files": 1,
  "completed_files": 0,
  "failed_files": 0
}
```

### Test 5: Check Job Status

```bash
TOKEN="your-access-token"
JOB_ID="uuid-from-step-4"

curl https://YOUR-API-ENDPOINT/jobs/$JOB_ID \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "job_id": "uuid",
  "user_email": "test@example.com",
  "status": "running",
  "created_at": "2026-03-28T...",
  "total_files": 1,
  "completed_files": 0,
  "failed_files": 0,
  "files": [
    {
      "file_id": "uuid",
      "filename": "audio.mp3",
      "status": "transcribing",
      "created_at": "2026-03-28T..."
    }
  ]
}
```

### Test 6: Test Web UI

Open in browser:
```
https://YOUR-API-ENDPOINT/
```

You should see the login/register page. Register a new user and test the upload interface.

## Step 7: Test YouTube Transcription

```bash
TOKEN="your-access-token"

curl -X POST https://YOUR-API-ENDPOINT/jobs/youtube \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
  }'
```

## Monitoring & Debugging

### View Lambda Logs

```bash
# Get Lambda function name
aws lambda list-functions --query 'Functions[?contains(FunctionName, `transcription`)].FunctionName' --output text

# Tail logs
aws logs tail /aws/lambda/transcription-api --follow
```

### View DynamoDB Data

```bash
# Scan users table
aws dynamodb scan \
  --table-name transcription-service \
  --filter-expression "begins_with(PK, :pk)" \
  --expression-attribute-values '{":pk":{"S":"USER#"}}'
```

### Check API Gateway

Visit AWS Console → API Gateway → TranscriptionServiceAPI → View logs in CloudWatch

## Cleanup

To delete all resources (careful - this deletes data!):

```bash
export AWS_PROFILE=personal
cd cdk
cdk destroy TranscriptionApiStack
```

## Troubleshooting

### Issue: "no identity-based policy allows the cloudformation:DescribeStacks action"

You need CloudFormation permissions in IAM. Add `CloudFormationFullAccess` policy to your IAM user.

### Issue: "The security token included in the request is invalid"

Your AWS credentials are wrong or expired. Reconfigure:
```bash
aws configure --profile personal
```

### Issue: Lambda function can't find Docker image

Make sure you pushed the Docker image to ECR (Step 3) before deploying.

### Issue: CORS errors in browser

Check that the API Gateway CORS settings allow your origin. The current config allows all origins (`*`).

### Issue: JWT authentication fails

Check that the JWT secret was created in Secrets Manager. View in AWS Console → Secrets Manager → `transcription-service/jwt-secret`.

## Cost Estimate

With typical friend usage (~10 hours/month of transcription):
- Lambda: $2-5/month (CPU time)
- DynamoDB: $0-1/month (PAY_PER_REQUEST)
- API Gateway: $0-1/month (first 1M requests free)
- S3: $1-2/month (storage + transfer)
- AWS Batch: $5-10/month (transcription compute)

**Total: ~$10-20/month**

To minimize costs:
- Delete old transcriptions from S3
- Use Spot instances for Batch (50-90% cheaper)
- Clean up completed jobs periodically
