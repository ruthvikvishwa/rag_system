# RAG System - Complete Usage Guide

## 📋 Overview

This guide shows you **exactly how to use** the RAG system, including:
- Installation and setup
- Adding your documents (PDFs, MD files, etc.)
- Searching and querying
- Integrating with your LLM (OpenAI, Claude, etc.)
- Memory optimization for large document collections

---

## 🚀 Quick Start

### Step 1: Setup

```bash
# Navigate to project
cd /Users/ruthvik/rag_system

# Verify everything is ready
ls -la

# Run the demo to test
python3 demo.py
```

### Step 2: Add Your Documents

```bash
# Navigate to documents folder
cd documents

# Place all your PDFs and MD files here
# For example:
# - employee_handbook.pdf
# - sales_report_Q3.pdf
# - company_policy.md
# - project_docs.md

cd ..  # Go back to rag_system
```

### Step 3: Initialize the System

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')

print('✅ RAG System initialized!')
print('   System:', system)
"
```

**Output:**
```
🚀 Initializing RAG System...
✅ RAG System initialized!
   Documents dir: documents
   Chunk size: 500
   Vector backend: chromadb
```

### Step 4: Add Your Documents

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')

print('\\n📄 Adding documents from:', system.documents_dir)

# Add all documents
system.add_documents()

print(f'\\n✅ {system.rag_system.get_statistics()} chunks indexed!')
"
```

**Output:**
```
📄 Adding documents from: documents
   Found 5 PDF files
   Processing...
   ✅ Documents processed!
   ✅ Chunks created and indexed!
   Total chunks indexed: 125
```

### Step 5: Start Searching!

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

# Search for a question
result = system.search('What is the revenue in Q3 2024?')

print('\\n📝 Answer:')
print(result.answer)

print('\\nConfidence:', result.confidence*100, '%')
"
```

**Output:**
```
🔍 Searching for: What is the revenue in Q3 2024?

📝 Answer:
Based on the retrieved documents...

📚 Sources:
[1] Sales Report Q3 2024
   Score: 0.92
[2] Company Policy
   Score: 0.78
```

---

## 🎯 Basic Usage Examples

### Example 1: Single Query

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

result = system.search('What are the key findings in Q3 2024?')

print('=== Answer ===')
print(result.answer)
"
```

### Example 2: Multiple Queries

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

# Multiple questions
queries = [
    'What is the revenue forecast for 2025?',
    'Who is the CEO?',
    'What are the company policies?',
    'Summarize all reports'
]

for q in queries:
    result = system.search(q)
    print(f'\\n=== Q: {q[:30]}... ===')
    print('A:', result.answer[:200])
"
```

### Example 3: Search Specific Document

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

# Search within ONE document
result = system.search_by_document('employee_handbook.pdf', 
                                  'What are the leave policies?')

print('=== Specific Document Search ===')
print('Document:', result.chunk_ids[0])
print('Answer:')
print(result.answer)
"
```

### Example 4: Get Documents List

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

# List all indexed documents
import os
docs_dir = system.documents_dir
print('=== Indexed Documents ===')
for f in os.listdir(docs_dir):
    print(f'   - {f}')
"
```

---

## 🔗 Integrating with Your LLM

This is the **most important part** - connecting RAG with your LLM!

### Setup Your LLM Client

#### Option 1: OpenAI

```bash
# Install OpenAI Python library
pip3 install openai

# Set your API key
export OPENAI_API_KEY='your-api-key-here'
```

#### Option 2: Anthropic (Claude)

```bash
pip3 install anthropic
export ANTHROPIC_API_KEY='your-api-key-here'
```

### Integration Example with OpenAI

```python
from rag_system import DemoRAGSystem
from openai import OpenAI

# Initialize RAG system
rag = DemoRAGSystem(documents_dir='./documents')
rag.add_documents()

# Initialize OpenAI client
client = OpenAI()

