#!/usr/bin/env python3
"""YouTube transcription worker - download YouTube audio and transcribe via parallel_transcribe.py"""

import json
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import boto3
from botocore.exceptions import ClientError
import yt_dlp

# Force unbuffered output for real-time logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# AWS configuration from environment
S3_INPUT_BUCKET = os.environ.get("S3_INPUT_BUCKET")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "RaTranscriptionJobs")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

if not S3_INPUT_BUCKET:
    print("ERROR: S3_INPUT_BUCKET environment variable not set")
    sys.exit(1)

# Initialize AWS clients
s3_client = boto3.client("s3", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)


def update_file_status(job_id: str, file_id: str, status: str, **kwargs) -> None:
    """Update file status in DynamoDB"""
    update_expr = "SET #status = :status"
    expr_attr_names = {"#status": "status"}
    expr_attr_values = {":status": status}

    # Add optional fields
    optional_fields = {
        "duration": "duration",
        "error": "error_message",
        "video_title": "video_title",
        "channel_name": "channel_name",
        "video_duration": "video_duration",
        "youtube_id": "youtube_id",
    }

    for key, db_field in optional_fields.items():
        if key in kwargs:
            update_expr += f", {db_field} = :{key}"
            expr_attr_values[f":{key}"] = kwargs[key]

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


