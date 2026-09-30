# Conversation Memory Guide

This guide explains how to use the conversation memory feature to record all your interactions with the RAG system and make them available as context for your LLM.

## Overview

The conversation logger automatically records every chat session you have and saves them as `.md` files. This serves two purposes:

1. **Memory**: Your LLM can read these files and "remember" past conversations
2. **History**: You can review and export your conversation history at any time

## Quick Start

### 1. Initialize the Conversation Logger

Add this to your Python script or notebook:

```python
from memory import ConversationLogger

# Initialize logger - conversations will be saved to ./memory folder
logger = ConversationLogger(
    storage_dir="./memory",      # Where to save conversations
    max_conversations=50,        # Keep last 50 sessions
    auto_save=True,              # Auto-save after each message
    file_format="md"             # Save as markdown (.md files)
)
```

### 2. Start a New Session

```python
session_id = logger.start_session("my_project_discussion")
print(f"Started session: {session_id}")
```

### 3. Add Messages to Your Conversation

```python
# User message
logger.add_message("my_project_discussion", "user", "How do I process PDFs?")

# Assistant response (from your RAG system)
logger.add_message("my_project_discussion", "assistant", "You can use the RAG system to...")
```

### 4. Access Conversation History

```python
# Get all messages in a session
history = logger.get_conversation_history("my_project_discussion")

# Get conversation as text
conversation_text = logger.get_conversation_text("my_project_discussion")
print(conversation_text)
```

## Integration with RAG System

### Option 1: Automatic Integration in main.py

Modify your `main.py` to automatically log conversations:

```python
# Add to your main.py after importing
from rag_system.memory import ConversationLogger

# Initialize once at startup
conversational_memory = ConversationLogger(
    storage_dir="./memory",
    max_conversations=50,
    auto_save=True,
    file_format="md"
)

# Wrap your RAG system
system = DemoRAGSystem(documents_dir='./documents')

# Before each search, log the query
session_id = conversational_memory.start_session("rag_search_session")

def wrapped_search(query):
    # Log user query
    conversational_memory.add_message(session_id, "user", query)
    
    # Perform search
    result = system.search(query=query)
    
    # Log assistant response
    response_text = f"""
Answer:
{result.answer}
        
Sources:
{chr(10).join([f"- {s['metadata'].get('doc_title', 'Unknown')} (Page {s['metadata'].get('page', '?')})" for s in result.sources[:3]])}
"""
    conversational_memory.add_message(session_id, "assistant", response_text)
    
    return result
```

### Option 2: Manual Integration

Use the logger independently:

```python
# Start a new session for this query
session_id = conversational_memory.start_session(f"query_{datetime.now().strftime('%H%M%S')}")

# Log the user's question
conversational_memory.add_message(session_id, "user", query)

# Your RAG system processes the query...
result = system.search(query)

# Log the answer back
conversational_memory.add_message(session_id, "assistant", result.answer)
```

## Using Memory as LLM Context

### Method 1: Get Last N Messages

```python
# Get last 5 messages from a session
recent_history = logger.get_conversation_history("my_session", limit=5)

# Convert to context string
context = []
for msg in recent_history:
    role_name = {"user": "User", "assistant": "Assistant"}.get(msg["role"], msg["role"])
    context.append(f"{role_name}: {msg['content']}")

context_string = "\n\n---\n\n".join(context)
```

### Method 2: Get Optimized Memory Context

```python
# Get last 4000 tokens worth of conversation (optimized for LLM)
memory_context = logger.get_memory_context("my_session", max_tokens=4000)

# Now use this as system prompt or context
full_prompt = f"""
System Instructions:
{memory_context}

---

Current Query: {new_query}

Use your knowledge and the conversation history above to answer the query.
"""
```

### Method 3: File-Based Memory (for external LLMs)

Save conversation files that external LLMs can read:

```python
# Export all conversations to a single file
logger.export_all_sessions("./memory/all_conversations.md")

# External LLM can read this file
# The LLM reads the .md file as context
```

## Reading Your Conversation Files

Once conversations are saved, you can read them anytime:

### View in Browser

```bash
open /Users/ruthvik/rag_system/memory/sessions/session_YYYYMMDD_HHMMSS_XXX.md
```

### Read with Python

```python
from pathlib import Path
import glob

# Find all markdown files in sessions folder
session_files = glob.glob("./memory/sessions/*.md")

# Read a specific session
session_id = "session_20240101_120000_123"
session_file = f"./memory/sessions/{session_id}.md"

with open(session_file, "r") as f:
    print(f.read())
```

### Search Past Conversations

