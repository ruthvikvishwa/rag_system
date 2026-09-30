"""
Fixed Size Chunker - Simple character-based chunking

Splits text into fixed-size chunks with optional overlap.
Simple and efficient for uniform text documents.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
import re

@dataclass
class Chunk:
    """Represents a fixed-size chunk of content."""
    chunk_id: str
    content: str
    metadata: Dict[str, str]

class FixedChunker:
    """
    Simple fixed-size text chunking.
    
    Splits text into chunks of fixed size with optional overlap.
    Does not preserve document structure - just simple splitting.
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50,
        min_content_length: int = 50
    ):
        """
        Initialize the fixed chunker.
        
        Args:
            chunk_size: Size of each chunk in characters
            overlap: Number of characters to overlap between chunks
            min_content_length: Minimum content length to consider a valid chunk
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_content_length = min_content_length
    
    def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        Split text into fixed-size chunks.
        
        Args:
            text: Text to chunk
            metadata: Optional document metadata
        
        Returns:
            List of Chunk objects
        """
        chunks = []
        chunk_counter = 0
        
        # Clean text - normalize line endings and extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split by paragraphs/sentences for better chunks
        paragraphs = text.split('\n\n')
        
        # Build chunks from paragraphs
        current_chunk = []
        current_size = 0
        paragraph_index = 0
        
        while paragraph_index < len(paragraphs):
            # Add new paragraph to current chunk
            if current_size >= self.chunk_size:
                # Save current chunk
                content = " ".join(current_chunk)
                if len(content) >= self.min_content_length:
                    chunk_counter += 1
                    chunks.append(Chunk(
                        chunk_id=f"fixed_{chunk_counter:04d}",
                        content=content[:self.chunk_size],
                        metadata={
                            "chunk_id": f"fixed_{chunk_counter:04d}",
                            "paragraph_count": paragraph_index + 1,
                            **(metadata or {})
                        }
                    ))
                
                # Start new chunk with overlap
                current_chunk = []
                current_size = 0
                paragraph_index -= 1  # Re-process the last paragraph
                
            current_chunk.append(paragraphs[paragraph_index])
            current_size += len(paragraphs[paragraph_index])
            paragraph_index += 1
        
        # Don't forget the last chunk
        if current_chunk or paragraph_index < len(paragraphs):
            content = " ".join(current_chunk)
            if len(content) >= self.min_content_length:
                chunk_counter += 1
                chunks.append(Chunk(
                    chunk_id=f"fixed_{chunk_counter:04d}",
                    content=content,
                    metadata={
                        "chunk_id": f"fixed_{chunk_counter:04d}",
                        "paragraph_count": paragraph_index + 1,
                        **(metadata or {})
                    }
                ))
        
        return chunks
    
    def chunk_by_sentences(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        Chunk by sentences instead of paragraphs.
        
        Useful for text where sentence boundaries are important.
        """
        chunks = []
        chunk_counter = 0
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            current_chunk.append(sentence)
            current_size += len(sentence)
            
            if current_size >= self.chunk_size:
                content = " ".join(current_chunk)
                chunk_counter += 1
                chunks.append(Chunk(
                    chunk_id=f"sentenced_{chunk_counter:04d}",
                    content=content[:self.chunk_size],
                    metadata={
                        "chunk_id": f"sentenced_{chunk_counter:04d}",
                        "sentence_count": len(current_chunk),
                        **(metadata or {})
                    }
                ))
                current_chunk = []
                current_size = 0
        
        # Don't forget the last chunk
        if current_chunk:
            content = " ".join(current_chunk)
            chunk_counter += 1
            chunks.append(Chunk(
                chunk_id=f"sentenced_{chunk_counter:04d}",
                content=content,
                metadata={
                    "chunk_id": f"sentenced_{chunk_counter:04d}",
                    "sentence_count": len(current_chunk),
                    **(metadata or {})
                }
            ))
        
        return chunks
    
    def smart_chunk(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        Smart fixed chunking that preserves content boundaries.
        
        Tries to split at natural boundaries (paragraphs, sections).
        Falls back to fixed splitting if no boundaries found.
        """
        chunks = []
        chunk_counter = 0
        
        # Try to detect content boundaries
        # Section headers
        section_pattern = re.compile(r'^(\d+\.\d*|Section\s+\d+|#\s+\w+:)', re.IGNORECASE)
        # Table markers
        table_pattern = re.compile(r'(?:Table\s+\d+:?|Fig\s+\d+:?)', re.IGNORECASE)
        # Code blocks
        code_pattern = re.compile(r'^```', re.MULTILINE)
        
        # Split by boundaries
        boundaries = []
        last_boundary = 0
        
        for match in section_pattern.finditer(text):
            boundaries.append(match.end())
        
        for match in table_pattern.finditer(text):
            boundaries.append(match.end())
        
        for match in code_pattern.finditer(text):
            boundaries.append(match.end())
        
        # Also add end of text
        boundaries.append(len(text))
        
        current_content = ""
        
        for boundary in boundaries:
            # Check if we need to save current chunk
            if len(current_content) >= self.chunk_size:
                chunk_counter += 1
                chunks.append(Chunk(
                    chunk_id=f"smart_{chunk_counter:04d}",
                    content=current_content[:self.chunk_size],
                    metadata={
                        "chunk_id": f"smart_{chunk_counter:04d}",
                        **(metadata or {})
                    }
                ))
            
            # Take content from last boundary to current boundary
            chunk_text = text[last_boundary:boundary]
            
            # If this chunk is too small, merge with previous
            if len(chunk_text) < self.min_content_length and chunks:
                if len(chunks[-1].content) < self.chunk_size * 2:
                    chunks[-1].content += " " + chunk_text
                else:
                    chunks.append(Chunk(
                        chunk_id=f"smart_{chunk_counter:04d}",
                        content=chunk_text[:min(len(chunk_text), self.chunk_size)],
                        metadata={
                            "chunk_id": f"smart_{chunk_counter:04d}",
                            **(metadata or {})
                        }
                    ))
                    chunk_counter += 1
            else:
                current_content = chunk_text
            
            last_boundary = boundary
        
        # Handle remaining content
        if current_content or (text[last_boundary:] and len(text[last_boundary:]) > 0):
            remaining = current_content + (text[last_boundary:] if last_boundary < len(text) else "")
            if remaining:
                chunk_counter += 1
                chunks.append(Chunk(
                    chunk_id=f"smart_{chunk_counter:04d}",
                    content=remaining[:self.chunk_size],
                    metadata={
                        "chunk_id": f"smart_{chunk_counter:04d}",
                        **(metadata or {})
                    }
                ))
        
        return chunks

# Quick test
if __name__ == "__main__":
    test_text = """
    Introduction
    This is a sample text with multiple paragraphs.
    The first paragraph discusses the introduction of our topic.
    It provides background information and sets the context.
    
    1. Main Topic
    This is the first main section.
    It contains detailed information about the primary subject.
    We will explore various aspects in depth.
    
    2. Sub-topic
    This is a subsection discussing a related topic.
    It provides additional context and supporting details.
    
    Conclusion
    We have covered the main points in this document.
    The key takeaways are...
    Thank you for reading.
    """
    
    chunker = FixedChunker(chunk_size=150, overlap=20)
    chunks = chunker.smart_chunk(test_text)
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\n{i+1}. [Chunk {chunk.chunk_id}]")
        print(chunk.content)
        print("-" * 50)