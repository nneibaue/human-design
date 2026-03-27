# Transcription Service API Design

**Date:** 2026-03-26
**Status:** Approved
**Author:** Claude Sonnet 4.5

## Context

Extract transcription functionality from the Ra-specific MCP server into a clean, general-purpose transcription service. The existing code is messy and tightly coupled to Ra Uru Hu lecture workflows. We need a standalone service that:

- Supports audio file uploads and YouTube URL transcription
- Provides user authentication with isolated storage per user
- Integrates with existing AWS Batch infrastructure
- Offers both REST API and simple web UI
- Runs on AWS with minimal operational cost

This service is intended for personal use with friends (low traffic, trust-based).

## Requirements

### Functional Requirements

1. **User Management**
   - Self-service registration with email/password
   - JWT-based authentication
   - Users only see their own recordings and transcriptions

2. **Audio Input**
   - Upload audio files (MP3, M4A, WAV, OGG) up to 10MB each via API (API Gateway payload limit)
   - For files larger than 10MB: use S3 pre-signed URLs for direct upload
   - Batch upload support (multiple files at once)
   - Submit YouTube URLs for audio extraction and transcription (no size limit)
   - Store audio in S3

3. **Transcription Processing**
   - Queue transcription jobs using existing AWS Batch infrastructure
   - Use faster-whisper with large-v3 model (CPU-based)
   - Real-time progress tracking (% complete, file-by-file status)
   - Store results indefinitely in S3

4. **Job Management**
   - List all jobs for authenticated user
   - View job details and file-level status
   - Download transcription results (JSON + TXT)
   - Delete jobs and associated files

5. **Interface**
   - REST API for programmatic access
   - Simple web UI (HTML forms, job dashboard)
   - Mobile-responsive design (works well on phones and tablets)

### Non-Functional Requirements

1. **Cost:** Minimize AWS costs using serverless architecture (Lambda + DynamoDB)
2. **Security:** Password-protected, JWT tokens, user data isolation
3. **Simplicity:** No rate limiting, trust-based for friends-only usage
4. **Reuse:** Leverage existing AWS Batch infrastructure from `transcribe_stack.py`
5. **Mobile-First:** Web UI must be fully functional and usable on mobile devices (responsive design, touch-friendly)

## Architecture

### System Components

```
┌─────────────┐
│   Browser   │
│   or API    │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────┐
│  API Gateway    │
│   (HTTP API)    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐      ┌──────────────┐
│  Lambda         │─────▶│  DynamoDB    │
│  (FastAPI +     │      │  (users,     │
│   Mangum)       │      │   jobs,      │
└──────┬──────────┘      │   files)     │
       │                 └──────────────┘
       │
       ├─────────────────▶ S3 Input Bucket
       │                   (audio files)
       │
       ├─────────────────▶ AWS Batch
       │                   (submit transcription jobs)
       │
       └─────────────────▶ S3 Output Bucket
                           (transcription results)
```

**Components:**

1. **API Gateway HTTP API** - Routes requests to Lambda, handles CORS
2. **Lambda Function** - FastAPI app wrapped with Mangum, handles all API logic
3. **DynamoDB** - Single table for users, jobs, and files
4. **S3 Buckets** - Reuse existing `hd-transcribe-input` and `hd-transcribe-output`
5. **AWS Batch** - Reuse existing job queue and Docker containers

### Data Model

**DynamoDB Single-Table Design:**

**Users:**
```
PK: USER#<email>
SK: METADATA
Attributes:
  - email: string
  - password_hash: string (bcrypt)
  - created_at: ISO timestamp
  - display_name: string (optional)
```

**Jobs:**
```
PK: USER#<email>
SK: JOB#<timestamp>#<uuid>
Attributes:
  - job_id: string (uuid)
  - status: queued | running | completed | failed
  - created_at: ISO timestamp
  - updated_at: ISO timestamp
  - total_files: int
  - completed_files: int
  - batch_job_ids: list[string] (AWS Batch job IDs)
  - job_type: upload | youtube
```

**Files:**
```
PK: JOB#<job_id>
SK: FILE#<file_id>
Attributes:
  - file_id: string (uuid)
  - filename: string (original name)
  - audio_s3_key: string (input bucket key)
  - transcription_s3_key: string (output bucket key, null until complete)
  - status: pending_upload | uploaded | queued | transcribing | completed | failed
  - duration_seconds: float (from transcription result)
  - created_at: ISO timestamp
```

