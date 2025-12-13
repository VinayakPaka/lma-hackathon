"""
GreenGuard ESG Platform - PDF Service
"""
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFService:
    """PDF service for extracting text and tables from PDF files."""
    
    def extract_text(self, pdf_path: str) -> Optional[str]:
        """Extract all text from a PDF file."""
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            full_text = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(full_text)} characters from {pdf_path}")
            return full_text
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            return None
    
    def extract_tables(self, pdf_path: str) -> List[List[List[str]]]:
        """Extract tables from a PDF file."""
        try:
            import pdfplumber
            all_tables = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    all_tables.extend(tables)
            return all_tables
        except Exception as e:
            logger.error(f"Table extraction failed: {str(e)}")
            return []


pdf_service = PDFService()
