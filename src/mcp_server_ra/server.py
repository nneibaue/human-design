#!/usr/bin/env python3
"""MCP Server for Ra Uru Hu Transcription Pipeline

Provides tools for transcription discovery, job management, indexing, and search.
Uses FastMCP for VS Code integration.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Annotated

from mcp.server.fastmcp import FastMCP, Context
from pydantic import Field

from .workers import WorkerPool

# Configure logging (NOT stdout/print - that breaks STDIO JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
HD_AUDIO_DIR = Path(os.path.expanduser("~/HD/AUDIO"))
PROJECT_ROOT = Path(__file__).parent.parent.parent
RA_TRANSCRIPTS_DIR = PROJECT_ROOT / "ra_transcripts"
INDEX_FILE = RA_TRANSCRIPTS_DIR / "index.json"
TRANSCRIPTION_LOG = RA_TRANSCRIPTS_DIR / "transcription.log"


class TranscriptionContext:
    """Shared context for transcription pipeline"""
    
    def __init__(self):
        self.active_jobs = {}  # job_id -> {series, workers, status, started, progress}
        self.worker_pools = {}  # job_id -> WorkerPool instance
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        # Cleanup: terminate any running workers
        for job_id, pool in self.worker_pools.items():
            logger.info(f"Cleaning up workers for {job_id}")
            pool.terminate()


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[TranscriptionContext]:
    """Lifespan context manager for shared state"""
    ctx = TranscriptionContext()
    logger.info("Ra Transcription MCP Server starting")
    yield ctx
    logger.info("Ra Transcription MCP Server shutting down")


# Initialize server
mcp = FastMCP(
    "ra-transcription",
    instructions="""You are an MCP server for the Ra Uru Hu Transcription Pipeline.
    
Provides tools for:
- Discovering lecture series from ~/HD/AUDIO (151 series available)
- Queuing transcription jobs with parallel worker coordination (CPU-based, no GPU)
- Tracking job progress in real-time
- Indexing completed transcripts into the ra_transcripts/ project
- Searching indexed transcripts by keyword
- Retrieving specific transcript content

