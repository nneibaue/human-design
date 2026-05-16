# Infrastructure Planning: GPU Cloud Setup for Transcription

**Status**: Planning phase (CPU-only for now)  
**Current Performance**: ~1-3 files/hour per worker (CPU int8, no GPU)  
**Estimated Timeline for Full Corpus**: 2-3 weeks with 3-4 CPU workers  
**GPU Acceleration Needed**: When targeting <1 week completion

---

## Executive Summary

The current CPU-based transcription pipeline is functional but slow for 151 series (500+ hours of audio, ~4,000+ files). This document outlines cloud GPU options to accelerate transcription 5-10x, enabling the full corpus to be processed in days instead of weeks.

### When to Use Cloud GPU

**Use GPU when:**
- Need full 151-series transcription in <7 days
- High-priority series require 24/7 transcription
- Rebecca needs urgent access to specific lecture series
- Batch processing multiple series in parallel

**CPU is fine when:**
- Transcribing 1-2 series at a time
- Can wait 2-3 weeks for full corpus
- Cost is priority over speed
- Sporadic transcription needs

---

## Option 1: AWS (Recommended)

### Instance: EC2 g4dn.xlarge

**Specifications:**
- **GPU**: 1x NVIDIA T4 (16GB VRAM)
- **CPU**: 4x Intel Xeon (shared)
- **Memory**: 16GB RAM
- **Cost**: ~$0.526/hour on-demand (~$380/month 24/7)
- **Performance**: 10-30 files/hour (10x vs CPU)
- **Availability**: All regions

**Setup Steps:**

1. **Launch Instance**
   ```bash
   # Via AWS Console or CLI
   aws ec2 run-instances \
     --image-id ami-0c55b159cbfafe1f0 \  # Ubuntu 22.04 LTS (us-east-1)
     --instance-type g4dn.xlarge \
     --key-name your-key-pair \
     --security-groups ra-transcription
   ```

2. **Install Dependencies**
   ```bash
   sudo apt update && sudo apt install -y python3.12 python3-pip
   pip install faster-whisper==0.10+ torch --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Mount Audio Directory**
   ```bash
   # Option A: EBS volume (persistent, recommended)
   # - Create EBS snapshot from ~/HD/AUDIO locally
   # - Attach to instance, mount to /data/audio
   
   # Option B: EFS (network filesystem, slower but flexible)
   # - Mount AWS EFS, sync audio files
   ```

4. **Run Transcription**
   ```bash
   python parallel_transcribe.py /data/audio /data/output 0 1000 large-v3
   ```

5. **Sync Results Back**
   ```bash
   # After job complete, sync outputs back to local machine
   aws s3 sync /data/output s3://your-bucket/transcripts/
   ```

**Pros:**
- ✅ Mature, well-documented
- ✅ Easy scaling (multiple instances)
- ✅ Flexible storage (S3, EBS, EFS)
- ✅ Pay-as-you-go pricing

**Cons:**
- ❌ Setup complexity (networking, security groups, AMI)
- ❌ Data transfer costs if not in same region
- ❌ Slightly higher per-GPU cost vs alternatives

---

## Option 2: Google Cloud (Good Alternative)

### Instance: Compute Engine n1-standard-4 + 1x NVIDIA T4

**Specifications:**
- **GPU**: 1x NVIDIA T4 (16GB VRAM)
- **CPU**: 4x vCPU (Intel Xeon)
- **Memory**: 15GB RAM
- **Cost**: ~$0.35/hour GPU + ~$0.19/hour compute (~$410/month)
- **Performance**: 10-30 files/hour (same as AWS)

**Setup Steps:**

1. **Create Instance**
   ```bash
   gcloud compute instances create ra-transcriber \
     --machine-type=n1-standard-4 \
     --accelerator=type=nvidia-tesla-t4,count=1 \
     --image-family=ubuntu-2204-lts \
     --image-project=ubuntu-os-cloud \
     --boot-disk-size=100GB
   ```

2. **Install NVIDIA Drivers + CUDA**
   ```bash
   # GCP provides startup script for GPU drivers
   # After instance boots, verify GPU:
   nvidia-smi
   ```

3. **Install Transcription Stack**
   ```bash
   pip install faster-whisper torch==2.0.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

