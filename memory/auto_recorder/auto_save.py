#!/usr/bin/env python3
"""
Auto Conversation Saver
Saves conversations to the memory folder automatically
"""

from datetime import datetime
from pathlib import Path

AUTO_SAVE_DIR = Path("./memory/AUTO_SAVED")
AUTO_SAVE_DIR.mkdir(parents=True, exist_ok=True)

def save_conversation(session_name, messages, metadata=None):
    """Save a conversation to a session folder."""
    # Create session folder with unique name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"{session_name}_{timestamp}" if session_name else f"auto_{timestamp}"
    
    session_folder = AUTO_SAVE_DIR / session_id
    session_folder.mkdir(parents=True, exist_ok=True)
    
    filepath = session_folder / f"{session_id}.md"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Conversation: {session_id}\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Messages:** {len(messages)}\n\n")
        
        f.write("## Messages\n\n")
        
        role_emoji = {"user": "User", "assistant": "Assistant", "system": "System"}
        
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Simple markdown format
            f.write(f"{i}. [{role_emoji.get(role, 'Unknown')}] {role.title()}\n")
            f.write(f"> {content}\n\n")
    
    print(f"✅ Saved: {session_id}")
    print(f"   Location: {filepath}")
    print(f"   Messages: {len(messages)}")

if __name__ == "__main__":
    # This is a demo - in real use, you would pass conversation data
    print("Auto Conversation Saver")
    print("=======================")
    print()
    print("Usage:")
    print("  1. Call save_conversation() with your conversation data")
    print("  2. Conversations will be saved to: ./memory/AUTO_SAVED/")
    print()
    print("Example:")
    print("""
    conversation = {
        "session_name": "my_rag_session",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        "metadata": {"topic": "test"}
    }
    
    save_conversation(conversation["session_name"], conversation["messages"], 
                     conversation.get("metadata"))
    """)
