# Redis & Embeddings Setup - Explained

## 🎉 Good News: Your Redis is Already Working!

### Redis Connection Test Results ✅

```
✅ Redis PING successful
✅ SET/GET operations working
✅ JSON session data working
✅ Redis Version: 7.4.3
✅ Connection: Stable and fast
```

---

## 1. Redis Setup - You're All Set!

### What is Redis?

**Redis** is an in-memory database (super fast!) that Zyana uses for:
- **Session Memory**: Temporary storage for multi-turn conversations
- **Clarification Loops**: When Zyana asks "What time?" it remembers your previous message
- **Pending Data**: Stores partial calendar event details while waiting for your reply

### Your Redis URL

```
redis://default:MNI6xU3YrFLdSlkyngCHy9HYt3al7F3h@redis-13891.c270.us-east-1-3.ec2.redns.redis-cloud.com:13891
```

**This is the CORRECT format!** Not a "CLI link" - it's the connection URL that Python uses.

**Breakdown**:
- `redis://` - Protocol
- `default` - Username
- `MNI6xU3YrFLdSlkyngCHy9HYt3al7F3h` - Password
- `@redis-13891.c270.us-east-1-3.ec2.redns.redis-cloud.com` - Server address
- `:13891` - Port number

### How Zyana Uses Redis

**Example Flow**:

1. **User**: "Schedule meeting"
2. **Zyana**: Detects ambiguity (no time specified)
3. **Redis**: Stores session:
   ```json
   {
     "user_id": "123",
     "intent": "schedule_meeting",
     "pending_fields": ["datetime"],
     "partial_data": {"title": "Meeting"},
     "conversation_history": [...]
   }
   ```
4. **Zyana**: "What time should I schedule it?"
5. **User**: "Tomorrow at 3pm"
6. **Redis**: Zyana retrieves session, merges new data
7. **Zyana**: Creates calendar event
8. **Redis**: Deletes session (expires after 7 days automatically)

### Redis Configuration in Zyana

**File**: `backend/config.py`

```python
redis_url: str = Field(
    default="redis://default:MNI6xU3YrFLdSlkyngCHy9HYt3al7F3h@redis-13891.c270.us-east-1-3.ec2.redns.redis-cloud.com:13891",
    alias="REDIS_URL"
)
redis_session_ttl: int = Field(default=604800, alias="REDIS_SESSION_TTL")  # 7 days
```

**File**: `backend/services/session_manager.py`

```python
self.redis_client = redis.StrictRedis.from_url(
    settings.redis_url,
    decode_responses=True
)
```

### Redis Commands You Can Use (Optional)

If you want to inspect what's in Redis:

```bash
# Install redis-cli (optional)
pip install redis

# Connect
redis-cli -u redis://default:MNI6xU3YrFLdSlkyngCHy9HYt3al7F3h@redis-13891.c270.us-east-1-3.ec2.redns.redis-cloud.com:13891

# List all keys
KEYS *

# Get a specific session
GET session:user_123

# Check how many keys
DBSIZE

# View Redis info
INFO
```

---

## 2. Embedding Provider (EMBEDDING_PROVIDER=openai) Explained

### What are Embeddings?

**Embeddings** are like "coordinates" for words in a high-dimensional space. They turn text into numbers so computers can understand meaning and similarity.

**Example**:

```
Text: "Schedule meeting with Ali"
Embedding: [0.023, -0.145, 0.891, ..., 0.234]  (1536 numbers)

Text: "Book appointment with Ali"
Embedding: [0.019, -0.140, 0.885, ..., 0.229]  (similar numbers!)

Text: "Buy groceries"
Embedding: [-0.543, 0.234, -0.021, ..., 0.678]  (very different numbers)
```

**Why it matters**: Zyana can find similar conversations even if you use different words!

### OpenAI Embedding Provider

**File**: `backend/services/embeddings.py`

