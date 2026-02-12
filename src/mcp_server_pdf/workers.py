#!/usr/bin/env python3
"""Parallel workers for PDF processing"""

import logging
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List

from .extractors import PDFExtractor
from .ocr import OCRProcessor

logger = logging.getLogger(__name__)


class PageProcessor:
    """Process a single PDF page (extract text/image, OCR if needed)"""

    def __init__(self, pdf_path: Path, output_dir: Path, ocr_language: str = "eng"):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ocr = OCRProcessor(language=ocr_language)

    def process_page(self, page_num: int) -> Dict:
        """Process a single page

        Args:
            page_num: 0-indexed page number

        Returns:
            Dict with status, paths, and extracted text
        """
        try:
            extractor = PDFExtractor(self.pdf_path)

            # Extract text first
            text = extractor.extract_page_text(page_num)
            page_display = page_num + 1  # 1-indexed for display

            # If text is minimal, treat as image page
            if len(text.strip()) < 100:
                logger.info(f"Page {page_display}: Image page detected, extracting image + OCR")

                # Save as PNG
                image_path = self.output_dir / f"page_{page_display:04d}.png"
                extractor.extract_page_image(page_num, image_path)

                # Run OCR
                ocr_text = self.ocr.ocr_image(image_path)

                # Save markdown
                md_path = self.output_dir / f"page_{page_display:04d}.md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(f"# Page {page_display}\n\n")
                    f.write(f"![Page {page_display}](page_{page_display:04d}.png)\n\n")
                    f.write(ocr_text)

                extractor.close()
                return {
                    "page": page_display,
                    "type": "image",
                    "image_path": str(image_path),
                    "markdown_path": str(md_path),
                    "text_length": len(ocr_text),
                    "status": "success"
                }

            else:
                logger.info(f"Page {page_display}: Text page detected, extracting text")

                # Save markdown
                md_path = self.output_dir / f"page_{page_display:04d}.md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(f"# Page {page_display}\n\n")
                    f.write(text)

                extractor.close()
                return {
                    "page": page_display,
                    "type": "text",
                    "markdown_path": str(md_path),
                    "text_length": len(text),
                    "status": "success"
                }

        except Exception as e:
            logger.error(f"Error processing page {page_num + 1}: {e}")
            return {
                "page": page_num + 1,
                "status": "error",
                "error": str(e)
            }


def process_page_worker(args):
    """Worker function for multiprocessing"""
    pdf_path, output_dir, page_num, ocr_language = args
    processor = PageProcessor(pdf_path, output_dir, ocr_language)
    return processor.process_page(page_num)


class PDFWorkerPool:
    """Parallel processing pool for PDF pages"""

    def __init__(self, pdf_path: Path, output_dir: Path, num_workers: int = 4, ocr_language: str = "eng"):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.num_workers = num_workers
        self.ocr_language = ocr_language

        # Get total pages
        extractor = PDFExtractor(pdf_path)
        self.total_pages = extractor.total_pages
        extractor.close()

        logger.info(f"Initialized worker pool: {num_workers} workers, {self.total_pages} pages")

    def process_all(self, progress_callback=None) -> List[Dict]:
        """Process all pages in parallel

        Args:
            progress_callback: Optional callback(completed, total) for progress updates

        Returns:
            List of results for each page
        """
        # Prepare args for each page
        args_list = [
            (self.pdf_path, self.output_dir, page_num, self.ocr_language)
            for page_num in range(self.total_pages)
        ]

        results = []

        with mp.Pool(processes=self.num_workers) as pool:
            for i, result in enumerate(pool.imap(process_page_worker, args_list)):
                results.append(result)

                if progress_callback:
                    progress_callback(i + 1, self.total_pages)

                logger.info(f"Progress: {i + 1}/{self.total_pages} pages processed")

        return results
