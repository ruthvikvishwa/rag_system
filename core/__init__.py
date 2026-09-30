"""
RAG Retriever - Orchestrates document processing, chunking, and retrieval

Combines:
1. Document ingestion and processing
2. Intelligent chunking
3. Vector storage and retrieval
4. Query processing and answer synthesis
"""

from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
import os
import sys
from pathlib import Path
import shutil
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import time
import re
import json
from tqdm import tqdm

# Import local modules
from .pdf_parser import extract_text, extract_tables, extract_ocr, has_tables, process_pdf, process_batch_pdfs
from .vector_store import LocalVectorStore, VectorBackend, get_vector_store

@dataclass
class RAGResult:
    """Result of a RAG query."""
    query: str
    chunks: List[Dict]
    answer: str
    sources: List[Dict]
    confidence: float
    processing_time: float
    chunk_ids: List[str]

class RAGRetriever:
    """
    Retrieval-Augmented Generation system.
    
    Supports:
    - Multiple document formats (PDF, TXT, DOCX)
    - Mixed PDF types (text, scanned, tables)
    - Intelligent chunking with metadata
    - Hybrid search (semantic + keyword)
    - Re-ranking for improved results
    """
    
    def __init__(
        self,
        vector_store: Optional[LocalVectorStore] = None,
        collection_name: str = "documents",
        chunk_strategy: str = "hybrid",
        chunk_size: int = 500,
        overlap: int = 50,
        top_k: int = 5,
        rerank: bool = True,
        rerank_top_k: int = 3,
        embed_model: Optional[str] = None,
        auto_process: bool = True,
        persist: bool = True
    ):
        self.collection_name = collection_name
        self.chunk_strategy = chunk_strategy
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.top_k = top_k
        self.rerank = rerank
        self.rerank_top_k = rerank_top_k
        self.embed_model = embed_model
        
        # Initialize vector store
        if vector_store:
            self.vector_store = vector_store
            self._validate_store()
        else:
            self.vector_store = get_vector_store(
                collection_name=collection_name,
                backend=VectorBackend.CHROMA,
                persist_directory="./vector_data",
                embed_model=embed_model,
                persist=persist
            )
        
        # Initialize document processor (placeholder)
        self.doc_processor = None
        
        # Reranker (if enabled)
        if rerank:
            try:
                from langchain.retrievers.contextual_compressor import ContextualRecompression
                self.reranker = ContextualRecompression(relevance_query_prompt="This query:")
            except ImportError:
                self.reranker = None
    
    def _validate_store(self):
        """Validate that the vector store is properly initialized."""
        if self.vector_store is None:
            raise ValueError("Vector store must be initialized")
    
    def add_documents(
        self,
        document_paths: Union[str, List[str]],
        output_dir: Optional[str] = None,
        auto_process: bool = True,
        show_progress: bool = False
    ) -> Dict:
        """
        Ingest documents into the RAG system.
        
        Args:
            document_paths: Single path or list of paths to documents
            output_dir: Optional directory to save processed documents
            auto_process: Whether to auto-detect document type
            show_progress: Whether to show progress bar
        
        Returns:
            Statistics about ingested documents
        """
        # Handle single path
        if isinstance(document_paths, str):
            document_paths = [document_paths]
        
        # Filter to supported formats
        supported_formats = ['.pdf', '.txt', '.md', '.docx']
        valid_paths = []
        for path in document_paths:
            path_lower = path.lower()
            if any(path_lower.endswith(fmt) for fmt in supported_formats):
                valid_paths.append(path)
            elif path.endswith('.pdf'):
                valid_paths.append(path)  # Process all PDFs
        
        # Process documents
        if auto_process:
            processed_docs = process_batch_pdfs(
                valid_paths,
                strategy="auto",
                output_dir=output_dir
            )
        else:
            processed_docs = []
            for path in valid_paths:
                content = extract_text(path)
                processed_docs.append({
                    "path": path,
                    "content": content,
                    "content_type": "text",
                    "pages": self.doc_processor.count_pdf_pages(path) if path.endswith('.pdf') else 0
                })
        
        # Chunk documents
        chunk_strategy_map = {
            "text": "fixed",
            "table": "table_aware",
            "ocr": "semantic",
            "mixed": "hybrid"
        }
        
        all_chunks = []
        doc_id_map = {}
        chunk_counter = 0
        
        for doc in processed_docs:
            doc_id = doc['path'].split('/')[-1].replace('.pdf', '')
            doc_id_map[doc['path']] = doc_id
            
            chunk_strategy = chunk_strategy_map.get(doc['content_type'], "hybrid")
            chunks = self._chunk_document(
                content=doc['content'],
                strategy=chunk_strategy,
                metadata={
                    "doc_id": doc_id,
                    "doc_title": doc.get('title', os.path.basename(doc['path'])),
                    "doc_path": doc['path'],
                    "content_type": doc['content_type'],
                    "pages": doc.get('pages', 0)
                }
            )
            all_chunks.extend(chunks)
        
        # Store in vector store
        doc_metadata = []
        for i, chunk in enumerate(all_chunks):
            doc_metadata.append(chunk.metadata)
        
        self.vector_store.add_documents(
            documents=all_chunks,
            overwrite=False
        )
        
        # Get statistics
        stats = self._get_statistics()
        stats['documents_added'] = len(processed_docs)
        stats['chunks_added'] = stats['total_chunks']
        
        if show_progress:
            print(f"\n✅ Documents added successfully!")
            print(f"   Documents: {stats['documents_added']}")
            print(f"   Total chunks: {stats['chunks_added']}")
        
        return stats
    
    def _chunk_document(
        self,
        content: str,
        strategy: str,
        metadata: Dict
    ) -> List[Dict]:
        """
        Chunk a single document.
        
        Args:
            content: Document content
            strategy: Chunking strategy
            metadata: Document metadata
        
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        if strategy == "hybrid":
            from .chunking.hybrid_chunker import HybridChunker
            chunker = HybridChunker(
                content_chunk_size=self.chunk_size,
                table_chunk_size=self.chunk_size * 3
            )
        elif strategy == "semantic":
            from .chunking.semantic_chunker import SemanticChunker
            chunker = SemanticChunker(
                chunk_size=self.chunk_size,
                overlap=self.overlap
            )
        elif strategy == "hierarchical":
            from .chunking.hierarchical_chunker import HierarchicalChunker
            chunker = HierarchicalChunker(
                page_chunk_size=self.chunk_size,
                content_chunk_size=self.chunk_size // 2
            )
        elif strategy == "table_aware":
            from .chunking.table_aware_chunker import TableAwareChunker
            chunker = TableAwareChunker(
                content_chunk_size=self.chunk_size,
                table_chunk_size=self.chunk_size * 5
            )
        else:
            from .chunking.fixed_chunker import FixedChunker
            chunker = FixedChunker(chunk_size=self.chunk_size)
        
        document_chunks = chunker.chunk(content)
        
        for chunk_data in document_chunks:
            # Enhance metadata with document info
            enhanced_metadata = metadata.copy()
            enhanced_metadata.update(chunk_data.metadata)
            
            chunks.append({
                "chunk_id": chunk_data.chunk_id,
                "content": chunk_data.content,
                "metadata": enhanced_metadata
            })
        
        return chunks
    
    def search(
        self,
        query: str,
        k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None,
        use_rerank: bool = True
    ) -> RAGResult:
        """
        Search for relevant chunks and generate an answer.
        
        Args:
            query: Search query
            k: Number of top chunks to retrieve
            filter_metadata: Optional metadata filters
            use_rerank: Whether to use re-ranking
        
        Returns:
            RAGResult with chunks and synthesized answer
        """
        start_time = time.time()
        
        # Determine k
        k = k if k is not None else self.top_k
        
        # Retrieve chunks
        results = self.vector_store.search(
            query=query,
            k=k,
            filter_metadata=filter_metadata
        )
        
        # Extract just the chunks
        chunks = []
        for result in results:
            chunks.append({
                "chunk_id": result['chunk_id'],
                "content": result['content'],
                "metadata": result['metadata'],
                "score": result['score']
            })
        
        # Re-rank if enabled
        if use_rerank and self.reranker:
            chunks = self._rerank_chunks(chunks, query)
        
        # Synthesize answer
        answer = self._synthesize_answer(chunks, query)
        
        processing_time = time.time() - start_time
        
        return RAGResult(
            query=query,
            chunks=chunks[:self.rerank_top_k] if use_rerank else chunks,
            answer=answer,
            sources=chunks,
            confidence=self._calculate_confidence(chunks),
            processing_time=processing_time,
            chunk_ids=[c['chunk_id'] for c in chunks]
        )
    
    def _rerank_chunks(self, chunks: List[Dict], query: str) -> List[Dict]:
        """
        Re-rank chunks using a cross-encoder model.
        
        Note: This may be slow for large numbers of chunks.
        """
        if not self.reranker:
            return chunks
        
        # Create query-chunk pairs for re-ranking
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
        
        rerank_results = self.reranker.relevant_chunks(
            chunks,
            query=query
        )
        
        # Reorder chunks by score
        chunks_sorted = sorted(
            rerank_results,
            key=lambda x: x.get('score', 0),
            reverse=True
        )[:self.rerank_top_k]
        
        return chunks_sorted
    
    def _synthesize_answer(self, chunks: List[Dict], query: str) -> str:
        """
        Generate answer based on retrieved chunks.
        
        This is a template-based approach. For production,
        you would integrate with your preferred LLM.
        """
        if not chunks:
            return "No relevant information found in the documents."
        
        # Format sources
        sources = []
        for i, chunk in enumerate(chunks, 1):
            source_info = f"[{i}] {chunk['metadata'].get('doc_title', 'Unknown Document')} " \
                         f"(Page {chunk['metadata'].get('page', '?')})"
            sources.append(f"{source_info}\n\n{chunk['content']}")
        
        # Generate answer (simplified - replace with actual LLM call)
        context = "\n\n---\n\n".join(sources)
        
        # This is a placeholder - replace with actual LLM generation
        # For now, just return a synthesized response
        answer = f"""