def download_youtube_audio(youtube_url: str, output_dir: Path) -> tuple[Path, dict]:
    """Download YouTube audio with yt-dlp and return path + metadata"""

    print(f"\n{'='*60}")
    print(f"Downloading YouTube audio: {youtube_url}")
    print(f"{'='*60}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info without downloading first (to get metadata)
            info = ydl.extract_info(youtube_url, download=False)

            # Get metadata
            video_id = info.get('id')
            video_title = info.get('title', 'Unknown Title')
            channel_name = info.get('uploader', 'Unknown Channel')
            duration = info.get('duration', 0)  # seconds

            print(f"Title: {video_title}")
            print(f"Channel: {channel_name}")
            print(f"Duration: {duration}s ({duration/60:.1f} min)")
            print(f"Video ID: {video_id}")

            # Now download
            print("\nDownloading...")
            ydl.download([youtube_url])

            # Find the downloaded file (should be video_id.mp3)
            audio_file = output_dir / f"{video_id}.mp3"

            if not audio_file.exists():
                raise FileNotFoundError(f"Downloaded audio file not found: {audio_file}")

            file_size_mb = audio_file.stat().st_size / 1024 / 1024
            print(f"Downloaded: {audio_file.name} ({file_size_mb:.1f} MB)")

            metadata = {
                'video_id': video_id,
                'video_title': video_title,
                'channel_name': channel_name,
                'duration': duration,
                'file_size_bytes': audio_file.stat().st_size,
            }

            return audio_file, metadata

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "Video unavailable" in error_msg:
            raise RuntimeError(f"Video unavailable: {youtube_url}")
        elif "region" in error_msg.lower():
            raise RuntimeError(f"Video region-restricted: {youtube_url}")
        elif "private" in error_msg.lower():
            raise RuntimeError(f"Video is private: {youtube_url}")
        else:
            raise RuntimeError(f"yt-dlp download failed: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"Failed to download YouTube audio: {e}")


def upload_to_s3(local_path: Path, s3_uri: str) -> None:
    """Upload file to S3"""
    parsed = urlparse(s3_uri)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")

    print(f"\nUploading to S3: s3://{bucket}/{key}")
    file_size_mb = local_path.stat().st_size / 1024 / 1024
    print(f"File size: {file_size_mb:.1f} MB")

    try:
        s3_client.upload_file(str(local_path), bucket, key)
        print(f"Uploaded successfully")
    except ClientError as e:
        raise RuntimeError(f"S3 upload failed: {e}")


def transcribe_youtube(
    youtube_url: str,
    output_s3_uri: str,
    job_id: str,
    file_id: str,
    model_name: str = "large-v3"
) -> int:
    """Download YouTube audio, upload to S3, and transcribe"""

    print(f"\n{'#'*60}")
    print(f"# YOUTUBE TRANSCRIPTION WORKER")
    print(f"# YouTube URL: {youtube_url}")
    print(f"# Output: {output_s3_uri}")
    print(f"# Job ID: {job_id}")
    print(f"# File ID: {file_id}")
    print(f"# Model: {model_name}")
    print(f"# S3 Input Bucket: {S3_INPUT_BUCKET}")
    print(f"# DynamoDB Table: {DYNAMODB_TABLE}")
    print(f"{'#'*60}")

    # Update status to downloading
    update_file_status(job_id, file_id, "downloading")

    # Create temporary directory for audio file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        try:
            # Step 1: Download YouTube audio
            audio_file, metadata = download_youtube_audio(youtube_url, tmpdir_path)

            # Update DynamoDB with video metadata
            update_file_status(
                job_id,
                file_id,
                "uploading",
                video_title=metadata['video_title'],
                channel_name=metadata['channel_name'],
                video_duration=metadata['duration'],
                youtube_id=metadata['video_id'],
            )

            # Step 2: Upload to S3
            s3_key = f"youtube/{job_id}/{file_id}.mp3"
            input_s3_uri = f"s3://{S3_INPUT_BUCKET}/{s3_key}"

            upload_to_s3(audio_file, input_s3_uri)

            # Step 3: Call parallel_transcribe.py
            print(f"\n{'='*60}")
            print(f"Starting transcription via parallel_transcribe.py")
            print(f"{'='*60}")

            script_dir = Path(__file__).parent
            parallel_transcribe_path = script_dir / "parallel_transcribe.py"

            if not parallel_transcribe_path.exists():
                raise FileNotFoundError(f"parallel_transcribe.py not found: {parallel_transcribe_path}")

            # Execute parallel_transcribe.py with subprocess
            cmd = [
                sys.executable,
                str(parallel_transcribe_path),
                input_s3_uri,
                output_s3_uri,
                job_id,
                file_id,
                model_name,
            ]

            print(f"Command: {' '.join(cmd)}\n")

            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            # Print transcription output
            print(result.stdout)

            print(f"\n{'#'*60}")
            print(f"# YOUTUBE TRANSCRIPTION COMPLETE")
            print(f"# File ID: {file_id}")
            print(f"# Video: {metadata['video_title']}")
            print(f"# Channel: {metadata['channel_name']}")
            print(f"{'#'*60}\n")

            return 0

        except subprocess.CalledProcessError as e:
            error_msg = f"Transcription subprocess failed: {e.stdout}"
            print(f"\n✗ {error_msg}")
            update_file_status(job_id, file_id, "failed", error=error_msg)
            return 1

        except RuntimeError as e:
            error_msg = str(e)
            print(f"\n✗ {error_msg}")
            update_file_status(job_id, file_id, "failed", error=error_msg)
            return 1

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(f"\n✗ {error_msg}")
            update_file_status(job_id, file_id, "failed", error=error_msg)
            return 1

        finally:
            # Cleanup happens automatically via tempfile.TemporaryDirectory context manager
            print(f"\nCleaned up temporary files in {tmpdir}")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python youtube_transcribe.py <youtube_url> <output_s3_uri> <job_id> <file_id> [model_name]")
        print("Example: python youtube_transcribe.py https://youtube.com/watch?v=... s3://bucket/output/ job_123 file_456 large-v3")
        print("")
        print("Environment variables:")
        print("  S3_INPUT_BUCKET - Input S3 bucket (required)")
        print("  DYNAMODB_TABLE - DynamoDB table name (default: RaTranscriptionJobs)")
        print("  AWS_REGION - AWS region (default: us-east-1)")
        sys.exit(1)

    youtube_url = sys.argv[1]
    output_s3_uri = sys.argv[2]
    job_id = sys.argv[3]
    file_id = sys.argv[4]
    model_name = sys.argv[5] if len(sys.argv) > 5 else "large-v3"

    exit_code = transcribe_youtube(
        youtube_url, output_s3_uri, job_id, file_id, model_name
    )
    sys.exit(exit_code)