```python
import re
from pathlib import Path

# Search for a topic in all past conversations
pattern = r"how do I process pdfs"

for md_file in Path("./memory/sessions").glob("*.md"):
    content = md_file.read_text()
    if pattern.lower() in content.lower():
        print(f"Found in: {md_file.name}")
        print(content[:500])
```

## Command-Line Examples

### Start a Session from Terminal

```bash
# You'll need to modify the code to support CLI, or use Python directly
cd /Users/ruthvik/rag_system

python3 -c "
from rag_system.memory import ConversationLogger
logger = ConversationLogger(storage_dir='./memory')
session_id = logger.start_session('my_docs_session')
print(f'Session started: {session_id}')
"
```

### Add a Message from Terminal

```bash
python3 -c "
from rag_system.memory import ConversationLogger

logger = ConversationLogger(storage_dir='./memory')
session_id = 'my_docs_session'

logger.add_message(session_id, 'user', 'How do I list all my documents?')
logger.add_message(session_id, 'assistant', 'You can use the search function...')
"
```

### Export All Conversations

```bash
python3 -c "
from rag_system.memory import ConversationLogger

logger = ConversationLogger(storage_dir='./memory')
logger.export_all_sessions('./memory/conversation_history.md')
"
```

## File Format

### Markdown Format (.md)

Each session is saved as a markdown file with this structure:

```markdown
# Conversation: session_20240101_120000_123
**Started:** 2024-01-01 12:00:00
**Total Messages:** 2

## Metadata
- session_id: session_20240101_120000_123

## Messages

💬 **User**
> How do I list all documents?
   - query: How do I list all documents?

🤖 **Assistant**
> To list all documents, use the following command:
> python3 main.py --documents ./documents

   - query: How do I list all documents?
```

### JSON Format (.json)

Each session saved as individual JSON objects (one per line):

```json
{
  "session_id": "session_20240101_120000_123",
  "session_start": "2024-01-01T12:00:00",
  "conversations": [...],
  "metadata": {...},
  "message_count": 2,
  "last_updated": "2024-01-01T12:05:00"
}
{
  "role": "user",
  "content": "How do I list all documents?",
  "timestamp": "2024-01-01T12:00:01",
  "metadata": {...}
}
{
  "role": "assistant",
  "content": "To list all documents, use... ",
  "timestamp": "2024-01-01T12:05:02",
  "metadata": {...}
}
```

## Integrating with Your Current RAG System

### Automatic Conversation Logging in DemoRAGSystem

You can modify your `rag_system/core/__init__.py` to include conversation logging:

```python
# At the top of RAGRetriever class, add a new parameter
class RAGRetriever:
    def __init__(
        self,
        vector_store: Optional[LocalVectorStore] = None,
        collection_name: str = "documents",
        chunk_strategy: str = "hybrid",
        chunk_size: int = 500,
        overlap: int = 50,
        top_k: int = 5,
        rerank: bool = True,
        rerank_top_k: int = 3,
        embed_model: Optional[str] = None,
        auto_process: bool = True,
        persist: bool = True,
        conversation_logger: Optional[ConversationLogger] = None  # NEW
    ):
        # ... existing code ...
        
        # Initialize conversation logger if provided
        if conversation_logger:
            self.conversation_logger = conversation_logger
        else:
            self.conversation_logger = ConversationLogger(auto_save=False)
    
    def search(self, query: str, k: Optional[int] = None, ...):
        # ... existing code ...
        
        # Log the query and result
        session_id = self.conversation_logger.start_session("rag_search")
        self.conversation_logger.add_message(session_id, "user", query)
        
        # Perform search...
        
        # Log result
        result_text = f"Answer: {result.answer}\n\nSources: ..."
        self.conversation_logger.add_message(session_id, "assistant", result_text)
        
        return result
```

## Memory Management

### Automatic Cleanup

The logger can automatically delete old conversations:

```python
# Keep only the last 20 sessions
logger.cleanup_old_sessions(keep_last=20)

# Or delete all sessions
logger.cleanup_old_sessions(keep_last=0)
```

### Manual Export

```python
# Export everything to a file
logger.export_all_sessions("/path/to/backup/all_conversations.md")
```

### Import Existing Conversations

```python
# Load existing conversation files
imported_sessions = logger.import_from_file("/path/to/conversations.md")
```

## Example: Complete Workflow

