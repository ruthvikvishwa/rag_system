"""
RAG System - Main Entry Point

Quickstart:
1. Add your PDF documents
2. Search and retrieve information
3. Get synthesized answers
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_system.core import RAGRetriever

from rag_system.chunking import SemanticChunker, FixedChunker, TableAwareChunker
from rag_system.vector_store import LocalVectorStore, VectorBackend

class DemoRAGSystem:
    """
    Demonstration RAG system with step-by-step workflow.
    
    Usage:
        python main.py --documents path/to/pdfs --query "your question"
    """
    
    def __init__(self, documents_dir: str = "./documents"):
        """
        Initialize the RAG system.
        
        Args:
            documents_dir: Directory containing PDF documents
            persist: Whether to persist vector store data
        """
        self.documents_dir = Path(documents_dir)
        self.vector_store = None
        self.rag_system = None
        self.chunk_size = 500
        self.rerank = True
        
        print("🚀 Initializing RAG System...")
        
        # Initialize vector store
        self.vector_store = LocalVectorStore(
            collection_name="my_documents",
            backend=VectorBackend.CHROMA,
        )
        
        # Create RAG retriever
        self.rag_system = RAGRetriever(
            vector_store=self.vector_store,
            collection_name="my_documents",
            chunk_strategy="hybrid",
            chunk_size=self.chunk_size,
            top_k=5,
            rerank=self.rerank,
        )
        
        print(f"✅ RAG System initialized!")
        print(f"   Documents dir: {self.documents_dir}")
        print(f"   Chunk size: {self.chunk_size}")
        print(f"   Vector backend: {self.vector_store.backend.value}")
    
    def add_documents(self):
        """
        Add all PDFs from the documents directory.
        """
        print("\n📄 Adding documents from:", self.documents_dir)
        
        # Find all PDF files
        pdf_files = []
        for ext in ['*.pdf', '*.PDF']:
            pdf_files.extend(self.documents_dir.glob(ext))
        
        print(f"   Found {len(pdf_files)} PDF files")
        
        if not pdf_files:
            print("   ⚠️  No PDF files found!")
            return
        
        # Add to RAG system
        stats = self.rag_system.add_documents(
            document_paths=[str(pdf) for pdf in pdf_files],
            auto_process=True,
            show_progress=True
        )
        
        print("\n📊 Statistics:")
        print(f"   Documents indexed: {stats['documents_added']}")
        print(f"   Total chunks: {stats['chunks_added']}")
    
    def search(self, query: str):
        """
        Search for the given query.
        
        Args:
            query: Search query
        """
        print("\n🔍 Searching for:", query)
        
        # Search
        result = self.rag_system.search(
            query=query,
            k=5,
            use_rerank=self.rerank
        )
        
        print(f"\n📝 Found {len(result.chunks)} relevant chunks")
        print(f"   Confidence: {result.confidence * 100:.1f}%")
        print(f"   Processing time: {result.processing_time:.2f}s")
        
        print("\n" + "=" * 60)
        print("Answer:")
        print("=" * 60)
        print(result.answer)
        
        print("\n" + "=" * 60)
        print("\n📚 Sources:")
        for i, source in enumerate(result.sources[:3], 1):
            meta = source['metadata']
            print(f"\n[{i}] {meta.get('doc_title', 'Unknown')}")
            print(f"    Page: {meta.get('page', '?')}")
            print(f"    Chunk ID: {meta.get('chunk_id', '?')}")
            print(f"    Score: {source.get('score', 0):.3f}")
        
        return result
    
    def search_document(self, document_id: str, query: str):
        """
        Search within a specific document.
        
        Args:
            document_id: ID or filename of the document
            query: Search query
        """
        print("\n🔍 Searching in document:", document_id)
        print("   Query:", query)
        
        result = self.rag_system.search_by_document(
            document_id=document_id,
            query=query,
            k=3
        )
        
        print(f"\n📝 Found {len(result.chunks)} relevant chunks")
        print(f"   Confidence: {result.confidence * 100:.1f}%")
        
        print("\nAnswer:")
        print(result.answer)
        
        return result
    
    def clear(self):
        """Clear all documents from the vector store."""
        print("\n🗑️  Clearing all documents...")
        self.rag_system.clear_documents()
        print("✅ Done!")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="RAG System - Retrieve answers from your PDF documents"
    )
    
    parser.add_argument(
        "--documents", "-d",
        type=str,
        default="./documents",
        help="Directory containing PDF documents to index"
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        required=True,
        help="Search query"
    )
    
    parser.add_argument(
        "--document",
        type=str,
        default=None,
        help="Optional: Search within a specific document"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Chunk size in characters (default: 500)"
    )
    
    parser.add_argument(
        "--rerank",
        type=str,
        choices=["true", "false"],
        default="true",
        help="Enable re-ranking for better results (default: true)"
    )
    
    args = parser.parse_args()
    
    # Create system
    system = DemoRAGSystem(
        documents_dir=args.documents,
        persist=True
    )
    
    # Check if documents already indexed
    vector_data_dir = Path("./vector_data")
    if args.document is None:
        # Just search
        system.search(query=args.query)
    else:
        # Search specific document
        system.search_document(
            document_id=args.document,
            query=args.query
        )
    
    return 0

if __name__ == "__main__":
    exit(main())