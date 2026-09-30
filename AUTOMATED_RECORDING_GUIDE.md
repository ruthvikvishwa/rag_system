# Automated Conversation Recording Guide

This guide explains how to automatically record all your conversations so your LLM can remember them across chat sessions.

## Overview

We've created an automated conversation recording system that:
1. **Saves conversations** to `./memory/AUTO_SAVED/` folder
2. **Organizes by session** with unique session IDs
3. **Provides a simple API** for integration with your RAG system
4. **Supports multiple tools** (Python, Bash, manual)

## Quick Start

### Method 1: Python Script (Recommended)

Save this to your project or use it as-is:

```python
from memory.auto_recorder.auto_save import save_conversation

# Example: Save a conversation
conversation = {
    "session_name": "rag_initial_setup",
    "messages": [
        {"role": "user", "content": "What is the RAG system?"},
        {"role": "assistant", "content": "The RAG system is a framework for..."}
    ],
    "metadata": {
        "topic": "RAG basics",
        "created_by": "auto_recorder"
    }
}

save_conversation(
    session_name=conversation["session_name"],
    messages=conversation["messages"],
    metadata=conversation.get("metadata", {})
)
```

This will create: `./memory/AUTO_SAVED/rag_initial_setup_YYYYMMDD_HHMMSS/rag_initial_setup_YYYYMMDD_HHMMSS.md`

### Method 2: Via Terminal (When you have bash access)

```bash
# Save from command line
python3 memory/auto_recorder/auto_save.py --save "my_session_name"

# Or save from a markdown file
python3 memory/auto_recorder/auto_save.py --from-file ./chat_transcript.md

# List all saved conversations
python3 memory/auto_recorder/auto_save.py --list
```

### Method 3: Manual Integration

Add this to your RAG workflow:

```python
# At the start of each new chat session, call:
save_conversation("session_" + datetime.now().strftime("%Y%m%d"), current_messages)

# Later, retrieve conversations when you need context
conversations = list_auto_saved_conversations()
```

## File Structure

```
memory/
├── sessions/          # Demo conversations (created manually)
│   ├── getting_started/
│   ├── using_the_system/
│   └── pdf_processing/
├── AUTO_SAVED/        # Automatically saved conversations
│   ├── session_20240129_213600_123/
│   │   └── session_20240129_213600_123.md
│   └── rag_initial_session_214500_456/
│       └── rag_initial_session_214500_456.md
└── ALL_CONVERSATIONS/ # Combined backup of all conversations
```

## Saving a Conversation

### What to Provide

When you want to save a conversation, provide:

1. **Session Name**: A meaningful name for this conversation
   - Good: `rag_setup`, `pdf_handling`, `code_review`
   - Bad: `session_20240129_213600_12345`

2. **Messages**: List of all messages in order
   ```python
   messages = [
       {"role": "user", "content": "User question 1"},
       {"role": "assistant", "content": "AI answer 1"},
       {"role": "user", "content": "User question 2"},
       {"role": "assistant", "content": "AI answer 2"}
   ]
   ```

3. **Metadata** (Optional):
   ```python
   metadata = {
       "topic": "RAG development",
       "notes": "Important for future reference",
       "priority": "high"
   }
   ```

### Using the API

```python
from datetime import datetime
from memory.auto_recorder.auto_save import save_conversation, generate_session_name

# Option 1: Provide custom session name
save_conversation(
    session_name="rag_development_session",
    messages=[{"role": "user", "content": "How do RAG systems work?"}],
    metadata={"topic": "learning", "date": datetime.now().strftime("%Y-%m-%d")}
)

# Option 2: Auto-generate session name
save_conversation(
    session_name=None,  # Will auto-generate
    messages=[{"role": "user", "content": "Quick question"}]
)
```

### Capturing THIS Conversation

Since I can't automatically capture conversations from this chat interface, here's how to capture what we've discussed:

```python
# Copy this entire conversation and format it:
conversation_data = {
    "session_name": "rag_initial_setup_session",
    "session_start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "messages": [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "We need to create a RAG system..."},
        {"role": "user", "content": "I have nothing in mind as of now..."},
        {"role": "assistant", "content": "I'll help you build a RAG system..."},
        # ... continue with all messages from this conversation
        {"role": "assistant", "content": "Now I've created the auto-recorder..."}
    ],
    "metadata": {
        "topic": "RAG system initial setup",
        "purpose": "Recording conversation about RAG development",
        "notes": "User wants to record all future conversations"
    }
}

# Save it
save_conversation(
    session_name="rag_initial_setup_session",
    messages=conversation_data["messages"],
    metadata=conversation_data.get("metadata", {})
)
```

