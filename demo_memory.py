"""
Conversation Logger Demo

Run this to test the conversation logging feature.

Usage:
    python demo_memory.py

Features:
- Start new conversation sessions
- Add messages (user and assistant)
- View conversation history
- Export conversations to markdown
"""

from memory import ConversationLogger
from datetime import datetime

# Initialize the conversation logger
logger = ConversationLogger(
    storage_dir="./memory",
    max_conversations=50,
    auto_save=True,  # Automatically save after each message
    file_format="md"  # Save as markdown files
)

print("=" * 60)
print("Conversation Logger Demo")
print("=" * 60)
print()

# 1. Start a new session
print("Step 1: Starting a new conversation session...")
session_id = logger.start_session("my_first_session")
print(f"Session started: {session_id}")
print()

# 2. Add some messages
print("Step 2: Adding messages to the conversation...")
print()

# First exchange
logger.add_message(session_id, "user", "Hi! This is a test conversation.")
logger.add_message(session_id, "assistant", "Hello! How can I help you today?")

# Second exchange
logger.add_message(session_id, "user", "I'm trying to understand the RAG system. Can you explain it?")
logger.add_message(session_id, "assistant", """
The RAG (Retrieval-Augmented Generation) system is designed to:

1. Process your documents (PDFs, MD files, etc.)
2. Chunk the content intelligently (by pages, topics, tables)
3. Create embeddings for vector storage
4. Answer queries based on your documents

It's like giving your LLM access to a database of your documents!
""")

# Third exchange with metadata
logger.add_message(
    session_id, 
    "user", 
    "How do I add PDFs to the system?",
    metadata={"topic": "pdf_handling", "context": "getting_started"}
)

logger.add_message(
    session_id, 
    "assistant", 
    """
To add PDFs to the RAG system:

    python3 main.py --documents /path/to/pdfs --query "your question"

The system will:
1. Scan the directory for PDF files
2. Extract text/tables/OCR from each PDF
3. Chunk the content intelligently
4. Store in a vector database
5. Answer your query using the indexed documents
""")

print("Messages added!")
print()

# 3. View the conversation
print("Step 3: Viewing your conversation...")
print()

conversation_text = logger.get_conversation_text(session_id)
print(conversation_text)
print()

# 4. Get recent history
print("Step 4: Getting last 3 messages from this session...")
print()

last_3_messages = logger.get_conversation_history(session_id, limit=3)
for i, msg in enumerate(last_3_messages, 1):
    role_name = {"user": "User", "assistant": "Assistant"}.get(msg["role"], msg["role"])
    print(f"[{i}] [{role_name}] {msg['content'][:50]}...")
print()

# 5. Get optimized memory context
print("Step 5: Generating memory context optimized for LLM (max 4000 tokens)...")
memory_context = logger.get_memory_context(session_id, max_tokens=4000)
print()
print("Memory Context:")
print("-" * 40)
print(memory_context)
print()

# 6. Export all conversations
print("Step 6: Exporting all conversations...")
logger.export_all_sessions("./memory/all_conversations.md")
print()

# 7. View stored files
print("Step 7: Your conversation files are saved at:")
print(f"   {logger.storage_dir.absolute()}")
print()

# List all session folders
import os
sessions_dir = logger.storage_dir / "sessions"
if sessions_dir.exists():
    session_files = list(sessions_dir.glob("*.md"))
    print(f"   Found {len(session_files)} conversation files:")
    for sf in session_files[:5]:  # Show first 5
        size = sf.stat().st_size
        print(f"   - {sf.name} ({size} bytes)")
    if len(session_files) > 5:
        print(f"   ... and {len(session_files) - 5} more")
print()

print("=" * 60)
print(f"Total sessions: {len(logger.get_all_sessions())}")
print("=" * 60)
print()

print("Demo complete! Your conversations are being saved.")
