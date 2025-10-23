# Environment Variables Setup Guide

## Backend Environment Variables

Create a `.env` file in the `backend` directory with these variables:

```env
# Environment
ENVIRONMENT=production

# Fal AI (for image generation)
FAL_API_KEY=your_fal_api_key_here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Google OAuth (for calendar integration)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_PROJECT_ID=your_google_project_id_here
GOOGLE_REDIRECT_URI=https://your-backend-url.onrender.com/auth/google/callback

# Supabase (Database & Auth)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here

# Qdrant (Vector Database)
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here

# Redis (Job Queue - Upstash or Render Redis)
REDIS_URL=redis://default:password@host:port

# Backend Settings
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
JWT_SECRET=your_long_random_secret_key_here_min_32_chars
WEBHOOK_URL=https://your-backend-url.onrender.com

# PostgreSQL (Optional - if not using Supabase for this)
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=zyana
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your_password
```

## Frontend Environment Variables

Create a `.env.local` file in the `frontend` directory:

```env
# Supabase (for authentication)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Backend API URL
NEXT_PUBLIC_API_URL=https://your-backend-url.onrender.com
```

## How to Get Each API Key

### Fal AI API Key
1. Go to [fal.ai](https://fal.ai)
2. Sign up / Log in
3. Go to Dashboard → API Keys
4. Create new key

### Telegram Bot Token
1. Open Telegram
2. Search for [@BotFather](https://t.me/botfather)
3. Send `/newbot`
4. Follow instructions
5. Copy your bot token

### Google OAuth (Optional - for Calendar)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project or select existing
3. Enable Google Calendar API
4. Go to "Credentials"
5. Create OAuth 2.0 Client ID
6. Copy Client ID and Client Secret

### Supabase
1. Go to [supabase.com](https://supabase.com)
2. Create project
3. Go to Settings → API
4. Copy URL, anon key, and service_role key

### Qdrant Cloud
1. Go to [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create cluster (free tier available)
3. Copy cluster URL and API key

### Upstash Redis
1. Go to [upstash.com](https://upstash.com)
2. Create Redis database (free tier available)
3. Copy connection URL

### JWT Secret
Generate a random 32+ character string:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## ⚠️ Important Security Notes

- Never commit `.env` or `.env.local` files to Git
- Use different secrets for development and production
- Rotate API keys regularly
- Keep `SUPABASE_SERVICE_KEY` secret - it has admin access!

