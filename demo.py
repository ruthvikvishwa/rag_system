"""
RAG System Demo

Interactive demonstration of the RAG system functionality.

Run this script to:
1. See document processing pipeline
2. Test different chunking strategies
3. Try sample queries
4. Compare results
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_system import DemoRAGSystem

def main():
    """Main demo function."""
    print("=" * 70)
    print(" " * 20 + "🚀 RAG SYSTEM DEMO")
    print("=" * 70)
    
    # Create the RAG system
    print("\n[1] Initializing RAG System...")
    system = DemoRAGSystem(
        documents_dir="./demo_documents",
        persist=True,
        chunk_size=400,
        top_k=5
    )
    
    print("\n[2] Welcome! Let's see what we have:")
    print("\nSystem Configuration:")
    print(f"  - Documents Directory: {system.documents_dir}")
    print(f"  - Chunk Size: {system.chunk_size}")
    print(f"  - Top-K: {system.top_k}")
    print(f"  - Re-ranking: Enabled" if system.rag_system.rerank else "Disabled")
    print(f"  - Vector Backend: {system.vector_store.backend.value}")
    
    # Demo queries
    demo_queries = [
        "What are the main topics discussed in the document?",
        "Summarize the key findings.",
        "What challenges are mentioned?",
        "How do the results compare to previous periods?",
    ]
    
    print("\n[3] Running Demo Queries...")
    print("=" * 70)
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"Question: {query}")
        
        result = system.search(query)
        
        print(f"\nAnswer:")
        print(result.answer)
        
        print(f"\nSources ({len(result.sources)} chunks found):")
        for j, source in enumerate(result.sources[:3], 1):
            meta = source['metadata']
            print(f"  {j}. {meta.get('doc_title', 'Unknown')} (Page {meta.get('page', '?')})")
            print(f"     Score: {source.get('score', 0):.3f}")
        
        print(f"\nConfidence: {result.confidence * 100:.1f}%")
        print(f"Processing Time: {result.processing_time:.2f}s")
    
    # Print statistics
    print("\n" + "=" * 70)
    print("[4] System Statistics")
    print("=" * 70)
    
    stats = system.get_statistics()
    print(f"\nTotal Documents Indexed: {stats}")
    print(f"Total Chunks in Vector Store: {stats}")
    
    # Interactive query
    print("\n" + "=" * 70)
    print("[5] Interactive Mode")
    print("=" * 70)
    print("\nEnter your query (or 'quit' to exit):")
    
    while True:
        try:
            user_query = input("\n📝 Your Query: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for using RAG System!")
                break
            
            if not user_query:
                print("Please enter a non-empty query.")
                continue
            
            result = system.search(user_query)
            print("\n" + "-" * 70)
            print("Answer:")
            print("-" * 70)
            print(result.answer)
            print("-" * 70)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Exiting...")
            break
        except EOFError:
            break
    
    return 0

if __name__ == "__main__":
    try:
        exit(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)