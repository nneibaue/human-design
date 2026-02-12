#!/usr/bin/env python3
"""OCR utilities for image-based PDF pages"""

import logging
from pathlib import Path

import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Perform OCR on images using Tesseract"""

    def __init__(self, language: str = "eng"):
        """
        Args:
            language: Tesseract language code (default: eng)
        """
        self.language = language

        # Check if tesseract is available
        try:
            pytesseract.get_tesseract_version()
            logger.info(f"Tesseract available, using language: {language}")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
            logger.warning("Install with: sudo apt-get install tesseract-ocr")

    def ocr_image(self, image_path: Path) -> str:
        """Perform OCR on an image file

        Args:
            image_path: Path to image file (PNG, JPG, etc.)

        Returns:
            Extracted text
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        logger.info(f"Running OCR on {image_path}")

        # Open image
        img = Image.open(image_path)

        # Perform OCR
        text = pytesseract.image_to_string(
            img,
            lang=self.language,
            config="--psm 1"  # Automatic page segmentation with OSD
        )

        logger.info(f"OCR extracted {len(text)} characters from {image_path.name}")
        return text

    def ocr_to_markdown(self, image_path: Path, output_path: Path) -> Path:
        """Perform OCR and save as markdown

        Args:
            image_path: Path to image file
            output_path: Where to save the markdown

        Returns:
            Path to saved markdown file
        """
        text = self.ocr_image(image_path)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(f"Saved OCR markdown to {output_path}")
        return output_path
