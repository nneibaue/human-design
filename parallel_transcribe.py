#!/usr/bin/env python3
"""AWS Batch transcription worker - transcribe audio from S3 and update DynamoDB"""

import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from faster_whisper import WhisperModel
import boto3
from botocore.exceptions import ClientError

# Force unbuffered output for real-time logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# AWS configuration from environment
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "RaTranscriptionJobs")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Initialize AWS clients
s3_client = boto3.client("s3", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

# Human Design terminology prompt to improve transcription accuracy
HD_PROMPT = """
Human Design lecture by Ra Uru Hu. Terms include: Manifestor, Generator,
Manifesting Generator, Projector, Reflector, bodygraph, gates, channels,
centers, defined, undefined, open centers, strategy, authority, sacral authority,
emotional authority, splenic authority, profile, incarnation cross, I Ching,
hexagram, Rave cosmology, conditioning, not-self, deconditioning, aura,
planetary imprint, Moon, Sun, Earth, nodes, design, personality, unconscious,
conscious, transit, penta, composite, definition, split definition, single definition,
triple split, quadruple split, no definition, lines, colors, tones, bases.
"""


def parse_s3_uri(s3_uri: str) -> tuple[str, str]:
    """Parse S3 URI into bucket and key"""
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3":
        raise ValueError(f"Invalid S3 URI: {s3_uri}")
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    return bucket, key


def download_from_s3(s3_uri: str, local_path: Path) -> None:
    """Download file from S3 to local path"""
    bucket, key = parse_s3_uri(s3_uri)
    print(f"Downloading s3://{bucket}/{key} to {local_path}")
    s3_client.download_file(bucket, key, str(local_path))
    print(f"Downloaded {local_path.stat().st_size / 1024 / 1024:.1f} MB")


def upload_to_s3(local_path: Path, s3_uri: str) -> None:
    """Upload file from local path to S3"""
    bucket, key = parse_s3_uri(s3_uri)
    print(f"Uploading {local_path} to s3://{bucket}/{key}")
    s3_client.upload_file(str(local_path), bucket, key)
    print(f"Uploaded {local_path.stat().st_size / 1024:.1f} KB")


def update_file_status(job_id: str, file_id: str, status: str, **kwargs) -> None:
    """Update file status in DynamoDB"""
    update_expr = "SET #status = :status"
    expr_attr_names = {"#status": "status"}
    expr_attr_values = {":status": status}

    # Add optional fields
    if "duration" in kwargs:
        update_expr += ", duration = :duration"
        expr_attr_values[":duration"] = kwargs["duration"]
    if "error" in kwargs:
        update_expr += ", error_message = :error"
        expr_attr_values[":error"] = kwargs["error"]
    if "transcript_s3" in kwargs:
        update_expr += ", transcript_s3 = :transcript_s3"
        expr_attr_values[":transcript_s3"] = kwargs["transcript_s3"]
    if "segments_s3" in kwargs:
        update_expr += ", segments_s3 = :segments_s3"
        expr_attr_values[":segments_s3"] = kwargs["segments_s3"]

    # Always update timestamp
    update_expr += ", updated_at = :updated_at"
    expr_attr_values[":updated_at"] = datetime.utcnow().isoformat()

    try:
        table.update_item(
            Key={"job_id": job_id, "file_id": file_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
        )
        print(f"Updated DynamoDB: {job_id}/{file_id} → {status}")
    except ClientError as e:
        print(f"Warning: Failed to update DynamoDB: {e}")
        # Don't fail the whole job if DynamoDB update fails


def transcribe_file_from_s3(
    model: WhisperModel,
    input_s3_uri: str,
    output_s3_base: str,
    job_id: str,
    file_id: str,
) -> dict:
    """Transcribe audio file from S3 and upload results"""

    print(f"\n{'='*60}")
    print(f"Transcribing: {input_s3_uri}")
    print(f"Job ID: {job_id}, File ID: {file_id}")
    print(f"{'='*60}")

    # Update status to transcribing
    update_file_status(job_id, file_id, "transcribing")

    # Create temporary directory for downloads/uploads
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        local_audio = tmpdir_path / "input.mp3"

        try:
            # Download from S3
            download_from_s3(input_s3_uri, local_audio)

            start_time = datetime.now()

            # Transcribe with VAD filtering and HD terminology prompt
            segments, info = model.transcribe(
                str(local_audio),
                beam_size=5,
                vad_filter=True,
                initial_prompt=HD_PROMPT,
            )

            # Collect segments
            all_segments = []
            full_text_lines = []

            for segment in segments:
                seg_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                }
                all_segments.append(seg_data)
                full_text_lines.append(
                    f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text.strip()}"
                )
                print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text.strip()}")

            elapsed = (datetime.now() - start_time).total_seconds()

            # Prepare result
            result = {
                "file_id": file_id,
                "job_id": job_id,
                "input_s3_uri": input_s3_uri,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration_seconds": info.duration,
                "transcription_time_seconds": elapsed,
                "segments": all_segments
            }

            # Save outputs to temporary files
            json_path = tmpdir_path / f"{file_id}.json"
            txt_path = tmpdir_path / f"{file_id}.txt"

            # Save JSON with metadata and timestamps
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            # Save plain text with timestamps
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"# File: {file_id}\n")
                f.write(f"# Job: {job_id}\n")
                f.write(f"# Language: {info.language} (confidence: {info.language_probability:.2%})\n")
                f.write(f"# Duration: {info.duration:.1f}s\n\n")
                f.write("\n".join(full_text_lines))

            # Upload to S3
            # Ensure output_s3_base ends with /
            if not output_s3_base.endswith("/"):
                output_s3_base += "/"

            segments_s3_uri = f"{output_s3_base}{file_id}.json"
            transcript_s3_uri = f"{output_s3_base}{file_id}.txt"

            upload_to_s3(json_path, segments_s3_uri)
            upload_to_s3(txt_path, transcript_s3_uri)

            print(f"\n✓ Completed in {elapsed:.1f}s")
            print(f"  Duration: {info.duration:.1f}s")
            print(f"  Segments: {segments_s3_uri}")
            print(f"  Transcript: {transcript_s3_uri}")

            # Update status to completed with S3 URIs
            update_file_status(
                job_id,
                file_id,
                "completed",
                duration=info.duration,
                segments_s3=segments_s3_uri,
                transcript_s3=transcript_s3_uri,
            )

            return result

        except Exception as e:
            error_msg = f"Transcription failed: {e}"
            print(f"\n✗ {error_msg}")
            update_file_status(job_id, file_id, "failed", error=error_msg)
            raise


