#!/usr/bin/env python3
"""MCP Server for PDF Processing and RAG Pipeline

Provides tools for PDF inspection, extraction, OCR, and markdown conversion.
Follows the pattern of mcp_server_ra for consistency.
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Annotated

from mcp.server.fastmcp import FastMCP, Context
from pydantic import Field

from .extractors import PDFExtractor
from .workers import PDFWorkerPool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
PDF_OUTPUT_DIR = PROJECT_ROOT / "pdf_extracted"
PDF_OUTPUT_DIR.mkdir(exist_ok=True)


class PDFProcessingContext:
    """Shared context for PDF processing jobs"""

    def __init__(self):
        self.active_jobs = {}  # job_id -> {pdf_path, status, progress, ...}
        self.worker_pools = {}  # job_id -> PDFWorkerPool instance

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # Cleanup
        logger.info("Cleaning up PDF processing context")


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[PDFProcessingContext]:
    """Lifespan context manager for shared state"""
    ctx = PDFProcessingContext()
    logger.info("PDF Processing MCP Server starting")
    yield ctx
    logger.info("PDF Processing MCP Server shutting down")


# Initialize server
mcp = FastMCP(
    "pdf-processing",
    instructions="""You are an MCP server for PDF processing and RAG pipeline preparation.

Provides tools for:
- Inspecting PDF structure (text vs image pages)
- Extracting pages to markdown + images
- OCR for image-based pages (using Tesseract)
- Parallel processing with worker pools
- Tracking job progress