Based on the retrieved documents, here's the answer to your query:

**Query:** {query}

**Relevant Information:**

{context[:2000]}  # Limit to avoid excessive length

Please let me know if you need more specific information or additional documents.
        """.strip()
        
        return answer
    
    def _calculate_confidence(self, chunks: List[Dict]) -> float:
        """
        Calculate confidence score based on retrieval quality.
        
        Confidence is based on:
        - Number of relevant chunks found
        - Average score of chunks
        - Coverage of query in chunks
        """
        if not chunks:
            return 0.0
        
        # Average score
        avg_score = sum(c.get('score', 0) for c in chunks) / len(chunks)
        
        # Count of chunks
        chunk_count = len(chunks)
        
        # Coverage score (approximate)
        total_query_words = len(query.split())
        chunk_word_count = sum(len(c.get('content', '').split()) for c in chunks)
        coverage = min(chunk_word_count / total_query_words, 2.0) if total_query_words > 0 else 1.0
        
        # Weighted confidence
        confidence = (
            0.4 * min(avg_score / 0.85, 1.0) +  # Score component
            0.3 * min(chunk_count / self.top_k, 1.0) +  # Count component
            0.3 * min(coverage, 1.0)  # Coverage component
        )
        
        return round(confidence, 3)
    
    def get_statistics(self) -> Dict:
        """Get RAG system statistics."""
        return self.vector_store.count()
    
    def clear_documents(self):
        """Clear all documents from the vector store."""
        self.vector_store.clear()
    
    def search_by_document(self, document_id: str, query: str, k: int = 5) -> RAGResult:
        """
        Search within a specific document.
        
        Args:
            document_id: ID of the document to search
            query: Search query
            k: Number of results
        
        Returns:
            RAGResult with document-specific results
        """
        return self.search(
            query=query,
            k=k,
            filter_metadata={"doc_id": document_id}
        )
    
    def export_statistics(self, output_path: str):
        """
        Export RAG system statistics to a file.
        
        Args:
            output_path: Path to save the statistics file
        """
        stats = self.get_statistics()
        
        with open(output_path, 'w') as f:
            f.write("=" * 50 + "\n")
            f.write("RAG System Statistics\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Collection Name: {self.collection_name}\n")
            f.write(f"Chunk Strategy: {self.chunk_strategy}\n")
            f.write(f"Chunk Size: {self.chunk_size}\n")
            f.write(f"Overlap: {self.overlap}\n")
            f.write(f"Top-K: {self.top_k}\n")
            f.write(f"Re-rank: {self.rerank}\n")
            f.write(f"Embed Model: {self.embed_model}\n\n")
            
            f.write("-" * 50 + "\n")
            f.write("Storage Statistics\n")
            f.write("-" * 50 + "\n\n")
            
            f.write(f"Total Documents: {stats.get('documents', 0)}\n")
            f.write(f"Total Chunks: {stats.get('chunks', 0)}\n")
            f.write(f"Vector Dimension: {self.vector_store.embedding_dimension}\n\n")
            
            # Group by document type
            type_counts = {}
            for chunk in stats.get('all_chunks', []):
                ctype = chunk['metadata'].get('content_type', 'unknown')
                type_counts[ctype] = type_counts.get(ctype, 0) + 1
            
            f.write("Documents by Type:\n")
            for ctype, count in sorted(type_counts.items()):
                f.write(f"  {ctype}: {count}\n")
            
            f.write("\n" + "=" * 50 + "\n")
        
        print(f"✅ Statistics exported to: {output_path}")

# Convenience function for quick setup
def create_rag_system(
    collection_name: str = "documents",
    backend: str = "chroma",
    persist: bool = True
) -> RAGRetriever:
    """
    Create a RAG system with default settings.
    
    Args:
        collection_name: Name for the vector collection
        backend: Vector backend ("chroma", "faiss", "sqlite", "pgvector", "weaviate")
        persist: Whether to persist data
    
    Returns:
        Configured RAGRetriever instance
    """
    backend_map = {
        "chroma": VectorBackend.CHROMA,
        "faiss": VectorBackend.FAIS,
        "sqlite": VectorBackend.SQLITE,
        "pgvector": VectorBackend.PGVECTOR,
        "weaviate": VectorBackend.WEAVIATE
    }
    
    backend_enum = backend_map.get(backend.lower(), VectorBackend.CHROMA)
    
    return RAGRetriever(
        collection_name=collection_name,
        vector_backend=backend_enum,
        persist=persist
    )