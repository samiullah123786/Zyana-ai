# 🤖 Zyana AI - Your Personal Multi-Agent Assistant

Zyana is an intelligent AI assistant that helps you manage finances across multiple businesses, organize calendar events, and search through your personal memory - all through natural conversation on Telegram or a beautiful web dashboard.

![Status](https://img.shields.io/badge/status-production-brightgreen)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

- 💰 **Multi-Business Finance Tracking** - Track income, expenses, and loans across different businesses
- 📅 **Smart Calendar Management** - Sync with Google Calendar, get reminders
- 🧠 **Personal Memory Search** - Vector-based search through your conversations and notes
- 🤖 **Multi-Agent System** - Specialized agents for different tasks
- 💬 **Telegram Integration** - Natural conversation interface
- 🎨 **Web Dashboard** - Beautiful Next.js frontend for visualization
- 🔐 **Secure Authentication** - Supabase auth with JWT tokens

---

## 🚀 Quick Start - Deploy in 30 Minutes

Deploy Zyana completely FREE to the cloud:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/zyana.git
cd zyana

# 2. Follow the deployment guide
# See QUICK_DEPLOY.md for 30-minute deployment
# Or DEPLOYMENT_GUIDE.md for detailed instructions
```

### ⚡ Deploy To:
- **Backend** → [Render.com](https://render.com) (Free tier)
- **Frontend** → [Vercel](https://vercel.com) (Free tier)
- **Database** → [Supabase](https://supabase.com) (Free tier)
- **Vector DB** → [Qdrant Cloud](https://cloud.qdrant.io) (Free tier)
- **Redis** → [Upstash](https://upstash.com) (Free tier)

**Total Cost: $0/month** 🎉

[📖 **Read Deployment Guide**](DEPLOYMENT_GUIDE.md) | [⚡ **Quick Deploy**](QUICK_DEPLOY.md) | [✅ **Checklist**](DEPLOYMENT_CHECKLIST.md)

---

## 🏗️ Architecture

```
┌─────────────────┐
│   User/Telegram │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Frontend       │      │   Backend        │
│  Next.js        │─────▶│   FastAPI        │
│  (Vercel)       │      │   (Render)       │
└─────────────────┘      └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
            ┌───────────┐  ┌──────────┐  ┌──────────┐
            │ Supabase  │  │  Qdrant  │  │  Upstash │
            │ PostgreSQL│  │  Vectors │  │   Redis  │
            └───────────┘  └──────────┘  └──────────┘
```

### Key Components:

- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python 3.11) with async support
- **Database**: Supabase (PostgreSQL) with RLS
- **Vector DB**: Qdrant for semantic search
- **Queue**: Redis (Upstash) for background jobs
- **Auth**: Supabase Auth with JWT
- **Agents**: Finance, Calendar, Memory, Habit Learner

---

## 💻 Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Backend Setup

   ```bash
   cd backend

# Create virtual environment
   python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
   pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your values

# Run migrations (in Supabase SQL Editor)
# Copy and run: migrations/001_initial_schema.sql

# Start server
   uvicorn main:app --reload
   ```

Backend runs on: `http://localhost:8000`

### Frontend Setup

   ```bash
   cd frontend

# Install dependencies
   npm install

# Copy environment variables
cp .env.example .env.local
# Edit .env.local with your values

# Start dev server
   npm run dev
   ```

Frontend runs on: `http://localhost:3000`

---

## 📱 Using Zyana

### Telegram Bot

1. Get your bot token from [@BotFather](https://t.me/botfather)
2. Set up webhook (see deployment guide)
3. Start chatting!

**Example commands:**
```
I received 50k from milk sales today
Lent Ahmad Rs 10,000 from Vidify
Meeting with team tomorrow at 3pm
How much did I lend to Ahmad?
```

### Web Dashboard

Visit your deployed frontend or `http://localhost:3000` for:
- 📊 Financial overview across all businesses
- 📈 Transaction history and analytics
- 📅 Calendar view
- 🧠 Memory search
- ⚙️ Settings and configuration

---

## 🔧 Configuration

### Environment Variables

See [`ENV_SETUP.md`](ENV_SETUP.md) for complete guide on all environment variables.

**Required:**
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anon key
- `FAL_API_KEY` - Fal.ai API key
- `JWT_SECRET` - Random secret for JWT tokens

**Optional:**
- `GOOGLE_CLIENT_ID` - For Google Calendar sync
- `QDRANT_URL` - Vector database URL
- `REDIS_URL` - Redis connection string

---

## 📖 Documentation

- [**Deployment Guide**](DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [**Quick Deploy**](QUICK_DEPLOY.md) - 30-minute deployment guide
- [**Deployment Checklist**](DEPLOYMENT_CHECKLIST.md) - Step-by-step checklist
- [**Environment Setup**](ENV_SETUP.md) - All environment variables explained
- [**Architecture**](docs/architecture.md) - System architecture details
- [**API Documentation**](docs/api.md) - Backend API reference

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Supabase** - PostgreSQL database & auth
- **Qdrant** - Vector database for semantic search
- **Redis** - Job queue and caching
- **Python-telegram-bot** - Telegram integration
- **Google Calendar API** - Calendar sync

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **Supabase JS** - Client library

### Infrastructure
- **Render.com** - Backend hosting
- **Vercel** - Frontend hosting
- **Supabase** - Database & auth
- **Qdrant Cloud** - Vector database
- **Upstash** - Redis hosting

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Next.js](https://nextjs.org/) - Frontend framework
- [Supabase](https://supabase.com/) - Backend as a Service
- [Render](https://render.com/) - Hosting platform
- [Vercel](https://vercel.com/) - Frontend hosting

---

## 📞 Support

- 📧 Email: support@zyana.ai
- 💬 Telegram: [@zyana_support](https://t.me/zyana_support)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/zyana/issues)

---

## 🚀 What's Next?

- [ ] Desktop agent with system automation
- [ ] Voice interface
- [ ] Mobile app
- [ ] More AI agents (health, travel, etc.)
- [ ] Team collaboration features
- [ ] Advanced analytics

---

<div align="center">

**Made with ❤️ by the Zyana Team**

[Website](https://zyana.ai) • [Documentation](./docs) • [Telegram](https://t.me/zyana_bot)

⭐ Star us on GitHub — it helps!

</div>
