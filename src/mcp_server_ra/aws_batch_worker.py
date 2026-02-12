"""AWS Batch worker pool for parallel transcription

Replaces local Docker orchestration with AWS Batch job submission.
Handles S3 upload/download and job monitoring.
"""

import json
import logging
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from datetime import datetime

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

logger = logging.getLogger(__name__)


@dataclass
class AWSBatchJob:
    """Metadata for an AWS Batch transcription job"""
    job_id: str
    series_name: str
    s3_input_bucket: str
    s3_output_bucket: str
    num_workers: int
    model_name: str
    total_files: int
    status: str = "submitted"  # submitted, running, completed, failed
    batch_job_ids: List[str] = field(default_factory=list)
    submitted_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        return asdict(self)


class AWSBatchWorkerPool:
    """Submits transcription jobs to AWS Batch instead of local Docker"""

    def __init__(
        self,
        audio_dir: Path,
        output_dir: Path,
        num_workers: int,
        model_name: str,
        s3_input_bucket: str,
        s3_output_bucket: str,
        job_queue: str,
        job_definition: str,
        job_id: Optional[str] = None,
    ):
        """Initialize AWS Batch worker pool

        Args:
            audio_dir: Local directory containing audio files
            output_dir: Local directory for downloading results
            num_workers: Number of parallel Batch jobs to submit
            model_name: Whisper model name (large-v3, etc)
            s3_input_bucket: S3 bucket name for input audio
            s3_output_bucket: S3 bucket name for output transcripts
            job_queue: AWS Batch job queue name
            job_definition: AWS Batch job definition name (with revision)
            job_id: Optional job ID (auto-generated if not provided)
        """
        if not HAS_BOTO3:
            raise ImportError(
                "boto3 required for AWS Batch support. Install with: pip install boto3"
            )

        self.audio_dir = Path(audio_dir)
        self.output_dir = Path(output_dir)
        self.num_workers = num_workers
        self.model_name = model_name
        self.s3_input_bucket = s3_input_bucket
        self.s3_output_bucket = s3_output_bucket
        self.job_queue = job_queue
        self.job_definition = job_definition
        self.job_id = job_id or f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # AWS clients
        self.batch = boto3.client('batch')
        self.s3 = boto3.client('s3')

        # Get all audio files
        mp3_files = list(self.audio_dir.glob("*.mp3")) + list(
            self.audio_dir.glob("**/*.mp3")
        )
        m4a_files = list(self.audio_dir.glob("*.m4a")) + list(
            self.audio_dir.glob("**/*.m4a")
        )
        self.audio_files = sorted(list(set(mp3_files + m4a_files)))
        self.total_files = len(self.audio_files)

        logger.info(
            f"[{self.job_id}] AWSBatchWorkerPool initialized: {self.total_files} files, "
            f"{num_workers} workers, model={model_name}"
        )

    def _calculate_ranges(self) -> List[tuple]:
        """Calculate start_index and count for each worker

        Same logic as local Docker workers.

        Example: 100 files, 3 workers -> [(0, 34), (34, 33), (67, 33)]
        """
        if self.total_files == 0:
            return []

        ranges = []
        files_per_worker = self.total_files // self.num_workers
        remainder = self.total_files % self.num_workers

        start_idx = 0
        for i in range(self.num_workers):
            count = files_per_worker + (1 if i < remainder else 0)
            ranges.append((start_idx, count))
            start_idx += count

        logger.info(f"[{self.job_id}] Calculated ranges: {ranges}")
        return ranges

    def _upload_audio_to_s3(self, series_name: str):
        """Upload audio files from local directory to S3 input bucket

        Args:
            series_name: Series name for S3 prefix (e.g., "Ra-Uru-Hu-1999-Living-Your-Design-7h")
        """
        # Use series name as S3 prefix (sanitized)
        s3_prefix = series_name.replace(" ", "-").replace("/", "-")

        logger.info(f"[{self.job_id}] Uploading audio to S3...")
        logger.info(f"  Bucket: {self.s3_input_bucket}")
        logger.info(f"  Prefix: {s3_prefix}")
        logger.info(f"  Files: {len(self.audio_files)}")

        uploaded = 0
        for audio_file in self.audio_files:
            s3_key = f"{s3_prefix}/{audio_file.name}"
            logger.debug(f"  Uploading: {audio_file.name}")
            self.s3.upload_file(str(audio_file), self.s3_input_bucket, s3_key)
            uploaded += 1

        logger.info(f"✓ Uploaded {uploaded} files to S3")
        return s3_prefix

    def _submit_batch_job(
        self, worker_id: int, s3_prefix: str, start_index: int, count: int
    ) -> str:
        """Submit a single AWS Batch job for a file range

        Args:
            worker_id: Worker number (0, 1, 2, ...)
            s3_prefix: S3 prefix for input/output
            start_index: Starting file index
            count: Number of files to process

        Returns:
            AWS Batch job ID
        """
        job_name = f"{self.job_id}-worker-{worker_id}"

        # S3 URIs for this job
        s3_input = f"s3://{self.s3_input_bucket}/{s3_prefix}"
        s3_output = f"s3://{self.s3_output_bucket}/{s3_prefix}"

        # Command to run in container
        # parallel_transcribe.py <audio_dir> <output_dir> <start_index> <count> <model> <s3_output>
        command = [
            "python",
            "/workspace/parallel_transcribe.py",
            s3_input,  # Will trigger S3 download in script
            s3_output,  # Will trigger S3 upload in script
            str(start_index),
            str(count),
            self.model_name,
        ]

        response = self.batch.submit_job(
            jobName=job_name,
            jobQueue=self.job_queue,
            jobDefinition=self.job_definition,
            containerOverrides={
                'command': command,
            },
        )

        batch_job_id = response['jobId']
        logger.info(
            f"[{self.job_id}] Submitted Batch job {worker_id+1}/{self.num_workers}: "
            f"files {start_index}-{start_index+count-1} (jobId: {batch_job_id})"
        )

        return batch_job_id

    async def run(self, series_name: str) -> Dict:
        """Upload audio to S3 and submit AWS Batch jobs

        Args:
            series_name: Name of the series (used for S3 prefix)

        Returns:
            {
                "job_id": str,
                "series_name": str,
                "total_files": int,
                "num_workers": int,
                "batch_job_ids": [id1, id2, ...],
                "s3_input": str,
                "s3_output": str,
                "status": "submitted",
                "submitted_at": ISO timestamp
            }
        """
        if self.total_files == 0:
            logger.warning(f"[{self.job_id}] No audio files to transcribe")
            return {
                "job_id": self.job_id,
                "status": "error",
                "error": "No audio files found",
                "total_files": 0,
            }

        # Upload audio files to S3
        s3_prefix = self._upload_audio_to_s3(series_name)

        # Calculate file ranges
        ranges = self._calculate_ranges()

        # Submit Batch jobs
        batch_job_ids = []
        for worker_id, (start_index, count) in enumerate(ranges):
            batch_job_id = self._submit_batch_job(
                worker_id, s3_prefix, start_index, count
            )
            batch_job_ids.append(batch_job_id)

        logger.info(
            f"[{self.job_id}] ✓ Submitted {len(batch_job_ids)} AWS Batch jobs"
        )

        return {
            "job_id": self.job_id,
            "series_name": series_name,
            "total_files": self.total_files,
            "num_workers": self.num_workers,
            "batch_job_ids": batch_job_ids,
            "s3_input": f"s3://{self.s3_input_bucket}/{s3_prefix}",
            "s3_output": f"s3://{self.s3_output_bucket}/{s3_prefix}",
            "status": "submitted",
            "submitted_at": datetime.now().isoformat(),
        }

    def download_transcripts(self, series_name: str):
        """Download completed transcripts from S3 to local output directory

        Args:
            series_name: Series name (used for S3 prefix)
        """
        s3_prefix = series_name.replace(" ", "-").replace("/", "-")

        logger.info(f"[{self.job_id}] Downloading transcripts from S3...")
        logger.info(f"  Bucket: {self.s3_output_bucket}")
        logger.info(f"  Prefix: {s3_prefix}")
        logger.info(f"  Local: {self.output_dir}")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # List objects in S3
        paginator = self.s3.get_paginator('list_objects_v2')
        downloaded = 0

        for page in paginator.paginate(
            Bucket=self.s3_output_bucket, Prefix=s3_prefix
        ):
            for obj in page.get('Contents', []):
                key = obj['Key']
                filename = Path(key).name

                # Download transcript files (.json, .txt)
                if filename.endswith(('.json', '.txt')):
                    local_path = self.output_dir / filename
                    logger.debug(f"  Downloading: {filename}")
                    self.s3.download_file(self.s3_output_bucket, key, str(local_path))
                    downloaded += 1

        logger.info(f"✓ Downloaded {downloaded} files from S3")

    def get_job_status(self, batch_job_ids: List[str]) -> Dict:
        """Query AWS Batch for job status

        Args:
            batch_job_ids: List of AWS Batch job IDs

        Returns:
            {
                "job_id": str,
                "batch_jobs": [
                    {"jobId": str, "jobName": str, "status": str, "statusReason": str},
                    ...
                ],
                "overall_status": "SUBMITTED" | "PENDING" | "RUNNABLE" | "RUNNING" | "SUCCEEDED" | "FAILED"
            }
        """
        if not batch_job_ids:
            return {"job_id": self.job_id, "overall_status": "NO_JOBS"}

        # Describe jobs
        response = self.batch.describe_jobs(jobs=batch_job_ids)

        job_statuses = []
        all_succeeded = True
        any_failed = False
        any_running = False

        for job in response['jobs']:
            status = job['status']
            job_statuses.append(
                {
                    "jobId": job['jobId'],
                    "jobName": job['jobName'],
                    "status": status,
                    "statusReason": job.get('statusReason', ''),
                }
            )

            if status != 'SUCCEEDED':
                all_succeeded = False
            if status == 'FAILED':
                any_failed = True
            if status in ('PENDING', 'RUNNABLE', 'RUNNING', 'STARTING'):
                any_running = True

        # Determine overall status
        if all_succeeded:
            overall_status = "SUCCEEDED"
        elif any_failed:
            overall_status = "FAILED"
        elif any_running:
            overall_status = "RUNNING"
        else:
            overall_status = "SUBMITTED"

        return {
            "job_id": self.job_id,
            "batch_jobs": job_statuses,
            "overall_status": overall_status,
        }