Designed for PDFs created with vFlat or other scanning apps (typically image-only).
""",
    lifespan=lifespan,
)


# ============================================================================
# INSPECTION TOOLS
# ============================================================================


@mcp.tool()
async def inspect_pdf(
    pdf_path: Annotated[str, Field(description="Full path to PDF file")],
    ctx: Context = None,
) -> str:
    """Inspect PDF structure and analyze page types

    Returns metadata, page count, and breakdown of text vs image pages.
    Use this first to understand what you're working with.
    """
    pdf_path = Path(pdf_path).expanduser()

    if not pdf_path.exists():
        return json.dumps({"error": f"PDF not found: {pdf_path}"}, indent=2)

    try:
        extractor = PDFExtractor(pdf_path)
        inspection = extractor.inspect()
        extractor.close()

        logger.info(f"Inspected PDF: {pdf_path.name} ({inspection['total_pages']} pages)")

        return json.dumps({
            "pdf_path": str(pdf_path),
            "title": inspection["title"],
            "author": inspection["author"],
            "total_pages": inspection["total_pages"],
            "page_type_summary": inspection["type_summary"],
            "note": "Use process_pdf() to extract content with OCR"
        }, indent=2)

    except Exception as e:
        logger.error(f"Error inspecting PDF: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_page_details(
    pdf_path: Annotated[str, Field(description="Full path to PDF file")],
    page_range: Annotated[str, Field(description="Page range (e.g., '1-10' or '5')")] = None,
    ctx: Context = None,
) -> str:
    """Get detailed information about specific pages

    Returns page-by-page breakdown of content type and characteristics.
    Useful for understanding which pages need OCR.
    """
    pdf_path = Path(pdf_path).expanduser()

    if not pdf_path.exists():
        return json.dumps({"error": f"PDF not found: {pdf_path}"}, indent=2)

    try:
        extractor = PDFExtractor(pdf_path)
        inspection = extractor.inspect()

        # Parse page range
        if page_range:
            if '-' in page_range:
                start, end = map(int, page_range.split('-'))
                pages = inspection["page_types"][start-1:end]
            else:
                page_num = int(page_range)
                pages = [inspection["page_types"][page_num-1]]
        else:
            pages = inspection["page_types"][:20]  # First 20 by default

        extractor.close()

        return json.dumps({
            "pdf_path": str(pdf_path),
            "pages": pages,
            "note": f"Showing {len(pages)} pages"
        }, indent=2)

    except Exception as e:
        logger.error(f"Error getting page details: {e}")
        return json.dumps({"error": str(e)}, indent=2)


# ============================================================================
# PROCESSING TOOLS
# ============================================================================


@mcp.tool()
async def process_pdf(
    pdf_path: Annotated[str, Field(description="Full path to PDF file")],
    output_name: Annotated[str, Field(description="Name for output directory (e.g., 'human-design-system')")] = None,
    workers: Annotated[int, Field(description="Number of parallel workers (1-8)", ge=1, le=8)] = 4,
    ocr_language: Annotated[str, Field(description="OCR language code (default: eng)")] = "eng",
    ctx: Context = None,
) -> str:
    """Process entire PDF: extract text, OCR images, save as markdown

    Creates a job that processes all pages in parallel:
    - Text pages → markdown
    - Image pages → PNG + OCR → markdown

    Returns a job_id to track progress.
    """
    pdf_path = Path(pdf_path).expanduser()

    if not pdf_path.exists():
        return json.dumps({"error": f"PDF not found: {pdf_path}"}, indent=2)

    # Create output directory
    if not output_name:
        output_name = pdf_path.stem

    job_id = f"{output_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = PDF_OUTPUT_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create worker pool
        pool = PDFWorkerPool(
            pdf_path=pdf_path,
            output_dir=output_dir,
            num_workers=workers,
            ocr_language=ocr_language,
        )

        # Store in context
        context = ctx.request_context.lifespan_context
        context.active_jobs[job_id] = {
            "pdf_path": str(pdf_path),
            "output_dir": str(output_dir),
            "total_pages": pool.total_pages,
            "workers": workers,
            "status": "running",
            "started": datetime.now().isoformat(),
            "completed_pages": 0,
        }
        context.worker_pools[job_id] = pool

        logger.info(f"Started PDF processing job {job_id}: {pdf_path.name}")

        # Process in background
        def progress_callback(completed, total):
            context.active_jobs[job_id]["completed_pages"] = completed
            logger.info(f"Job {job_id}: {completed}/{total} pages processed")

        # Run synchronously for now (could be async in future)
        results = pool.process_all(progress_callback=progress_callback)

        # Update status
        context.active_jobs[job_id]["status"] = "completed"
        context.active_jobs[job_id]["completed_pages"] = pool.total_pages

        # Generate combined markdown
        combined_md = output_dir / "full_document.md"
        with open(combined_md, "w", encoding="utf-8") as f:
            for result in results:
                if result["status"] == "success" and "markdown_path" in result:
                    md_path = Path(result["markdown_path"])
                    if md_path.exists():
                        f.write(md_path.read_text())
                        f.write("\n\n---\n\n")

        logger.info(f"Job {job_id} completed. Combined markdown: {combined_md}")

        return json.dumps({
            "job_id": job_id,
            "status": "completed",
            "total_pages": pool.total_pages,
            "output_dir": str(output_dir),
            "combined_markdown": str(combined_md),
            "note": "All pages processed. Use get_job_status() for details."
        }, indent=2)

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        if job_id in context.active_jobs:
            context.active_jobs[job_id]["status"] = "failed"
            context.active_jobs[job_id]["error"] = str(e)
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_job_status(
    job_id: Annotated[str, Field(description="Job ID from process_pdf()")],
    ctx: Context = None,
) -> str:
    """Get status of a PDF processing job

    Returns progress, completed pages, and output paths.
    """
    context = ctx.request_context.lifespan_context

    if job_id not in context.active_jobs:
        return json.dumps({"error": f"Job not found: {job_id}"}, indent=2)

    job = context.active_jobs[job_id]

    return json.dumps({
        "job_id": job_id,
        "status": job["status"],
        "progress": {
            "completed": job["completed_pages"],
            "total": job["total_pages"],
            "percent": round(100 * job["completed_pages"] / job["total_pages"], 1) if job["total_pages"] > 0 else 0,
        },
        "output_dir": job["output_dir"],
        "started": job["started"],
    }, indent=2)


@mcp.tool()
async def extract_to_markdown_simple(
    pdf_path: Annotated[str, Field(description="Full path to PDF file")],
    output_path: Annotated[str, Field(description="Where to save markdown file")] = None,
    ctx: Context = None,
) -> str:
    """Quick conversion: Extract entire PDF to markdown using pymupdf4llm

    Faster than process_pdf() but doesn't do OCR or page-by-page processing.
    Good for text-based PDFs or quick previews.
    """
    pdf_path = Path(pdf_path).expanduser()

    if not pdf_path.exists():
        return json.dumps({"error": f"PDF not found: {pdf_path}"}, indent=2)

    if not output_path:
        output_path = PDF_OUTPUT_DIR / f"{pdf_path.stem}.md"
    else:
        output_path = Path(output_path)

    try:
        extractor = PDFExtractor(pdf_path)
        result_path = extractor.extract_to_markdown(output_path)
        extractor.close()

        logger.info(f"Extracted PDF to markdown: {result_path}")

        return json.dumps({
            "pdf_path": str(pdf_path),
            "markdown_path": str(result_path),
            "status": "completed",
            "note": "For better OCR results on image PDFs, use process_pdf()"
        }, indent=2)

    except Exception as e:
        logger.error(f"Error extracting to markdown: {e}")
        return json.dumps({"error": str(e)}, indent=2)


def main():
    """Entry point for MCP server"""
    logger.info("Starting PDF Processing MCP Server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