## Retrieving Saved Conversations

### As a File

```bash
# View a specific session
cat ./memory/AUTO_SAVED/session_name/session_name.md

# View multiple sessions
ls -la ./memory/AUTO_SAVED/

# Search for a topic
grep -r "your search term" ./memory/AUTO_SAVED/
```

### Via Python API

Add these methods to the auto_save.py module:

```python
def get_conversation(session_id: str):
    """Get a specific saved conversation."""
    session_folder = AUTO_SAVE_DIR / session_id
    if session_folder.exists():
        filepath = list(session_folder.glob("*.md"))[0]
        return filepath.read_text()
    return None

def list_all_sessions() -> List[str]:
    """Get all saved session IDs."""
    session_ids = []
    for folder in AUTO_SAVE_DIR.iterdir():
        if folder.is_dir():
            session_ids.append(folder.name)
    return session_ids

def get_all_conversations_as_text():
    """Get all saved conversations as one text block."""
    all_text = []
    
    for session_id in sorted(list_all_sessions()):
        content = get_conversation(session_id)
        all_text.append(f"\n\n---\n\n## Session: {session_id}\n\n{content}")
    
    return "\n".join(all_text)
```

## Integration with RAG System

### Simple Integration

```python
from memory.auto_recorder.auto_save import save_conversation

# At the START of each new chat session with the LLM:
def start_llm_conversation():
    # Get current conversation history
    current_messages = get_conversation_history()
    
    # Save to auto-recorder
    session_id = save_conversation(
        session_name="chat_" + datetime.now().strftime("%Y%m%d"),
        messages=current_messages
    )
    
    return session_id
```

### Advanced Integration

```python
class ConversationAutoRecorder:
    def __init__(self, storage_dir="./memory/AUTO_SAVED"):
        self.storage_dir = Path(storage_dir)
        self.sessions = {}
        self.counter = 0
    
    def start_new_session(self, session_name: str) -> str:
        """Start recording a new conversation session."""
        self.counter += 1
        
        if not session_name:
            session_name = f"auto_{self.counter}"
        
        session_name = session_name.replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{session_name}_{timestamp}_{self.counter}"
        
        # Save the session start
        save_conversation(session_id, [])
        
        return session_id
    
    def add_to_session(self, session_id: str, message: Dict):
        """Add a message to an existing session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append(message)
        
        # Auto-save periodically
        if len(self.sessions[session_id]) % 3 == 0:
            save_conversation(session_id, self.sessions[session_id])
    
    def get_recent_conversations(self, query: str, limit: int = 5):
        """Find conversations related to a query."""
        # Simple keyword matching
        relevant = []
        for session_id, session_msgs in self.sessions.items():
            for msg in session_msgs:
                if query.lower() in msg["content"].lower():
                    relevant.append({
                        "session_id": session_id,
                        "content": msg["content"],
                        "relevance": msg["content"].lower().count(query.lower())
                    })
        
        return sorted(relevant, key=lambda x: x["relevance"], reverse=True)[:limit]
    
    def get_context_for_llm(self, query: str, max_context: int = 4000) -> str:
        """Get conversation context optimized for LLM."""
        context_parts = []
        
        # Add relevant past conversations
        relevant = self.get_recent_conversations(query)
        for conv in relevant:
            context_parts.append(f"Past: {conv['content'][:500]}")
        
        # Add current query
        context_parts.append(f"Current Query: {query}")
        
        return "\n\n".join(context_parts)[:max_context]
```

## File Formats

### Markdown Format (.md)

Default format, easy for humans and LLMs to read:

```markdown
# Conversation: my_session_20240129

**Date:** 2024-01-29 10:30:00
**Messages:** 2

## Messages

1. [User] What is RAG?
> RAG stands for Retrieval-Augmented Generation...

2. [Assistant] RAG is a system that...
> RAG uses a vector database to...
```

### JSON Format (.json)

Alternative format for programmatic access:

```json
{
  "session_id": "my_session_20240129",
  "session_start": "2024-01-29T10:30:00",
  "messages": [
    {"role": "user", "content": "What is RAG?", "timestamp": "2024-01-29T10:30:01"},
    {"role": "assistant", "content": "RAG is...", "timestamp": "2024-01-29T10:30:05"}
  ],
  "metadata": {"topic": "RAG basics"}
}
```