**GSI for Job Lookup:**
```
GSI: job_id-index
PK: job_id
SK: (none)
```

**Access Patterns:**
1. Get user by email: Query `PK = USER#<email>, SK = METADATA`
2. List jobs for user: Query `PK = USER#<email>, SK begins_with JOB#`
3. Get job by job_id: Query GSI `job_id = <uuid>`
4. List files for job: Query `PK = JOB#<job_id>, SK begins_with FILE#`

## API Design

### Authentication

**JWT Tokens:**
- Algorithm: HS256
- Expiration: 7 days
- Secret stored in AWS Secrets Manager
- Tokens contain: `{email, exp}`

**Protected Endpoints:**
- Require `Authorization: Bearer <token>` header
- Lambda validates JWT signature and expiration
- Extract user email from token for authorization

### REST API Endpoints

**Authentication:**
```
POST /auth/register
Body: {email: string, password: string, display_name?: string}
Response: {message: "User created", email: string}

POST /auth/login
Body: {email: string, password: string}
Response: {access_token: string, token_type: "bearer"}

GET /auth/me
Headers: Authorization: Bearer <token>
Response: {email: string, created_at: string, display_name?: string}
```

**Jobs:**
```
POST /jobs/upload
Headers: Authorization: Bearer <token>
Content-Type: multipart/form-data
Body: files[] (multiple audio files, each <= 10MB)
Response: {job_id: string, total_files: int, status: "queued"}

POST /jobs/upload/presigned
Headers: Authorization: Bearer <token>
Body: {files: [{filename: string, content_type: string, size_bytes: int}]}
Response: {
  job_id: string,
  uploads: [{file_id: string, filename: string, upload_url: string}]
}
Note: For files > 10MB. Client uploads directly to S3 via presigned URL, then calls complete endpoint.

POST /jobs/upload/complete
Headers: Authorization: Bearer <token>
Body: {job_id: string, file_ids: [string]}
Response: {job_id: string, status: "queued"}
Note: Confirms upload complete, queues transcription jobs.

POST /jobs/youtube
Headers: Authorization: Bearer <token>
Body: {urls: [string]}
Response: {job_id: string, total_files: int, status: "queued"}

GET /jobs
Headers: Authorization: Bearer <token>
Query: ?limit=50&offset=0
Response: {jobs: [{job_id, status, created_at, total_files, completed_files}]}

GET /jobs/{job_id}
Headers: Authorization: Bearer <token>
Response: {
  job_id: string,
  status: string,
  total_files: int,
  completed_files: int,
  files: [{file_id, filename, status, download_url?}]
}

GET /jobs/{job_id}/files/{file_id}/download
Headers: Authorization: Bearer <token>
Response: Pre-signed S3 URL (redirect or JSON)

DELETE /jobs/{job_id}
Headers: Authorization: Bearer <token>
Response: {message: "Job deleted"}
```

**Web UI (HTML):**
```
GET /
Response: Landing page with login/register forms

GET /dashboard
Headers: Cookie with JWT
Response: HTML dashboard with job list and upload form

GET /jobs/{job_id}
Headers: Cookie with JWT
Response: HTML job detail page with file list and download links
```

**Web UI Implementation (Mobile-Responsive):**
- CSS framework: None (vanilla CSS with media queries for simplicity)
- Viewport meta tag: `<meta name="viewport" content="width=device-width, initial-scale=1">`
- Touch-friendly: Buttons min 44x44px tap targets, adequate spacing
- Responsive breakpoints: Mobile (<768px), Tablet (768-1024px), Desktop (>1024px)
- Mobile upload: Use `<input type="file" multiple accept="audio/*">` for native file picker
- Progress polling: Auto-refresh job status every 5 seconds, pause when tab hidden
- Minimal JavaScript: Form validation, file upload progress, status polling

### File Upload Flow

**Small files (≤ 10MB):**
1. User uploads files via `POST /jobs/upload`
2. Lambda receives multipart form data
3. For each file:
   - Generate unique S3 key: `{user_email}/{job_id}/{file_id}/{filename}`
   - Stream file to S3 using `boto3.upload_fileobj`
   - Create File record in DynamoDB (status: `uploaded`)
4. Create Job record in DynamoDB (status: `queued`)
5. Submit AWS Batch jobs (one per file or batched)
6. Return job_id to user

