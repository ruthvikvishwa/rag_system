# Conversation: using_the_system
**Started:** 2026-09-29 21:43:33

## Previous Conversation
---

# Conversation: using_the_system
**Started:** 2026-09-29 21:43:33


1. [💬 User]
> How do I use the system?

---

## New Message

2. [🤖 Assistant]
> 
**Step 1:** Add your documents
```bash
python3 main.py --documents ./my_documents
```

**Step 2:** Search for information
```bash
python3 main.py --documents ./my_documents -q "your question"
```

**Step 3:** Review results
The system will:
- Find relevant document chunks
- Calculate relevance scores
- Generate a comprehensive answer
- Show source documents


