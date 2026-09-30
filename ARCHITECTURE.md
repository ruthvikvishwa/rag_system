# RAG System Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                              │
│                        (Search Query)                           │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        QUERY HANDLER                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Query Processing & Normalization                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RETRIEVAL LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Query Embedding (LLM/Embedding Model)                  │   │
│  └─────────────────────────────────────────────────────────┘   │
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      VECTOR STORE                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              HYBRID SEARCH                               │   │
│  │  ┌────────────────────┐  ┌────────────────────┐         │   │
│  │  │ Semantic Search    │  │  Keyword Search     │         │   │
│  │  └────────────────────┘  └────────────────────┘         │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              RERANKING ENGINE                           │   │
│  │  (Cross-encoder for re-ranking top candidates)          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        RAG ENGINE                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Context Assembly                                        │   │
│  │  (Combine retrieved chunks with metadata)              │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  LLM Integration                                         │   │
│  │  (Generate answer based on context)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Response Formatting & Citation                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         USER OUTPUT                            │
│     (Answer with citations)                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Document Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                      DOCUMENT INGESTION                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  PDF Processor                                          │   │
│  │  ┌──────────────┬──────────────┬──────────────┐         │   │
│  │  │ Text PDF     │ Scanned PDF  │ Complex PDF   │         │   │
│  │  │ (PyMuPDF)    │ (OCR)        │ (Tables+Text) │         │   │
│  │  └──────────────┴──────────────┴──────────────┘         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CHUNKING LAYER                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Strategy Selection                                     │   │
│  │  ┌──────────┬──────────┬──────────┬──────────┐         │   │
│  │  │ Semantic │ Hierarchical│ Table- │   Fixed │         │   │
│  │  │          │           │ Aware    │   Hybrid │         │   │
│  │  └──────────┴──────────┴──────────┴──────────┘         │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Chunk Generation:                                      │   │
│  │  - Content Chunks (text)                                │   │
│  │  - Table Chunks                                         │   │
│  │  - Code Chunks                                          │   │
│  │  - Figure Chunks                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EMBEDDING LAYER                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Text Embedding Model                                    │   │
│  │  (e.g., BGE-M3, E5, or OpenAI embeddings)              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     VECTOR STORAGE                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Vector Database                             │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Collections:                                        │ │   │
│  │  │  - documents                                         │ │   │
│  │  │  - tables                                            │ │   │
│  │  │  - code                                              │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                          │ │   │
│  │  Chunks: {id, content, metadata, vector, position}         │ │   │
│  │                                                          │ │   │
│  │  Index: HNSW / IVF / Flat (configured)                    │ │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Chunk Types

```
┌─────────────────────────────────────────────────────────────────┐
│                         CHUNK TYPES                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  DOCUMENT LEVEL                                                  │
│  └─ Summary of entire document                                    │
│     doc_id, total_pages, content_type, metadata                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  SECTION LEVEL                                                   │
│  └─ Individual sections/chapters                                  │
│     - Section title                                              │
│     - Section content                                            │
│     - Metadata: doc_id, page, section_name                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PAGE LEVEL                                                      │
│  └─ Content per page                                             │
│     - Page number                                               │
│     - Page content                                              │
│     - Metadata: doc_id, page_num                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  CONTENT LEVEL (Fine-grained)                                    │
│  └─ Fixed-size text chunks                                       │
│     - Text content                                              │
│     - Overlap with previous chunk                               │
│     - Metadata: doc_id, chunk_id, position                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  SPECIAL ELEMENTS                                               │
│  ├─ TABLE CHUNKS: Complete tables, not split                     │
│  │   - Table data                                               │
│  │   - Table headers                                            │
│  │   - Position metadata                                        │
│  └─ CODE CHUNKS: Code blocks                                    │
│  │   - Code content                                             │
│  │   - Language tag                                             │
│  └─ FIGURE CHUNKS: Captions and descriptions                    │
│  │   - Figure/caption text                                       │
│  │   - Description                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Vector Backend Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    VECTOR BACKENDS                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┬────────────────┬─────────────────────┐
│   Backend       │   Use Case     │    Pros/Cons        │
├─────────────────┼────────────────┼─────────────────────┤
│ ChromaDB        │ Local Demo     │ + Easy setup        │
│                 │                │ - Single process    │
│                 │                │ - Local storage     │
├─────────────────┼────────────────┼─────────────────────┤
│ FAISS           │ Large Local    │ + Very fast         │
│                 │ Collections     │ - CPU only          │
│                 │                │ - Memory intensive  │
├─────────────────┼────────────────┼─────────────────────┤
│ PostgreSQL+     │ Production     │ + Scalable          │
│   PGVector      │                │ - Database needed   │
├─────────────────┼────────────────┼─────────────────────┤
│ Weaviate        │ Cloud/Scale    │ + Managed option    │
│                 │                │ - External service  │
└─────────────────┴────────────────┴─────────────────────┘
```

