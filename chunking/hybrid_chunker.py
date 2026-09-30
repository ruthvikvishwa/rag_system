"""
Hybrid Chunker - Combines multiple chunking strategies

Intelligently combines semantic, table-aware, and fixed chunking
for optimal results with mixed-content documents.
"""

from typing import List, Dict, Optional, Union
from dataclasses import dataclass, field
import re
from tqdm import tqdm

# Import other chunkers
from .semantic_chunker import SemanticChunker
from .table_aware_chunker import TableAwareChunker
from .fixed_chunker import FixedChunker

@dataclass
class HybridChunk:
    """Chunk with enhanced metadata from hybrid strategy."""
    chunk_id: str
    content: str
    metadata: Dict[str, str]
    source_type: str  # "semantic", "table", "code", "text"
    
    @property
    def content_length(self) -> int:
        return len(self.content)

class HybridChunker:
    """
    Hybrid chunker that combines multiple strategies.
    
    Strategy:
    1. First pass: Detect and separate content types
    2. Second pass: Apply appropriate chunking to each type
    3. Merge and sort by position
    4. Add cross-document references
    
    This approach preserves:
    - Document structure
    - Table integrity
    - Semantic coherence
    """
    
    def __init__(
        self,
        content_chunk_size: int = 500,
        table_chunk_size: int = 2000,
        code_chunk_size: int = 2000,
        semantic_window: int = 500,
        overlap: int = 50,
        max_chunks_per_doc: int = 500,
        include_references: bool = True
    ):
        """
        Initialize hybrid chunker.
        
        Args:
            content_chunk_size: Size for regular text chunks
            table_chunk_size: Size for table chunks
            code_chunk_size: Size for code chunks
            semantic_window: Window size for semantic chunking
            overlap: Overlap between chunks
            max_chunks_per_doc: Limit chunks per document
            include_references: Whether to add cross-reference chunks
        """
        self.content_chunk_size = content_chunk_size
        self.table_chunk_size = table_chunk_size
        self.code_chunk_size = code_chunk_size
        self.semantic_window = semantic_window
        self.overlap = overlap
        self.max_chunks_per_doc = max_chunks_per_doc
        self.include_references = include_references
        
        # Initialize sub-chunkers
        self.semantic_chunker = SemanticChunker(
            chunk_size=semantic_window,
            overlap=overlap
        )
        self.table_chunker = TableAwareChunker(
            content_chunk_size=content_chunk_size,
            table_chunk_size=table_chunk_size
        )
        self.fixed_chunker = FixedChunker(
            chunk_size=content_chunk_size,
            overlap=overlap
        )
    
    def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[HybridChunk]:
        """
        Chunk text using hybrid strategy.
        
        Args:
            text: Text to chunk
            metadata: Document metadata
        
        Returns:
            List of HybridChunk objects
        """
        chunks = []
        chunk_counter = 0
        
        # Step 1: Classify and extract content types
        text_sections = self._classify_sections(text)
        
        # Step 2: Apply appropriate chunker to each type
        processed_chunks = []
        
        # Process text sections
        text_content = text_sections.get('text', '')
        if text_content.strip():
            text_chunks = self._chunk_text_sections(text_content, metadata)
            processed_chunks.extend(text_chunks)
        
        # Process tables
        tables = text_sections.get('tables', [])
        for table in tables[:10]:  # Limit to first 10 tables
            table_text = table.get('text', '')
            if len(table_text) > self.table_chunk_size // 2:
                for i in range(0, len(table_text), self.table_chunk_size // 2):
                    chunk_counter += 1
                    chunks.append(HybridChunk(
                        chunk_id=f"hybrid_table_{chunk_counter:04d}",
                        content=table_text[i:i + self.table_chunk_size // 2],
                        metadata={
                            **table.get('metadata', {}),
                            "source_type": "table",
                            "chunk_type": "table_fragment",
                            "table_fragment": i // (self.table_chunk_size // 2),
                            **(metadata or {})
                        }
                    ))
            else:
                chunk_counter += 1
                chunks.append(HybridChunk(
                    chunk_id=f"hybrid_table_{chunk_counter:04d}",
                    content=table_text[:self.table_chunk_size],
                    metadata={
                        **table.get('metadata', {}),
                        "source_type": "table",
                        "chunk_type": "table",
                        **(metadata or {})
                    }
                ))
        
        # Process code blocks
        code_blocks = text_sections.get('code', [])
        for code in code_blocks[:10]:  # Limit to first 10 code blocks
            chunk_counter += 1
            chunks.append(HybridChunk(
                chunk_id=f"hybrid_code_{chunk_counter:04d}",
                content=code[:self.code_chunk_size],
                metadata={
                    "source_type": "code",
                    "code_language": code.get('language', 'unknown'),
                    **(metadata or {})
                }
            ))
        
        # Process OCR/text content
        ocr_content = text_sections.get('ocr', '')
        if ocr_content.strip():
            # Use fixed chunking for OCR content
            ocr_chunks = self.fixed_chunker.chunk(ocr_content, metadata)
            for oc in ocr_chunks:
                chunk_counter += 1
                chunks.append(HybridChunk(
                    chunk_id=f"hybrid_ocr_{chunk_counter:04d}",
                    content=oc.content,
                    metadata={
                        **oc.metadata,
                        "source_type": "ocr",
                        "chunk_type": "text",
                        **(metadata or {})
                    }
                ))
        
        # Limit total chunks
        if len(chunks) > self.max_chunks_per_doc:
            chunks = chunks[:self.max_chunks_per_doc]
        
        return chunks
    
    def _classify_sections(self, text: str) -> Dict:
        """
        Classify text into sections by type.
        
        Returns:
            Dict with 'text', 'tables', 'code', 'ocr' keys
        """
        result = {
            'text': [],
            'tables': [],
            'code': [],
            'ocr': []
        }
        
        # Detect tables
        table_pattern = r'(?<=\n)\|[^\n]*\n([^\n]+\n[^|][^\n]+\n)[^\n]*\n(?=\|)'
        tables = re.findall(table_pattern, text)
        
        # Code blocks
        code_blocks = []
        for match in re.finditer(r'```[\s\S]*?```', text):
            code_blocks.append({
                'text': match.group(),
                'language': match.group()[:3],
                'start': match.start()
            })
        
        # OCR/extracted text
        remaining_text = text
        for tbl in tables:
            remaining_text = remaining_text.replace(tbl, '')
        for code in code_blocks:
            remaining_text = remaining_text.replace(code['text'], '')
        
        result['tables'] = tables[:10]  # Limit tables
        result['code'] = code_blocks[:10]  # Limit code blocks
        result['ocr'] = remaining_text
    
    def _chunk_text_sections(self, text: str, metadata: Optional[Dict]) -> List[HybridChunk]:
        """
        Chunk text sections using semantic chunking.
        """
        chunks = []
        
        # Use semantic chunking for text
        semantic_chunks = self.semantic_chunker.chunk(text)
        
        for sc in semantic_chunks:
            chunk_counter += 1
            chunks.append(HybridChunk(
                chunk_id=f"hybrid_semantic_{chunk_counter:04d}",
                content=sc.content,
                metadata={
                    **sc.metadata,
                    "source_type": "semantic",
                    "chunk_type": "text",
                    **(metadata or {})
                }
            ))
        
        return chunks
    
    def chunk_document(self, document_info: Dict) -> List[HybridChunk]:
        """
        Chunk a complete document.
        
        Args:
            document_info: Dict with 'content', 'pages', 'metadata'
        
        Returns:
            List of HybridChunk objects
        """
        all_chunks = []
        content = document_info.get('content', '')
        metadata = document_info.get('metadata', {})
        doc_id = metadata.get('doc_id', 'unknown')
        
        # Chunk the document content
        document_chunks = self.chunk(content, metadata)
        all_chunks.extend(document_chunks)
        
        # Add document-level chunk
        all_chunks.insert(0, HybridChunk(
            chunk_id=f"hybrid_doc_{doc_id}",
            content=f"Document: {metadata.get('doc_title', 'Untitled')} ({len(content)} chars)",
            metadata={
                "doc_id": doc_id,
                "doc_title": metadata.get('doc_title', 'Untitled'),
                "doc_path": metadata.get('doc_path', ''),
                "source_type": "document",
                "content_type": "document_summary",
                "total_chunks": len(document_chunks)
            }
        ))
        
        return all_chunks
    
    def smart_chunk(
        self,
        text: str,
        metadata: Optional[Dict] = None,
        auto_detect: bool = True
    ) -> List[HybridChunk]:
        """
        Smart chunking with automatic strategy selection.
        
        Analyzes content and selects best chunking strategy.
        """
        if auto_detect:
            # Analyze content distribution
            text_count = len(re.findall(r'\n\n(?=[A-Z][a-z]+)', text))
            table_count = len(re.findall(r'\|\s*.*?\|', text))
            code_count = len(re.findall(r'```', text))
            
            # Select strategy based on content
            if table_count > text_count * 0.5:
                from .table_aware import TableAwareChunker
                chunker = TableAwareChunker(
                    content_chunk_size=self.content_chunk_size,
                    table_chunk_size=self.table_chunk_size
                )
            elif code_count > text_count * 0.3:
                from .code_aware import CodeAwareChunker
                chunker = CodeAwareChunker(
                    text_chunk_size=self.content_chunk_size,
                    code_chunk_size=self.code_chunk_size
                )
            else:
                from .semantic import SemanticChunker
                chunker = SemanticChunker(
                    chunk_size=self.semantic_window,
                    overlap=self.overlap
                )
        else:
            # Explicit strategy
            if metadata and metadata.get('content_type') == 'table':
                from .table_aware import TableAwareChunker
                chunker = TableAwareChunker(
                    content_chunk_size=self.content_chunk_size,
                    table_chunk_size=self.table_chunk_size
                )
            elif metadata and metadata.get('content_type') == 'code':
                from .code_aware import CodeAwareChunker
                chunker = CodeAwareChunker(
                    text_chunk_size=self.content_chunk_size,
                    code_chunk_size=self.code_chunk_size
                )
            else:
                from .semantic import SemanticChunker
                chunker = SemanticChunker(
                    chunk_size=self.semantic_window,
                    overlap=self.overlap
                )
        
        return chunker.chunk(text, metadata)


# Usage examples
if __name__ == "__main__":
    sample_text = """
    # Business Report - Q3 2024

    ## Executive Summary
    This quarter we achieved remarkable growth across all key metrics.
    Revenue increased by 25%, exceeding our targets by 5%.
    Profit margins improved from 12% to 15%.
    
    ## Financial Performance
    Key financial metrics for Q3 2024:
    
    | Metric | Q3 2024 | Q2 2024 | Q3 2023 | YoY Change |
    |--------|--------|--------|--------|------------|
    | Revenue | $125M  | $100M  | $85M   | +47%       |
    | Profit  | $18M   | $14M   | $10M   | +80%       |
    | Margin  | 15%    | 14%    | 12%    | +3%        |
    | Growth  | 25%    | 18%    | 22%    | +3%        |

    The growth was driven by:
    1. New product launches in North America
    2. European market expansion
    3. Operational efficiency improvements
    
    ## Operational Highlights
    
    ```python
    # Revenue calculation
    def calculate_revenue(reports):
        total = 0
        for region, data in reports.items():
            total += data['monthly_revenue']
        return total
    
    # Profit margin
    def calculate_margin(revenue, expenses):
        return ((revenue - expenses) / revenue) * 100
    ```

    Key operational achievements:
    - Reduced overhead by 8%
    - Increased headcount by 15%
    - Implemented new CRM system
    
    ## Regional Breakdown
    
    | Region | Revenue | Market Share | Growth |
    |--------|--------|-------------|--------|
    | NA     | $75M   | 60%         | +28%   |
    | EU     | $35M   | 28%         | +22%   |
    | Asia   | $15M   | 12%         | +18%   |
    
    ## Strategic Initiatives
    
    We launched three major initiatives:
    1. AI-powered customer service
    2. Cloud migration
    3. Mobile app enhancement
    
    Each initiative is on track to deliver value by Q4 2024.
    
    ## Outlook for Q4 2024
    
    We project continued growth with:
    - Revenue: $140M (12% increase)
    - New product launches: 3
    - Market expansion: 2 new regions
    
    ## Conclusion
    
    Q3 2024 was a highly successful quarter.
    Strategic initiatives are paying off.
    We are well-positioned for 2025.
    """
    
    chunker = HybridChunker(
        content_chunk_size=300,
        table_chunk_size=1500,
        code_chunk_size=800,
        overlap=50
    )
    
    chunks = chunker.chunk(sample_text)
    
    print(f"Created {len(chunks)} hybrid chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\n{i+1}. [{chunk.source_type.upper()}] {chunk.chunk_id}")
        print(f"   Length: {chunk.content_length} chars")
        print(f"   Type: {chunk.metadata.get('chunk_type', chunk.metadata.get('source_type', 'unknown'))}")
        print(f"   Preview: {chunk.content[:200]}...")
        print("-" * 70)