**Large files (> 10MB):**
1. User calls `POST /jobs/upload/presigned` with file metadata
2. Lambda generates pre-signed S3 upload URLs (15-minute expiration)
3. Lambda creates Job and File records (status: `pending_upload`)
4. User uploads files directly to S3 using pre-signed URLs
5. User calls `POST /jobs/upload/complete` to confirm uploads
6. Lambda verifies files exist in S3, updates status to `queued`
7. Lambda submits AWS Batch jobs

### YouTube Download Flow

1. User submits URLs via `POST /jobs/youtube`
2. Lambda validates YouTube URLs (basic regex check)
3. Create Job record (status: `queued`, job_type: `youtube`)
4. For each URL:
   - Create File record with filename from URL
   - Submit AWS Batch job with `yt-dlp` command
5. Batch worker:
   - Downloads audio with `yt-dlp --extract-audio --audio-format mp3`
   - Uploads to S3 input bucket
   - Transcribes using existing `parallel_transcribe.py`
   - Uploads results to S3 output bucket
   - Updates DynamoDB file status
6. Return job_id to user

### Progress Tracking

**Real-time status polling:**
- User polls `GET /jobs/{job_id}` every 5 seconds
- Lambda queries DynamoDB for job and file records
- Aggregates: total_files, completed_files, failed_files
- Returns file-level status and download URLs for completed files

**Job status calculation:**
- `queued`: Job created, Batch jobs not yet running
- `running`: At least one Batch job running
- `completed`: All files completed successfully
- `failed`: All files failed

## AWS Batch Integration

### Job Submission

**Lambda submits to existing Batch infrastructure:**
```python
import boto3

batch = boto3.client('batch')

batch.submit_job(
    jobName=f"transcribe-{file_id}",
    jobQueue="transcribe-queue",
    jobDefinition="transcribe-job",
    containerOverrides={
        "command": [
            "python", "/workspace/parallel_transcribe.py",
            f"s3://{input_bucket}/{s3_key}",
            f"s3://{output_bucket}/{job_id}",
            "0", "1", "large-v3"
        ],
        "environment": [
            {"name": "JOB_ID", "value": job_id},
            {"name": "FILE_ID", "value": file_id},
            {"name": "DYNAMODB_TABLE", "value": table_name}
        ]
    }
)
```

### Docker Container Updates

**Modify `parallel_transcribe.py`:**
1. Accept S3 paths instead of local paths
2. Download file from S3 to `/tmp/`
3. Transcribe locally
4. Upload results to S3
5. Update DynamoDB file record:
   ```python
   dynamodb.update_item(
       TableName=table_name,
       Key={"PK": f"JOB#{job_id}", "SK": f"FILE#{file_id}"},
       UpdateExpression="SET #status = :status, transcription_s3_key = :key",
       ExpressionAttributeNames={"#status": "status"},
       ExpressionAttributeValues={
           ":status": "completed",
           ":key": f"{output_bucket}/{job_id}/{file_id}.json"
       }
   )
   ```

**Add YouTube support:**
- Install `yt-dlp` in Dockerfile
- Create `youtube_transcribe.py` script:
  ```python
  import yt_dlp

  ydl_opts = {
      'format': 'bestaudio/best',
      'outtmpl': '/tmp/%(id)s.%(ext)s',
      'postprocessors': [{
          'key': 'FFmpegExtractAudio',
          'preferredcodec': 'mp3',
      }]
  }

  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      ydl.download([url])

  # Upload to S3, transcribe, update DynamoDB
  ```

### Error Handling

