# 🧠 RAG System with Automatic Memory

A powerful, modular RAG (Retrieval Augmented Generation) system designed for PDF documents with **automatic memory management across chat sessions**.

![RAG System Architecture](architecture_diagram.png)

## ✨ Key Features

### 🧠 Automatic Memory Management (NEW!)

**Memory persists across all chat sessions automatically:**

1. **Multi-Session Memory**: Your preferences, facts, and conversation history are stored
2. **Auto-Retrieval**: When you ask a question, relevant memories from ALL past sessions are automatically retrieved
3. **Context Fusion**: Memory is seamlessly merged with document search results
4. **No Manual Effort**: Memory is stored and retrieved automatically - you never need to "remember" anything yourself

### 📄 Mixed PDF Support

Automatically detects and processes:
- Text-based PDFs (fast extraction)
- Scanned/image-based PDFs (OCR processing)
- Complex PDFs with tables and formulas

### 🔍 Intelligent Chunking

Multiple chunking strategies:
- **Semantic**: Groups related content by meaning
- **Hierarchical**: Preserves document structure (pages → sections)
- **Table-Aware**: Keeps tables intact
- **Fixed**: Simple fixed-size splitting
- **Hybrid**: Best for mixed content (automatic!)

### 💾 Memory Storage

Your chat history is automatically stored and managed:

```
memory_storage/
├── preferences.json          # Your user preferences
├── session_123/              # Individual chat sessions
│   └── _memory_timestamp.json
└── memory_collections/       # Thematic memory collections
```

### 🎯 Memory Types

The system automatically extracts and stores:
- **Preferences**: What you like/don't like (e.g., "prefer code examples", "avoid jargon")
- **Facts**: About you (e.g., "Your name is...", "You work at...")
- **Topics**: Subjects you discuss across sessions
- **Decisions**: Important decisions made during conversations
- **Conversation History**: Recent chat messages

### 🔄 Memory Fusion

When you ask a question:
```
Your Query → Memory Retrieval + Document Search → Enriched Context → Answer
```

The answer considers:
1. Your current conversation history
2. Relevant memories from ALL past sessions
3. Relevant content from your documents

### ⚡ Auto-Session Management

- **Automatic**: Sessions are created and managed automatically
- **Persistent**: Memory survives across restarts
- **Filterable**: Search by specific session or all sessions
- **Exportable**: Backup and restore your memory

## 🚀 Quick Start

### Installation

```bash
cd rag-system
pip install -r requirements.txt
```

### Start a Chat Session

```bash
# Add your documents
python demo.py --documents ./my_documents

# Start chatting (memory is automatically managed)
python demo.py
```

### Your Memory is Already Working

```bash
# Ask a question - memory is automatically included
python demo.py -q "What are your preferences?"

# The system automatically retrieves and uses:
# - Your preferences from past sessions
# - Facts about you
# - Topics you've discussed
```

### Multi-Session Usage

```bash
# Start a new session
python demo.py -s "session_2"

# Add messages to this session
echo "I prefer detailed explanations with examples" | python demo.py -s "session_2"

echo "What is machine learning?" | python demo.py -s "session_2"

# Now ask from a different session - memory from session_2 is included!
echo "Remember my preference for detailed explanations?" | python demo.py -s "session_3"
```

## 📖 Usage Examples

### Document Search with Memory

```bash
# Search documents with automatic memory fusion
python demo.py -d ./my_documents -q "How should I format code in responses?"

# Answer considers:
# - Your preferences (auto-stored)
# - Past conversations about code
# - Relevant document content
```

### Session Management

```bash
# List all active sessions
python demo.py -s list

# View a specific session
python demo.py -s session_123

# Show memory statistics
python demo.py -s stats

# Show your preferences
python demo.py -s prefs

# Export memory for backup
python demo.py -s export

# Clear session memory
python demo.py -s session_123 -c clear

# Clear all memory (careful!)
python demo.py -c all-clear
```

### Python API