4. **Mount Audio from Google Cloud Storage**
   ```bash
   # Option A: gsutil (simple, one-time sync)
   gsutil -m cp -r gs://your-bucket/HD_AUDIO /data/audio
   
   # Option B: Persistent Disk (attach storage)
   gcloud compute disks create audio-disk --size=500GB
   gcloud compute instances attach-disk ra-transcriber --disk=audio-disk
   ```

5. **Run Transcription**
   ```bash
   python parallel_transcribe.py /data/audio /data/output 0 1000 large-v3
   ```

**Pros:**
- ✅ Slightly cheaper per GPU-hour
- ✅ Integrated with GCS (Cloud Storage)
- ✅ Simpler startup (pre-configured GPU support)
- ✅ Free tier credits ($300)

**Cons:**
- ❌ Less mature marketplace for on-demand instances
- ❌ Smaller community for troubleshooting
- ❌ Persistent disk costs add up

---

## Option 3: Lambda Labs (Fastest Setup)

### Specifications
- **GPU**: 1x NVIDIA A100 (40GB VRAM, ultra-fast)
- **Cost**: ~$1.10/hour (~$800/month)
- **Performance**: 50-100 files/hour (fastest option)
- **Setup**: 5 minutes (pre-built, no config)

**Setup Steps:**

1. **Create Account & SSH Key**
   - Go to lambdalabs.com
   - Add public SSH key

2. **Launch Instance**
   - Choose region + GPU type (A100 preferred)
   - Instance boots in 2-3 minutes with PyTorch pre-installed

3. **Install Transcription Stack**
   ```bash
   pip install faster-whisper
   ```

4. **Transfer Audio**
   ```bash
   rsync -avz ~/HD/AUDIO user@lambda_ip:/data/audio
   ```

5. **Run Transcription**
   ```bash
   python parallel_transcribe.py /data/audio /data/output 0 1000 large-v3
   ```

**Pros:**
- ✅ Fastest setup (literally 5 minutes)
- ✅ Fastest performance (A100 GPU)
- ✅ Pre-built Python environments
- ✅ Great for rapid prototyping

**Cons:**
- ❌ Highest per-hour cost
- ❌ Limited region availability
- ❌ Less flexibility for long-term projects

---

## Option 4: Together AI (API-Based Alternative)

### Specifications
- **Model**: Whisper API (managed, no infrastructure)
- **Cost**: ~$0.006 per minute of audio
- **Setup**: 5 minutes (just API key)
- **Performance**: Depends on their backend

**Cost Estimate:**
- 500 hours audio × 60 min/hour = 30,000 minutes
- 30,000 × $0.006 = **$180 total** (!)

**Setup Steps:**

1. **Get API Key**
   - Sign up at together.ai
   - Generate API key

2. **Batch Transcription Script**
   ```python
   import together
   
   together.api_key = "your-key"
   
   for audio_file in audio_files:
       response = together.Complete.create(
           model="whisper",
           prompt=open(audio_file, "rb"),
       )
   ```

3. **Run Against All 4,000+ Files**
   - Parallelize requests
   - Handle rate limits
   - Collect outputs

**Pros:**
- ✅ Cheapest option by far ($180 for full corpus)
- ✅ Zero infrastructure management
- ✅ Pay per use (no monthly commitment)

**Cons:**
- ❌ API dependency (rate limits, downtime risk)
- ❌ Requires rewriting transcription pipeline
- ❌ Less control over model parameters
- ❌ Slower per-file (network round-trips)

---

## Recommendation Matrix

| Scenario | Best Choice | Cost | Speed |
|----------|-------------|------|-------|
| **Now (CPU good enough)** | Local CPU | Free | 1-3 files/hr |
| **Urgent (1 week timeline)** | AWS g4dn.xlarge | $380/mo | 10-30 files/hr |
| **Budget-conscious (1 series)** | Together API | $10-50 | ~5 files/hr |
| **Speed demons** | Lambda A100 | $800/mo | 50-100 files/hr |
| **Long-term (bulk transcription)** | GCP Compute + T4 | $400/mo | 10-30 files/hr |
| **Hybrid** | CPU + AWS for urgent | $0 + $380 | Flexible |

---

## Implementation Roadmap

### Phase 1: CPU-Only (Current)
- **Timeline**: ✅ Now
- **Coverage**: Start with high-priority series (Rave ABC, Living Your Design)
- **Cost**: $0
- **Timeline for full corpus**: 2-3 weeks

### Phase 2: GPU for High-Priority Series (Optional)
- **Timeline**: When business case justifies cost
- **Coverage**: Transcribe 20-30 high-value series first
- **Cost**: ~$50 (2 days on g4dn.xlarge)
- **Timeline for batch**: 2-5 days