def chat_with_rag(query, chat_history=None):
    """
    Chat with your documents using RAG.
    
    Args:
        query: Your question
        chat_history: List of previous messages (for multi-turn chat)
    
    Returns:
        LLM response
    """
    
    # Step 1: Search RAG for relevant chunks
    rag_result = rag.search(
        query=query,
        k=5,  # Number of chunks to retrieve
        use_rerank=True  # Improve result quality
    )
    
    # Step 2: Build context for LLM
    context = rag_result.answer
    
    # Step 3: Build LLM messages
    messages = []
    
    if chat_history:
        # Add conversation history
        for msg in chat_history[-5:]:  # Only last 5 messages
            messages.append(msg)
    
    # System instruction
    system_msg = 'You are a helpful assistant. Answer based ONLY on the provided context. '
    system_msg += 'If you cannot find the answer in the context, state that explicitly.'
    
    messages.append({'role': 'system', 'content': system_msg})
    
    # User query with context
    messages.append({
        'role': 'user',
        'content': f'''Context:
{context}

Previous conversation:
{[f"{h['role']}: {h['content']}" for h in chat_history]}

Question: {query}'''
    })
    
    # Step 4: Call LLM
    response = client.chat.completions.create(
        model='gpt-4',  # Your LLM model
        messages=messages,
        max_tokens=500,
        temperature=0.2  # Lower = more consistent
    )
    
    return response.choices[0].message['content']

# Usage
print("=== Chat Demo ===\n")

# Start the conversation
user_query = input("You: What is the revenue in Q3 2024? ")
answer = chat_with_rag(user_query)

print(f"Bot: {answer}\n")

# User can ask follow-up questions
user_query = input("You: How about Q2? ")
answer = chat_with_rag(user_query, chat_history=[])

print(f"Bot: {answer}\n")

# And more...
user_query = input("You: Show me the full report. ")
answer = chat_with_rag(user_query)

print(f"Bot: {answer}")
```

### Integration Example with Claude

```python
from rag_system import DemoRAGSystem
import anthropic

# Initialize RAG
rag = DemoRAGSystem(documents_dir='./documents')
rag.add_documents()

client = Anthropic()