## Data Flow

```
Document Input
    │
    │ (PDF, DOCX, TXT)
    ▼
PDF Processing
    │
    │ (Extract text, tables, OCR)
    ▼
Chunking
    │
    │ (Split into chunks)
    ▼
Embedding
    │
    │ (Generate vector embeddings)
    ▼
Vector Store
    │
    │ (Store in vector database)
    ▼
Query Time
    │
    │ (User enters query)
    ▼
Query Processing
    │
    │ (Embed query)
    ▼
Vector Search
    │
    │ (Retrieve similar chunks)
    ▼
Reranking
    │
    │ (Re-rank top results)
    ▼
Context Assembly
    │
    │ (Combine chunks)
    ▼
LLM Generation
    │
    │ (Generate answer)
    ▼
Response with Citations
    │
    │ (Final output)
    ▼
User
```

## Module Architecture

```
rag-system/
│
├── __init__.py              # Package exports
│
├── main.py                 # CLI entry point
├── demo.py                 # Interactive demo
├── requirements.txt        # Dependencies
│
├── documents/              # Input PDFs
│
└── core/                   # Core functionality
    │
    ├── __init__.py
    │
    ├── pdf_parser.py       # PDF processing
    │   └── Extracts: text, tables, OCR
    │
    ├── chunking/           # Chunking strategies
    │   │
    │   ├── __init__.py
    │   ├── fixed_chunker.py
    │   ├── semantic_chunker.py
    │   ├── hierarchical_chunker.py
    │   ├── table_aware_chunker.py
    │   └── hybrid_chunker.py
    │
    ├── vector_store/       # Vector databases
    │   │
    │   └── __init__.py
    │       └── LocalVectorStore
    │           ├── ChromaDB backend
    │           ├── FAISS backend
    │           ├── SQLite backend
    │           ├── PGVector backend
    │           └── Weaviate backend
    │
    └── rag_retriever.py    # RAG orchestration
        └── Combines all components
```

## Configuration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        CONFIGURATION                            │
└─────────────────────────────────────────────────────────────────┘

User Choice                  Auto-Detection
    │                              │
    ▼                              ▼
┌───────────────┐          ┌───────────────┐
│ Document Type │          │ Heuristics    │
│               │          │ Analysis      │
└───────────────┘          └───────────────┘
    │                              │
    └──────────────┬───────────────┘
                   ▼
           ┌───────────────┐
           │ Strategy      │
           │ Selection     │
           └───────────────┘
                   │
                   ▼
           ┌───────────────┐
           │ Processing    │
           │ Pipeline      │
           └───────────────┘
```

## Performance Optimization

```
1. Pre-computation
   └─ Embed offline documents
   └─ Cache frequent queries

2. Chunk Optimization
   └─ Smaller chunks = faster search
   └─ Smart overlap = better retrieval

3. Vector Index
   └─ HNSW for fast search
   └─ Adjustive parameters

4. Caching Layer
   └─ Store frequent results
   └─ Skip re-embedding

5. Query Optimization
   └─ Limit top_k
   └─ Filter irrelevant results
   └─ Skip re-ranking if not needed
```

## Memory Usage

```
Document Processing:    ~50 MB per PDF (in memory)
Chunking:               ~5 MB per 100 pages
Embedding:             ~0.5 GB for 10,000 docs
Vector Store:         ~1-2 GB for 500 docs
                    ~5-10 GB for 2000 docs
                    ~10-20 GB for 5000 docs
```

## Scalability

| Docs | Pages | Memory | Time (Add) | Time (Search) |
|------|-------|--------|------------|---------------|
| 50   | ~2500 | ~500 MB | ~5 min     | ~0.1s         |
| 200  | ~10000| ~2 GB   | ~20 min    | ~0.2s         |
| 500  | ~25000| ~5 GB   | ~45 min    | ~0.4s         |
| 2000 |~100000| ~15 GB  | ~3 hrs     | ~1s           |
| 5000 |~250000| ~40 GB  | ~8 hrs     | ~3s           |

## Future Improvements

- [ ] Multi-modal support (images, diagrams)
- [ ] Real-time document processing
- [ ] Advanced query understanding (semantic search)
- [ ] Multi-document summarization
- [ ] Citation verification
- [ ] Multi-language support
- [ ] API for web interface
- [ ] Dashboard for monitoring

---

**Built with modularity and scalability in mind!** 🚀