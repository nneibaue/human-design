"""
Pydantic AI agent for orchestrating the YouTube transcription pipeline.

Handles: download audio → upload to S3 → submit Batch jobs → monitor → pull results.

Usage:
    from human_design.agents.transcribe import transcribe_agent, TranscribeDeps

    deps = TranscribeDeps.create()
    result = await transcribe_agent.run(
        "Transcribe all videos from https://youtu.be/...",
        deps=deps,
    )
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import boto3
from pydantic_ai import Agent, RunContext

from human_design.models.transcription import (
    ChannelDownload,
    TranscriptionJob,
    TranscriptionPipeline,
)

INPUT_BUCKET = "hd-transcribe-input"
OUTPUT_BUCKET = "hd-transcribe-output"
JOB_QUEUE = "transcribe-queue"
JOB_DEFINITION = "transcribe-job"


@dataclass
class TranscribeDeps:
    """Dependencies for the transcription agent."""

    s3: boto3.client
    batch: boto3.client
    audio_base_dir: Path = field(default_factory=lambda: Path.home() / "HD" / "AUDIO")
    yt_dlp_path: str = "yt-dlp"

    @classmethod
    def create(cls) -> TranscribeDeps:
        """Create deps with default boto3 clients."""
        return cls(
            s3=boto3.client("s3"),
            batch=boto3.client("batch"),
        )


transcribe_agent = Agent(
    "anthropic:claude-sonnet-4-6",
    deps_type=TranscribeDeps,
    output_type=TranscriptionPipeline,
    instructions=(
        "You orchestrate YouTube audio transcription. "
        "Given a channel name and YouTube URLs, you: "
        "1) Download audio with the download tool, "
        "2) Upload to S3 with the upload tool, "
        "3) Submit Batch jobs with the submit tool, "
        "4) Check status with the status tool. "
        "Return a TranscriptionPipeline summary when done."
    ),
)


@transcribe_agent.tool
async def download_audio(
    ctx: RunContext[TranscribeDeps],
    channel_name: str,
    youtube_urls: list[str],
) -> ChannelDownload:
    """Download audio from YouTube URLs as MP3 files using yt-dlp."""
    output_dir = ctx.deps.audio_base_dir / channel_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Download all URLs in parallel (4 workers)
    url_input = "\n".join(youtube_urls)
    proc = subprocess.run(
        [
            "bash", "-c",
            f'echo "{url_input}" | xargs -P4 -I{{}} '
            f'{ctx.deps.yt_dlp_path} --extract-audio --audio-format mp3 '
            f'--audio-quality 0 -o "{output_dir}/%(title)s.%(ext)s" "{{}}"',
        ],
        capture_output=True,
        text=True,
    )

    mp3_files = list(output_dir.glob("*.mp3"))
    return ChannelDownload(
        channel_name=channel_name,
        youtube_url=youtube_urls[0] if youtube_urls else "",
        local_audio_dir=str(output_dir),
        file_count=len(mp3_files),
        s3_prefix=f"{channel_name}/",
    )


@transcribe_agent.tool
async def upload_to_s3(
    ctx: RunContext[TranscribeDeps],
    channel_name: str,
    local_audio_dir: str,
) -> int:
    """Upload all MP3 files from local directory to S3 input bucket. Returns file count."""
    audio_dir = Path(local_audio_dir)
    s3 = ctx.deps.s3
    uploaded = 0

    for mp3 in sorted(audio_dir.glob("*.mp3")):
        key = f"{channel_name}/{mp3.name}"
        s3.upload_file(str(mp3), INPUT_BUCKET, key)
        uploaded += 1

    return uploaded


@transcribe_agent.tool
async def submit_batch_jobs(
    ctx: RunContext[TranscribeDeps],
    channel_name: str,
    transcribe_prompt: str = "",
) -> list[TranscriptionJob]:
    """Submit AWS Batch transcription jobs for all MP3s in the S3 input prefix."""
    s3 = ctx.deps.s3
    batch = ctx.deps.batch

    # List files in S3
    resp = s3.list_objects_v2(Bucket=INPUT_BUCKET, Prefix=f"{channel_name}/")
    mp3_keys = [
        obj["Key"] for obj in resp.get("Contents", [])
        if obj["Key"].endswith(".mp3")
    ]

    jobs = []
    for key in mp3_keys:
        filename = key.rsplit("/", 1)[-1]
        job_name = f"t-{filename[:45].replace(' ', '-')}"
        # Remove non-alphanumeric chars except hyphens
        job_name = "".join(c for c in job_name if c.isalnum() or c == "-")

        s3_input = f"s3://{INPUT_BUCKET}/{key}"
        s3_output = f"s3://{OUTPUT_BUCKET}/{channel_name}/"

        response = batch.submit_job(
            jobName=job_name,
            jobQueue=JOB_QUEUE,
            jobDefinition=JOB_DEFINITION,
            containerOverrides={
                "command": [
                    "parallel_transcribe.py",
                    s3_input,
                    s3_output,
                    "0",
                ],
                "environment": [
                    {"name": "TRANSCRIBE_PROMPT", "value": transcribe_prompt},
                ],
            },
        )

        jobs.append(TranscriptionJob(
            job_id=response["jobId"],
            job_name=job_name,
            s3_input_uri=s3_input,
            s3_output_uri=s3_output,
            status="SUBMITTED",
            channel_name=channel_name,
        ))

    return jobs


@transcribe_agent.tool
async def check_job_status(
    ctx: RunContext[TranscribeDeps],
    job_ids: list[str],
) -> dict[str, str]:
    """Check the status of AWS Batch jobs. Returns {job_id: status}."""
    batch = ctx.deps.batch
    statuses = {}

    # Batch describe-jobs accepts up to 100 at a time
    for i in range(0, len(job_ids), 100):
        chunk = job_ids[i:i + 100]
        resp = batch.describe_jobs(jobs=chunk)
        for job in resp.get("jobs", []):
            statuses[job["jobId"]] = job["status"]

    return statuses


@transcribe_agent.tool
async def pull_transcripts(
    ctx: RunContext[TranscribeDeps],
    channel_name: str,
) -> int:
    """Download completed transcripts from S3 to local ~/HD/TRANSCRIPTS/. Returns file count."""
    s3 = ctx.deps.s3
    local_dir = Path.home() / "HD" / "TRANSCRIPTS" / channel_name
    local_dir.mkdir(parents=True, exist_ok=True)

    resp = s3.list_objects_v2(Bucket=OUTPUT_BUCKET, Prefix=f"{channel_name}/")
    downloaded = 0

    for obj in resp.get("Contents", []):
        key = obj["Key"]
        filename = key.rsplit("/", 1)[-1]
        if not filename:
            continue
        local_path = local_dir / filename
        s3.download_file(OUTPUT_BUCKET, key, str(local_path))
        downloaded += 1

    return downloaded
