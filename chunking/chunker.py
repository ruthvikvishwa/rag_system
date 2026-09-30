"""
Intelligent Document Chunking

Supports multiple chunking strategies:
1. Semantic chunking - groups related content by meaning
2. Hierarchical chunking - preserves document structure
3. Fixed-size chunking - simple size-based chunks
4. Table-aware chunking - handles tables as single chunks
"""

from typing import List, Dict, Optional, Union
from dataclasses import dataclass, field
import re
from tqdm import tqdm
import fitz  # PyMuPDF
import pdfplumber
import pdf2image
from PIL import Image
import io
import subprocess
import tempfile
import os
from pathlib import Path
import hashlib
from concurrent.futures import ThreadPoolExecutor

@dataclass
class Chunk:
    """Represents a single chunk of content."""
    chunk_id: str
    content: str
    metadata: Dict[str, str]
    vector: Optional[bytes] = None  # Will be set by embedding model
    
    @property
    def chunk_hash(self) -> str:
        """Generate unique hash for this chunk."""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()
        return f"{self.chunk_id}_{content_hash}"

class SemanticChunker:
    """
    Semantic-based chunking that groups related content.
    Uses simple keyword/topic analysis instead of external embeddings
    for efficiency.
    """
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        # Topic keywords that help identify section boundaries
        self.section_patterns = {
            'section': r'(\d+\.\d*|Section\s+\d+|\d+\s+\w+)?:\s*\n?\s*',
            'header': r'(##?#+\s+\S+)',
            'table': r'(?:Table\s+\d+|##?\s+\d+\.?\s*|\d+\s*\|\s*)',
            'code': r'```[\w\s]*?\n(?:.*?\n)*?```',
            'reference': r'(?:\[\d+|\[\[\d+|\(?\d+[,)]?\)?|footnotes|references|bibliography)',
        }
    
    def detect_sections(self, text: str) -> List[Dict]:
        """Detect section boundaries in text."""
        sections = []
        current_section = {"name": "", "content": "", "start_pos": 0}
        pos = 0
        
        # Look for section headers
        for pattern, regex in self.section_patterns.items():
            for match in re.finditer(regex, text):
                section_name = match.group().strip()
                section_end = match.end()
                
                if pattern == 'reference' and 'footnote' in section_name.lower():
                    # End current section, save it
                    if current_section["content"]:
                        sections.append(current_section)
                    # Start new reference section
                    content_segment = text[pos:section_end]
                    sections.append({
                        "name": "References",
                        "content": content_segment,
                        "end_pos": section_end
                    })
                elif pattern == 'table':
                    # End current section if we have content
                    if current_section["content"]:
                        sections.append(current_section)
                    sections.append({
                        "name": "Table",
                        "content": "",
                        "end_pos": section_end
                    })
                else:
                    # New content section
                    current_section = {
                        "name": section_name,
                        "content": text[pos:section_end],
                        "end_pos": section_end
                    }
                pos = section_end
        
        # Add final section if there's remaining content
        if current_section["content"]:
            sections.append(current_section)
        
        return sections
    
    def chunk(self, text: str) -> List[Chunk]:
        """Chunk text semantically."""
        chunks = []
        
        # Detect and separate sections
        sections = self.detect_sections(text)
        
        chunk_counter = 0
        for section in sections:
            # If content is too small, combine with previous
            if len(section["content"]) < self.chunk_size and chunks:
                prev = chunks[-1]
                if len(prev.content) < self.chunk_size:
                    prev.content += " " + section["content"]
                    chunk_counter = chunks[-1].chunk_id
            else:
                chunk_counter += 1
                
            content = section["content"][:self.chunk_size]
            chunks.append(Chunk(
                chunk_id=f"chunk_{chunk_counter:04d}",
                content=content,
                metadata={
                    "section": section["name"],
                    "section_start": section.get("start_pos", 0),
                    "section_end": section.get("end_pos", len(text))
                }
            ))
        
        return chunks

