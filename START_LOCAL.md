# 🚀 Start Zyana Locally

Quick guide to run Zyana on your local machine for development and testing.

---

## Prerequisites

- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ Git
- ✅ Supabase account (free)
- ✅ API keys ready (see ENV_SETUP.md)

---

## Step 1: Clone & Setup

```bash
# Clone repository
git clone https://github.com/yourusername/zyana.git
cd zyana
```

---

## Step 2: Backend Setup (5 min)

### Install Python dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Setup environment variables

```bash
# Create .env file
copy .env.example .env    # Windows
# OR
cp .env.example .env      # Mac/Linux

# Edit .env with your values
# See ENV_SETUP.md for details
```

### Run migrations

1. Go to Supabase SQL Editor: https://supabase.com/dashboard
2. Open `backend/migrations/001_initial_schema.sql`
3. Copy all and paste in SQL Editor
4. Click RUN

### Start backend

```bash
# Make sure you're in backend/ folder and venv is activated
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend running at: http://localhost:8000
✅ API docs at: http://localhost:8000/docs

---

## Step 3: Frontend Setup (3 min)

### Install Node dependencies

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install
```

### Setup environment variables

```bash
# Create .env.local file
copy .env.example .env.local    # Windows
# OR
cp .env.example .env.local      # Mac/Linux

# Edit .env.local with your values:
# NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Start frontend

```bash
npm run dev
```

✅ Frontend running at: http://localhost:3000

---

## Step 4: Test Telegram Bot Locally (Optional)

For local testing with Telegram, you need ngrok or a similar tunneling service:

### Using ngrok

```bash
# Install ngrok: https://ngrok.com
# Start ngrok tunnel
ngrok http 8000
```

You'll get a URL like: `https://abc123.ngrok.io`

### Set webhook

```powershell
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" `
  -H "Content-Type: application/json" `
  -d '{"url": "https://abc123.ngrok.io/webhook/telegram"}'
```

Now send messages to your bot - they'll come to your local backend!

⚠️ **Note**: For production, use the cloud deployment (see DEPLOYMENT_GUIDE.md)

---

## 🧪 Testing Your Setup

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status": "healthy", "services": {...}}
```

### Test Frontend

1. Open: http://localhost:3000
2. Try to login with Supabase auth
3. Navigate around the dashboard

### Test API

Visit: http://localhost:8000/docs

Try the endpoints:
- GET `/` - Root endpoint
- GET `/health` - Health check
- POST `/agent/chat` - Send message to agent

---

## 📂 Project Structure

```
zyana/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── agents/              # AI agents
│   ├── routers/             # API routes
│   ├── services/            # Business logic
│   ├── models/              # Data models
│   └── requirements.txt     # Python dependencies
│
├── frontend/
│   ├── app/                 # Next.js app
│   ├── components/          # React components
│   ├── lib/                 # Utilities
│   └── package.json         # Node dependencies
│
└── docs/                    # Documentation
```

---

## 🔧 Common Issues

### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check .env file exists
ls .env  # or dir .env on Windows
```

### Frontend won't start

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Database connection error

- Check your Supabase URL and keys in `.env`
- Verify Supabase project is active
- Check if migrations ran successfully

### Redis connection error

For local development, you can comment out Redis-dependent features or use local Redis:

```bash
# Install Redis locally
# Windows: https://github.com/microsoftarchive/redis/releases
# Mac: brew install redis
# Linux: sudo apt-get install redis-server

# Start Redis
redis-server
```

---

## 🎯 What's Next?

1. ✅ Read the architecture docs: `docs/architecture.md`
2. ✅ Explore the API: http://localhost:8000/docs
3. ✅ Make changes and see them live reload!
4. ✅ When ready, deploy to production: `DEPLOYMENT_GUIDE.md`

---

## 🛠️ Development Commands

### Backend

```bash
# Run tests
pytest

# Format code
black .

# Lint code
flake8 .

# Type check
mypy .
```

### Frontend

```bash
# Run tests (when added)
npm test

# Lint
npm run lint

# Build for production
npm run build

# Start production build
npm run start
```

---

## 🐛 Debugging

### Backend Logs

The backend will log to console. Look for:
- 🚀 Startup messages
- ❌ Error messages
- ℹ️ Info about requests

### Frontend Logs

- Check browser console (F12)
- Check terminal where `npm run dev` is running

### Database Queries

View in Supabase Dashboard:
- Go to Table Editor to see data
- Go to Logs to see queries

---

## 🚀 Ready to Deploy?

Once everything works locally, deploy to production:

1. **Quick**: See `QUICK_DEPLOY.md` (30 min)
2. **Detailed**: See `DEPLOYMENT_GUIDE.md`
3. **Checklist**: See `DEPLOYMENT_CHECKLIST.md`

---

**Happy coding! 💻✨**

