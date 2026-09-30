#!/usr/bin/env python3
"""
Conversation Recorder - Saves your conversations to memory files

Usage:
    python3 record_conversation.py

This script records the current conversation and saves it as a .md file
in the memory folder for future reference.

Requirements:
    pip install python-dotenv (optional, for environment variables)
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import sys

# Configuration
MEMORY_DIR = Path("./memory")
ALL_CONVERSATIONS_DIR = MEMORY_DIR / "ALL_CONVERSATIONS"
RECORDS_DIR = MEMORY_DIR / "RECORDS"

# Create directories
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
ALL_CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
RECORDS_DIR.mkdir(parents=True, exist_ok=True)


def format_conversation(conversation: Dict) -> str:
    """
    Format a conversation (list of messages) as markdown.
    
    Expected conversation format:
    {
        "session_id": "some_id",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        "metadata": {...}
    }
    """
    lines = []
    
    # Session header
    session_id = conversation.get("session_id", datetime.now().strftime("%Y%m%d_%H%M%S_%N"))
    session_start = conversation.get("session_start", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    lines.append(f"# Conversation: {session_id}")
    lines.append(f"**Started:** {session_start}")
    lines.append(f"**Total Messages:** {len(conversation.get('messages', []))}")
    lines.append("")
    
    # Metadata
    metadata = conversation.get("metadata", {})
    if metadata:
        lines.append("## Metadata")
        for key, value in metadata.items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    
    # Messages
    lines.append("## Messages")
    lines.append("")
    
    for i, msg in enumerate(conversation.get("messages", []), 1):
        role_emoji = {
            "user": "💬",
            "assistant": "🤖",
            "system": "⚙️"
        }.get(msg.get("role", "user"), "💬")
        
        role_title = msg.get("role", "user").title()
        
        content = msg.get("content", "")
        # Escape markdown in content
        content = content.replace("```", "<<<CODE>>>").replace(">>>", "<<<>")
        
        lines.append(f"{role_emoji} **{role_title}**")
        lines.append(f"> {content}")
        
        if msg.get("metadata"):
            for key, value in msg["metadata"].items():
                lines.append(f"   - {key}: {value}")
        lines.append("")
    
    return "\n".join(lines)


def save_conversation(conversation: Dict):
    """Save a conversation to the memory folder."""
    session_id = conversation.get("session_id", datetime.now().strftime("%Y%m%d_%H%M%S_%N"))
    
    # Create session folder
    session_folder = RECORDS_DIR / session_id
    session_folder.mkdir(parents=True, exist_ok=True)
    
    # Create .md file
    filepath = session_folder / f"{session_id}.md"
    
    # Format and save
    content = format_conversation(conversation)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Saved conversation: {session_id}")
    print(f"   📁 Location: {filepath}")
    print(f"   📊 Messages: {len(conversation.get('messages', []))}")
    
    return filepath


def list_all_conversations():
    """List all saved conversations."""
    conversations = []
    
    # Find all .md files in RECORDS_DIR
    for md_file in RECORDS_DIR.glob("**/*.md"):
        conversations.append({
            "path": str(md_file),
            "session_id": md_file.stem,
            "modified": md_file.stat().st_mtime,
            "size": md_file.stat().st_size
        })
    
    # Sort by modification time (newest first)
    conversations.sort(key=lambda x: x["modified"], reverse=True)
    
    return conversations


def print_conversation_summary():
    """Print a summary of all saved conversations."""
    conversations = list_all_conversations()
    
    print("=" * 60)
    print("Saved Conversations")
    print("=" * 60)
    print()
    
    if not conversations:
        print("No conversations saved yet.")
        return
    
    print(f"Total: {len(conversations)} conversations")
    print()
    
    # Group by session
    sessions = {}
    for conv in conversations:
        session_id = conv["session_id"].split("_")[0]  # Get the main session name
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append(conv)
    
    # Print each session
    for session_id, sessions_list in sorted(sessions.items(), key=lambda x: x[0]):
        print(f"\n### {session_id}:")
        for conv in sessions_list[:3]:  # Show last 3
            print(f"   - {conv['session_id']}")
            print(f"     {conv['size']:,} bytes ({conv['size'] // 1024:.1f} KB)")
        if len(sessions_list) > 3:
            print(f"   ... and {len(sessions_list) - 3} more")
    
    print()
    print(f"Total: {len(conversations)} conversation files")
    total_size = sum(c["size"] for c in conversations)
    print(f"Total size: {total_size / 1024:.1f} KB")


def load_conversation(session_id: str):
    """Load a specific conversation by session ID."""
    sessions_dir = RECORDS_DIR / session_id
    if not sessions_dir.exists():
        print(f"❌ Session not found: {session_id}")
        return None
    
    # Get the most recent file for this session
    md_files = list(sessions_dir.glob("*.md"))
    if not md_files:
        print(f"❌ No files found for session: {session_id}")
        return None
    
    # Return the newest one
    md_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return md_files[0]


def export_all_conversations(output_path: str = "./memory/ALL_CONVERSATIONS/combined.md"):
    """Export all conversations to a single file."""
    conversations = list_all_conversations()
    
    if not conversations:
        print("No conversations to export.")
        return
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# All Saved Conversations\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Conversations:** {len(conversations)}\n\n")
        
        f.write("## Conversation List\n\n")
        for i, conv in enumerate(conversations[:20], 1):  # Show first 20
            f.write(f"### {i}. {conv['session_id']}\n")
            f.write(f"- Created: {datetime.fromtimestamp(conv['modified']).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- Size: {conv['size']:,} bytes\n\n")
        
        if len(conversations) > 20:
            f.write(f"\n... and {len(conversations) - 20} more conversations\n\n")
        
        f.write("\n## Full Content\n\n")
        
        for conv in conversations:
            f.write(f"---\n\n## Session: {conv['session_id']}\n\n")
            filepath = Path(conv["path"])
            f.write(filepath.read_text())
            f.write("\n\n")
    
    print(f"✅ Exported {len(conversations)} conversations to {output_path}")


# === MAIN ===

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Record and manage conversations")
    parser.add_argument("--save", "-s", action="store_true", 
                       help="Save current conversation")
    parser.add_argument("--list", "-l", action="store_true",
                       help="List all saved conversations")
    parser.add_argument("--load", "-t", type=str,
                       help="Load a specific conversation by session ID")
    parser.add_argument("--export", "-e", type=str,
                       help="Export all conversations to a file")
    parser.add_argument("--json", "-j", action="store_true",
                       help="Output in JSON format (for scripts)")
    
    args = parser.parse_args()
    
    if args.json:
        if args.save:
            # Return conversation data
            conversation_data = {
                "session_id": "current_session",
                "session_start": datetime.now().isoformat(),
                "messages": [
                    {
                        "role": args.input_role or "user",
                        "content": args.input_content or ""
                    }
                ],
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "script": "record_conversation.py"
                }
            }
            print(json.dumps(conversation_data, indent=2, default=str))
        elif args.list:
            conversations = list_all_conversations()
            print(json.dumps(conversations, indent=2, default=str))
        elif args.load:
            conv = load_conversation(args.load)
            if conv:
                print(conv.read_text())
            else:
                print("Conversation not found")
        elif args.export:
            export_all_conversations(args.export)
        else:
            print("Usage: --save or --list or --load <session_id> or --export <output>")
    else:
        if args.save:
            print("=" * 60)
            print("Conversation Recorder")
            print("=" * 60)
            print()
            
            # Get conversation data from environment or stdin
            conversation_data = {
                "session_id": os.environ.get("CONVERSATION_ID", f"session_{datetime.now().strftime('%H%M%S')}"),
                "session_start": os.environ.get("SESSION_START", datetime.now().isoformat()),
                "messages": os.environ.get("MESSAGES", "[]").strip("[]"),
                "metadata": {}
            }
            
            # Parse messages from environment
            import json
            try:
                conversation_data["messages"] = json.loads(os.environ.get("MESSAGES", "[]"))
            except:
                pass
            
            # Save the conversation
            save_conversation(conversation_data)
            print()
            
            print("Next steps:")
            print("  - Run this script before each new chat session")
            print("  - Set environment variables:")
            print("    CONVERSATION_ID=<your session name>")
            print("    MESSAGES=[{\"role\": \"user\", \"content\": \"...\"}, ...]")
            print()
        
        elif args.list:
            print_conversation_summary()
        
        elif args.load:
            filepath = load_conversation(args.load)
            if filepath:
                content = filepath.read_text()
                print(content[:5000])  # Limit output
            else:
                print(f"❌ Session not found: {args.load}")
        
        elif args.export:
            export_all_conversations(args.export)
        
        else:
            print("Usage:")
            print("  python3 record_conversation.py --save    # Save current conversation")
            print("  python3 record_conversation.py --list    # List all saved conversations")
            print("  python3 record_conversation.py --load <session_id>  # Load a conversation")
            print("  python3 record_conversation.py --export <output.md>  # Export all")
            print()
            print("For API usage, use --json flag with arguments.")
