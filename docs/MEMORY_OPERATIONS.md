# Memory & Learning System - Operations Guide

## Overview

Zyana's Memory & Learning System provides intelligent context-aware responses through:

- **Semantic Memory**: Vector-based storage for conversations, voice logs, and user interactions
- **RAG (Retrieval-Augmented Generation)**: Contextual memory retrieval for informed responses
- **Mirror Mode**: Communication style learning and imitation
- **Feedback Loop**: Continuous improvement through user ratings
- **Background Workers**: Automatic embedding generation and nightly summarization

---

## Architecture

```
User Message
     ↓
Intent Router → RAG Service → Retrieve Memories from Qdrant
     ↓                              ↓
Fal AI (with context)    ←    Memory Context
     ↓
Response Generation
     ↓
Mirror Mode Transformation
     ↓
Final Response
     ↓
Store Conversation → Embeddings Worker → Store in Qdrant
```

---

## Components

### 1. **Embedding Service** (`services/embeddings.py`)

**Purpose**: Pluggable embedding generation with multiple provider support.

**Providers**:
- **OpenAI** (primary): `text-embedding-3-small` - Fast, reliable
- **Fal AI** (fallback): Slower but integrated

**Configuration**:
```bash
EMBEDDING_PROVIDER=openai  # or "fal"
EMBEDDING_MODEL=text-embedding-3-small
```

**Features**:
- Automatic chunking for long texts
- Retry logic with exponential backoff
- Fallback provider support

**Usage**:
```python
from services.embeddings import embedding_service

# Single embedding
embedding = await embedding_service.embed_single("text")

# Batch embeddings
embeddings = await embedding_service.get_embedding(["text1", "text2"])

# With auto-chunking
results = await embedding_service.embed_with_chunking(long_text)
```

---

### 2. **RAG Service** (`services/rag.py`)

**Purpose**: Memory retrieval and context building for AI responses.

**Key Methods**:

- `retrieve_relevant_memories(query, user_id, top_k=5)`: Semantic search in Qdrant
- `build_rag_prompt(query, user_context, memories)`: Format context for AI
- `get_user_memory_context(user_id, query)`: Comprehensive context including Mirror Mode

**Configuration**:
```bash
MEMORY_SUMMARY_DAYS=90  # How far back to search
MIRROR_EMBED_K=5        # Number of Mirror Mode samples
```

**How It Works**:

1. User sends message
2. RAG retrieves top-K relevant memories from last 90 days
3. Fetches user preferences and habits
4. If Mirror Mode enabled, retrieves style samples
5. Formats all context into system prompt
6. Fal AI generates response with full context

---

### 3. **Embeddings Worker** (`workers/embeddings_worker.py`)

**Purpose**: Automatically embed new records and store in Qdrant.

**Processes**:
- `conversations` → `zyana_memory` collection
- `voice_logs` → `zyana_memory` collection
- `user_message_samples` → `mirror_samples` metadata

**Schedule**: On-demand or via cron (every 5 minutes recommended)

**Manual Run**:
```python
from workers.embeddings_worker import run_embeddings_worker
results = await run_embeddings_worker()
# Returns: {'conversations': 10, 'voice_logs': 5, 'mirror_samples': 3, 'errors': 0}
```

---

### 4. **Nightly Summarizer** (`workers/nightly_summarizer.py`)

**Purpose**: Daily memory consolidation and summarization.

**Schedule**: Daily at 2 AM (configurable)

**Process**:

1. For each user, fetch yesterday's conversations
2. Generate 3-5 bullet point summary via Fal AI
3. Store in `memory_summaries` table
4. Embed summary and store in Qdrant
5. (Optional) Cleanup old conversations

**Manual Run**:
```python
from workers.nightly_summarizer import run_nightly_summarization
results = await run_nightly_summarization()
# Returns: {'users_processed': 5, 'summaries_created': 5, 'errors': 0}
```

**Configuration**:
```bash
MEMORY_SUMMARY_DAYS=90  # Retention window
```

---

### 5. **Feedback System** (`routers/feedback.py`)

**Purpose**: Collect user ratings to improve response quality.

**API Endpoints**:

- `POST /feedback` - Submit rating (1-5) and optional comment
- `GET /feedback/recent` - List recent feedback (admin)
- `GET /feedback/stats` - Statistics (avg rating, distribution)
- `PUT /feedback/{id}` - Mark as reviewed (admin)

**Example**:
```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123",
    "source_type": "message",
    "rating": 5,
    "comment": "Great response!"
  }'
```

**Integration**: Add thumbs up/down buttons in Telegram messages.

---

### 6. **Mirror Mode** (`services/mirror_mode.py`)

**Purpose**: Learn and imitate user communication style.

**How It Works**:

1. User messages stored in `user_message_samples` table
2. Samples embedded and stored in Qdrant
3. When generating response, retrieve top-K similar samples
4. Include as few-shot examples in prompt
5. Apply style transformation to response

**Enable/Disable**:
```python
from services.mirror_mode import mirror_mode_service

# Enable
await mirror_mode_service.enable_mirror_mode(user_id)

# Disable
await mirror_mode_service.disable_mirror_mode(user_id)

# Check status
enabled = await mirror_mode_service.is_mirror_mode_enabled(user_id)
```

**Limit**: Max 100 samples per user (auto-managed via trigger)

---

## Database Tables

### `conversations`
Stores all user-assistant message exchanges.

```sql
- id: BIGSERIAL
- user_id: VARCHAR(255)
- session_id: VARCHAR(255)
- message: TEXT
- role: VARCHAR(50)  -- 'user' or 'assistant'
- timestamp: TIMESTAMPTZ
```

### `memory_summaries`
Daily conversation summaries.

