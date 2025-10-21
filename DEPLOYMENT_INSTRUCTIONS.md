# Zyana AI - Deployment Instructions

## 🎉 Project Complete!

The complete Zyana AI system has been built and is ready for deployment.

## What Has Been Built

### ✅ Backend (FastAPI)
- **Location:** `backend/`
- **Features:**
  - FastAPI application with CORS and error handling
  - Fal AI client for LLM chat and embeddings
  - Supabase client for database operations
  - Qdrant client for vector storage
  - Message parser with two-stage approach
  - Specialized agents (Finance, Calendar, Memory, Video, Habit Learner)
  - REST API endpoints for all functionality
  - Background workers (RQ) for scheduled tasks
  - Telegram bot integration

### ✅ Frontend (Next.js)
- **Location:** `frontend/`
- **Features:**
  - Modern dashboard with business overview
  - Transaction tracking and visualization
  - Memory search with AI-powered results
  - Agent console for direct commands
  - Responsive design with Tailwind CSS
  - TypeScript for type safety

### ✅ Desktop Agent (Electron)
- **Location:** `desktop-agent/`
- **Features:**
  - File system monitoring for video files
  - Automated job submission to backend
  - Configuration UI for watch folders
  - Activity logs
  - Secure command whitelisting

### ✅ Database Schema
- **Location:** `backend/migrations/001_initial_schema.sql`
- **Tables:** businesses, users, transactions, loans, goals, events, agent_logs, habit_profiles, memory_summaries
- **Features:** RLS policies, indexes, materialized views

### ✅ Documentation
- **Location:** `docs/`
- **Files:**
  - `architecture.md` - System architecture overview
  - `deployment.md` - Deployment guide (Docker, VPS, PaaS)
  - `onboarding.md` - User onboarding guide
  - `api.md` - Complete API documentation

### ✅ Tests & CI/CD
- **Tests:** `backend/tests/`
- **CI/CD:** `.github/workflows/ci.yml`
- **Features:** Pytest setup, GitHub Actions pipeline

## Quick Start

### 1. Apply Database Migrations

**Option A: Via Supabase Dashboard**
1. Go to https://supabase.com/dashboard/project/YOUR_PROJECT/sql
2. Copy contents of `backend/migrations/001_initial_schema.sql`
3. Paste and run

**Option B: Via psql**
```bash
psql $SUPABASE_CONNECTION_STRING < backend/migrations/001_initial_schema.sql
```

### 2. Start Infrastructure (Development)

```bash
# Start Postgres, Redis, Qdrant
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:3000

### 5. Set Telegram Webhook

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "http://your-backend-url/webhook/telegram"}'
```

For local testing, use ngrok or similar:
```bash
ngrok http 8000
# Use the https URL for webhook
```

### 6. Authorize Google Calendar

1. Visit: http://localhost:8000/calendar/auth/google
2. Copy the authorization URL
3. Open in browser and grant permissions
4. Complete authorization

## Environment Variables Required

Your `.env` file already contains:
```
FAL_API_KEY=e6f8df20-14bf-4ac4-bb36-d2f04ec664dd:935918035b5a881d42db9ecb1147893c
TELEGRAM_BOT_TOKEN=7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU
GOOGLE_CLIENT_ID=711714603933-p5ffenv2uumnmnapu98el3ahktdssbu0.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_PROJECT_ID=zyana-475803
SUPABASE_URL=https://yrwlvurrjzsosfkyaacq.supabase.co
SUPABASE_ANON_KEY=<your_anon_key>
SUPABASE_SERVICE_KEY=<your_service_key>
```

## Verify Everything Works

### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "redis": "ok",
    "qdrant": "ok",
    "fal_ai": "ok"
  }
}
```

### 2. Send Test Message via Telegram

Open Telegram, find your bot, send:
```
I received Rs 50,000 from milk sales today
```

Expected response from Zyana:
```
✅ Recorded income: PKR 50,000
Business: MilkBusiness
Category: sales
```

### 3. Check Dashboard

Open http://localhost:3000 and verify:
- Businesses are displayed (Vidify, MilkBusiness, Yazman Express)
- Navigation works
- Memory search is accessible

## Production Deployment

### Option 1: Docker (Recommended)

```bash
# Build and run
docker-compose -f docker-compose.dev.yml up -d

# Or use production compose file (create one based on dev)
```

### Option 2: Platform as a Service

**Backend on Railway:**
1. Connect GitHub repo
2. Set environment variables
3. Deploy

**Frontend on Vercel:**
1. Import project
2. Set `frontend/` as root directory
3. Add environment variables
4. Deploy

See `docs/deployment.md` for detailed instructions.

## Desktop Agent (Optional)

```bash
cd desktop-agent
npm install
npm run dev
```

Configure:
1. API URL: http://localhost:8000
2. Auth Token: (get from backend)
3. Add watch folders

## Testing

Run backend tests:
```bash
cd backend
pytest tests/ -v
```

## Troubleshooting

### Backend won't start
- Check environment variables in `.env`
- Verify Postgres is running (Docker Compose or Supabase)
- Check logs for specific errors

### Telegram bot not responding
- Verify webhook is set: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
- Check backend is accessible from internet
- Review backend logs

### Frontend can't connect
- Verify `NEXT_PUBLIC_API_URL` points to backend
- Check CORS settings in backend
- Open browser console for errors

## Next Steps

1. **Apply migrations** to Supabase
2. **Start services** (backend, frontend)
3. **Set Telegram webhook**
4. **Test with sample messages**
5. **Authorize Google Calendar**
6. **Deploy to production** (optional)

## File Structure

```
zyana/
├── backend/                 # FastAPI backend
│   ├── agents/             # AI agents
│   ├── clients/            # External API clients
│   ├── migrations/         # Database migrations
│   ├── models/             # Pydantic schemas
│   ├── prompts/            # AI prompts
│   ├── routers/            # API endpoints
│   ├── services/           # Business logic
│   ├── workers/            # Background jobs
│   ├── memory/             # Vector operations
│   └── tests/              # Unit tests
├── frontend/               # Next.js dashboard
│   ├── app/                # App router pages
│   ├── components/         # React components
│   └── lib/                # Utilities
├── desktop-agent/          # Electron app
│   └── src/
│       ├── main/           # Main process
│       └── renderer/       # UI
├── docs/                   # Documentation
├── config/                 # Configuration files
├── .github/workflows/      # CI/CD
└── docker-compose.dev.yml  # Docker setup
```

## Resources

- **Architecture:** `docs/architecture.md`
- **Deployment:** `docs/deployment.md`
- **Onboarding:** `docs/onboarding.md`
- **API Docs:** `docs/api.md`
- **Swagger UI:** http://localhost:8000/docs

## Support

- Check documentation in `docs/`
- Review API docs at `/docs` endpoint
- Check logs for errors
- Verify environment variables

---

**🚀 Zyana AI is ready to use!**

Start your backend and frontend, set the Telegram webhook, and begin chatting with your AI assistant.

For questions or issues, refer to the comprehensive documentation in the `docs/` directory.

