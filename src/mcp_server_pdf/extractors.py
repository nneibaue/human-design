#!/usr/bin/env python3
"""PDF extraction utilities for text, images, and metadata"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import fitz  # PyMuPDF
import pymupdf4llm
from PIL import Image

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract content from PDFs with automatic text/image detection"""

    def __init__(self, pdf_path: Path):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        self.doc = fitz.open(self.pdf_path)
        self.total_pages = len(self.doc)
        logger.info(f"Opened PDF: {pdf_path} ({self.total_pages} pages)")

    def inspect(self) -> Dict:
        """Analyze PDF structure and content types"""
        metadata = self.doc.metadata

        page_types = []
        for page_num in range(self.total_pages):
            page = self.doc[page_num]
            text = page.get_text().strip()
            images = page.get_images()

            # Classify page type
            if len(text) > 100:
                page_type = "text"
            elif images:
                page_type = "image"
            else:
                page_type = "mixed" if text else "empty"

            page_types.append({
                "page": page_num + 1,
                "type": page_type,
                "text_length": len(text),
                "image_count": len(images),
            })

        # Summary stats
        type_counts = {}
        for pt in page_types:
            t = pt["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "title": metadata.get("title", "Unknown"),
            "author": metadata.get("author", "Unknown"),
            "total_pages": self.total_pages,
            "page_types": page_types,
            "type_summary": type_counts,
        }

    def extract_page_text(self, page_num: int) -> str:
        """Extract text from a specific page"""
        if page_num < 0 or page_num >= self.total_pages:
            raise ValueError(f"Invalid page number: {page_num} (total: {self.total_pages})")

        page = self.doc[page_num]
        text = page.get_text()
        logger.info(f"Extracted text from page {page_num + 1}: {len(text)} chars")
        return text

    def extract_page_image(self, page_num: int, output_path: Path, dpi: int = 300) -> Path:
        """Render page to PNG image"""
        if page_num < 0 or page_num >= self.total_pages:
            raise ValueError(f"Invalid page number: {page_num}")

        page = self.doc[page_num]

        # Calculate zoom for DPI
        # PyMuPDF default is 72 DPI, so zoom = target_dpi / 72
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)

        pix = page.get_pixmap(matrix=mat)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        pix.save(str(output_path))
        logger.info(f"Saved page {page_num + 1} as image: {output_path}")
        return output_path

    def extract_to_markdown(self, output_path: Path, page_range: Optional[tuple] = None) -> Path:
        """Extract entire PDF to markdown using pymupdf4llm

        Args:
            output_path: Where to save the markdown file
            page_range: Optional (start, end) tuple for page range (1-indexed)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # pymupdf4llm expects page numbers to be 0-indexed
        if page_range:
            start, end = page_range
            # Convert 1-indexed to 0-indexed
            start_page = start - 1
            end_page = min(end, self.total_pages)
            logger.info(f"Converting pages {start} to {end} to markdown")
        else:
            start_page = 0
            end_page = self.total_pages
            logger.info(f"Converting all {self.total_pages} pages to markdown")

        # Extract markdown
        md_text = pymupdf4llm.to_markdown(
            str(self.pdf_path),
            pages=list(range(start_page, end_page)),
            write_images=True,
            image_path=str(output_path.parent / "images"),
        )

        # Save to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_text)

        logger.info(f"Saved markdown to {output_path}")
        return output_path

    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()
            logger.info(f"Closed PDF: {self.pdf_path}")
