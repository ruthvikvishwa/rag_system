"""
Table-Aware Chunker - Keeps tables intact during chunking

Special handling for table content to prevent splitting tables
across multiple chunks.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re
import numpy as np

@dataclass
class Chunk:
    """Represents a chunk, possibly containing table data."""
    chunk_id: str
    content: str
    metadata: Dict[str, str]

class TableAwareChunker:
    """
    Chunk-aware of table structure.
    
    Keeps entire tables together and separates them from
    other content types during chunking.
    """
    
    def __init__(
        self,
        content_chunk_size: int = 500,
        table_chunk_size: int = 2000,
        figure_chunk_size: int = 1500,
        code_chunk_size: int = 2000,
        overlap: int = 50
    ):
        """
        Initialize with size limits for different content types.
        
        Args:
            content_chunk_size: Size for regular text chunks
            table_chunk_size: Size limit for table chunks
            figure_chunk_size: Size limit for figure/caption chunks
            code_chunk_size: Size limit for code blocks
            overlap: Overlap between chunks
        """
        self.content_chunk_size = content_chunk_size
        self.table_chunk_size = table_chunk_size
        self.figure_chunk_size = figure_chunk_size
        self.code_chunk_size = code_chunk_size
        self.overlap = overlap
        
        # Table detection patterns
        self.table_patterns = [
            r'\|\s*.*?\|',  # | col | col | pattern
            r'[|–—]+',  # ━ table separator
            r'^\d+\s*\|\s*',  # Number followed by |
        ]
        
        # Figure patterns
        self.figure_patterns = [
            r'(?:Figure\s+\d+|Fig\s+\d+|\[\d+\]\s*Figure)',
            r'(?:Image\s+\d+|Appendix\s+\d+)',
            r'(?:Table\s+\d+|Table:\s*\d+)',
        ]
        
        # Code block patterns
        self.code_patterns = [
            r'```(?:\w+)?',  # ```code``` or ```language```
            r'```',  # Simple code block
            r'<<<\w+.*?>>>',  # Markdown code blocks
        ]
    
    def detect_tables(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Detect tables in text.
        
        Returns:
            List of (table_text, start_pos, end_pos) tuples
        """
        tables = []
        pos = 0
        
        for pattern in self.table_patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                # Extract surrounding content
                table_start = max(pos, match.start())
                table_content = text[table_start:match.end()]
                
                # Look for table continuation
                current_pos = match.end()
                continuation = ""
                depth = 0
                
                for i in range(current_pos, min(current_pos + 1000, len(text))):
                    if text[i] == '|':
                        depth += 1
                    elif text[i] == '|' and depth == 0:
                        break
                    elif text[i] == '|':
                        depth -= 1
                
                if depth <= 0:
                    tables.append((table_content, table_start, i + 1))
                    pos = i + 1
        
        return tables
    
    def detect_figures(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Detect figure/table captions and references.
        
        Returns:
            List of (content, start_pos, end_pos) tuples
        """
        figures = []
        
        for pattern in self.figure_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Get full figure content (caption + description)
                start = match.start()
                end = start + self.figure_chunk_size
                
                # Look for continuation
                while end < len(text) and not re.match(r'(?i)(?:^|\n)(?:##?\s+\d+|Chapter|\d+\.\s+\w+)', text[end:end+20]):
                    end += 1
                
                figures.append((text[start:end], start, end))
        
        return figures
    
    def detect_code_blocks(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Detect code blocks.
        
        Returns:
            List of (code, start_pos, end_pos) tuples
        """
        code_blocks = []
        
        for pattern in self.code_patterns:
            for match in re.finditer(pattern, text):
                # Get full code block
                start = match.end()  # Start after backticks
                end = start
                
                # Count backticks to find closing
                depth = 0
                for i in range(start, min(start + 1000, len(text))):
                    if text[i] in ['`', '#']:
                        depth += 1
                    elif text[i] in ['`', '#']:
                        depth -= 1
                    
                    if depth <= 0:
                        end = i + 1
                        break
                
                code_blocks.append((text[start:end], start, end))
        
        return code_blocks
    
    def _remove_tables(self, text: str) -> str:
        """Remove tables from text for separate processing."""
        result = text
        for pattern in self.table_patterns:
            result = re.sub(pattern, '[TABLE]', result)
        return result
    
    def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        Chunk text while keeping tables together.
        
        Strategy:
        1. Extract all tables, figures, code
        2. Chunk regular text (replacing special elements)
        3. Create separate chunks for special elements
        4. Sort by position to maintain order
        """
        chunks = []
        chunk_counter = 0
        
        # Detect all special elements
        tables = self.detect_tables(text)
        figures = self.detect_figures(text)
        code_blocks = self.detect_code_blocks(text)
        
        # Create placeholders for text-only regions
        text_only = self._remove_tables(text)
        text_positions = self._extract_text_only_positions(text_only)
        
        # Chunk regular text (excluding special elements)
        text_chunks = []
        pos = 0
        current_content = []
        current_size = 0
        
        for word in re.findall(r'\S+', text_only):
            if pos + len(word) > len(text_positions):
                # Need to save current chunk
                if current_content and len(" ".join(current_content)) > self.content_chunk_size:
                    chunk_text = " ".join(current_content)
                    chunk_counter += 1
                    chunks.append(Chunk(
                        chunk_id=f"table_aware_text_{chunk_counter:04d}",
                        content=chunk_text,
                        metadata={
                            "chunk_type": "text",
                            "content_chunk_size": self.content_chunk_size,
                            **(metadata or {})
                        }
                    ))
                current_content = []
                current_size = 0
            
            current_content.append(word)
            current_size += len(word)
            pos += len(word)
        
        # Don't forget last chunk
        if current_content:
            chunk_counter += 1
            chunk_text = " ".join(current_content)
            chunks.append(Chunk(
                chunk_id=f"table_aware_text_{chunk_counter:04d}",
                content=chunk_text[:self.content_chunk_size],
                metadata={
                    "chunk_type": "text",
                    "content_chunk_size": self.content_chunk_size,
                    **(metadata or {})
                }
            ))
        
        # Create special element chunks
        for table_text, start, end in tables:
            if len(table_text) > self.table_chunk_size // 2:
                # Split large table
                for i in range(0, len(table_text), self.table_chunk_size // 2):
                    chunk_counter += 1
                    chunks.append(Chunk(
                        chunk_id=f"table_{chunk_counter:04d}",
                        content=table_text[i:i + self.table_chunk_size // 2],
                        metadata={
                            "chunk_type": "table",
                            "table_start": start,
                            "table_end": start + i + self.table_chunk_size // 2,
                            "original_position": start,
                            **(metadata or {})
                        }
                    ))
            else:
                chunk_counter += 1
                chunks.append(Chunk(
                    chunk_id=f"table_{chunk_counter:04d}",
                    content=table_text[:self.table_chunk_size],
                    metadata={
                        "chunk_type": "table",
                        "table_start": start,
                        "table_end": end,
                        "original_position": start,
                        **(metadata or {})
                    }
                ))
        
        for fig_text, start, end in figures:
            chunk_counter += 1
            chunks.append(Chunk(
                chunk_id=f"figure_{chunk_counter:04d}",
                content=fig_text[:self.figure_chunk_size],
                metadata={
                    "chunk_type": "figure",
                    "figure_start": start,
                    "original_position": start,
                    **(metadata or {})
                }
            ))
        
        for code_text, start, end in code_blocks:
            chunk_counter += 1
            chunks.append(Chunk(
                chunk_id=f"code_{chunk_counter:04d}",
                content=code_text[:self.code_chunk_size],
                metadata={
                    "chunk_type": "code",
                    "code_start": start,
                    "original_position": start,
                    **(metadata or {})
                }
            ))
        
        # Sort by position to maintain reading order
        chunks.sort(key=lambda c: c.metadata.get('original_position', float('inf')))
        
        return chunks
    
    def _extract_text_only_positions(self, text: str) -> List[Tuple[int, str]]:
        """Extract positions and content from text-only regions."""
        positions = []
        pos = 0
        
        while pos < len(text):
            # Find next special element
            next_match = None
            for pattern in self.table_patterns + self.figure_patterns + self.code_patterns:
                match = re.search(pattern, text[pos:])
                if match:
                    next_match = (pos + match.start(), pos + match.end())
                    break
            
            if next_match:
                positions.append((next_match[0], next_match[1]))
                pos = next_match[0]
            else:
                positions.append((pos, len(text)))
        
        return positions


# Quick test
if __name__ == "__main__":
    sample_text = """
    # Quarterly Report

    ## Financial Summary

    This quarter we achieved significant growth in revenue and profitability.
    Key metrics show strong performance across all business units.

    | Metric | Q3 2024 | Q2 2024 | Change |
    |--------|--------|--------|--------|
    | Revenue | $125M | $100M | +25% |
    | Profit  | $18M   | $14M   | +28% |
    | Growth  | 14.5%  | 12%    | +2.5% |

    ## Operational Performance

    Our operational efficiency improved significantly this quarter.
    We reduced costs by 8% while increasing output by 12%.

    ```python
    def calculate_metrics(data):
        revenue = data['revenue']
        profit = data['profit']
        growth = ((revenue - prev_revenue) / prev_revenue) * 100
        return {'revenue': revenue, 'profit': profit, 'growth': growth}
    ```

    ## Regional Breakdown

    | Region | Revenue | Market Share |
    |--------|--------|-------------|
    | NA     | $75M   | 60%         |
    | EU     | $35M   | 28%         |
    | Asia   | $15M   | 12%         |

    ## Conclusion

    Overall performance exceeds expectations for Q3 2024.
    Strategic initiatives are delivering results.
    """
    
    chunker = TableAwareChunker(
        content_chunk_size=200,
        table_chunk_size=300,
        code_chunk_size=200
    )
    
    chunks = chunker.chunk(sample_text)
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\n{i+1}. [{chunk.metadata['chunk_type']}] {chunk.chunk_id}")
        print(f"   Content preview: {chunk.content[:100]}...")