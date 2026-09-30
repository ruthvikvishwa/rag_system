"""
PDF Processor - Handles multiple PDF types intelligently

Supports:
1. Text-based PDFs (fast extraction with PyMuPDF)
2. Scanned/image-based PDFs (OCR with pytesseract)
3. Complex PDFs with tables/formulas (pdfplumber)
"""

import fitz  # PyMuPDF
import pdfplumber
import pdf2image
from PIL import Image
import io
import fitz  # PyMuPDF
import pdfplumber
import pdf2image
from PIL import Image
import io
from typing import Optional
from dataclasses import dataclass
import os
import tempfile
import subprocess
from pathlib import Path

# PDF Parser for text-based PDFs
from langchain_community.document_loaders import PyMuPDFLoader
import fitz
from langchain.text_splitter import RecursiveCharacterTextSplitter

def process_pdf(pdf_path: str, strategy: str = "auto") -> str:
    """
    Process PDF and extract text/tables.
    
    Args:
        pdf_path: Path to PDF file
        strategy: "auto", "text", "table", "ocr", "full"
    
    Returns:
        Text content with metadata about extraction
    """
    if strategy == "auto":
        # Auto-detect PDF type and use best strategy
        sample = extract_text_sample(pdf_path)
        if sample:
            return extract_full_text(pdf_path)
        elif has_tables(pdf_path):
            return extract_tables(pdf_path)
        else:
            return extract_ocr(pdf_path)
    
    elif strategy == "text":
        return extract_text(pdf_path)
    
    elif strategy == "table":
        return extract_tables(pdf_path)
    
    elif strategy == "ocr":
        return extract_ocr(pdf_path)
    
    elif strategy == "full":
        # Get everything: text + tables + OCR
        result = {"text": [], "tables": [], "ocr": []}
        result["text"].append(extract_text(pdf_path))
        result["tables"].append(extract_tables(pdf_path))
        result["ocr"].append(extract_ocr(pdf_path))
        return result
    
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

def extract_text(pdf_path: str) -> str:
    """Extract text from text-based PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    doc.close()
    return text

def extract_tables(pdf_path: str) -> str:
    """Extract tables from PDF using pdfplumber."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_tables()
            if table:
                for t in table:
                    row_data = [cell if cell else "" for cell in t[0]] if t else []
                    tables.append("|".join(row_data))
    return "\n".join(tables)

def extract_ocr(pdf_path: str) -> str:
    """Extract text from scanned/image-based PDF using OCR."""
    images = []
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        images.append(pix.tobytes())
    doc.close()
    
    ocr_text = []
    for image_bytes in images:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
            with open(tmp_path, "rb") as f:
                img = Image.open(io.BytesIO(f.read()))
            
            img.save(tmp_path.replace(".png", ".jpg"), "JPEG", quality=95)
        
            # Run Tesseract OCR
            result = subprocess.run(
                ["tesseract", tmp_path.replace(".jpg", ""), "stdout"],
                capture_output=True,
                text=True,
                check=True
            )
            ocr_text.append(result.stdout)
    
    os.unlink(tmp_path)
    os.unlink(tmp_path.replace(".png", ".jpg"))
    
    return "\n".join(ocr_text)

def has_tables(pdf_path: str) -> bool:
    """Check if PDF contains tables."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    return True
        return False
    except:
        return False

def extract_text_sample(pdf_path: str, pages: int = 2) -> str:
    """Extract text from first few pages to detect PDF type."""
    doc = fitz.open(pdf_path)
    text = ""
    for i, page in enumerate(doc[:min(pages, len(doc))]):
        page_text = page.get_text("text")
        if page_text.strip():
            text += page_text + "\n\n"
    doc.close()
    
    # Check if significant text was extracted
    return text if len(text.strip()) > 100 else None

def process_batch_pdfs(pdf_paths: list, strategy: str = "auto", output_dir: Optional[str] = None):
    """
    Process multiple PDFs and save results.
    
    Args:
        pdf_paths: List of PDF file paths
        strategy: Extraction strategy
        output_dir: Optional directory to save extracted text
    
    Returns:
        List of extracted text/documents
    """
    results = []
    for pdf_path in pdf_paths:
        try:
            if strategy == "full" or strategy == "text":
                result = extract_text(pdf_path)
                content_type = "text"
            elif strategy == "table":
                result = extract_tables(pdf_path)
                content_type = "table"
            elif strategy == "ocr":
                result = extract_ocr(pdf_path)
                content_type = "ocr"
            else:
                result = process_pdf(pdf_path, strategy="auto")
                if isinstance(result, dict):
                    content_type = "mixed"
                else:
                    content_type = result
                    
            doc_info = {
                "path": pdf_path,
                "content": result,
                "content_type": content_type,
                "pages": count_pdf_pages(pdf_path)
            }
            results.append(doc_info)
            
            # Save to output directory if specified
            if output_dir:
                basename = os.path.basename(pdf_path)
                with open(os.path.join(output_dir, basename), "w", encoding="utf-8") as f:
                    f.write(result)
                    
        except Exception as e:
            results.append({
                "path": pdf_path,
                "content": f"ERROR: {str(e)}",
                "content_type": "error",
                "pages": 0
            })
    
    return results

def count_pdf_pages(pdf_path: str) -> int:
    """Count number of pages in a PDF."""
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count

def get_pdf_strategy(pdf_path: str) -> str:
    """Auto-detect the best extraction strategy for a PDF."""
    # Check if text extraction works well
    try:
        doc = fitz.open(pdf_path)
        text = ""
        sample_pages = min(3, len(doc))
        for page in doc[:sample_pages]:
            page_text = page.get_text("text")
            text += page_text
            if len(text.strip()) > 500:
                doc.close()
                return "text"  # Good text extraction
        doc.close()
    except:
        pass
    
    # Check for tables
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                if page.extract_tables():
                    return "table"
    except:
        pass
    
    # Default to OCR for problematic PDFs
    return "ocr"