1. **Batch job fails:**
   - Container exits with non-zero code
   - Update DynamoDB file status to `failed`
   - Job continues (don't fail entire job if one file fails)

2. **Partial success:**
   - Job status remains `running` until all files finish
   - User can download completed files while others are processing

3. **No automatic retries:**
   - User can manually delete and re-submit failed jobs

## Deployment

### CDK Infrastructure

**New Stack: `TranscriptionApiStack`**

Location: `cdk/transcription_api_stack.py`

**Resources:**

1. **DynamoDB Table**
   ```python
   table = dynamodb.Table(
       self, "TranscriptionTable",
       table_name="transcription-service",
       partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
       sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
       billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
       point_in_time_recovery=True,
       removal_policy=RemovalPolicy.RETAIN,
   )

   table.add_global_secondary_index(
       index_name="job_id-index",
       partition_key=dynamodb.Attribute(name="job_id", type=dynamodb.AttributeType.STRING),
       projection_type=dynamodb.ProjectionType.ALL,
   )
   ```

2. **JWT Secret**
   ```python
   secret = secretsmanager.Secret(
       self, "JWTSecret",
       secret_name="transcription-jwt-secret",
       generate_secret_string=secretsmanager.SecretStringGenerator(
           secret_string_template='{}',
           generate_string_key='jwt_secret',
           exclude_characters=' %+~`#$&*()|[]{}:;<>?!\'/@"\\',
       )
   )
   ```

3. **Lambda Function**
   ```python
   lambda_function = lambda_.Function(
       self, "TranscriptionAPI",
       function_name="transcription-api",
       runtime=lambda_.Runtime.PYTHON_3_14,
       handler="main.handler",
       code=lambda_.Code.from_asset("src/transcription_service"),
       memory_size=512,
       timeout=Duration.seconds(30),
       environment={
           "DYNAMODB_TABLE": table.table_name,
           "INPUT_BUCKET": input_bucket.bucket_name,
           "OUTPUT_BUCKET": output_bucket.bucket_name,
           "BATCH_JOB_QUEUE": "transcribe-queue",
           "BATCH_JOB_DEFINITION": "transcribe-job",
           "JWT_SECRET_ARN": secret.secret_arn,
       }
   )

   # Grant permissions
   table.grant_read_write_data(lambda_function)
   input_bucket.grant_read_write(lambda_function)
   output_bucket.grant_read(lambda_function)
   secret.grant_read(lambda_function)
   lambda_function.add_to_role_policy(
       iam.PolicyStatement(
           actions=["batch:SubmitJob"],
           resources=["*"]
       )
   )
   ```

4. **API Gateway HTTP API**
   ```python
   api = apigatewayv2.HttpApi(
       self, "TranscriptionHttpApi",
       api_name="transcription-api",
       cors_preflight=apigatewayv2.CorsPreflightOptions(
           allow_origins=["*"],
           allow_methods=[apigatewayv2.CorsHttpMethod.ANY],
           allow_headers=["*"],
       )
   )

   api.add_routes(
       path="/{proxy+}",
       methods=[apigatewayv2.HttpMethod.ANY],
       integration=integrations.HttpLambdaIntegration(
           "LambdaIntegration",
           lambda_function
       )
   )
   ```

**Cross-Stack References:**
- Import S3 buckets from `TranscribeStack` using `Fn.import_value()`
- Import Batch job queue/definition ARNs

### File Structure

```
src/transcription_service/
├── main.py                  # FastAPI app + Mangum handler
├── models.py                # Pydantic models
├── auth.py                  # JWT utils, password hashing
├── database.py              # DynamoDB operations
├── s3.py                    # S3 upload/download helpers
├── batch.py                 # AWS Batch job submission
├── routers/
│   ├── auth.py              # Auth endpoints
│   ├── jobs.py              # Job management endpoints
│   └── web.py               # HTML UI endpoints
├── static/
│   ├── css/
│   │   └── main.css         # Mobile-responsive styles
│   └── js/
│       └── app.js           # File upload, status polling, form validation
└── templates/
    ├── base.html            # Base template with mobile viewport meta tag
    ├── index.html           # Landing page
    ├── dashboard.html       # Job list + upload form
    └── job_detail.html      # Job detail page
```

### Dependencies

```toml
[project.dependencies]
fastapi = "^0.109.0"
mangum = "^0.17.0"
pydantic = "^2.6.0"
python-jose[cryptography] = "^3.3.0"
passlib[bcrypt] = "^1.7.4"
boto3 = "^1.34.0"
python-multipart = "^0.0.7"
jinja2 = "^3.1.3"
```

### Deployment Commands

```bash
# Build and deploy CDK stack
cd cdk
cdk deploy TranscriptionApiStack