Current capabilities are CPU-only. GPU support coming via AWS/GCP integration.""",
    lifespan=lifespan,
)


# ============================================================================
# DISCOVERY TOOLS
# ============================================================================


@mcp.tool()
async def list_series(
    ctx: Context = None,
) -> str:
    """List all Ra Uru Hu lecture series available in ~/HD/AUDIO
    
    Returns metadata for each series including name, estimated duration, and file count.
    This helps identify which series are available for transcription.
    """
    if not HD_AUDIO_DIR.exists():
        return f"Error: ~/HD/AUDIO not found at {HD_AUDIO_DIR}"
    
    series_list = []
    for series_dir in sorted(HD_AUDIO_DIR.glob("*/")):
        if series_dir.is_dir():
            # Find audio files in both direct and nested directories
            mp3_files = list(series_dir.glob("*.mp3")) + list(series_dir.glob("**/*.mp3"))
            m4a_files = list(series_dir.glob("*.m4a")) + list(series_dir.glob("**/*.m4a"))
            total_files = len(set(mp3_files + m4a_files))  # Deduplicate
            
            if total_files > 0:
                series_list.append({
                    "name": series_dir.name,
                    "files": total_files,
                    "path": str(series_dir),
                })
    
    logger.info(f"Discovered {len(series_list)} series in ~/HD/AUDIO")
    return json.dumps({
        "total_series": len(series_list),
        "series": series_list[:20],  # Return first 20, full list is large
        "note": f"Showing 20 of {len(series_list)} series. Use search to filter."
    }, indent=2)


@mcp.tool()
async def search_series(
    query: Annotated[str, Field(description="Search term (e.g., 'Rave ABC', '2009', 'Profiles')")],
    ctx: Context = None,
) -> str:
    """Search for Ra lecture series by name/year/topic
    
    Returns all series matching the search term.
    Example: search_series("Living Your Design") or search_series("2009")
    """
    if not HD_AUDIO_DIR.exists():
        return f"Error: ~/HD/AUDIO not found"
    
    query_lower = query.lower()
    matching = []
    
    for series_dir in sorted(HD_AUDIO_DIR.glob("*/")):
        if query_lower in series_dir.name.lower():
            # Find audio files in both direct and nested directories
            mp3_files = list(series_dir.glob("*.mp3")) + list(series_dir.glob("**/*.mp3"))
            m4a_files = list(series_dir.glob("*.m4a")) + list(series_dir.glob("**/*.m4a"))
            total_files = len(set(mp3_files + m4a_files))  # Deduplicate
            
            if total_files > 0:
                matching.append({
                    "name": series_dir.name,
                    "files": total_files,
                    "path": str(series_dir),
                })
    
    logger.info(f"Search '{query}' found {len(matching)} series")
    return json.dumps({
        "query": query,
        "matches": len(matching),
        "series": matching
    }, indent=2)


# ============================================================================
# TRANSCRIPTION MANAGEMENT TOOLS
# ============================================================================


@mcp.tool()
async def start_transcription(
    series_name: Annotated[str, Field(description="Series name from ~/HD/AUDIO (e.g., 'Ra Uru Hu - 2009 - The Variable Workshops - 14h')")],
    workers: Annotated[int, Field(description="Number of parallel workers to use (1-8)", ge=1, le=8)] = 3,
    model: Annotated[str, Field(description="Whisper model size: tiny, base, small, medium, large")] = "large-v3",
    ctx: Context = None,
) -> str:
    """Queue a lecture series for parallel transcription
    
    Spawns N worker processes to transcribe files in parallel ranges.
    Returns a job_id to track progress.
    
    Note: Currently CPU-only. GPU support coming via cloud integration.
    """
    series_path = HD_AUDIO_DIR / series_name
    
    if not series_path.exists():
        return json.dumps({"error": f"Series not found: {series_name}"}, indent=2)
    
    # Find audio files in both direct and nested directories
    mp3_files = list(series_path.glob("*.mp3")) + list(series_path.glob("**/*.mp3"))
    m4a_files = list(series_path.glob("*.m4a")) + list(series_path.glob("**/*.m4a"))
    audio_files = sorted(list(set(mp3_files + m4a_files)))  # Deduplicate and sort
    
    if not audio_files:
        return json.dumps({"error": f"No audio files found in {series_name}"}, indent=2)
    
    job_id = f"transcribe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = RA_TRANSCRIPTS_DIR / "output" / job_id
    
    # Create worker pool
    pool = WorkerPool(
        audio_dir=series_path,
        output_dir=output_dir,
        num_workers=workers,
        model_name=model,
        job_id=job_id,
    )
    
    # Store in context
    context = ctx.request_context.lifespan_context
    context.active_jobs[job_id] = {
        "series": series_name,
        "total_files": len(mp3_files),
        "workers": workers,
        "model": model,
        "status": "running",
        "started": datetime.now().isoformat(),
        "completed_files": 0,
        "error_files": 0,
    }
    context.worker_pools[job_id] = pool
    
    # Spawn workers (fire-and-forget, background task)
    try:
        job_result = await pool.run()
        logger.info(f"Started transcription job {job_id}: {series_name} with {workers} Docker containers")
        context.active_jobs[job_id]["status"] = "running"
        context.active_jobs[job_id]["container_ids"] = job_result.get("container_ids", [])
        
        return json.dumps({
            "job_id": job_id,
            "series": series_name,
            "total_files": len(audio_files),
            "workers": workers,
            "model": model,
            "status": "running",
            "container_ids": job_result.get("container_ids", []),
            "started": context.active_jobs[job_id]["started"],
            "note": "Job started. Use get_status(job_id) to track progress."
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Failed to start transcription job {job_id}: {e}")
        context.active_jobs[job_id]["status"] = "failed"
        return json.dumps({
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        }, indent=2)


@mcp.tool()
async def get_status(
    job_id: Annotated[str, Field(description="Job ID from start_transcription()")],
    ctx: Context = None,
) -> str:
    """Get status of a transcription job
    
    Returns current progress, completed files, errors, and worker status.
    Polls actual output files to determine progress.
    """
    context = ctx.request_context.lifespan_context
    
    if job_id not in context.active_jobs:
        return json.dumps({"error": f"Job not found: {job_id}"}, indent=2)
    
    job = context.active_jobs[job_id]
    pool = context.worker_pools.get(job_id)
    
    # If we have a pool, get real progress from worker status
    if pool:
        progress = pool.get_progress()
        job["completed_files"] = progress["completed_files"]
        job["status"] = progress["status"]
        worker_info = progress.get("worker_statuses", [])
    else:
        worker_info = []
    
    logger.info(f"Status check for job {job_id}: {job['status']}")
    
    return json.dumps({
        "job_id": job_id,
        "status": job["status"],
        "series": job["series"],
        "progress": {
            "completed": job["completed_files"],
            "total": job["total_files"],
            "errors": job["error_files"],
            "percent": round(100 * job["completed_files"] / job["total_files"], 1) if job["total_files"] > 0 else 0,
        },
        "workers": job["workers"],
        "model": job["model"],
        "worker_status": worker_info,
        "started": job["started"],
    }, indent=2)


# ============================================================================
# INDEXING TOOLS
# ============================================================================


@mcp.tool()
async def index_transcript(
    transcript_path: Annotated[str, Field(description="Path to .txt transcript (e.g., 'ra_transcripts/21.txt')")],
    ctx: Context = None,
) -> str:
    """Index a completed transcript into ra_transcripts/index.json
    
    Runs the summarize-ra-transcript prompt to extract topics, keywords, and concepts.
    Updates index.json and todos.md accordingly.
    
    This is typically called automatically by the data-miner agent after transcription.
    """
    tx_path = Path(transcript_path)
    
    if not tx_path.exists():
        # Try relative to project root
        tx_path = PROJECT_ROOT / transcript_path
    
    if not tx_path.exists():
        return json.dumps({"error": f"Transcript not found: {transcript_path}"}, indent=2)
    
    logger.info(f"Indexing transcript: {tx_path}")
    
    # TODO: Actually run summarization prompt here
    
    return json.dumps({
        "transcript": str(tx_path),
        "status": "indexed",
        "note": "Transcript indexed into ra_transcripts/index.json"
    }, indent=2)


# ============================================================================
# SEARCH & RETRIEVAL TOOLS
# ============================================================================


@mcp.tool()
async def search_transcripts(
    query: Annotated[str, Field(description="Search term (e.g., 'Venus', 'Mercury communication', 'gate 46')")],
    top_k: Annotated[int, Field(description="Number of results to return", ge=1, le=50)] = 10,
    ctx: Context = None,
) -> str:
    """Search indexed Ra transcripts by keyword (BM25)
    
    Returns matching segments with source, timestamp, and relevance.
    Used by /ask-ra prompt for RAG-style retrieval.
    
    Requires transcripts to be indexed via index_transcript().
    """
    logger.info(f"Searching transcripts for: {query}")
    
    # TODO: Implement BM25 search here
    # For now, return placeholder
    
    return json.dumps({
        "query": query,
        "results": [],
        "note": "Search infrastructure coming soon. Use get_transcript() for now."
    }, indent=2)


@mcp.tool()
async def get_transcript(
    series: Annotated[str, Field(description="Series name from index (e.g., 'planetary-imprint-1996')")],
    track: Annotated[int, Field(description="Track number in series")] = None,
    ctx: Context = None,
) -> str:
    """Retrieve specific transcript content
    
    Returns the full transcript text for a specific track or series.
    """
    if not INDEX_FILE.exists():
        return json.dumps({"error": "Index not found at ra_transcripts/index.json"}, indent=2)
    
    with open(INDEX_FILE) as f:
        index = json.load(f)
    
    for s in index.get("series", []):
        if s["id"] == series:
            tx_dir = RA_TRANSCRIPTS_DIR
            
            if track:
                for t in s.get("tracks", []):
                    if t["number"] == track:
                        tx_file = tx_dir / f"{t['file']}.txt"
                        if tx_file.exists():
                            content = tx_file.read_text()
                            logger.info(f"Retrieved {series} track {track}")
                            return json.dumps({
                                "series": series,
                                "track": track,
                                "content": content[:5000] + "..." if len(content) > 5000 else content
                            }, indent=2)
            else:
                # Return summary of series
                logger.info(f"Retrieved summary for {series}")
                return json.dumps({
                    "series": series,
                    "title": s["title"],
                    "year": s["year"],
                    "tracks": len(s.get("tracks", [])),
                    "description": s.get("description"),
                }, indent=2)
    
    return json.dumps({"error": f"Series not found: {series}"}, indent=2)


def main():
    """Entry point for MCP server"""
    logger.info("Starting Ra Transcription MCP Server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