```python
from rag_system.memory.manager import MemoryManager

# Initialize memory manager
manager = MemoryManager(storage_dir="./my_memory")

# Start a session
session = manager.start_session(name="Project Alpha")

# Add messages
manager.add_message(session.session_id, "user", "What is RAG?")
manager.add_message(session.session_id, "assistant", "RAG stands for...")

# Later, in a new session, memory is automatically available
session2 = manager.start_session(name="New Chat")
context = manager.get_memory_context("Explain it simply")

# Memory from ALL your sessions is automatically retrieved!
```

## 🔧 Programmatic Integration

### With Memory

```python
from rag_system.memory.manager import MemoryManager
from rag_system.core import RAGRetriever

# Initialize memory manager
memory_manager = MemoryManager(storage_dir="./memory")

# Create memory retriever
memory_retriever = memory_manager.memory_retriever

# Initialize RAG with memory
rag = RAGRetriever(
    memory_retriever=memory_retriever,
    top_k=5
)

# Process query with automatic memory
result = rag.search(
    query="Your question",
    include_memory=True  # Default!
)

# Memory is automatically retrieved and fused with documents!
print(f"Answer: {result.answer}")
```

### Enhanced Query Handler

```python
from rag_system.query_handler.query_handler import create_enhanced_query_handler
from rag_system.memory.manager import MemoryManager

# Create handler with automatic memory
handler = create_enhanced_query_handler(
    memory_storage_dir="./memory",
    auto_enrich=True
)

# Process any query with memory context
result = handler.handle_query("How does RAG work?")

# Result includes:
# - Relevant memories from all sessions
# - Relevant document chunks
# - Your conversation history
# - Fused into one enriched context
```

## 📊 How Memory Works

### Session Flow

```
User: "I prefer I prefer detailed explanations"
       ↓
[MemoryStore: Saves preference]
       ↓
User: "What is RAG?"
       ↓
[MemoryRetriever: Retrieves relevant memories]
       ↓
[Documents: Search for relevant chunks]
       ↓
[QueryHandler: Fuses memory + documents]
       ↓
Answer with memory context included!
```

### Memory Fusion

```python
# When you ask a question:
query = "How should I format the output?"

# System retrieves:
1. Memory: "Please use code blocks and markdown"
2. Memory: "I want step-by-step explanations"
3. Document: "Python output formatting guidelines"

# Answer considers all of them:
"Here's how to format output, 
following your preference for code blocks 
and step-by-step instructions,
with reference to Python guidelines..."
```

## 🎯 Memory Features

### Automatic Extraction

The system automatically extracts memory from conversations:

**Preferences**:
- "I prefer verbose responses" → Preference: `verbose`
- "Please don't use emojis" → Preference: `no_emojis`
- "I like code examples" → Preference: `include_code`

**Facts**:
- "Your name is Ruthvik" → Fact: `name`
- "You work in software" → Fact: `occupation`
- "You use Python" → Fact: `preferred_language`

**Topics**:
- "RAG", "memory", "vector", "documents" → Stored as topics

**Decisions**:
- "We should use ChromaDB" → Decision: `chromadb_selected`

### Memory Relevance Scoring

Memories are scored based on:

1. **Keyword Matching**: How many words from your query appear in the memory
2. **Importance Weight**: Preferences are boosted (0.8), facts (0.6), general conversation (0.3)
3. **Recency Decay**: Newer memories have a slight boost (decays over 3 days)
4. **Threshold**: Only memories above threshold (default 0.3) are returned

### Multi-Session Search

```bash
# Search across ALL your sessions
python demo.py -q "What preferences do I have?"

# Automatically retrieves from:
# - session_1: "I like Python"
# - session_5: "Prefer code examples"
# - session_8: "Don't use emojis"

# Returns all relevant memories, sorted by relevance!
```

## 💾 Memory Storage

### Storage Format