def transcribe_from_batch(
    input_s3_uri: str,
    output_s3_base: str,
    job_id: str,
    file_id: str,
    model_name: str = "large-v3"
):
    """Transcribe single audio file from S3 (AWS Batch worker)"""

    print(f"\n{'#'*60}")
    print(f"# AWS BATCH TRANSCRIPTION WORKER")
    print(f"# Input: {input_s3_uri}")
    print(f"# Output: {output_s3_base}")
    print(f"# Job ID: {job_id}")
    print(f"# File ID: {file_id}")
    print(f"# Model: {model_name} (CPU)")
    print(f"# DynamoDB Table: {DYNAMODB_TABLE}")
    print(f"{'#'*60}")

    # Load model
    print(f"\nLoading model: {model_name}...")
    total_start = datetime.now()
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    model_load_time = (datetime.now() - total_start).total_seconds()
    print(f"Model loaded in {model_load_time:.1f}s!\n")

    # Transcribe
    try:
        result = transcribe_file_from_s3(
            model, input_s3_uri, output_s3_base, job_id, file_id
        )
        total_elapsed = (datetime.now() - total_start).total_seconds()

        # Summary
        print(f"\n\n{'#'*60}")
        print(f"# WORKER COMPLETE")
        print(f"# File: {file_id}")
        print(f"# Duration: {result['duration_seconds']:.1f}s")
        print(f"# Transcription: {result['transcription_time_seconds']:.1f}s")
        print(f"# Total time: {total_elapsed:.1f}s")
        print(f"{'#'*60}\n")

        return 0

    except Exception as e:
        print(f"\n\n{'#'*60}")
        print(f"# WORKER FAILED")
        print(f"# File: {file_id}")
        print(f"# Error: {e}")
        print(f"{'#'*60}\n")
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python parallel_transcribe.py <input_s3_uri> <output_s3_uri> <job_id> <file_id> [model_name]")
        print("Example: python parallel_transcribe.py s3://bucket/input.mp3 s3://bucket/output/ job_123 file_456 large-v3")
        print("")
        print("Environment variables:")
        print("  DYNAMODB_TABLE - DynamoDB table name (default: RaTranscriptionJobs)")
        print("  AWS_REGION - AWS region (default: us-east-1)")
        sys.exit(1)

    input_s3_uri = sys.argv[1]
    output_s3_base = sys.argv[2]
    job_id = sys.argv[3]
    file_id = sys.argv[4]
    model_name = sys.argv[5] if len(sys.argv) > 5 else "large-v3"

    exit_code = transcribe_from_batch(
        input_s3_uri, output_s3_base, job_id, file_id, model_name
    )
    sys.exit(exit_code)