class HierarchicalChunker:
    """
    Hierarchical chunking preserves document structure:
    Document → Sections → Pages → Chunks
    """
    
    def __init__(self, page_chunk_size: int = 500, 
                 content_chunk_size: int = 300,
                 overlap: int = 50):
        self.page_chunk_size = page_chunk_size
        self.content_chunk_size = content_chunk_size
        self.overlap = overlap
    
    def chunk_document(self, document_info: Dict) -> List[Chunk]:
        """Chunk a document preserving its structure."""
        chunks = []
        content = document_info.get("content", "")
        page_info = document_info.get("pages", [])
        metadata = document_info.get("metadata", {})
        
        chunk_counter = 0
        
        for page_num in page_info:
            page_content = content.split('\n\n')[page_num] if page_num < len(content.split('\n\n')) else ""
            
            # Extract page info
            page_content = content[:min(self.page_chunk_size, len(content))]
            
            chunk_counter += 1
            chunks.append(Chunk(
                chunk_id=f"doc_{metadata.get('doc_id', 'unknown')}_page_{page_num}_chunk_{chunk_counter:02d}",
                content=page_content,
                metadata={
                    "doc_id": metadata.get("doc_id", "unknown"),
                    "page": page_num,
                    "doc_title": metadata.get("doc_title", "Unknown"),
                    "chunk_type": "page"
                }
            ))
            
            content = content[self.page_chunk_size:]
        
        return chunks

