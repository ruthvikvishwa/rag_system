"""
Document Processor Package

Submodules:
- pdf_parser: PDF processing utilities
"""

from .pdf_parser import (
    PDFParser,
    process_pdf,
    extract_text,
    extract_tables,
    extract_ocr,
    has_tables,
    extract_text_sample,
    process_batch_pdfs,
    count_pdf_pages,
    get_pdf_strategy
)

__all__ = [
    'PDFParser',
    'process_pdf',
    'extract_text',
    'extract_tables',
    'extract_ocr',
    'has_tables',
    'extract_text_sample',
    'process_batch_pdfs',
    'count_pdf_pages',
    'get_pdf_strategy'
]