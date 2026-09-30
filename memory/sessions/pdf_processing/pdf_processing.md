# Conversation: pdf_processing
**Started:** 2026-09-29 21:43:33

## Previous Conversation
---

# Conversation: pdf_processing
**Started:** 2026-09-29 21:43:33


1. [💬 User]
> How do you handle different PDF types?

---

## New Message

2. [🤖 Assistant]
> 
The system intelligently detects and handles different PDF types:

**1. Text-based PDFs:**
- Extract text using PyMuPDF (fast, ~0.1s per page)
- Works well for regular documents

**2. Scanned PDFs:**
- Uses OCR with Tesseract
- Converts images to text

**3. PDFs with tables:**
- Extracts tables using pdfplumber
- Preserves table structure

**4. Complex PDFs (mixed):**
- Auto-detects best strategy
- Combines text + tables + OCR

Example:
```python
# Auto-detect and process
from document_processor import process_pdf
content = process_pdf(pdf_path, strategy="auto")
```


