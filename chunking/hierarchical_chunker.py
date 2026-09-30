"""
Hierarchical Chunker - Preserves document structure

Chunks documents maintaining the hierarchy:
Document → Sections → Pages → Chunks

Useful when you need to preserve context and document navigation.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import re
from tqdm import tqdm

@dataclass
class Chunk:
    """Represents a hierarchical chunk with full context."""
    chunk_id: str
    content: str
    metadata: Dict[str, str]

class HierarchicalChunker:
    """
    Hierarchical chunking preserves document structure.
    
    Level 1: Document level (full document summary)
    Level 2: Section level (full sections)
    Level 3: Page level (page summaries)
    Level 4: Content chunks (fixed-size pieces)
    
    This allows users to navigate from broad to specific.
    """
    
    def __init__(
        self,
        page_chunk_size: int = 500,
        content_chunk_size: int = 500,
        overlap: int = 50,
        include_headers: bool = True,
        include_page_numbers: bool = True
    ):
        """
        Initialize the hierarchical chunker.
        
        Args:
            page_chunk_size: Max size per page chunk
            content_chunk_size: Max size for content chunks
            overlap: Overlap between chunks
            include_headers: Include section/page headers
            include_page_numbers: Include page numbers in output
        """
        self.page_chunk_size = page_chunk_size
        self.content_chunk_size = content_chunk_size
        self.overlap = overlap
        self.include_headers = include_headers
        self.include_page_numbers = include_page_numbers
    
    def chunk_document(self, document_info: Dict) -> List[Chunk]:
        """
        Chunk a document hierarchically.
        
        Args:
            document_info: Dict with keys:
                - content: Full document text
                - pages: List of page numbers
                - sections: List of section titles
                - metadata: Document metadata
        
        Returns:
            List of Chunk objects at all hierarchy levels
        """
        all_chunks = []
        content = document_info.get('content', '')
        pages = document_info.get('pages', [])
        metadata = document_info.get('metadata', {})
        doc_id = metadata.get('doc_id', 'unknown')
        
        # Level 1: Document summary (full doc if small enough)
        doc_chunk = self._create_document_chunk(content, metadata)
        all_chunks.append(doc_chunk)
        
        # Level 2: Section chunks
        section_chunks = self._chunk_by_sections(content, metadata)
        all_chunks.extend(section_chunks)
        
        # Level 3: Page chunks
        page_chunks = self._chunk_by_pages(content, pages)
        all_chunks.extend(page_chunks)
        
        # Level 4: Content chunks (fine-grained)
        content_chunks = self._chunk_content(content, doc_id)
        all_chunks.extend(content_chunks)
        
        return all_chunks
    
    def _create_document_chunk(self, content: str, metadata: Dict) -> Chunk:
        """Create a chunk representing the entire document."""
        return Chunk(
            chunk_id=f"doc_{metadata.get('doc_id', 'unknown')}_DOC",
            content=f"DOCUMENT: {metadata.get('doc_title', 'Untitled Document')}\n\n{content[:500]}",
            metadata={
                "doc_id": metadata.get('doc_id', 'unknown'),
                "doc_title": metadata.get('doc_title', 'Untitled'),
                "doc_path": metadata.get('doc_path', ''),
                "doc_type": metadata.get('content_type', 'unknown'),
                "total_pages": len(pages),
                "content_level": "document"
            }
        )
    
    def _detect_sections(self, content: str) -> List[str]:
        """
        Detect section boundaries in content.
        
        Returns:
            List of section titles
        """
        sections = []
        section_patterns = {
            r'(##?\s+\S+|\d+\.\d*:\s*|\d+\s+\w+:\s*)',  # Markdown, numbered, etc.
            r'(Chapter\s+\d+|\d+\.\s+\w+)',  # Chapter pattern
        }
        
        current_section = ""
        
        for pattern in section_patterns:
            for match in re.finditer(pattern, content):
                section_name = match.group()
                # Look ahead to get full section name
                pos = match.start()
                before = content[max(0, pos - 50):pos]
                words = re.findall(r'\b\w+\b', before)
                if words:
                    section_name = words[-1] + " " + section_name
                sections.append(section_name)
                break  # Use first matching pattern
        
        return sections[:10]  # Limit to first 10 sections
    
    def _chunk_by_sections(self, content: str, metadata: Dict) -> List[Chunk]:
        """
        Create chunks for each section.
        
        Splits content by section headers and creates chunks for each.
        """
        chunks = []
        chunk_counter = 0
        
        # Detect sections
        sections = self._detect_sections(content)
        
        for section_title in sections:
            # Find section content
            pattern = rf'{re.escape(section_title)}.*?(?=\n{re.escape(sections[0] if len(sections) > 1 else "")}|$)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                section_content = match.group(0)
                chunk_counter += 1
                
                # Add header if enabled
                chunk_content = section_content
                if self.include_headers:
                    chunk_content = f"## {section_title}\n\n{chunk_content}"
                
                # Add section info
                metadata_with_section = metadata.copy()
                metadata_with_section['current_section'] = section_title
                metadata_with_section['section_level'] = 2
                
                chunks.append(Chunk(
                    chunk_id=f"doc_{metadata['doc_id']}_section_{chunk_counter:04d}",
                    content=chunk_content[:self.content_chunk_size],
                    metadata={
                        **metadata_with_section,
                        "section": section_title,
                        "section_level": 2,
                        "content_level": "section"
                    }
                ))
        
        return chunks
    
    def _chunk_by_pages(self, content: str, page_numbers: List[int]) -> List[Chunk]:
        """
        Create chunks for each page.
        
        Useful when the query is page-specific.
        """
        chunks = []
        
        for page_num in page_numbers:
            # Find page content
            page_start = page_num * self.page_chunk_size
            if page_num == 0:
                page_content = content[:self.page_chunk_size]
            else:
                page_content = content[page_start:page_start + self.page_chunk_size]
            
            if not page_content.strip():
                continue
            
            chunk_counter = 1
            for _ in range(page_num):
                chunk_counter += 1
            
            chunks.append(Chunk(
                chunk_id=f"doc_{self._extract_doc_id(content)}_page_{page_num}_level3",
                content=page_content,
                metadata={
                    **self._extract_metadata(content),
                    "page": page_num,
                    "page_level": 3,
                    "content_level": "page"
                }
            ))
        
        return chunks
    
    def _extract_doc_id(self, content: str) -> str:
        """Extract document ID from content."""
        # Look for doc_id in metadata or content
        match = re.search(r'doc_id[:\s]*([^\s\,\.]+)', content, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return "unknown"
    
    def _extract_metadata(self, content: str) -> Dict:
        """Extract metadata from content."""
        metadata = {}
        
        # Title
        title_match = re.search(r'(?:Title:|Title\s*:|title)\s*([^\n]+)', content, re.IGNORECASE)
        if title_match:
            metadata['doc_title'] = title_match.group(1).strip()
        
        # Path
        path_match = re.search(r'(?:Path:|Path\s*:|file)\s*([^\n]+)', content, re.IGNORECASE)
        if path_match:
            metadata['doc_path'] = path_match.group(1).strip()
        
        return metadata
    
    def _chunk_content(self, content: str, doc_id: str) -> List[Chunk]:
        """
        Create fine-grained content chunks.
        
        Simple fixed-size chunks with document-level metadata.
        """
        chunks = []
        chunk_counter = 0
        
        # Clean content
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        current_chunk = []
        current_size = 0
        
        for char in content:
            current_chunk.append(char)
            current_size += 1
            
            if current_size >= self.content_chunk_size:
                chunk_counter += 1
                chunk_text = ''.join(current_chunk)
                overlap_text = chunk_text[-self.overlap:]
                
                chunks.append(Chunk(
                    chunk_id=f"doc_{doc_id}_content_{chunk_counter:04d}",
                    content=chunk_text[:-len(overlap_text)],
                    metadata={
                        "doc_id": doc_id,
                        "chunk_overlap": overlap_text,
                        "content_level": "fine",
                        "overlap": self.overlap
                    }
                ))
                
                current_chunk = []
                current_size = 0
        
        # Don't forget the last chunk
        if current_chunk or chunk_counter == 0:
            chunk_counter += 1
            chunk_text = ''.join(current_chunk)
            chunks.append(Chunk(
                chunk_id=f"doc_{doc_id}_content_{chunk_counter:04d}",
                content=chunk_text[:self.content_chunk_size],
                metadata={
                    "doc_id": doc_id,
                    "content_level": "fine"
                }
            ))
        
        return chunks
    
    def chunk_with_navigation(self, document_info: Dict) -> Dict:
        """
        Chunk with navigation structure.
        
        Returns hierarchical structure for easier navigation:
        {
            "document": {...},
            "sections": [
                {"section": "...", "page": 1, "subsections": [...]},
                {"section": "...", "page": 2, "subsections": [...]}
            ],
            "pages": [...],
            "chunks": [...]
        }
        """
        chunks = self.chunk_document(document_info)
        
        return {
            "document": chunks[0] if chunks else None,
            "sections": [c for c in chunks if c.metadata.get('section_level') == 2],
            "pages": [c for c in chunks if c.metadata.get('page_level') == 3],
            "content": [c for c in chunks if c.metadata.get('content_level') == 'fine'],
            "navigation": {
                "doc_id": document_info.get('doc_id', 'unknown'),
                "doc_title": document_info.get('doc_title', 'Unknown'),
                "total_sections": len([c for c in chunks if c.metadata.get('section_level') == 2]),
                "total_pages": len(document_info.get('pages', []))
            }
        }


# Quick test
if __name__ == "__main__":
    sample_doc = {
        "content": """
        # Executive Summary
        
        This is the executive summary of our Q4 report.
        We achieved remarkable growth across all key metrics.
        Revenue increased by 25%, up from 18% in Q3.
        
        ## Financial Performance
        
        Our financial performance has been outstanding.
        - Revenue: $125M (up 25% YoY)
        - Net Income: $18M (up 30% YoY)
        - Operating Margin: 14.5% (up from 12%)
        
        The growth was driven by strong performance in:
        - North American market
        - European expansion
        - New product launches
        
        ## Operational Highlights
        
        Operationally, we streamlined our processes and reduced costs.
        Headcount increased by 15%, supporting our growth trajectory.
        Technology investments increased by 20%.
        
        ## Outlook
        
        For Q1 2025, we project:
        - Revenue: $140M
        - Continued market expansion
        - New product launches in Asia
        
        ## Conclusion
        
        Overall, Q4 2024 was a highly successful quarter.
        We are well-positioned for continued growth in 2025.
        Thank you for your continued support.
        """,
        "pages": [0, 1, 2],
        "sections": ["Executive Summary", "Financial Performance", "Operational Highlights", "Outlook", "Conclusion"],
        "metadata": {
            "doc_id": "q4_report_2024",
            "doc_title": "Q4 2024 Annual Report",
            "doc_path": "/reports/q4_2024.pdf",
            "content_type": "text"
        }
    }
    
    chunker = HierarchicalChunker(page_chunk_size=200, content_chunk_size=200)
    result = chunker.chunk_document(sample_doc)
    
    print(f"Created {len(result)} chunks at all hierarchy levels:")
    for i, chunk in enumerate(result):
        print(f"\n{i+1}. {chunk.chunk_id}")
        print(f"   Level: {chunk.metadata.get('content_level', chunk.metadata.get('section_level', 'doc'))}")
        print(f"   Content: {chunk.metadata.get('section', chunk.metadata.get('doc_title', 'Unknown'))}")
        print(f"   Page: {chunk.metadata.get('page', 'N/A')}")
        print("-" * 60)