## Storage Management

### Limit Storage

If you have many conversations, limit how many are kept:

```python
def limit_storage(max_sessions: int = 50):
    """Keep only the most recent N sessions."""
    session_ids = list_all_sessions()
    
    # Delete old sessions
    for old_id in session_ids[max_sessions:]:
        # Delete folder
        (AUTO_SAVE_DIR / old_id).rmdir()
```

### Export for Backup

```bash
# Export everything to a single file
python3 memory/auto_recorder/auto_save.py --export backup.md

# Or use the ConversationLogger class
from memory import ConversationLogger
logger = ConversationLogger()
logger.export_all_sessions("./backup/all_conversations.md")
```

## Complete Example

Here's a complete example of how to set up and use the auto-recorder:

```python
from datetime import datetime
from memory.auto_recorder.auto_save import save_conversation, list_all_sessions
from pathlib import Path

# Initialize
storage_dir = Path("./memory/AUTO_SAVED")
storage_dir.mkdir(parents=True, exist_ok=True)

def start_session(name: str = None):
    """Start a new conversation session."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"({name or 'new'})_{timestamp}"
    
    save_conversation(
        session_name=session_id,
        messages=[]
    )
    
    return session_id

def add_message(session_id: str, role: str, content: str, metadata: dict = None):
    """Add a message to a session."""
    messages = [
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "First answer"},
        # Add your messages here
        {"role": role, "content": content}
    ]
    
    save_conversation(
        session_name=session_id,
        messages=messages,
        metadata=metadata or {}
    )
    
    return session_id

# Usage example
session_id = start_session("rag_tutorial")
add_message(session_id, "user", "What is RAG?")
add_message(session_id, "assistant", "RAG is Retrieval-Augmented Generation...")

# Later, view your sessions
sessions = list_all_sessions()
print(f"You have {len(sessions)} saved conversation sessions")

# Find a specific session
session_files = [f for f in storage_dir.iterdir() if f.is_dir()]
```

## Troubleshooting

### Issue: "No session found"

**Solution:** Check that the session name exists:
```python
sessions = list_all_sessions()
print(sessions)  # Should list all available session IDs
```

### Issue: File not readable by LLM

**Solution:** LLMs can read markdown files. Just provide the path:
```python
# Tell your LLM to read the file
llm_message = f"Read this file: {filepath}"
```

### Issue: Too many files consuming disk space

**Solution:** Delete old sessions:
```python
# Keep only last 20 sessions
sessions = list_all_sessions()
for old_id in sessions[20:]:
    (AUTO_SAVE_DIR / old_id).rmdir()
```

## FAQ

**Q: Will this record EVERY conversation automatically?**  
A: No, you need to explicitly call `save_conversation()` for each conversation you want to save.

**Q: Can this record my LM Studio chat conversations?**  
A: Not automatically. LM Studio conversations aren't accessible programmatically. However, you can:
1. Manually copy important conversations and save them using the API
2. Use export/import to move conversations between sessions
3. Set up a script to periodically export from LM Studio (if LM Studio provides an API)

**Q: How do other users access my saved conversations?**  
A: They need to have the same `memory/AUTO_SAVED/` folder structure with your files. Share the folder contents.

**Q: What happens to conversations when I close this session?**  
A: They're already saved in `./memory/AUTO_SAVED/` folder, so they persist even after this session ends.

## Next Steps

1. **Test the auto-recorder** with a simple conversation
2. **Integrate with your RAG system** by adding the `save_conversation()` call
3. **Set up a backup routine** to export conversations regularly
4. **Share the memory folder** with other users if needed

## Summary

You now have:
- ✅ `memory/` - Storage for conversations
- ✅ `memory/auto_recorder/auto_save.py` - Auto-saver script
- ✅ `memory/__init__.py` - ConversationLogger class
- ✅ `memory/sessions/` - Demo conversations
- ✅ `CONVERSATION_MEMORY_USAGE.md` - Usage guide

**To record conversations:**

```python
# Call this after each important conversation
save_conversation(
    session_name="your_session_name",
    messages=[
        {"role": "user", "content": "Your message"},
        {"role": "assistant", "content": "AI response"}
    ]
)
```

**That's it!** Your conversations will be automatically recorded and stored for future reference.