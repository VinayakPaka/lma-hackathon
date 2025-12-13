"""
GreenGuard ESG Platform - OCR Service
"""
import logging
from pathlib import Path
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)


class OCRService:
    """OCR service for extracting text from images."""
    
    def extract_text(self, image_path: str) -> Optional[str]:
        """Extract text from an image file."""
        try:
            import pytesseract
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            logger.info(f"Extracted {len(text)} characters from {image_path}")
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return None
    
    def extract_from_bytes(self, image_bytes: bytes) -> Optional[str]:
        """Extract text from image bytes."""
        try:
            import pytesseract
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes))
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return None


ocr_service = OCRService()
