"""Worker pool coordinator for parallel transcription

Manages spawning and coordinating parallel worker processes to transcribe
audio files in parallel ranges. Each worker gets a subset of files to process.

Currently uses subprocess with faster-whisper (CPU-based).
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionJob:
    """Metadata for a transcription job"""
    job_id: str
    series_name: str
    audio_dir: str  # Stored as string for JSON serialization
    output_dir: str
    num_workers: int
    model_name: str
    total_files: int
    status: str = "queued"  # queued, running, completed, completed_with_errors, failed
    completed_files: int = 0
    failed_files: int = 0
    error_log: List[str] = field(default_factory=list)
    worker_pids: List[int] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        return asdict(self)


class WorkerPool:
    """Manages a pool of parallel Docker containers for transcription"""
    
    DOCKER_IMAGE = "ra-transcribe:latest"
    
    def __init__(
        self,
        audio_dir: Path,
        output_dir: Path,
        num_workers: int = 3,
        model_name: str = "large-v3",
        model_dir: Optional[Path] = None,
        job_id: Optional[str] = None,
    ):
        self.audio_dir = Path(audio_dir)
        self.output_dir = Path(output_dir)
        self.num_workers = num_workers
        self.model_name = model_name
        self.model_dir = Path(model_dir) if model_dir else None
        self.job_id = job_id or f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Get all audio files from direct and nested directories
        mp3_files = list(self.audio_dir.glob("*.mp3")) + list(self.audio_dir.glob("**/*.mp3"))
        m4a_files = list(self.audio_dir.glob("*.m4a")) + list(self.audio_dir.glob("**/*.m4a"))
        self.audio_files = sorted(list(set(mp3_files + m4a_files)))  # Deduplicate and sort
        self.total_files = len(self.audio_files)
        self.container_ids: List[str] = []

        logger.info(
            f"[{self.job_id}] WorkerPool initialized (Docker): {self.total_files} files, "
            f"{num_workers} containers, model={model_name}"
        )
    
    def _calculate_ranges(self) -> List[tuple]:
        """Calculate start_index and count for each worker
        
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
    
    def _get_parallel_transcribe_script(self) -> Path:
        """Locate the parallel_transcribe.py script in workspace root"""
        script_path = Path(__file__).parent.parent.parent / "parallel_transcribe.py"
        if not script_path.exists():
            raise FileNotFoundError(f"parallel_transcribe.py not found at {script_path}")
    
    def _get_parallel_transcribe_script(self) -> Path:
        """Locate the parallel_transcribe.py script in workspace root"""
        script_path = Path(__file__).parent.parent.parent / "parallel_transcribe.py"
        if not script_path.exists():
            raise FileNotFoundError(f"parallel_transcribe.py not found at {script_path}")
        return script_path
    
    async def run(self) -> Dict:
        """Spawn all Docker containers and coordinate transcription.
        
        Starts N Docker containers, each processing a range of audio files
        using faster-whisper. Returns job metadata for tracking.
        
        Returns:
            {
                "job_id": str,
                "total_files": int,
                "num_workers": int,
                "ranges": [(start, count), ...],
                "status": "running",
                "container_ids": [id1, id2, ...],
                "started_at": ISO timestamp
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
        
        ranges = self._calculate_ranges()
        script_path = self._get_parallel_transcribe_script()
        
        logger.info(f"[{self.job_id}] Starting {self.num_workers} Docker containers for {self.total_files} files")
        logger.info(f"[{self.job_id}] Audio directory: {self.audio_dir}")
        logger.info(f"[{self.job_id}] Output directory: {self.output_dir}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        container_ids = []
        
        # Spawn a Docker container for each range
        for worker_id, (start_index, count) in enumerate(ranges):
            container_name = f"{self.job_id}-worker-{worker_id}"
            
            cmd = [
                "docker", "run",
                "--rm",  # Remove container when done
                "-v", f"{self.audio_dir}:/workspace/audio:ro",  # Mount audio (read-only)
                "-v", f"{self.output_dir}:/workspace/output",  # Mount output
            ]

            # Mount model directory if provided (avoids re-downloading)
            if self.model_dir:
                cmd.extend(["-v", f"{self.model_dir}:/root/.cache/huggingface:ro"])

            cmd.extend([
                "--name", container_name,
                self.DOCKER_IMAGE,
                "/workspace/parallel_transcribe.py",
                "/workspace/audio",
                "/workspace/output",
                str(start_index),
                str(count),
                self.model_name,
            ])
            
            # Log file for this container
            log_path = self.output_dir / f"worker_{worker_id}.log"
            
            try:
                logger.info(
                    f"[{self.job_id}] Spawning Docker container {worker_id+1}/{self.num_workers}: "
                    f"files {start_index}-{start_index+count-1}"
                )
                
                with open(log_path, "w") as log_file:
                    proc = subprocess.Popen(
                        cmd,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        text=True,
                    )
                
                # For Docker, we track the process but also need the container_id
                # Container ID comes from docker inspect, but we use process for monitoring
                self.container_ids.append(container_name)
                logger.info(f"[{self.job_id}] Container {worker_id+1} launched: {container_name}")
                
            except Exception as e:
                logger.error(f"[{self.job_id}] Failed to spawn container {worker_id+1}: {e}")
                raise
        
        return {
            "job_id": self.job_id,
            "total_files": self.total_files,
            "num_workers": self.num_workers,
            "ranges": ranges,
            "status": "running",
            "container_ids": self.container_ids,
            "started_at": datetime.now().isoformat(),
        }

    def get_progress(self) -> Dict:
        """Poll worker status and count completed output files.
        
        Returns:
            {
                "job_id": str,
                "total_files": int,
                "completed_files": int,
                "failed_files": int,
                "percent_complete": float,
                "status": "running" | "completed" | "completed_with_errors",
                "worker_statuses": [{"pid": int, "running": bool, "return_code": int}, ...],
            }
        """
        # Count completed output files (one .json per successfully transcribed file)
        completed = 0
        failed = 0
        
        for audio_file in self.audio_files:
            json_path = self.output_dir / f"{audio_file.stem}.json"
            if json_path.exists():
                completed += 1
        
        # Check worker process status
        worker_statuses = []
        all_done = True
        
        for i, proc in enumerate(self.processes):
            poll_result = proc.poll()
            is_running = poll_result is None
            worker_statuses.append({
                "worker_id": i,
                "pid": proc.pid,
                "running": is_running,
                "return_code": poll_result,
            })
            if is_running:
                all_done = False
        
        # Determine overall status
        if all_done:
            status = "completed" if failed == 0 else "completed_with_errors"
        else:
            status = "running"
        
        percent = (completed / self.total_files * 100) if self.total_files > 0 else 0
        
        logger.debug(
            f"[{self.job_id}] Progress: {completed}/{self.total_files} "
            f"({percent:.1f}%) - {status}"
        )
        
        return {
            "job_id": self.job_id,
            "total_files": self.total_files,
            "completed_files": completed,
            "failed_files": failed,
            "percent_complete": percent,
            "status": status,
            "worker_statuses": worker_statuses,
        }

    def terminate(self):
        """Stop all worker processes"""
        logger.info(f"[{self.job_id}] Terminating {len(self.processes)} workers...")
        for i, proc in enumerate(self.processes):
            if proc.poll() is None:  # Still running
                proc.terminate()
                logger.info(f"[{self.job_id}] Terminated worker {i+1} (PID {proc.pid})")
        
        # Give processes time to terminate gracefully
        for i, proc in enumerate(self.processes):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                logger.warning(f"[{self.job_id}] Force-killed worker {i+1} (PID {proc.pid})")
