"""
Semantic Chunker - Groups content by semantic similarity

Uses pattern matching and keyword analysis to identify related content.
Efficient for large documents without external embedding models.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import re
import string

@dataclass
class Chunk:
    """Represents a chunk of content."""
    chunk_id: str
    content: str
    metadata: Dict[str, str]
    
    @property
    def content_length(self) -> int:
        """Return length of content in characters."""
        return len(self.content)

class SemanticChunker:
    """
    Semantic-based chunking using keyword analysis.
    
    Instead of using external embeddings, this uses:
    - Pattern matching for section headers
    - Topic keyword extraction
    - Reference/frequency analysis
    
    This makes it fast and works offline without API costs.
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50,
        min_chunk_size: int = 100,
        section_threshold: float = 0.3
    ):
        """
        Initialize the semantic chunker.
        
        Args:
            chunk_size: Target size for each chunk
            overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum size before creating a chunk
            section_threshold: Threshold for creating new sections
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.section_threshold = section_threshold
        
        # Section pattern regex for detecting content boundaries
        self.section_patterns = {
            'section': r'(\d+\.\d*|Section\s+\d+|\d+\s+\w+)?:\s*\n?\s*',
            'subsection': r'(\d+\.\d+\.\d*|Subsection\s+\d+)?:\s*\n?\s*',
            'header': r'(##?#+\s+\S+)',
            'table': r'(?:Table\s+\d+|##?\s+\d+\.?\s*|\d+\s*\|\s*)',
            'code': r'```[\w\s]*?\n(?:.*?\n)*?```',
            'formula': r'(\d+\s*=|\(.*?\)|\[.*?\])',
            'reference': r'(?:\[\d+|\[\[\d+|\(?\d+[,)]?\)?|footnotes|references|bibliography)',
            'image': r'(?:Figure\s+\d+|Image\s+\d+|Appendix\s+\d+)',
            'appendix': r'(?:Appendix\s+\w+|Appendices)',
        }
        
        # Stop words to filter out (common English words)
        self.stop_words = set(string.punctuation + ' ' * len(string.punctuation))
        
        # Domain-specific keywords (can be customized)
        self._domain_keywords = {
            'legal': ['court', 'plaintiff', 'defendant', 'verdict', 'damages'],
            'scientific': ['hypothesis', 'method', 'results', 'conclusion', 'abstract'],
            'business': ['revenue', 'profit', 'growth', 'market', 'strategy'],
        }
        
        # Auto-detect document type
        self._detect_document_type = True
    
    def _extract_keywords(self, text: str, num_keywords: int = 20) -> List[str]:
        """Extract important keywords from text."""
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', text.lower())
        words = [w for w in words if len(w) > 2 and w not in self.stop_words]
        
        # Count frequency
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort by frequency
        most_common = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [w for w, _ in most_common[:num_keywords]]
    
    def _detect_sections(self, text: str, min_threshold: float = 0.3) -> List[Dict]:
        """
        Detect semantic section boundaries in text.
        
        A new section starts when:
        - A section pattern matches
        - Keyword density changes significantly
        """
        sections = []
        current_section = {"name": "", "content": "", "keywords": [], "start_pos": 0}
        pos = 0
        
        # Look for section headers
        for pattern_name, regex in self.section_patterns.items():
            for match in re.finditer(regex, text):
                section_end = match.end()
                section_start = match.start()
                
                # Extract content for this section
                if pattern_name == 'reference' and 'footnote' in pattern_name.lower():
                    # End current section
                    if current_section["content"] and len(current_section["content"]) > self.min_chunk_size:
                        sections.append(current_section)
                    sections.append({
                        "name": "References",
                        "content": text[section_start:section_end] if section_start < section_end else "",
                        "end_pos": section_end
                    })
                elif pattern_name == 'table':
                    if current_section["content"] and len(current_section["content"]) > self.min_chunk_size:
                        sections.append(current_section)
                    sections.append({
                        "name": "Tables",
                        "content": "",
                        "end_pos": section_end
                    })
                else:
                    # New content section
                    current_section = {
                        "name": match.group().strip(),
                        "content": text[section_start:section_end],
                        "keywords": [],
                        "end_pos": section_end
                    }
                pos = section_end
        
        # Add final section
        if current_section["content"]:
            sections.append(current_section)
        
        return sections
    
    def _calculate_keyword_similarity(self, text1: str, text2: str) -> float:
        """Calculate keyword similarity between two text segments."""
        keywords1 = self._extract_keywords(text1)
        keywords2 = self._extract_keywords(text2)
        
        set1 = set(keywords1)
        set2 = set(keywords2)
        
        # Jaccard similarity
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _detect_topic_changes(self, text: str, window_size: int = 500) -> List[float]:
        """Detect changes in topic across the document."""
        topic_changes = []
        window = text[:window_size]
        
        for i in range(0, len(text) - window_size, window_size // 2):
            current_window = text[i:i + window_size]
            previous_window = text[max(0, i - window_size // 2):i + window_size // 2]
            
            # Calculate topic similarity between windows
            if current_window and previous_window:
                similarity = self._calculate_keyword_similarity(current_window, previous_window)
                topic_changes.append((i, 1.0 - similarity))  # 1 - similarity = change
            else:
                topic_changes.append((i, 0.0))
        
        return topic_changes
    
    def _find_optimal_chunk_boundaries(self, topic_changes: List[tuple]) -> List[int]:
        """Find optimal chunk boundaries based on topic changes."""
        if not topic_changes:
            return []
        
        # Sort by change magnitude
        sorted_changes = sorted(topic_changes, key=lambda x: x[1], reverse=True)
        
        # Select significant changes (above threshold)
        boundaries = [change[0] for change in sorted_changes if change[1] > self.section_threshold]
        
        return boundaries[:10]  # Limit to 10 major boundaries
    
    def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        Chunk text semantically.
        
        Args:
            text: Text to chunk
            metadata: Document metadata
        
        Returns:
            List of Chunk objects
        """
        chunks = []
        chunk_counter = 0
        
        # Detect sections
        sections = self._detect_sections(text)
        
        # Detect major topic changes
        topic_changes = self._detect_topic_changes(text)
        optimal_boundaries = self._find_optimal_chunk_boundaries(topic_changes)
        
        # Group sections by topic changes
        processed_sections = []
        current_section = {"name": "", "content": "", "start_pos": 0, "topic": "general"}
        
        for section in sections:
            # Check if this is a major boundary
            found_boundary = False
            for boundary in optimal_boundaries:
                if boundary > section.get("start_pos", 0) and boundary < section.get("end_pos", len(text)):
                    # Save current section
                    if current_section["content"]:
                        processed_sections.append(current_section)
                    # Start new section
                    current_section = {
                        "name": section["name"],
                        "content": text[boundary:boundary + self.chunk_size],
                        "start_pos": boundary,
                        "topic": f"topic_{len(processed_sections) + 1}"
                    }
                    found_boundary = True
                    break
            
            if not found_boundary:
                current_section["content"] = section["content"][:self.chunk_size]
                current_section["start_pos"] = section.get("start_pos", 0)
                current_section["topic"] = section.get("topic", "general")
        
        # Add final section
        if current_section["content"]:
            processed_sections.append(current_section)
        
        # Create chunks from sections
        chunk_counter = 0
        for section in processed_sections:
            chunk_counter += 1
            
            # Ensure minimum chunk size
            content = section["content"]
            if len(content) < self.min_chunk_size:
                if chunks and len(chunks[-1].content) + len(content) >= self.min_chunk_size:
                    chunks[-1].content += content
                continue
            
            chunk = Chunk(
                chunk_id=f"semantic_{chunk_counter:04d}",
                content=content[:self.chunk_size],
                metadata={
                    "chunk_id": f"semantic_{chunk_counter:04d}",
                    "section": section["name"],
                    "topic": section.get("topic", "general"),
                    "start_pos": section.get("start_pos", 0),
                    "end_pos": section.get("end_pos", len(text)),
                    **(metadata or {})
                }
            )
            chunks.append(chunk)
        
        return chunks


# Quick test function
def test_semantic_chunker():
    """Test the semantic chunker with sample text."""
    sample_text = """
    Executive Summary
    This document provides an overview of our quarterly performance.
    Key metrics include revenue, expenses, and profit margins.
    
    1. Revenue Analysis
    Our revenue increased by 15% compared to the previous quarter.
    This growth was driven by increased sales in the North American region.
    We also saw strong performance in our European markets.
    
    2. Expense Breakdown
    Operating expenses increased by 8%, primarily due to:
    - Higher marketing costs
    - Increased employee benefits
    - Software subscription renewals
    
    3. Profit Margins
    Despite increased expenses, profit margins improved by 3%.
    This indicates better operational efficiency.
    
    References
    1. Q3 Financial Report - Company Internal
    2. Market Analysis Report - Consulting Firm
    """
    
    chunker = SemanticChunker(chunk_size=200, min_chunk_size=50)
    chunks = chunker.chunk(sample_text)
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\n{i+1}. {chunk.metadata.get('section', 'Unknown')}")
        print(chunk.content)
        print("-" * 50)
    
    return chunks

if __name__ == "__main__":
    test_semantic_chunker()