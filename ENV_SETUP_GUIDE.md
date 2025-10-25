# Environment Setup Guide

## 🔑 Required API Keys

### For Local Development

Create `backend/.env` file with:

```bash
# OpenAI (for embeddings)
OPENAI_API_KEY=your_openai_api_key_here

# Embedding Settings
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small

# Other existing variables...
FAL_API_KEY=your_fal_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_key
TELEGRAM_BOT_TOKEN=your_telegram_token
```

### For Production (Render)

Add these environment variables in Render Dashboard:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key (get from platform.openai.com) |
| `EMBEDDING_PROVIDER` | Set to `openai` |
| `EMBEDDING_MODEL` | Set to `text-embedding-3-small` |

## ✅ Verification

After adding the key, check logs for:
```
✅ OpenAI client initialized successfully
✅ EmbeddingService initialized with provider: openai
```

##  🔒 Security

- ⚠️ **NEVER** commit API keys to Git
- ⚠️ **NEVER** share API keys publicly
- ⚠️ Always use `.env` file (which is in `.gitignore`)

## 💰 Cost

- Model: `text-embedding-3-small`
- Price: $0.02 per 1M tokens
- Typical usage: ~$0.50-$1/month