### Phase 3: Full Corpus + Continuous Transcription
- **Timeline**: After all major series done
- **Coverage**: Remaining 100+ series, incoming new lectures
- **Cost**: $100-200/month for on-demand
- **Timeline**: 1 week for remaining corpus

### Phase 4: RAG + Advanced Search (Future)
- **Depends on**: GPU corpus completion
- **Enables**: Full-text semantic search, cross-lecture synthesis
- **Cost**: Minimal (post-processing on completed transcripts)

---

## Setup Checklist

### For AWS g4dn.xlarge (Recommended)

- [ ] Create AWS account (if not exists)
- [ ] Generate EC2 key pair, save locally
- [ ] Create security group (allow SSH inbound)
- [ ] Create EBS snapshot from ~/HD/AUDIO (on local machine):
  ```bash
  # Create 500GB local copy, upload to S3
  aws s3 sync ~/HD/AUDIO s3://your-bucket/HD_AUDIO --region us-east-1
  ```
- [ ] Launch g4dn.xlarge with Ubuntu 22.04 LTS
- [ ] SSH into instance, run setup script (see below)
- [ ] Start transcription jobs
- [ ] Sync outputs back to local via S3
- [ ] Terminate instance (don't forget!)

### Setup Script for Instance

```bash
#!/bin/bash
# Install GPU drivers + CUDA
sudo apt update
sudo apt install -y python3.12 python3-pip
sudo apt install -y nvidia-driver-535  # or latest stable

# Install Python packages
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install faster-whisper numpy

# Download audio from S3
mkdir -p /data/output
aws s3 sync s3://your-bucket/HD_AUDIO /data/audio

# Verify GPU
nvidia-smi
```

---

## Cost Projections

### Full Corpus (500 hours, ~4,000 files)

| Method | Duration | Cost |
|--------|----------|------|
| **CPU (3 workers)** | 2-3 weeks | $0 (local) |
| **AWS g4dn.xlarge** | 2-3 days | $25-40 |
| **Lambda A100** | 1-2 days | $50-100 |
| **Together API** | 3-5 days | $180 |

### Per-Series Costs

| Series | Size | CPU Time | GPU Cost (AWS) |
|--------|------|----------|----------------|
| Rave ABC | 50 files | 24-48 hrs | $5-10 |
| Living Your Design | 80 files | 40-80 hrs | $10-20 |
| Variable Workshops | 100 files | 50-100 hrs | $15-25 |

---

## Notes & Caveats

1. **Audio Storage**: 22.4GB in ~/HD/AUDIO. AWS data transfer costs ~$0.02/GB if outside region.
2. **Model Selection**: `large-v3` is slowest but most accurate. `base` is 5x faster but lower quality.
3. **Quantization**: CPU uses int8; GPU can use fp16 or fp32 (more accurate but slower).
4. **Parallelization**: Each GPU handles 1 worker. Multiple GPUs → multiple instances (cost scaling).
5. **Output Management**: Store transcripts in S3 or GCS for durability; don't rely on instance storage.

---

## Decision Points

**Ready to start GPU transcription when:**
- [ ] MCP server validated with CPU jobs
- [ ] Rapid transcription needed for user request
- [ ] Budget approved for cloud infrastructure
- [ ] 50+ series identified as high-priority

**Switch to API-based (Together) if:**
- [ ] Cost absolute priority
- [ ] One-time batch transcription (not ongoing)
- [ ] Don't need model parameter control

**Stick with CPU if:**
- [ ] Content transcription can be staggered
- [ ] Prefer zero cloud infrastructure
- [ ] Local resources available 24/7

---

## Contact & Support

- **AWS**: Support + docs at docs.aws.amazon.com
- **GCP**: docs.cloud.google.com (excellent tutorials)
- **Lambda Labs**: Support dashboard at lambdalabs.com
- **Together AI**: API docs at together.ai/docs
- **faster-whisper**: GitHub issues at github.com/guillaumekln/faster-whisper

---

## Next Steps

1. Validate MCP server on local CPU with 1-2 series
2. Once stable, present GPU options to Rebecca with cost/timeline
3. Approve cloud infrastructure budget + region preference
4. Set up test instance, run 1 series as POC
5. Scale to full batch based on results

**Current Status**: ✅ Awaiting budget approval for Phase 2