# Output will include API Gateway URL
# https://xxxxxx.execute-api.us-east-1.amazonaws.com
```

## Testing Strategy

### Unit Tests
- Auth: JWT generation/validation, password hashing
- Database: DynamoDB query patterns
- S3: Upload/download helpers
- Batch: Job submission logic

### Integration Tests
- End-to-end API tests using `httpx.AsyncClient`
- Test with LocalStack (DynamoDB, S3)
- Mock AWS Batch responses

### Manual Testing
1. Register user via web UI
2. Upload audio files
3. Submit YouTube URL
4. Poll job status
5. Download transcription results
6. Delete job

## Security Considerations

1. **Password Storage:** bcrypt with salt rounds = 12
2. **JWT Signing:** HS256 with 256-bit secret
3. **Authorization:** Every endpoint validates JWT and filters by user email
4. **S3 Access:** Pre-signed URLs for downloads (expiration: 1 hour)
5. **CORS:** Restrict origins in production (currently `*` for development)
6. **Input Validation:** Pydantic models validate all inputs
7. **File Size Limits:** API Gateway max payload: 10MB; files larger than 10MB require S3 pre-signed URL upload flow

## Cost Estimates

**AWS Free Tier (first 12 months):**
- Lambda: 1M requests/month, 400,000 GB-seconds compute
- DynamoDB: 25GB storage, 25 WCU, 25 RCU
- API Gateway: 1M HTTP API requests/month
- S3: 5GB storage, 20,000 GET, 2,000 PUT

**Expected monthly costs (friends-only usage, ~100 jobs/month):**
- Lambda: $0 (well under free tier)
- DynamoDB: $0 (under free tier)
- API Gateway: $0 (under free tier)
- S3: ~$2-5 (storage for audio + transcriptions)
- AWS Batch: ~$0-10 (EC2 compute time for transcription)

**Total: ~$2-15/month**

## Future Enhancements

1. **Email notifications:** Send email when transcription completes
2. **Webhooks:** POST to user-provided URL on completion
3. **Custom terminology:** Allow users to provide custom prompt for domain-specific terms
4. **Model selection:** Let users choose whisper model size (speed vs accuracy)
5. **Transcript search:** Full-text search across transcriptions
6. **Sharing:** Generate shareable links for transcriptions
7. **Admin dashboard:** View all users, jobs, storage usage

## Verification Plan

**End-to-end test scenario:**

1. **Deploy infrastructure:**
   ```bash
   cdk deploy TranscriptionApiStack
   ```
   - Verify: API Gateway URL in CloudFormation outputs
   - Verify: DynamoDB table created
   - Verify: Lambda function deployed

2. **Test user registration:**
   ```bash
   curl -X POST https://<api-url>/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test123"}'
   ```
   - Verify: 200 response with user email
   - Verify: User record in DynamoDB

3. **Test login:**
   ```bash
   curl -X POST https://<api-url>/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test123"}'
   ```
   - Verify: JWT token returned
   - Verify: Token contains valid expiration

4. **Test file upload:**
   ```bash
   curl -X POST https://<api-url>/jobs/upload \
     -H "Authorization: Bearer <token>" \
     -F "files[]=@test.mp3"
   ```
   - Verify: job_id returned
   - Verify: File uploaded to S3 input bucket
   - Verify: AWS Batch job submitted
   - Verify: Job and File records in DynamoDB

5. **Test job status:**
   ```bash
   curl https://<api-url>/jobs/<job_id> \
     -H "Authorization: Bearer <token>"
   ```
   - Verify: Returns job status, file list
   - Verify: Status updates as transcription progresses

6. **Test YouTube download:**
   ```bash
   curl -X POST https://<api-url>/jobs/youtube \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"urls":["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]}'
   ```
   - Verify: job_id returned
   - Verify: Batch job downloads audio with yt-dlp
   - Verify: Audio transcribed and results uploaded to S3

7. **Test transcription download:**
   ```bash
   curl https://<api-url>/jobs/<job_id>/files/<file_id>/download \
     -H "Authorization: Bearer <token>"
   ```
   - Verify: Pre-signed S3 URL returned or redirected
   - Verify: Transcription JSON/TXT downloadable

8. **Test web UI:**
   - Open `https://<api-url>/` in browser
   - Register account, login
   - Upload file via dashboard
   - Verify job appears in list
   - Click job to see file-level status
   - Download transcription when complete

9. **Test authorization:**
   - Create second user
   - Verify user A cannot access user B's jobs
   - Verify invalid JWT returns 401

10. **Verify AWS Batch integration:**
    - Check CloudWatch logs for Batch container output
    - Verify transcription results appear in S3 output bucket
    - Verify DynamoDB file status updates to "completed"
