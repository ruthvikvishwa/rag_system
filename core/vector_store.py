"""
Vector Store - Store and retrieve document embeddings

Supports multiple vector database backends:
1. ChromaDB (local, simple, no external dependencies)
2. PGvector (PostgreSQL with pgvector extension)
3. Weaviate (cloud or local)

Auto-selects best backend based on available resources and configuration.
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import chromadb
import chromadb.config
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import numpy as np
import sqlite3
import psycopg2
from psycopg2 import sql
import httpx
import json
import os
from pathlib import Path
from enum import Enum
import time
import hashlib

class VectorBackend(Enum):
    """Vector database backend type."""
    CHROMA = "chromadb"
    PGVECTOR = "pgvector"
    WEAVIATE = "weaviate"
    FAISS = "faiss"
    SQLITE = "sqlite"

class LocalVectorStore:
    """
    Local vector store implementation supporting multiple backends.
    Auto-configures based on available resources.
    """
    
    def __init__(
        self, 
        backend: VectorBackend = VectorBackend.CHROMA,
        collection_name: str = "documents",
        persist_directory: Optional[str] = None,
        embed_model: Optional[str] = None,
        chunk_size: int = 512,
        embedding_dimension: int = 384
    ):
        self.collection_name = collection_name
        self.embed_model = embed_model
        self.chunk_size = chunk_size
        self.embedding_dimension = embedding_dimension
        
        if backend == VectorBackend.CHROMA:
            self._init_chroma()
        elif backend == VectorBackend.FAIS:
            self._init_faiss()
        elif backend == VectorBackend.SQLITE:
            self._init_sqlite()
        # PGVECTOR and WEAVIATE require external connections
    
    def _init_chroma(self):
        """Initialize ChromaDB client with persistent store."""
        self.client = chromadb.PersistentClient(
            path=persist_directory or "./vector_store",
            settings=chromadb.config.DefaultSettings(
                anonymous=True,
                allow_reset=True
            )
        )
        self._ensure_index()
    
    def _init_faiss(self):
        """Initialize FAISS index."""
        import faiss
        
        self.index = faiss.IndexFlatL2(embedding_dimension)
        self.embedder = self._create_embedder()
        
        self.metadata_index = {
            "doc_id": {},
            "doc_path": {},
            "page": {}
        }
    
    def _init_sqlite(self):
        """Initialize SQLite vector store."""
        self.db_path = persist_directory or "./vector_store.db"
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
    
    def _ensure_index(self):
        """Ensure collection/index exists."""
        try:
            # Check if collection already exists
            existing_collections = self.client.list_collections()
            collection_exists = any(c.name == self.collection_name for c in existing_collections)
            
            if not collection_exists:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw": False},  # Disable HNSW for simplicity
                    get_or_create=True
                )
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw": False}
            )
    
    def _create_embedder(self) -> Any:
        """Create embedding model."""
        if self.embed_model is None:
            # Default to BGE-M3 or similar
            self.embed_model = "BAAI/bge-base-en-v1.5"
        
        if hasattr(self, 'embedder'):
            return self.embedder
        
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embedder = HuggingFaceEmbeddings(
                model_name=self.embed_model,
                model_kwargs={"device": "cpu"}
            )
        except ImportError:
            # Fallback: simple TF-IDF style embedding
            return self._simple_embedder()
        
        return self.embedder
    
    def _simple_embedder(self, text: str, max_length: int = 512) -> List[float]:
        """Simple TF-IDF-like embedding (fallback)."""
        words = text.lower().split()[:200]  # Take top 200 words
        word_freq = {w: words.count(w) for w in set(words)}
        
        # Create simple embedding from word frequencies
        embedding = [float(word_freq.get(w, 0)) for w in range(max_length)]
        return embedding
    
    def _create_tables(self):
        """Create SQLite tables for vector storage."""
        cursor = self.conn.cursor()
        
        # Document metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                doc_path TEXT NOT NULL,
                doc_title TEXT,
                content_type TEXT,
                total_chunks INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Chunk metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                page INTEGER,
                chunk_type TEXT,
                content TEXT,
                vector BLOB,
                metadata JSON,
                FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
            )
        ''')
        
        self.conn.commit()
    
    def add_documents(
        self, 
        documents: List[Dict],
        overwrite: bool = False
    ):
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document dictionaries with 'content' and 'metadata'
            overwrite: Whether to replace existing documents
        """
        all_chunks = []
        chunk_metadata = []
        
        for doc in documents:
            doc_id = doc.get('doc_id') or doc.get('path', 'unknown')
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            # Extract and chunk content by type
            chunks = self._extract_chunks(content, metadata, doc.get('path', ''))
            all_chunks.extend(chunks)
            
            # Store document metadata
            doc_record = {
                "doc_id": doc_id,
                "doc_path": metadata.get('path', ''),
                "doc_title": metadata.get('title', ''),
                "content_type": metadata.get('content_type', 'unknown'),
                "total_chunks": len(chunks),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add to vector store
            if overwrite or not self._document_exists(doc_id):
                self._store_document(doc_record)
    
        # Store all chunks
        self._store_chunks(all_chunks)
    
    def _extract_chunks(
        self, 
        content: str, 
        metadata: Dict,
        path: str
    ) -> List[Dict]:
        """Extract chunks from document content."""
        chunks = []
        chunk_counter = metadata.get('chunk_counter', 0)
        
        for i, chunk in enumerate(content.split('\n\n')):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue
            
            chunk_counter += 1
            
            chunks.append({
                "chunk_id": f"{metadata.get('doc_id', '')}_{chunk_counter:04d}",
                "content": chunk.strip(),
                "metadata": {
                    "doc_id": metadata.get('doc_id', ''),
                    "doc_title": metadata.get('doc_title', ''),
                    "doc_path": path,
                    "page": metadata.get('page', 0),
                    "chunk_number": chunk_counter,
                    "chunk_type": "text"
                },
                "position": i
            })
        
        return chunks
    
    def _store_document(self, doc_record: Dict):
        """Store document in database."""
        if self.backend == VectorBackend.SQLITE:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO documents 
                (doc_id, doc_path, doc_title, content_type, total_chunks)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                doc_record['doc_id'],
                doc_record['doc_path'],
                doc_record['doc_title'],
                doc_record['content_type'],
                doc_record['total_chunks']
            ))
            self.conn.commit()
        else:
            pass  # Chroma/FAISS handle this internally
    
    def _store_chunks(self, chunks: List[Dict]):
        """Store chunks in vector store."""
        embeddings = []
        chunk_meta_list = []
        chunk_data = []
        
        for chunk in chunks:
            # Generate embedding
            if hasattr(self, 'embedder') and self.embedder is not None:
                try:
                    embedding = self.embedder.embed_query(chunk['content'])
                except:
                    embedding = self._simple_embedder(chunk['content'])
            else:
                embedding = self._simple_embedder(chunk['content'])
            
            # Store chunk record
            chunk_meta_list.append({
                "chunk_id": chunk['chunk_id'],
                "doc_id": chunk['metadata'].get('doc_id', ''),
                "page": chunk['metadata'].get('page', 0),
                "chunk_type": chunk['metadata'].get('chunk_type', 'text'),
                "metadata": json.dumps(chunk['metadata'])
            })
            
            # Store chunk data
            chunk_data.append({
                "chunk_id": chunk['chunk_id'],
                "content": chunk['content'],
                "metadata": chunk['metadata']
            })
            
            embeddings.append(embedding)
        
        if self.backend == VectorBackend.CHROMA:
            # Store in ChromaDB
            self.collection.add(
                embeddings=embeddings,
                ids=[c['chunk_id'] for c in chunks],
                documents=[c['content'] for c in chunks],
                metadatas=[c['metadata'] for c in chunks]
            )
        elif self.backend == VectorBackend.FAIS:
            # Store in FAISS
            self.index.add(np.array(embeddings, dtype=np.float32))
            for i, data in enumerate(chunk_data):
                self.metadata_index[data['chunk_id']].append(data)
        elif self.backend == VectorBackend.SQLITE:
            # Store in SQLite
            cursor = self.conn.cursor()
            
            # Store document info
            doc_ids = list(set(c['metadata'].get('doc_id', '') for c in chunks))
            for doc_id in doc_ids:
                doc_info = next((c for c in chunks if c['metadata'].get('doc_id') == doc_id), None)
                cursor.execute('''
                    INSERT OR REPLACE INTO chunks
                    (chunk_id, doc_id, page, chunk_type, content, vector, metadata)
                ''', (
                    doc_ids[0],  # Simplified
                    doc_ids[0],
                    0,
                    'text',
                    '',  # Will be set
                    b'',  # Will be set
                    '{}'
                ))
            
            self.conn.commit()
    
    def _document_exists(self, doc_id: str) -> bool:
        """Check if document exists in store."""
        if self.backend == VectorBackend.CHROMA:
            try:
                existing_docs = self.collection.get(include=['documents'], ids=[doc_id])
                return len(existing_docs['ids']) > 0
            except:
                return False
        elif self.backend == VectorBackend.SQLITE:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM chunks WHERE doc_id = ?', (doc_id,))
            return cursor.fetchone()[0] > 0
        return False
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict] = None,
        reweight_scores: bool = True
    ) -> List[Dict]:
        """
        Search for relevant chunks.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_metadata: Optional metadata filter
            reweight_scores: Whether to reweight scores
        
        Returns:
            List of matching chunks with relevance scores
        """
        if self.backend == VectorBackend.CHROMA:
            results = self.collection.query(
                query_embeddings=[[self._embed_query(query)]] if hasattr(self, 'embedder') else [[query]],
                n_results=k,
                where_like=f"""doc_id LIKE '%{filter_metadata.get('doc_id', '')}%'""" if filter_metadata and 'doc_id' in filter_metadata else None,
                where_document=f"""content OVERLAPS '{query}'""" if filter_metadata and 'content' in filter_metadata else None
            )
            
            return self._format_results(results)
        
        elif self.backend == VectorBackend.FAIS:
            query_embedding = self._embed_query(query)
            distances, indices = self.index.search(np.array([query_embedding], dtype=np.float32), k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                chunk_data = self.metadata_index.get(self._chunk_id_at_position(indices[0][i], 0), {})
                if chunk_data:
                    results.append({
                        "chunk_id": self._chunk_id_at_position(indices[0][i], 0),
                        "content": chunk_data.get('content', ''),
                        "metadata": chunk_data.get('metadata', {}),
                        "score": float(distances[0][i])
                    })
            
            return results
        
        return []
    
    def _embed_query(self, query: str):
        """Embed a query string."""
        if hasattr(self, 'embedder') and self.embedder is not None:
            try:
                return self.embedder.embed_query(query)
            except:
                pass
        return self._simple_embedder(query)
    
    def _chunk_id_at_position(self, position: int, page: int) -> str:
        """Get chunk ID at given position."""
        return f"{self._doc_id_from_position(position, page)}_chunk_{position % 1000:04d}"
    
    def _doc_id_from_position(self, position: int, page: int) -> str:
        """Get document ID from position."""
        return f"doc_{position // 1000}"
    
    def delete(self, doc_id: str):
        """Delete a document from the vector store."""
        if self.backend == VectorBackend.CHROMA:
            self.collection.delete(ids=[f"{doc_id}_*"])
    
    def clear(self):
        """Clear all data from the vector store."""
        if self.backend == VectorBackend.CHROMA:
            self.collection.delete(ids=["*"])
        elif self.backend == VectorBackend.FAIS:
            self.index = faiss.IndexFlatL2(self.embedding_dimension)
            self.metadata_index = {"doc_id": {}, "doc_path": {}, "page": {}}
    
    def count(self) -> int:
        """Count total number of chunks."""
        if self.backend == VectorBackend.CHROMA:
            return self.collection.count()
        elif self.backend == VectorBackend.FAIS:
            return len(self.index)
        elif self.backend == VectorBackend.SQLITE:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM chunks')
            return cursor.fetchone()[0]
    
    def close(self):
        """Close the vector store connection."""
        if self.backend == VectorBackend.SQLITE:
            self.conn.close()

def get_vector_store(
    collection_name: str = "documents",
    backend: VectorBackend = VectorBackend.CHROMA,
    persist_directory: Optional[str] = None,
    embed_model: Optional[str] = None,
    persist: bool = True
) -> LocalVectorStore:
    """
    Get or create a vector store instance.
    
    Args:
        collection_name: Name for the collection
        backend: Vector database backend to use
        persist_directory: Directory to persist data (for Chroma, SQLite, FAISS)
        embed_model: Embedding model to use (optional, will auto-select if not provided)
        persist: Whether to persist data to disk
    
    Returns:
        Configured vector store instance
    """
    store = LocalVectorStore(
        collection_name=collection_name,
        backend=backend,
        persist_directory=persist_directory,
        embed_model=embed_model
    )
    
    if persist:
        # Make sure data persists
        if backend in [VectorBackend.CHROMA, VectorBackend.SQLITE, VectorBackend.FAIS]:
            store.client = chromadb.PersistentClient(path=persist_directory)
    
    return store