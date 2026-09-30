# Conversation Memory - How to Use This Feature

This document explains how to use conversation memory files to record and leverage your chat history with the RAG system.

## What is Conversation Memory?

Conversation memory is a way to save your chats as `.md` files so:
1. **You can review them later** - Find conversations you had weeks ago
2. **Your LLM can "remember" them** - Feed past conversations as context to increase the LLM's effective context window
3. **No need to repeat yourself** - Past context is available when needed

## File Structure

When you use the conversation memory feature, files are saved like this:

```
/Users/ruthvik/rag_system/memory/
└── sessions/
    ├── getting_started/
    │   └── getting_started.md
    ├── using_the_system/
    │   └── using_the_system.md
    └── pdf_processing/
        └── pdf_processing.md
```

Each session gets its own folder with a `.md` file containing all the conversation history.

## How to Record Your Conversations

### Option 1: Manual (Simplest)

Just keep a notes file or use the memory folder directly. Example:

```bash
# After each RAG session, manually append to the file
echo "---" >> ./memory/sessions/your_session.md
```

Or better, use a script that logs after each RAG query.

### Option 2: Automatic with Python Code

Add this to your Python scripts:

```python
from pathlib import Path
from datetime import datetime
import re

# Initialize memory folder
MEMORY_DIR = Path("./memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# Start a new session
def start_session(name):
    session_id = name.replace(" ", "_").lower()
    session_folder = MEMORY_DIR / "sessions" / session_id
    session_folder.mkdir(parents=True, exist_ok=True)
    filepath = session_folder / f"{session_id}.md"
    # Create file with session header
    with open(filepath, "w") as f:
        f.write(f"# Conversation: {session_id}\n")
        f.write(f"**Started:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    return session_id, filepath

# Add messages
def add_message(session_id, role, content):
    filepath = Path(f"./memory/sessions/{session_id}/{session_id}.md")
    
    # Read existing content
    existing = ""
    if filepath.exists():
        existing = filepath.read_text()
    
    # Append new message
    with open(filepath, "w") as f:
        f.write(f"# Conversation: {session_id}\n")
        if existing:
            f.write(existing)
        f.write(f"\n\n### Message {len(existing.split('### Message')) + 1}\n\n")
        f.write(f"**{role.title()}:** {content}\n\n")
```

### Option 3: Use the ConversationLogger Class

We've already built a Python class for this:

```python
from memory import ConversationLogger

# Initialize once
memory = ConversationLogger(
    storage_dir="./memory",
    auto_save=True,  # Save after each message
    file_format="md"  # Output as markdown
)

# Start a session
session_id = memory.start_session("my_project")

# Add messages
memory.add_message(session_id, "user", "How do I use RAG?")
rag_answer = query_rag_system("How do I use RAG?")
memory.add_message(session_id, "assistant", rag_answer)

# View your conversation
print(memory.get_conversation_text(session_id))

# Get context optimized for LLM (last 4000 tokens)
context = memory.get_memory_context(session_id, max_tokens=4000)

# Export all sessions
memory.export_all_sessions("./memory/backup_all.md")
```

## How LLMs Can Use These Files

### 1. Direct File Reading

Most LLMs can read files directly:

```python
from langchain.document_loaders import TextLoader
from pathlib import Path

# Load a conversation file
loader = TextLoader("./memory/sessions/getting_started/getting_started.md")
documents = loader.load()

# Feed to your LLM chain
llm_chain = LLMChain(llm=llm, input_documents=documents)
```

### 2. Manual Context Injection

```python
from pathlib import Path

# Read conversation
session = Path("./memory/sessions/getting_started/getting_started.md")
conversation_content = session.read_text()

# Feed as system prompt
system_message = f"""
## Chat History:
{conversation_content}

## Current Question:
{user_question}

Please answer based on both the chat history and your knowledge.
"""

response = llm(system_message)
```

### 3. Programmatic Session Lookup

```python
from pathlib import Path
import glob

# Find all session files matching a pattern
session_files = glob.glob("./memory/sessions/pdf_*/getting_started*.md")

# Combine them into context
all_context = ""
for f in session_files:
    all_context += f.read_text() + "\n\n---\n\n"

# Feed to LLM
llm_query(all_context + user_question)
```

## Example Conversation File Format

```markdown
# Conversation: getting_started
**Started:** 2024-01-15 10:30:00

## Metadata
- session_id: getting_started
- topic: RAG basics
- purpose: first_time_user

## Messages

💬 **User**
> What is the RAG system?

🤖 **Assistant**
> The RAG (Retrieval-Augmented Generation) system is a framework for building...

💬 **User**
> How does it work?

🤖 **Assistant**
> RAG works by:
> 1. Document ingestion
> 2. Chunking
> 3. Embedding
> 4. Retrieval
> 5. Generation

## Summary
The user is asking basic questions about RAG system concepts and how to use it.
```

## Benefits of Using Conversation Memory

### 1. Increased Context Window

Without memory:
```
LLM can only see: current query
```

With memory:
```
LLM sees:
1. All past conversations (goals, decisions, context)
2. Current query
```

This effectively **multiplies** your LLM's context window!

### 2. Consistency

LLM remembers:
- Previous decisions
- Your preferences
- Project requirements
- Terminology you've established

### 3. Continuity

If your session crashes or ends:
- Just resume from where you left off
- All context is preserved in the .md file

### 4. Debugging

Keep a record of:
- What you asked
- What the RAG system answered
- What went wrong (and how you fixed it)

## Integrating with Your RAG System

### Method 1: Simple Wrapper