```sql
- id: SERIAL
- user_id: VARCHAR(255)
- summary: TEXT
- date: DATE
- conversation_count: INT
```

### `feedback`
User ratings and comments.

```sql
- id: SERIAL
- user_id: TEXT
- source_type: TEXT
- source_id: TEXT
- rating: INT (1-5)
- comment: TEXT
- reviewed: BOOLEAN
```

---

## Qdrant Collections

### `zyana_memory` (main)
All memories: conversations, voice logs, summaries.

**Payload**:
```json
{
  "user_id": "123",
  "table": "conversations",
  "row_id": "456",
  "date": "2025-10-25T10:00:00Z",
  "snippet": "Message text...",
  "type": "conversation"
}
```

### `mirror_samples` (metadata tag)
User communication style samples.

**Payload**:
```json
{
  "user_id": "123",
  "table": "mirror_samples",
  "row_id": "789",
  "type": "mirror_sample",
  "snippet": "User's message..."
}
```

---

## Retention & Data Management

### Default Policies

- **Conversations**: Retained indefinitely (cleanup disabled)
- **Memory Summaries**: 90 days (configurable via `MEMORY_SUMMARY_DAYS`)
- **Feedback**: Retained indefinitely
- **Qdrant Vectors**: Permanent (manual deletion only)

### Cleanup (Optional)

To enable automatic cleanup:

```python
# In nightly_summarizer.py, uncomment deletion logic
await nightly_summarizer.cleanup_old_conversations(retention_days=30)
```

### "Forget" Feature

Delete all memories for a user:

```python
from clients.qdrant_client import qdrant_client

# Delete from Qdrant
await qdrant_client.delete_user_memories(user_id="123")

# Delete from Supabase
supabase_client.admin.table("conversations").delete().eq("user_id", "123").execute()
supabase_client.admin.table("memory_summaries").delete().eq("user_id", "123").execute()
```

**⚠️ WARNING**: This is irreversible!

---

## Cost Awareness

### Embedding Costs (OpenAI)

- **Model**: `text-embedding-3-small`
- **Cost**: $0.02 per 1M tokens (~4M characters)
- **Estimate**: 1000 messages/day ≈ $0.01/day

### Qdrant Storage

- **Self-hosted**: Free (requires Docker/VM)
- **Cloud**: ~$25/month for 1GB (100K vectors)

### Fal AI Usage

- **Embeddings**: Not recommended (slow)
- **Chat**: ~$0.50 per 1M tokens
- **Estimate**: 1000 messages/day ≈ $0.10/day

**Monthly Estimate**: ~$5-10 for typical usage

---

## Troubleshooting

### Issue: Embeddings not generating

**Check**:
1. `OPENAI_API_KEY` or `FAL_API_KEY` set?
2. Qdrant accessible? (`docker ps | grep qdrant`)
3. Worker running? Check logs

**Fix**:
```bash
# Test embedding service
python -c "
from services.embeddings import embedding_service
import asyncio
asyncio.run(embedding_service.embed_single('test'))
"
```

### Issue: RAG not retrieving memories

**Check**:
1. Qdrant collection exists? (`curl http://localhost:6333/collections`)
2. Vectors stored? Check collection count
3. User ID matches between Supabase and Qdrant?

**Fix**:
```bash
# Check Qdrant collections
curl http://localhost:6333/collections

# Force re-embed recent conversations
python -c "
from workers.embeddings_worker import run_embeddings_worker
import asyncio
asyncio.run(run_embeddings_worker())
"
```

### Issue: Mirror Mode not working

**Check**:
1. Mirror Mode enabled for user?
2. Samples stored in `user_message_samples`?
3. `MIRROR_EMBED_K` > 0?

**Fix**:
```python
from services.mirror_mode import mirror_mode_service
await mirror_mode_service.enable_mirror_mode(user_id=1)
```

### Issue: Nightly summarization failing

**Check**:
1. Conversations exist from yesterday?
2. Fal AI API accessible?
3. Supabase writable?

**Fix**: Run manually and check logs:
```python
from workers.nightly_summarizer import run_nightly_summarization
import asyncio
asyncio.run(run_nightly_summarization())
```

---

## Monitoring

### Key Metrics

1. **Embedding Success Rate**: `embeddings_worker` results
2. **RAG Context Hit Rate**: % of queries with relevant memories
3. **Mirror Mode Adoption**: Users with Mirror Mode enabled
4. **Feedback Ratings**: Average rating over time

### Health Checks

```bash
# Check Qdrant
curl http://localhost:6333/collections

# Check embedding service
curl http://localhost:8000/health

# Check recent feedback
curl http://localhost:8000/feedback/stats
```

### Logs

```bash
# Backend logs
tail -f backend/logs/zyana.log

# Worker logs
tail -f backend/logs/workers.log
```

---

## Best Practices

1. **Enable Mirror Mode Gradually**: Only for users who explicitly consent
2. **Monitor Embedding Costs**: Set OpenAI usage alerts
3. **Regular Backups**: Backup Supabase + Qdrant snapshots weekly
4. **Feedback Collection**: Add thumbs up/down to every response
5. **Privacy**: Implement data deletion requests via "Forget" feature
6. **Testing**: Run integration tests before production deployment

---

## Future Enhancements

- [ ] Weekly/monthly memory consolidation
- [ ] User-specific embedding models (fine-tuning)
- [ ] Advanced feedback analysis (sentiment, topic clustering)
- [ ] Memory pruning (auto-delete low-relevance memories)
- [ ] Multi-modal embeddings (images, audio)
- [ ] Federated learning for privacy

---

## Support

For issues or questions:
- Check logs: `backend/logs/`
- Review tests: `pytest backend/tests/`
- Documentation: `docs/`

**Contact**: System administrator

