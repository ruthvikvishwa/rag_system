"""
Chunking Module - Multiple strategies for document chunking

Provides several chunking strategies:
1. SemanticChunker - Groups by semantic similarity
2. HierarchicalChunker - Preserves document structure
3. TableAwareChunker - Keeps tables intact
4. FixedChunker - Simple fixed-size splitting
5. HybridChunker - Combines multiple strategies

Usage:
    from chunking import SemanticChunker, HybridChunker
    
    # Semantic chunking
    chunker = SemanticChunker(chunk_size=500, overlap=50)
    chunks = chunker.chunk(text)
    
    # Hybrid chunking (recommended for mixed content)
    chunker = HybridChunker(chunk_size=500)
    chunks = chunker.chunk(text)
"""

from .fixed_chunker import FixedChunker
from .semantic_chunker import SemanticChunker
from .hierarchical_chunker import HierarchicalChunker
from .table_aware_chunker import TableAwareChunker
from .hybrid_chunker import HybridChunker

__all__ = [
    'FixedChunker',
    'SemanticChunker',
    'HierarchicalChunker',
    'TableAwareChunker',
    'HybridChunker'
]