```python
from rag_system import DemoRAGSystem
from pathlib import Path

class MemoryEnhancedRAG:
    def __init__(self, documents_dir, memory_dir="./memory"):
        self.rag = DemoRAGSystem(documents_dir)
        self.memory_dir = Path(memory_dir)
        self.current_session = None
    
    def query(self, user_query):
        # Start or continue session
        if not self.current_session:
            self.current_session = "session_auto"
        
        # Log user query
        self._log_message("user", user_query)
        
        # Get RAG answer
        rag_result = self.rag.search(user_query)
        
        # Format answer with memory context
        answer = f"""
**Based on your question:** {user_query}

**Current Context from Past Conversations:**
{self._get_relevant_memory(user_query)[:1000]}

**RAG Answer:**
{rag_result.answer}

**Sources:**
{chr(10).join([f"- {s['metadata'].get('doc_title')}" for s in rag_result.sources[:3]])}
"""
        
        # Log assistant response
        self._log_message("assistant", answer)
        
        return answer
    
    def _log_message(self, role, content):
        """Save message to conversation file."""
        session_folder = self.memory_dir / self.current_session
        session_folder.mkdir(parents=True, exist_ok=True)
        filepath = session_folder / f"{self.current_session}.md"
        
        with open(filepath, "a") as f:
            f.write(f"\n\n### Message\n\n")
            f.write(f"**{role.title()}:** {content}\n\n")
    
    def _get_relevant_memory(self, query):
        """Find and return relevant past conversations."""
        if not self.memory_dir.exists():
            return ""
        
        session_files = list(self.memory_dir.glob("sessions/*/*.md"))
        
        # Simple keyword matching
        context = []
        for sf in session_files[:10]:  # Limit to 10 files
            content = sf.read_text()
            if query.lower() in content.lower():
                context.append(f"From {sf.name}: {content[:500]}")
        
        return "\n\n".join(context)
```

## Reading Your Conversation Files

### View a Specific Session

```bash
cd /Users/ruthvik/rag_system
cat memory/sessions/getting_started/getting_started.md
```

Or open in your editor:
```bash
code memory/sessions/getting_started/getting_started.md
```

### Search Across All Conversations

```bash
# Search for a keyword
grep -r "how do I add pdfs" memory/sessions/

# Count matching conversations
grep -r "pdf" memory/sessions/ | wc -l
```

### Python Script to Search

```python
from pathlib import Path
import glob

# Search all conversation files
search_term = "add pdfs"
for f in Path("memory").glob("sessions/**/*.md"):
    if search_term.lower() in f.read_text().lower():
        print(f"Found in: {f.name}")
```

### Export All Conversations

```bash
# Use the ConversationLogger class
python3 -c "
from memory import ConversationLogger
logger = ConversationLogger()
logger.export_all_sessions('/path/to/backup/All_My_Conversations.md')
"
```

## Tips for Best Results

### 1. Use Meaningful Session Names

```python
# Good
memory.start_session("pdf_handling")
memory.start_session("code_review")
memory.start_session("research_project")

# Not so good
memory.start_session("session_20240115_103000_123")  # Too long, confusing
```

### 2. Add Metadata

When adding messages, include relevant metadata:

```python
memory.add_message(session_id, "user", query, metadata={
    "topic": "pdf_extraction",
    "priority": "high",
    "attempt": 1
})
```

### 3. Keep Sessions Focused

One session = one topic or one task.

```
❌ Mixed session:
  - Question 1: About RAG
  - Question 2: About PDFs
  - Question 3: About code

✅ Focused sessions:
  - RAG_basics/
  - PDF_handling/
  - Code_review/
```

### 4. Periodically Clean Up

```python
# Keep only last 20 sessions
memory.cleanup_old_sessions(keep_last=20)
```

Or manually:
```bash
# Delete sessions from old date
find memory/sessions -type f -mtime +30 -name "*.md" -delete
```

## Storage Estimation

Typical conversation file sizes:
- Short exchange: ~1KB
- Medium discussion: ~5KB
- Long technical deep-dive: ~20KB

For 50 conversations: ~50-1000KB (0.5-1MB)

This is very lightweight and won't fill your disk!

## FAQ

**Q: Do I have to use this feature?**  
A: No! It's optional. But it's very helpful for long conversations.

**Q: What format should I use?**  
A: Markdown (.md) is easiest for humans AND LLMs to read.

**Q: Where should I store the files?**  
A: Anywhere! We create `./memory` folder by default. You can use any path.

**Q: How often should I save?**  
A: Auto-save is recommended. Or manually after each query.

**Q: Can different LLMs read my files?**  
A: Yes! Any LLM that can read markdown files (Claude, GPT, etc.)

**Q: What if I want to start fresh?**  
A: Just create a new session: `memory.start_session("new_topic")`

**Q: How do I share my conversations?**  
A: Copy the session .md file or export all with `export_all_sessions()`

**Q: Can I search my conversations?**  
A: Yes! Use `grep` command or Python scripts to search through the files.

## Next Steps

1. **Read the demo files** in `./memory/sessions/` folder
2. **Try adding your own conversations** using the code examples
3. **Set up automatic logging** in your RAG scripts
4. **Use the memory** with your LLM for better answers

## Quick Reference

| Task | Code | Command |
|------|------|---------|
| Start session | `memory.start_session("name")` | N/A |
| Add message | `memory.add_message(sid, "user", "msg")` | See examples |
| Get history | `memory.get_conversation_text("session")` | `cat memory/sessions/name/name.md` |
| Export all | `memory.export_all_sessions("backup.md")` | N/A |
| Search | `memory.find_related_conversations(query)` | `grep -r "query" memory/` |

---

For the full ConversationLogger API, see `memory/__init__.py`.

For examples, see `CONVERSATION_MEMORY.md`.