class TableAwareChunker:
    """
    Chunk-aware of tables. Tables are kept together
    and not split across chunks.
    """
    
    def __init__(self, content_chunk_size: int = 300, 
                 table_chunk_size: int = 2000):
        self.content_chunk_size = content_chunk_size
        self.table_chunk_size = table_chunk_size
    
    def chunk(self, text: str) -> List[Chunk]:
        """Chunk text, keeping tables together."""
        chunks = []
        chunk_counter = 0
        
        # Detect tables (simple pattern matching)
        tables = re.findall(r'\|\s*.*?\|.*?\n(?:\|\s*\S|\|)', text)
        text_without_tables = re.sub(r'\|\s*.*?\|.*?\n(?:\|\s*\S|\|)', '', text)
        
        chunk_counter += len(tables)  # Account for table chunks
        
        # Create table chunks
        for table in tables[:max(len(tables), 5)]:  # Limit to first few tables
            if len(table) > self.table_chunk_size:
                # Split large table
                for i in range(0, len(table), self.table_chunk_size // 4):
                    chunks.append(Chunk(
                        chunk_id=f"table_{chunk_counter:04d}",
                        content=table[i:i + self.table_chunk_size // 4],
                        metadata={"chunk_type": "table"}
                    ))
                    chunk_counter += 1
            else:
                chunks.append(Chunk(
                    chunk_id=f"table_{chunk_counter:04d}",
                    content=table,
                    metadata={"chunk_type": "table"}
                ))
                chunk_counter += 1
        
        # Chunk regular text
        text_chunks = self._text_chunking(text_without_tables, self.content_chunk_size)
        chunks.extend(text_chunks)
        
        return chunks
    
    def _text_chunking(self, text: str, chunk_size: int) -> List[Chunk]:
        """Simple fixed-size text chunking."""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for char in text:
            current_chunk.append(char)
            current_size += 1
            if current_size >= chunk_size:
                chunks.append(Chunk(
                    chunk_id=f"text_{len(chunks):04d}",
                    content="".join(current_chunk),
                    metadata={"chunk_type": "text"}
                ))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append(Chunk(
                chunk_id=f"text_{len(chunks):04d}",
                content="".join(current_chunk),
                metadata={"chunk_type": "text"}
            ))
        
        return chunks

class HybridChunker:
    """
    Hybrid chunker combines multiple strategies:
    1. Extract sections, tables, code separately
    2. Apply appropriate chunking strategy to each
    3. Return ordered list of chunks
    """
    
    def __init__(self, content_chunk_size: int = 300, 
                 table_chunk_size: int = 2000):
        self.content_chunk_size = content_chunk_size
        self.table_chunk_size = table_chunk_size
        self.semantic_chunker = SemanticChunker(chunk_size=content_chunk_size)
        self.table_chunker = TableAwareChunker(content_chunk_size, table_chunk_size)
    
    def chunk(self, text: str) -> List[Chunk]:
        """Apply hybrid chunking strategy."""
        all_chunks = []
        chunk_counter = 0
        
        # Extract and process different content types
        sections = []
        tables = []
        code_blocks = []
        ocr_text = []
        
        # Simple extraction based on markers
        section_texts = re.split(r'(##?\s+\S+|\d+\.\d*|\[\d+)', text)
        for i, piece in enumerate(section_texts):
            if i % 2 == 0:  # Section title
                sections.append(piece)
            elif piece.strip():  # Section content
                # Check content type
                if '```' in piece:
                    code_blocks.append(piece)
                elif any(t.lower() in piece.lower() for t in ['table', 'fig.', 'table:']):
                    tables.append(piece)
                else:
                    sections.append(piece)
        
        # Chunk each type appropriately
        for section in sections[:20]:  # Limit sections to prevent too many chunks
            chunk_counter += 1
            all_chunks.append(Chunk(
                chunk_id=f"section_{chunk_counter:04d}",
                content=section[:self.content_chunk_size],
                metadata={"chunk_type": "section"}
            ))
        
        for table in tables[:5]:  # Limit tables
            chunk_counter += 1
            all_chunks.append(Chunk(
                chunk_id=f"table_{chunk_counter:04d}",
                content=table[:self.table_chunk_size],
                metadata={"chunk_type": "table"}
            ))
        
        for code in code_blocks[:10]:  # Limit code blocks
            chunk_counter += 1
            all_chunks.append(Chunk(
                chunk_id=f"code_{chunk_counter:04d}",
                content=code[:self.table_chunk_size],
                metadata={"chunk_type": "code"}
            ))
        
        return all_chunks

def chunk_text(
    text: str, 
    strategy: str = "hybrid",
    chunk_size: int = 300,
    table_chunk_size: int = 2000,
    metadata: Optional[Dict] = None
) -> List[Chunk]:
    """
    Chunk text using the specified strategy.
    
    Args:
        text: Text to chunk
        strategy: "semantic", "hierarchical", "table_aware", "fixed"
        chunk_size: Size of each chunk in characters
        metadata: Document metadata
    
    Returns:
        List of Chunk objects
    """
    if strategy == "semantic":
        chunker = SemanticChunker(chunk_size=chunk_size)
        chunks = chunker.chunk(text)
        if metadata:
            for c in chunks:
                c.metadata.update(metadata)
        return chunks
    
    elif strategy == "hierarchical":
        chunker = HierarchicalChunker(page_chunk_size=chunk_size, content_chunk_size=chunk_size)
        return chunker.chunk_document({"content": text, "metadata": metadata or {}})
    
    elif strategy == "table_aware":
        chunker = TableAwareChunker(content_chunk_size=chunk_size, table_chunk_size=table_chunk_size)
        chunks = chunker.chunk(text)
        return chunks
    
    elif strategy == "fixed":
        chunks = []
        current = []
        counter = 0
        for i in range(0, max(len(text), 300), chunk_size):
            chunk_text = text[i:i + chunk_size]
            counter += 1
            chunks.append(Chunk(
                chunk_id=f"fixed_{counter:04d}",
                content=chunk_text[:chunk_size],
                metadata={"chunk_type": "fixed"}
            ))
        return chunks
    
    else:
        chunker = HybridChunker(content_chunk_size=chunk_size, table_chunk_size=table_chunk_size)
        return chunker.chunk(text)