def chat_with_claude(query):
    # Search RAG
    rag_result = rag.search(query, k=5)
    
    # Build prompt
    prompt = f"""
Context:
{rag_result.answer}

Question: {query}

Please answer the question using only the context provided.
"""
    
    response = client.messages.create(
        model='claude-3-opus-20240229',
        max_tokens=500,
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    return response.content[0].text

print(chat_with_claude("What is the revenue forecast?"))
```

---

## 📊 Advanced Usage

### Batch Processing

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

# List all your questions
questions = [
    'What is the company revenue for Q3 2024?',
    'What are the company policies?',
    'Who are the key team members?',
    'What are the upcoming projects?'
]

results = []
for q in questions:
    result = system.search(q)
    results.append({
        'question': q,
        'answer': result.answer,
        'confidence': result.confidence
    })
    print(f'✅ {q[:50]}...')
    print(f'   Answer: {result.answer[:200]}...')
    print(f'   Confidence: {result.confidence*100:.1f}%')
    print()

# Get all answers at once
print('=== All Results ===')
for r in results:
    print(f\"Q: {r['question']}\")
    print(f\"A: {r['answer']}\")
    print(f\"Confidence: {r['confidence']*100}%\")
    print()
"
```

### Custom Chunking Strategy

```bash
python3 -c "
from rag_system import DemoRAGSystem
from rag_system.chunking import HybridChunker, SemanticChunker

# Custom RAG with custom chunker
rag = DemoRAGSystem(
    documents_dir='./documents',
    # Pass custom parameters
    rag_system=CustomRAGSystem(
        chunk_strategy='hybrid',  # Or 'semantic', 'table_aware', etc.
        chunk_size=800,  # Larger chunks for more context
        top_k=10  # More results
    )
)
"
```

### Clear and Reindex

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')

# Clear all documents and start fresh
system.clear_documents()

# Re-add documents
system.add_documents()

print('✅ Documents re-indexed!')
"
```

---

## 🔧 Custom Parameters

```bash
python3 -c "
from rag_system import DemoRAGSystem

# Configure your system
system = DemoRAGSystem(
    documents_dir='./documents',      # Where your PDFs are
    chunk_size=500,                   # Characters per chunk
    overlap=50,                       # Overlap between chunks
    top_k=5,                         # Number of results to return
    rerank=True                      # Use re-ranking for better results
)

system.add_documents()
result = system.search('Your question')
print(result.answer)
"
```

### Parameter Guide

| Parameter | Default | Description | Recommended Values |
|-----------|---------|-------------|-------------------|
| `documents_dir` | './documents' | Path to documents | './documents', '/path/to' |
| `chunk_size` | 500 | Characters per chunk | 300-1000 |
| `overlap` | 50 | Chunks overlap | 30-100 |
| `top_k` | 5 | Results to return | 3-10 |
| `rerank` | True | Use re-ranking | True for quality |

---

## 📚 Working with Different Document Types

### PDF Documents

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')

# Add PDFs with auto-detection
system.add_documents(['report1.pdf', 'report2.pdf'])

# Or specify strategy for specific type
system.add_documents(['scanned_report.pdf'], strategy='ocr')
system.add_documents(['table_report.pdf'], strategy='table')
system.add_documents(['text_report.pdf'], strategy='text')
"
```

### Markdown Documents

```bash
# Just add .md files like PDFs
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')
system.add_documents(['doc1.md', 'doc2.md'])

# They're treated as text!
result = system.search('What does the document say?')
print(result.answer)
"
```

### Code Files

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')

# Add Python files
system.add_documents(['script.py', 'utils.py'])

# Code-aware chunking preserves structure
result = system.search('How does authentication work?')
print(result.answer)
"
```

---

## 💡 Pro Tips

### Memory Optimization

```bash
# For large document collections (500+ PDFs):

python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(
    documents_dir='./documents',
    chunk_size=300,  # Smaller chunks = less memory
    top_k=3,         # Fewer results = faster
    rerank=False     # Skip re-ranking = faster
)
system.add_documents()
"
```

### Performance Optimization

```bash
# Use FAISS for faster search (but less accurate)
python3 -c "
from rag_system.vector_store import LocalVectorStore, VectorBackend

store = LocalVectorStore(
    backend=VectorBackend.FAIS,  # Faster than ChromaDB
    persist_directory='./vector_data'
)
"
```

### Document Organization

```bash
# Organize documents by type
mkdir -p documents/{reports,handbooks,meetings,projects}

# Process each type separately
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')

# Add all documents
system.add_documents()
"
```

### Query Optimization

```bash
# Good queries (specific, clear):
system.search('What is the revenue in Q3 2024?')
system.search('Who is the CEO and when did they join?')
system.search('What are the key project milestones?')

# Better queries (with context):
system.search('In the Q3 report, what is the revenue forecast?')
system.search('On page 5 of the handbook, what does section 2 say?')
system.search('Compare Q3 and Q4 revenue in the sales report')

# Too vague (might not get good results):
system.search('Tell me about the company')
system.search('What about money?')
system.search('Any important stuff?')
```

---

## 📖 Debugging

### Check if Documents are Indexed

```bash
python3 -c "
from rag_system import DemoRAGSystem

system = DemoRAGSystem(documents_dir='./documents')

# Check chunk count
stats = system.rag_system.get_statistics()
print(f'Total chunks: {stats}')
print(f'Expected chunks: 500+ (for 500 PDFs)')

if stats < 100:
    print('⚠️  Not enough chunks! Check if PDFs are readable.')
else:
    print('✅ Good! Documents are indexed.')
"
```

### Test Your Setup

```bash
# Create a simple test PDF first
echo "Test content: This is a test document. The answer is 42." > test.md

# Add test document
system = DemoRAGSystem(documents_dir='./documents')
system.add_documents(['test.md'])

# Search
result = system.search('What is the answer?')

if '42' in result.answer:
    print('✅ RAG system working correctly!')
else:
    print('❌ Something is wrong with the setup.')
"
```

---

## 🎓 Next Steps

### For Beginners

1. ✅ **Read this guide** - Understand how RAG works
2. ✅ **Run the demo** - See it in action
3. ✅ **Add your documents** - Test with real files
4. ✅ **Ask questions** - See what you get

### For Advanced Users

1. ✅ **Review full documentation** - README_full.md
2. ✅ **Customize chunking** - Use your own strategies
3. ✅ **Integrate with LLM** - Add your chat interface
4. ✅ **Optimize for performance** - Adjust parameters
5. ✅ **Scale to production** - Move to cloud

### For Developers

1. ✅ **Study the code** - Read the source files
2. ✅ **Customize the API** - Add your features
3. ✅ **Implement your LLM** - Use your preferred model
4. ✅ **Add your UI** - Web interface, app, etc.

---

## 🎯 Example: Complete Workflow

```bash
#!/bin/bash

# Complete RAG setup workflow

echo "=== RAG System Setup ==="
echo ""

# 1. Check current state
echo "1. Current state:"
python3 -c "
from rag_system import DemoRAGSystem
try:
    system = DemoRAGSystem(documents_dir='./documents')
    print('   ✅ System exists')
    print(f'   Chunks: {system.rag_system.vector_store.count()}')
except:
    print('   ⚠️  No system initialized yet')
"

echo ""
echo "2. Adding documents..."
python3 -c "
from rag_system import DemoRAGSystem
system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()
print('   ✅ Done!')
"

echo ""
echo "3. Testing queries:"
python3 -c "
from rag_system import DemoRAGSystem
system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

# Test queries
queries = [
    'What documents are available?',
    'What is the main topic?',
    'Summarize the document'
]

for q in queries:
    result = system.search(q)
    print(f'\\nQ: {q}')
    print(f'A: {result.answer[:200]}...')
    print(f'Confidence: {result.confidence*100:.1f}%')
"

echo ""
echo "=== Setup Complete! ==="
echo "Your RAG system is ready to use!"
echo "Run: python3 your_script.py to chat with your documents"
```

---

## 🌐 Integrating with Web Interfaces

### With Flask

```python
from flask import Flask, request, jsonify
from rag_system import DemoRAGSystem

app = Flask(__name__)
rag = DemoRAGSystem(documents_dir='./documents')
rag.add_documents()

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data['query']
    
    result = rag.search(query)
    
    return jsonify({
        'answer': result.answer,
        'confidence': result.confidence,
        'sources': [s['metadata'].get('doc_title') for s in result.sources]
    })

if __name__ == '__main__':
    app.run(port=5000)
```

### With Gradio

```python
import gradio as gr
from rag_system import DemoRAGSystem

rag = DemoRAGSystem(documents_dir='./documents')
rag.add_documents()

def chat(user_query, chat_history):
    result = rag.search(user_query)
    
    # Add to chat history
    chat_history.append({'role': 'user', 'content': user_query})
    chat_history.append({'role': 'assistant', 'content': result.answer})
    
    return result.answer, chat_history

demo = gr.ChatInterface(fn=chat)
demo.launch()
```

---

## 📞 Support

**Questions?** Check:
1. **[README_full.md](README_full.md)** - Complete documentation
2. `python3 demo.py --help` - Command line help
3. GitHub Issues - Report problems

**Need help?**
- Review the error messages
- Check if documents are in the right format
- Verify chunk count after adding documents
- Test with simple queries first

---

## 🎉 You're Ready!

You now have a complete RAG system that:
- ✅ Handles your PDF documents
- ✅ Processes different document types (PDF, MD, TXT)
- ✅ Searches efficiently (fast, memory-efficient)
- ✅ Integrates with any LLM
- ✅ Scales with your document collection

**Next step:** Add your documents and start asking questions!

```bash
python3 -c "
from rag_system import DemoRAGSystem
system = DemoRAGSystem(documents_dir='./documents')
system.add_documents()

# Ask away!
result = system.search('Your question here?')
print(result.answer)
"
```

Happy querying! 🚀

---

*Last updated: 2024-09-29*
*RAG System v0.1.0*