```python
from rag_system import DemoRAGSystem
from memory import ConversationLogger

# Initialize both systems
rag = DemoRAGSystem(documents_dir='./documents')
memory = ConversationLogger(
    storage_dir='./memory',
    auto_save=True
)

session_id = memory.start_session("my_rag_work")

# First interaction
query = "What PDFs do I have?"
memory.add_message(session_id, "user", query)
result = rag.search(query)
memory.add_message(session_id, "assistant", f"Here are your PDFs:\n{result.answer}")

# Second interaction - refers to previous conversation
query = "About what did we discuss PDFs?"
memory.add_message(session_id, "user", query)

# Get conversation context for the LLM
context = memory.get_memory_context(session_id, max_tokens=4000)

# LLM can now see the full context
answer = llm.generate(
    system_prompt="You are a helpful assistant...",
    messages=[
        {"role": "system", "content": context},
        {"role": "user", "content": query}
    ]
)

memory.add_message(session_id, "assistant", answer)

# View your conversation
print(memory.get_conversation_text(session_id))
```

## Tips for Best Results

1. **Session Names**: Use meaningful names like `pdf_processing`, `code_review`, `research`
2. **Metadata**: Add useful metadata when adding messages:
   ```python
   logger.add_message(session_id, "user", query, metadata={"topic": "pdf_handling", "context": "code"})
   ```
3. **Token Management**: Set `max_tokens` appropriately based on your LLM's context window
4. **Regular Cleanup**: Periodically call `cleanup_old_sessions()` if you have many conversations
5. **Backup**: Use `export_all_sessions()` regularly to back up your conversations

## Common Use Cases

### Case 1: Simple Chat History

```python
# Just record everything
memory = ConversationLogger(auto_save=True)
```

### Case 2: Session-Based Chat with Context

```python
memory = ConversationLogger()

def handle_query(query):
    session_id = memory.start_session("current_session")
    memory.add_message(session_id, "user", query)
    
    # Get context
    context = memory.get_memory_context("current_session", max_tokens=4000)
    
    # LLM uses context
    response = llm(chat_history=context, query=query)
    
    memory.add_message(session_id, "assistant", response)
    
    return response
```

### Case 3: RAG + Memory for Extended Context

```python
def handle_query(query):
    # Search RAG system
    rag_result = rag.search(query)
    
    # Find related conversations
    related_conversations = memory.find_related_conversations(query)
    
    # Combine into context
    rag_context = rag_result.answer[:2000]
    memory_context = "\n\n".join([c['preview'] for c in related_conversations[:3]])
    
    full_context = f"RAG Results:\n{rag_context}\n\nPast Conversations:\n{memory_context}"
    
    return llm(query=query, context=full_context)
```

## Next Steps

1. **Add to Your Project**: Integrate the ConversationLogger into your RAG workflow
2. **Start Using It**: Begin logging your conversations
3. **Monitor Storage**: Check `./memory` folder to see how much space conversations take
4. **Adjust Settings**: Modify `max_conversations` based on your needs
5. **Export Regularly**: Backup your conversation history

## Example: Creating a Conversation File

Run this to create your first conversation file:

```bash
cd /Users/ruthvik/rag_system

python3 -c "
from memory import ConversationLogger

# Initialize
memory = ConversationLogger(
    storage_dir='./memory',
    auto_save=True,
    file_format='md'
)

# Start a session
session_id = memory.start_session('demo_conversation')
print(f'Session: {session_id}')

# Add some messages
memory.add_message(session_id, 'user', 'Hello!')
memory.add_message(session_id, 'assistant', 'Hi there! How can I help?')

# Add query-related messages
memory.add_message(session_id, 'user', 'How do I use the RAG system?')
memory.add_message(session_id, 'assistant', 'You can use main.py or demo.py...')
"
```

This will create `./memory/sessions/{session_id}.md` with your conversation history.

## FAQ

**Q: Where are my conversations saved?**  
A: By default in `./memory/sessions/` folder, as `.md` files.

**Q: How much storage do conversations take?**  
A: Depends on length. A typical session might take 1-10KB. For 50 conversations, expect 50-500KB.

**Q: Can I have multiple sessions?**  
A: Yes! Use `start_session(name)` to create new named sessions.

**Q: How do I find a specific conversation?**  
A: Use `get_conversation_history(session_id, limit=10)` to get recent messages from a session.

**Q: How do I search past conversations?**  
A: Use `find_related_conversations(query)` or search the `./memory/sessions/` folder with grep:
```bash
grep -r "your search term" ./memory/sessions/
```

**Q: Can I use conversations with other LLMs?**  
A: Yes! Export to `./memory/all_conversations.md` and feed it to any LLM as context.

**Q: How do I delete old conversations?**  
A: Call `memory.cleanup_old_sessions(keep_last=20)` to keep only the 20 most recent.

---

For more details, see `README.md` and `USAGE.md`.