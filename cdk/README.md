# CDK Infrastructure for Ra Transcription

This directory contains AWS CDK infrastructure code for the Ra Uru Hu lecture transcription system.

## Prerequisites

### 1. Install Node.js and npm

AWS CDK CLI is a Node.js tool (even though your infrastructure code is Python).

**Check if already installed:**
```bash
node --version
npm --version
```

**If not installed, install Node.js:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install nodejs npm

# Or use nvm (recommended for version management)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc  # or restart terminal
nvm install --lts
```

### 2. Install AWS CDK CLI

```bash
# Install globally
npm install -g aws-cdk

# Verify installation
cdk --version
```

**Alternative:** Use `npx aws-cdk` instead of `cdk` if you don't want to install globally.

## Setup

Install Python CDK dependencies:

```bash
cd /home/nneibaue/code/human-design
./hd-env/bin/pip install -e ".[cdk]"
```

## Deployment

### First Time Setup

1. Configure AWS credentials (see main plan for details)
2. Bootstrap CDK (first time only):

```bash
cd cdk/
cdk bootstrap
```

3. Deploy the stack:

```bash
cdk deploy
```

This creates:
- S3 buckets for input/output
- ECR repository for Docker image
- IAM roles for Batch jobs
- Batch compute environment (Spot instances)
- Batch job queue and definition

### Update Infrastructure

```bash
cd cdk/
cdk diff    # Preview changes
cdk deploy  # Apply changes
```

### Destroy Infrastructure

```bash
cd cdk/
cdk destroy
```

## Stack Outputs

After deployment, the stack outputs:
- `inputBucket`: S3 bucket for audio files
- `outputBucket`: S3 bucket for transcriptions
- `ecrRepo`: ECR repository URI
- `jobQueue`: Batch job queue name
- `jobDefinition`: Batch job definition name

Access outputs:

```bash
aws cloudformation describe-stacks --stack-name RaTranscribeStack --query "Stacks[0].Outputs"
```