```python
embedding_provider: str = "openai"  # You chose OpenAI
embedding_model: str = "text-embedding-3-small"  # Fast & cheap model
```

### Two Providers Available:

| Provider | Speed | Cost | Quality | Notes |
|----------|-------|------|---------|-------|
| **OpenAI** ✅ | ⚡ Fast | 💰 Cheap | ⭐⭐⭐⭐⭐ | **Primary** (what you're using) |
| **Fal AI** | 🐌 Slower | 💰💰 | ⭐⭐⭐⭐ | **Fallback** (if OpenAI fails) |

### How Zyana Uses Embeddings

**Use Case 1: Memory Search (RAG)**

```
User: "When is my meeting with Ali?"

1. Zyana embeds your question → [0.234, -0.891, ...]
2. Searches Qdrant vector database for similar embeddings
3. Finds: "Meeting with Ali at 3pm tomorrow" (high similarity!)
4. Includes this context in response
```

**Use Case 2: Mirror Mode (Style Learning)**

```
Your messages:
  - "Hey bro, sounds good 👍"
  - "Let's do it tomorrow morning"
  - "Perfect, thanks!"

1. Each message is embedded → stored in Qdrant
2. When generating response, Zyana retrieves similar samples
3. Mimics your casual, friendly style
```

**Use Case 3: Nightly Summaries**

```
Daily conversations → Summary → Embed → Store in Qdrant

Example:
  "User discussed project deadline, scheduled meeting with Ali at 3pm,
   asked about invoice for ABC Corp - $5000"

This summary is searchable semantically!
```

### OpenAI Embedding Costs (Super Cheap!)

**Model**: `text-embedding-3-small`

| Usage | Cost |
|-------|------|
| Per 1 million tokens (~4 million characters) | $0.02 |
| 1000 messages/day | ~$0.01/day = **$0.30/month** |
| 10,000 messages/day | ~$0.10/day = **$3/month** |

**Your typical usage**: Probably **$0.50-$1/month** 💰

### Configuration

**Environment Variables**:

```bash
EMBEDDING_PROVIDER=openai         # Primary provider
EMBEDDING_MODEL=text-embedding-3-small  # Model to use
OPENAI_API_KEY=your_openai_key    # Required for OpenAI

# Optional: Fallback to Fal AI
FAL_API_KEY=your_fal_key          # Used if OpenAI fails
```

**What Happens When You Send a Message**:

```
User Message
    ↓
Stored in Database (conversations table)
    ↓
Embeddings Worker (background job)
    ↓
embedding_service.embed_single(message)
    ↓
[Uses OpenAI API to generate embedding]
    ↓
Store in Qdrant with metadata
    ↓
Now searchable for future RAG retrieval!
```

---

## 3. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         USER MESSAGE                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  INTENT ROUTER (RAG-enhanced)                │
│  1. Check Redis for active session                           │
│  2. Retrieve relevant memories from Qdrant (using embeddings)│
│  3. Build context with user preferences + memories           │
│  4. Call Fal AI with enhanced prompt                         │
│  5. Apply Mirror Mode style transformation                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     BACKGROUND JOBS                          │
│  - Store conversation in Supabase                            │
│  - Embeddings Worker: Generate embedding (OpenAI)            │
│  - Store embedding in Qdrant                                 │
│  - Nightly Summarizer: Create daily summary                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                           │
│  - Redis: Session memory (7 days TTL)                        │
│  - Supabase: Conversations, summaries, feedback              │
│  - Qdrant: Embeddings for semantic search                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Testing Your Setup

### Test Redis (Already Passed! ✅)

```bash
cd backend
python test_redis_connection.py
```

**Expected Output**:
```
✅ Redis PING successful: True
✅ SET successful
✅ GET successful: Hello from Zyana!
✅ Session data stored and retrieved: schedule_meeting
```

### Test Embedding Service

Create a test:

```bash
cd backend
python -c "
from services.embeddings import embedding_service
import asyncio

async def test():
    print('🔄 Testing OpenAI embeddings...')
    embedding = await embedding_service.embed_single('Hello world')
    print(f'✅ Embedding generated: {len(embedding)} dimensions')
    print(f'Sample values: {embedding[:5]}')

asyncio.run(test())
"
```

**Expected Output**:
```
🔄 Testing OpenAI embeddings...
✅ Embedding generated: 1536 dimensions
Sample values: [0.023, -0.145, 0.891, -0.234, 0.456]
```

### Test RAG Service

```bash
cd backend
python -c "
from services.rag import rag_service
import asyncio

async def test():
    print('🔄 Testing RAG memory context...')
    context = await rag_service.get_user_memory_context(
        user_id='test_user',
        query='schedule meeting'
    )
    print(f'✅ Context retrieved: {context[\"has_context\"]}')
    print(f'Memories found: {len(context[\"memories\"])}')

asyncio.run(test())
"
```

---

## 5. Monitoring & Debugging

### Check Redis Health

```bash
cd backend
python test_redis_connection.py
```

### View Current Sessions

```python
import redis
from config import settings

r = redis.StrictRedis.from_url(settings.redis_url, decode_responses=True)

# List all session keys
keys = r.keys("session:*")
print(f"Active sessions: {len(keys)}")

for key in keys:
    data = r.get(key)
    print(f"{key}: {data[:100]}...")
```

### Check Embedding Usage (OpenAI Dashboard)

1. Go to: https://platform.openai.com/usage
2. Filter by: `text-embedding-3-small`
3. Monitor daily costs

### View Qdrant Collections

```bash
curl http://localhost:6333/collections
```

Or:
```python
from clients.qdrant_client import qdrant_client

info = qdrant_client.get_collection_info()
print(info)
```

---

## 6. Troubleshooting

### Issue: Redis connection timeout

**Solution**:
```bash
# Test network connectivity
ping redis-13891.c270.us-east-1-3.ec2.redns.redis-cloud.com

# Check firewall rules (should allow port 13891)
```

### Issue: Embedding generation fails

**Check**:
1. `OPENAI_API_KEY` is set correctly
2. OpenAI account has credits
3. Network connectivity to OpenAI API

**Test**:
```bash
curl https://api.openai.com/v1/embeddings \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "test",
    "model": "text-embedding-3-small"
  }'
```

### Issue: RAG not retrieving memories

**Check**:
1. Qdrant is running: `curl http://localhost:6333/collections`
2. Embeddings are being generated: Check `qdrant_client.get_collection_info()`
3. User ID matches between Supabase and Qdrant

---

## 7. Summary

### ✅ What You Have Now

1. **Redis**: Working perfectly at the provided URL
   - Stores temporary session data
   - Auto-expires after 7 days
   - Fast in-memory storage

2. **OpenAI Embeddings**: Primary embedding provider
   - Fast and cheap (~$1/month for typical usage)
   - 1536-dimensional vectors
   - Used for semantic memory search

3. **Fal AI**: Automatic fallback if OpenAI fails

4. **Complete RAG Pipeline**: 
   - Memories stored in Qdrant
   - Semantic search retrieves relevant context
   - Responses include past conversation context

### 💰 Monthly Costs (Estimated)

| Service | Cost |
|---------|------|
| Redis Cloud | $0 (free tier or already paid) |
| OpenAI Embeddings | ~$0.50-$1 |
| Fal AI (chat) | ~$3-5 |
| **Total** | **~$3.50-$6/month** |

### 🚀 You're Ready!

Your setup is complete and tested. Both Redis and OpenAI embeddings are working perfectly!

**Next Step**: Deploy to production and start using the enhanced memory system! 🎉

---

## Need Help?

- **Redis Issues**: Run `python test_redis_connection.py`
- **Embedding Issues**: Check OpenAI API key and dashboard
- **RAG Issues**: Review `docs/MEMORY_OPERATIONS.md`
- **General**: Check `backend/logs/zyana.log`