```json
{
  "exported_at": "2026-10-19T12:00:00",
  "active_sessions": {
    "session_abc123": {
      "name": "Personal Chat",
      "messages": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I help?"}
      ],
      "extracted_memory": {
        "preferences": [
          {"type": "prefer", "value": "Detailed explanations"}
        ],
        "facts": ["Your name is Ruthvik"],
        "topics": ["RAG", "Python", "memory"],
        "decisions": ["You chose to use ChromaDB"]
      }
    }
  },
  "global_preferences": {
    "code_preference": "python",
    "output_style": "detailed"
  }
}
```

### Vector Storage

Memories are also stored as vectors for semantic search:

```
memory_storage/
└── vector_memory/
    └── session_abc/
        ├── preferences/     # Preference vectors
        ├── facts/          # Fact vectors
        └── general/        # Conversation vectors
```

## 🔐 Privacy & Security

- **Local Storage**: All memory stored on your machine
- **No Cloud**: Memory never leaves your computer
- **Selective**: Only retrieve memories when relevant
- **Session Control**: Each session is isolated
- **Auto-Cleanup**: Old memories can be automatically pruned

## 🛠️ Advanced Usage

### Custom Memory Threshold

```python
manager = MemoryManager(
    memory_threshold=0.8  # Only show highly relevant memories
)
```

### Specific Session Filtering

```python
# Only use memories from a specific session
context = manager.get_memory_context(query, session_id="session_123")
```

### Memory Type Filtering

```python
# Get only preferences
preferences = memory_retriever.get_memory_by_tag('preference')

# Get only facts
facts = memory_retriever.get_memory_by_tag('fact')
```

### Manual Memory Insertion

```python
# Insert a custom memory
memory_store.save_memory_chunk(
    chunk_id="manual_memory_1",
    chunk_data={
        "content": "User prefers markdown tables",
        "session_id": "session_123",
        "type": "preference",
        "timestamp": datetime.now().isoformat()
    }
)
```

## 🎓 Learning Path

1. **Basic Memory** - Start by adding your preferences
   ```bash
   echo "Please use simple language and no jargon" | python demo.py
   ```

2. **Multi-Session** - Create multiple chat sessions
   ```bash
   python demo.py -s "work_chat"
   python demo.py -s "personal_chat"
   ```

3. **Memory Retrieval** - Ask questions about your history
   ```bash
   python demo.py -q "What did I ask yesterday?"
   ```

4. **Document + Memory** - Search with both documents and memory
   ```bash
   python demo.py -d ./docs -q "How to implement RAG?"
   ```

5. **Memory Export** - Backup your memory
   ```bash
   python demo.py -s export
   ```

6. **Memory Restoration** - Restore from backup
   ```bash
   python demo.py -m ./backup_memory
   ```

## 📈 Performance

- **Memory Retrieval**: ~50ms for 100 memories
- **Document Search**: ~100ms for 1000 chunks
- **Total Processing**: ~150ms per query (without LLM)
- **Memory Storage**: Efficient disk-based storage

## 🔮 Future Enhancements

- [ ] **ML-based memory extraction**: Better detection using LLMs
- [ ] **Sentiment tracking**: Track how you feel about topics
- [ ] **Relationship memory**: Track people you mention
- [ ] **Goal memory**: Track your long-term goals
- [ ] **Memory suggestions**: Proactively suggest relevant memories
- [ ] **Cross-user memories**: Share memories across users (opt-in)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Credits

Built with ❤️ for the RAG community.

---

## 📚 Additional Documentation

- [Memory Usage Guide](MEMORY_USAGE.md) - Complete guide to memory features
- [API Reference](docs/api.md) - Full API documentation
- [Examples](examples/) - Usage examples and tutorials

## 🆘 Support

For issues:
- Check the [troubleshooting](MEMORY_USAGE.md#troubleshooting) section
- Review logs in `./memory_storage/logs/`
- Export your memory for debugging

For help:
- Check the [FAQ](FAQ.md)
- Review the [tutorial](tutorial.md)
- Contact the maintainers

---

**Version**: 2.0.0 (with Memory!)

**Note**: This version includes automatic memory management. Previous versions are for document-only RAG.
