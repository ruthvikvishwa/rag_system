# Quick Start Guide

## Prerequisites

- Python 3.8+
- tesseract-ocr (for OCR functionality) - Windows/Mac/Linux
- 2-4 GB RAM minimum (8 GB recommended)
- 5 GB disk space for vector storage

## Installation

### Option 1: pip install
```bash
pip install -r requirements.txt
```

### Option 2: Manual installation
```bash
# PDF Processing
pip install PyMuPDF pdfplumber pdf2image Pillow pytesseract python-tesseract

# Vector Storage
pip install chromadb

# Embeddings
pip install sentence-transformers
```

### Install OCR (if needed)
```bash
# Ubuntu/Debian
apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

## First Steps

### Step 1: Prepare Your Documents
Place your PDF documents in a folder:
```
my_documents/
  document1.pdf
  document2.pdf
  ...
```

### Step 2: Add Documents to RAG
```bash
python main.py -d ./my_documents
```

### Step 3: Search for Answers
```bash
# Search all documents
python main.py -d ./my_documents -q "your question"

# Search specific document
python main.py -d ./my_documents -q "your question" --document document1
```

## Example Session

```bash
$ python main.py -d ./my_documents -q "What is the revenue forecast for 2025?"

🚀 Initializing RAG System...
✅ RAG System initialized!

📄 Adding documents from: ./my_documents
   Found 15 PDF files
   Processing...
   ✅ Done!

📊 Statistics:
   Documents indexed: 15
   Total chunks: 420

🔍 Searching for: What is the revenue forecast for 2025?
   Found 5 relevant chunks
   Confidence: 87.5%
   Processing time: 0.45s

Answer:
Based on the retrieved documents...

📚 Sources:
[1] Financial Report (Page 5)
[2] Q4 Projections (Page 12)
[3] Executive Summary (Page 2)
```

## File Structure

```
rag-system/
├── __init__.py              # Package initialization
├── README.md                # Full documentation
├── requirements.txt         # Python dependencies
├── demo.py                 # Interactive demo
├── quickstart.md           # This file
│
├── documents/              # Your PDF documents
│   └── ...
│
├── vector_data/            # Vector store data
│   └── chroma/             # ChromaDB data
│       └── persist/
│           ├── collections/
│           └── metadatas/
│
└── core/                   # Core RAG modules
    ├── __init__.py
    ├── pdf_parser.py       # PDF processing
    ├── chunking/           # Chunking strategies
    │   ├── __init__.py
    │   ├── fixed_chunker.py
    │   ├── semantic_chunker.py
    │   ├── hierarchical_chunker.py
    │   ├── table_aware_chunker.py
    │   └── hybrid_chunker.py
    └── vector_store/       # Vector databases
        ├── __init__.py
        └── vector_store.py
```

## Configuration

### Editable Configuration
Create/edit `config.yaml`:

```yaml
rag:
  chunk_size: 500          # Characters per chunk
  top_k: 5                # Number of chunks to return
  rerank: true            # Enable re-ranking
  
chunking:
  strategy: "hybrid"       # Or: semantic, hierarchical, table_aware, fixed
  
vector_store:
  backend: "chroma"        # Or: faiss, sqlite, pgvector, weaviate
  persist_directory: "./vector_data"
  embed_model: "BAAI/bge-base-en-v1.5"
```

### Environment Variables
```bash
export VECTOR_BACKEND=chroma
export VECTOR_PERSIST_DIR=./vector_data
export EMBED_MODEL=BAAI/bge-base-en-v1.5
export PGVECTOR_HOST=localhost
```

## Common Use Cases

### 1. Document Summarization
```bash
python main.py -d ./docs -q "Summarize this document"
```

### 2. Question Answering
```bash
python main.py -d ./docs -q "What are the key recommendations?"
```

### 3. Table Analysis
```bash
python main.py -d ./docs -q "What are the sales figures in Q3?"
```

### 4. Code Search
```bash
python main.py -d ./code_docs -q "How to implement authentication?"
```

## Tips

### For Better Results
1. **Be specific** - "What was the revenue in Q3 2024 for the North American region?"
2. **Provide context** - "In the financial report, what..."
3. **Reference pages** - "On page 5, what does it say about..."

### For Large Document Collections
1. Use document-specific search: `--document document_name`
2. Filter by metadata: `--filter doc_id:my_document`
3. Reduce `top_k` for faster results

### For Memory Optimization
1. Reduce `chunk_size` 
2. Disable re-ranking: `--rerank false`
3. Use FAISS instead of ChromaDB

## Troubleshooting

### No Results Found
```bash
# Check if documents are indexed
python main.py -d ./my_documents

# Verify vector store
ls -la ./vector_data/
```

### Slow Performance
```bash
# Reduce chunk size
python main.py -d ./docs --chunk-size 300

# Disable re-ranking
python main.py -d ./docs --rerank false

# Clear and rebuild
rm -rf ./vector_data
python main.py -d ./docs
```

### OCR Issues
```bash
# Reinstall tesseract
apt-get install --reinstall tesseract-ocr

# Check OCR is working
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

## Advanced Usage

### Python API

```python
from rag_system import DemoRAGSystem

# Initialize
system = DemoRAGSystem(documents_dir="./my_documents")

# Add documents
system.add_documents()

# Search
result = system.search("Your query")
print(result.answer)
```

### Custom Chunking Strategy

```python
from rag_system.chunking import SemanticChunker

chunker = SemanticChunker(
    chunk_size=500,
    overlap=50,
    min_chunk_size=100
)

chunks = chunker.chunk(document_text)
```

### Custom Vector Store

```python
from rag_system.vector_store import LocalVectorStore
from rag_system.vector_store import VectorBackend

store = LocalVectorStore(
    backend=VectorBackend.PGVECTOR,
    persist_directory="./custom_vectors"
)
```

## Next Steps

1. **Add your documents**
   ```bash
   python main.py -d ./your_documents
   ```

2. **Try the demo**
   ```bash
   python demo.py
   ```

3. **Explore the API**
   ```python
   from rag_system import DemoRAGSystem, RAGRetriever
   ```

4. **Customize for your needs**
   - Modify chunking strategy
   - Adjust chunk sizes
   - Add custom document processors

## Support

- Check the main README.md for full documentation
- Report issues on GitHub
- Check documentation folder for tutorials

---

**Happy querying! 🎉**