"""
RAG System Package - Main Entry Point

Usage:
    from rag_system import DemoRAGSystem
    
    system = DemoRAGSystem(documents_dir="./my_documents")
    system.add_documents()
    result = system.search("your question")
    print(result.answer)
"""

__version__ = "0.1.0"
__author__ = "RAG System Team"

# Import the main demo class
from .main import DemoRAGSystem
from .demo import main as run_demo

__all__ = [
    'DemoRAGSystem',
    'run_demo',
    'pdf_parser',
    'chunking',
    'vector_store'
]