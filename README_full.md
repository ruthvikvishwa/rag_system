# RAG System Documentation

A complete Retrieval-Augmented Generation (RAG) system for processing and querying documents, especially PDFs with mixed content types (text, scanned images, tables, formulas).

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Usage Examples](#usage-examples)
5. [How It Works](#how-it-works)
6. [File Structure](#file-structure)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

**Purpose:**
This RAG (Retrieval-Augmented Generation) system allows you to:
- Process multiple PDF documents (text-based, scanned, complex with tables)
- Store document chunks in a vector database
- Query documents and get synthesized answers
- Extend your LLM's effective memory by managing document context

**Key Features:**
- ✅ Mixed PDF support (text, OCR, tables, formulas)
- ✅ Multiple chunking strategies (semantic, hierarchical, table-aware, fixed, hybrid)
- ✅ Local vector database (ChromaDB, FAISS, SQLite, PostgreSQL)
- ✅ Optimized for memory efficiency
- ✅ Chatbot-style interactions
- ✅ Works with various document formats (PDF, MD, TXT, code)

**Target Use Cases:**
- Company knowledge bases
- Research document libraries
- Personal documentation
- Code documentation
- Legal/medical record management

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER INPUT                          │
│                        (Search Query)                       │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      QUERY HANDLER                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Query Processing & Normalization                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                       RETRIEVAL LAYER                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Query Embedding (LLM/Embedding Model)            │   │
│  └─────────────────────────────────────────────────────┘   │
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      VECTOR STORE                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              HYBRID SEARCH                           │   │
│  │  Semantic + Keyword Search                         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              RERANKING ENGINE                       │   │
│  │  (Cross-encoder for improved results)             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                        RAG ENGINE                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Context Assembly (Combine retrieved chunks)       │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LLM Integration (Generate answer)                │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Response Formatting & Citation                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                         USER OUTPUT                        │
│     (Answer with citations from documents)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 File Structure

```
rag_system/
│
├── __init__.py              # Package entry point
│
├── main.py                 # CLI entry point
├── demo.py                 # Interactive demo
│
├── documents/              # Your document storage
│   └── (place your PDFs, MD files, etc.)
│
├── core/                   # Core RAG components
│   ├── pdf_parser.py       # PDF processing
│   │   └── Extract: text, tables, OCR
│   └── vector_store/       # Vector databases
│       └── __init__.py     # ChromaDB, FAISS, SQLite, etc.
│
├── chunking/              # Chunking strategies
│   ├── fixed_chunker.py    # Simple fixed-size chunks
│   ├── semantic_chunker.py # Group by meaning
│   ├── hierarchical_chunker.py # Preserve structure
│   ├── table_aware_chunker.py # Keep tables together
│   └── hybrid_chunker.py   # Best for mixed content
│
└── requirements.txt       # Python dependencies
```

---

## 🔧 Installation

### Step 1: Install System Dependencies

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/release/HEAD/install.sh)"

# Install tesseract-ocr (for OCR support)
brew install tesseract

# Install required Python dependencies
pip3 install -r requirements.txt
```

**System Requirements:**
- Python 3.8+
- macOS with Homebrew
- 4GB+ RAM recommended
- tesseract-ocr installed

### Step 2: Clone the Repository

```bash
cd /Users/ruthvik/rag_system
```

### Step 3: Add to Python Path

```bash
export PYTHONPATH="/Users/ruthvik/rag_system:$PYTHONPATH"
```

Or install as a package:

```bash
cd /Users/ruthvik/rag_system
pip3 install -e .
```

---

## 💻 Usage Examples

### Example 1: Initialize RAG System

```python
from rag_system import DemoRAGSystem

# Initialize with your documents directory
system = DemoRAGSystem(documents_dir='./documents')

# Add all PDF documents
system.add_documents()

print("✅ RAG System initialized!")
print(f"   Documents: {system.rag_system.vector_store.count()} chunks")
```

### Example 2: Search Queries

```python
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

# Search across all documents
result = system.search("What are the key findings in Q3 2024?")

print("\n" + "="*50)
print("Answer:")
print("="*50)
print(result.answer)
print(f"\nConfidence: {result.confidence*100:.1f}%")
print(f"Processing time: {result.processing_time:.2f}s")

print("\nSources:")
for i, source in enumerate(result.sources[:3], 1):
    print(f"  {i}. {source['metadata'].get('doc_title', 'Unknown')}")
```

### Example 3: Search Specific Document

```python
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

# Search within a specific document
result = system.search_by_document("document.pdf", "What is the conclusion?")

print(f"\nDocument: {result.chunk_ids[0].split('_')[0]}")
print(result.answer[:500])
```

### Example 4: Interactive Demo

```bash
cd /Users/ruthvik/rag_system
python3 demo.py
```

This will start an interactive demo where you can:
1. Initialize the RAG system
2. Add your documents
3. Ask questions interactively

### Example 5: Connect to Your LLM

```python
from rag_system import DemoRAGSystem
# Replace with your LLM client
from openai import OpenAI

# Initialize RAG
rag = DemoRAGSystem(documents_dir='./documents')
rag.add_documents()

# Initialize LLM
client = OpenAI(api_key='YOUR_API_KEY')

def chat_with_rag(query, chat_history=[]):
    """Chat with your documents using RAG"""
    
    # Step 1: Search RAG for relevant chunks
    rag_result = rag.search(query, k=5)
    
    # Step 2: Build LLM prompt with relevant context
    messages = [
        {
            'role': 'system', 
            'content': 'You are a helpful assistant. Use the provided context to answer questions accurately.'
        },
        {
            'role': 'user',
            'content': f'''Context:
{rag_result.answer}

Question: {query}

Please answer the question based on the context provided. If the answer is not in the context, state that you cannot answer.'''
        }
    ]
    
    # Step 3: Call LLM
    response = client.chat.completions.create(
        model='gpt-4',  # Your preferred model
        messages=messages,
        max_tokens=500,
        temperature=0.2
    )
    
    return response.choices[0].message['content']

# Usage
user_query = "What is the revenue forecast for 2025?"
answer = chat_with_rag(user_query)
print(f"\nQ: {user_query}")
print(f"A: {answer}")
```

### Example 6: Batch Processing Multiple Queries

```python
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

# List of queries to process
queries = [
    "What are the key findings in Q3 2024?",
    "Who is the CEO?",
    "What is the revenue forecast for 2025?",
    "What are the company policies?",
    "What challenges were mentioned?"
]

# Process all queries
for i, query in enumerate(queries, 1):
    print(f"\n{'='*60}")
    print(f"Query {i}: {query}")
    print("="*60)
    
    result = system.search(query)
    print(f"\nAnswer:\n{result.answer}")
    print(f"Confidence: {result.confidence*100:.1f}%")
```

---

## 📚 Document Processing

### Supported Document Types

| Format | Extension | Supported | Notes |
|--------|-----------|-----------|-------|
| PDF | `.pdf` | ✅ | Text, OCR, Tables |
| Markdown | `.md`, `.markdown` | ✅ | Works with plain text |
| Text | `.txt` | ✅ | Direct text |
| Code | `.py`, `.js`, `.json` | ✅ | Code-aware chunking |
| Images | `.png`, `.jpg` | ⚠️ | Limited (OCR only) |

### PDF Processing Strategies

```python
from rag_system import PDFParser

parser = PDFParser()

# Auto-detect and process PDF strategy
result = parser.process_pdf("document.pdf", strategy="auto")

# Manual strategy selection
result = parser.process_pdf("document.pdf", strategy="text")  # Fast, for text PDFs
result = parser.process_pdf("scanned.pdf", strategy="ocr")    # For scanned PDFs
result = parser.process_pdf("tables.pdf", strategy="table")   # For table-heavy PDFs
result = parser.process_pdf("mixed.pdf", strategy="full")    # Get everything

# Extract specific content
text = parser.extract_text("document.pdf")
tables = parser.extract_tables("document.pdf")
ocr_text = parser.extract_ocr("scanned.pdf")

# Check for tables
if parser.has_tables("document.pdf"):
    print("This PDF contains tables!")
    
# Count pages
page_count = parser.count_pdf_pages("document.pdf")
print(f"Total pages: {page_count}")
```

---

## 🔨 Chunking Strategies

### 1. Fixed Chunking (Simple)

```python
from rag_system.chunking import FixedChunker

chunker = FixedChunker(
    chunk_size=500,  # Characters per chunk
    overlap=50       # Overlap between chunks
)

chunks = chunker.chunk(document_text)
for i, chunk in enumerate(chunks, 1):
    print(f"{i}. {chunk.chunk_id}: {chunk.content[:100]}...")
```

### 2. Semantic Chunking (Groups by Meaning)

```python
from rag_system.chunking import SemanticChunker

chunker = SemanticChunker(
    chunk_size=500,
    overlap=50,
    section_threshold=0.3  # Threshold for new sections
)

chunks = chunker.chunk(document_text)
# Chunks are grouped by semantic similarity
```

### 3. Hierarchical Chunking (Preserves Structure)

```python
from rag_system.chunking import HierarchicalChunker

chunker = HierarchicalChunker(
    page_chunk_size=1000,  # Per page
    content_chunk_size=500,
    overlap=50
)

document_chunks = chunker.chunk(document_info)
for i, chunk in enumerate(document_chunks, 1):
    print(f"{chunk.metadata['content_level']}: {chunk.content[:100]}...")
```

### 4. Table-Aware Chunking (Keeps Tables Together)

```python
from rag_system.chunking import TableAwareChunker

chunker = TableAwareChunker(
    content_chunk_size=500,
    table_chunk_size=2000,  # Tables are larger
    overlap=50
)

chunks = chunker.chunk(document_text)
# Tables are kept intact and separate from text chunks
```

### 5. Hybrid Chunking (Recommended for Mixed Content)

```python
from rag_system.chunking import HybridChunker

chunker = HybridChunker(
    content_chunk_size=500,
    table_chunk_size=2000,
    code_chunk_size=2000
)

chunks = chunker.chunk(document_text)
for chunk in chunks:
    print(f"[{chunk.source_type}] {chunk.chunk_id}")
```

---

## 🗄️ Vector Store

### ChromaDB (Recommended for Demo)

```python
from rag_system.vector_store import LocalVectorStore, VectorBackend

# Initialize
store = LocalVectorStore(
    backend=VectorBackend.CHROMA,
    persist_directory="./vector_data",
    collection_name="documents"
)

# Add documents
chunks = [...]  # List of chunks
store.add_documents(chunks)

# Search
results = store.search(query="your question", k=5)
for result in results:
    print(f"{result['score']:.3f}: {result['content']}")
```

### SQLite (Lightweight)

```python
store = LocalVectorStore(
    backend=VectorBackend.SQLITE,
    persist_directory="./vector_data"
)
```

### FAISS (Fast Local Search)

```python
store = LocalVectorStore(
    backend=VectorBackend.FAIS,
    persist_directory="./vector_data"
)
```

---

## 🚨 Troubleshooting

### Error: "No module named 'rag_system'"

```bash
# Fix: Add to PYTHONPATH
export PYTHONPATH="/Users/ruthvik/rag_system:$PYTHONPATH"

# Or install as package
pip3 install -e .
```

### Error: "tesseract is not installed or it's not in your PATH"

```bash
# Install tesseract-ocr
brew install tesseract

# Add to PATH
export PATH="/opt/homebrew/bin:/opt/homebrew/opt/tesseract/bin:$PATH"

# Or update .zshrc
echo 'export PATH="/opt/homebrew/bin:/opt/homebrew/opt/tesseract/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Error: "Memory usage too high"

```python
# Reduce chunk size
rag = DemoRAGSystem(
    chunk_size=300,  # Smaller chunks
    top_k=3  # Fewer results
)
```

### Error: "PDF contains no text"

```python
# Use OCR strategy
result = parser.process_pdf("scanned.pdf", strategy="ocr")
```

### Error: "Vector store not found"

```bash
# Make sure data is persisted
mkdir -p vector_data
```

---

## 🎯 Memory Efficiency

### How RAG Extends LLM Context

**Problem:**
- 500 PDFs = Thousands of pages = Memory overflow
- LLM context windows (even 128K) get overwhelmed

**Solution:**
```
Step 1: Store all 500 PDFs in vector database
Step 2: When user asks a query, RAG retrieves only relevant chunks (5-10)
Step 3: Pass ONLY those chunks to LLM
Result: LLM sees 500-2000 tokens instead of 100,000+ tokens!
```

### Example with LLM

```python
# User has 500 PDFs in memory (using RAG)
rag = DemoRAGSystem(documents_dir='./documents')
rag.add_documents()  # Stores 500 PDFs in vector database

# User asks: "What are the key findings in Q3 2024?"
rag_result = rag.search("What are the key findings in Q3 2024?", k=5)

# Only 5 chunks sent to LLM (not 500 PDFs!)
llm_context = rag_result.answer  # ~1000-3000 tokens
response = llm.generate(llm_context)

# LLM memory usage: < 5KB (not 500 PDFs!)
```

### Memory Comparison

| Approach | Memory Usage | LLM Tokens | Result |
|----------|-------------|------------|--------|
| Load all PDFs | 500MB - 2GB | 500K+ tokens | ❌ OOM error |
| **RAG System** | 500MB (vector DB) | **5-10K tokens** | ✅ Works perfectly |

---

## 📄 Sample Documents Folder Structure

```
documents/
├── pdf_reports/
│   ├── Q1_2024_sales.pdf
│   ├── Q2_2024_sales.pdf
│   ├── Q3_2024_sales.pdf
│   └── Q4_2024_sales.pdf
├── pdf_handbooks/
│   ├── employee_handbook.pdf
│   └── benefits.pdf
├── md_documents/
│   ├── project_specs.md
│   ├── meeting_notes_Q3.md
│   ├── roadmap_2025.md
│   └── api_documentation.md
└── text/
    ├── notes.txt
    └── contacts.txt
```

### Add All Documents

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

print(f'\\n✅ Successfully indexed {system.rag_system.vector_store.count()} chunks!')
"
```

---

## 🔬 Example Queries

### Query 1: Document-Specific

```python
# Search only in one document
result = system.search_by_document("Q3_2024_sales.pdf", "What is the revenue?")

print(result.answer)
# Output: "The Q3 2024 revenue is $125M, up 25% from Q2."
```

### Query 2: Cross-Document

```python
# Search across all documents
result = system.search("What is the overall revenue for 2024?")

print(result.answer)
# Output: "Total 2024 revenue projected at $500M based on Q1-Q3 data..."
```

### Query 3: Multi-Topic

```python
# Ask multiple questions
result = system.search(
    "What are our financial projections for 2025 and what strategic initiatives are planned?"
)

print(result.answer)
```

---

## 🎓 Learning Resources

### Step 1: Understanding RAG

1. **What is RAG?**
   - Retrieval-Augmented Generation
   - Combines document retrieval + LLM generation
   - Like having a search engine for your documents

2. **Why RAG?**
   - Solve LLM hallucinations (answers not in documents)
   - Scale document libraries (500+ PDFs)
   - Reduce memory usage (don't load everything)

### Step 2: Understanding Vector Databases

- Embeddings: Convert text to vectors
- Similarity search: Find similar vectors
- Vector DBs store and search vectors efficiently

### Step 3: Understanding Chunking

- Documents are too large for LLM context
- Split into smaller chunks (500-1000 chars each)
- Smart chunking preserves structure

### Step 4: Putting It All Together

```
Documents → Process → Chunk → Embed → Store → Retrieve → Answer
```

---

## 🌟 Pro Tips

### For Best Results:

1. **Be Specific:** "What is Q3 revenue?" not "What about our business?"
2. **Use Context:** "In the Q3 report, what is the revenue forecast?"
3. **Check Confidence:** Only trust high-confidence answers (>70%)
4. **Review Sources:** Check which documents the answer came from

### For Document Preparation:

1. **Clean PDFs:** Remove passwords, redactions
2. **Use Headers:** `## Section Name` helps chunking
3. **Add Metadata:** Include dates, versions, authors
4. **Test First:** Always test with a few documents

### For Performance:

1. **Smaller Documents:** Split into logical sections
2. **Right Chunk Size:** Text=500, Tables=2000, Code=2000
3. **Cache Results:** Don't re-process same documents
4. **Use Appropriate Backend:** ChromaDB for local, PGVector for scale

---

## 📞 Support

**Questions or Issues?**

1. Check the troubleshooting section above
2. Review the architecture diagram
3. Study the usage examples
4. Create an issue on GitHub

**Getting Help:**

```bash
# Interactive help
python3 demo.py --help

# Start interactive session
python3 demo.py
```

---

## 📝 Summary

This RAG system provides:

✅ **Document Processing** - Handle PDFs (text, scanned, tables)
✅ **Smart Chunking** - Multiple strategies for different content
✅ **Vector Storage** - ChromaDB, FAISS, SQLite, PostgreSQL, Weaviate
✅ **RAG Retrieval** - Hybrid search + re-ranking
✅ **Memory Efficient** - Don't load all documents, only relevant ones
✅ **Multiple Formats** - PDF, MD, TXT, code, images
✅ **Easy to Use** - Simple API, interactive demo

**Start Here:**
1. Place your documents in `./documents/`
2. Run `python3 demo.py` or your custom script
3. Ask questions, get instant answers from your documents!

---

**Happy Querying! 🚀**

---

*Generated on: 2024-09-29*
*Version: 0.1.0*