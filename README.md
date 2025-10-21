# Zyana - Personal AI Assistant

Zyana is a message-first, multi-agent AI assistant designed to help manage finances, calendar events, video processing, communications, and personal memory. Built with cutting-edge AI technologies and modern development practices.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACES                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐     │
│  │ Telegram │  │  Next.js │  │  Electron Desktop    │     │
│  │   Bot    │  │ Dashboard│  │      Agent           │     │
│  └─────┬────┘  └────┬─────┘  └──────────┬───────────┘     │
└────────┼────────────┼────────────────────┼─────────────────┘
         │            │                    │
         └────────────┼────────────────────┘
                      ▼
         ┌────────────────────────────┐
         │    FastAPI Backend         │
         │  ┌──────────────────────┐  │
         │  │  Main Core Agent     │  │
         │  │    (Router)          │  │
         │  └──────────┬───────────┘  │
         │             │              │
         │  ┌──────────┴───────────┐  │
         │  │  Specialized Agents  │  │
         │  ├──────────────────────┤  │
         │  │ • Finance Agent      │  │
         │  │ • Calendar Agent     │  │
         │  │ • Memory Agent       │  │
         │  │ • Video Agent        │  │
         │  │ • Habit Learner      │  │
         │  └──────────────────────┘  │
         └────────────┬───────────────┘
                      │
         ┌────────────┴───────────────┐
         │                            │
         ▼                            ▼
┌─────────────────┐          ┌──────────────────┐
│   Fal AI API    │          │   Data Layer     │
│                 │          │                  │
│ • GPT-5 Chat    │          │ • Supabase/PG    │
│ • Embeddings    │          │ • Qdrant Vectors │
│ • Function Call │          │ • Redis Cache    │
└─────────────────┘          └──────────────────┘
```

## Features

### 🤖 Multi-Agent System
- **Finance Agent**: Track transactions, loans, repayments, and generate P&L reports across multiple businesses
- **Calendar Agent**: Bi-directional sync with Google Calendar, intelligent event creation
- **Memory Agent**: Semantic search across all your data using vector embeddings
- **Video Agent**: Automated video processing and metadata extraction
- **Habit Learner**: Learns your preferences and patterns for smarter defaults

### 💬 Natural Language Interface
- Message via Telegram in free-form text
- Zyana parses your intent and extracts structured data
- Conversational follow-ups for missing information
- Multi-language support (English, Urdu, Saraiki)

### 📊 Business Management
- Multi-business support (Vidify, MilkBusiness, Yazman Express, etc.)
- Transaction tracking with categories and tags
- Loan management with repayment tracking
- Goals and target tracking
- Automated weekly/monthly reports

### 🧠 Intelligent Memory
- Vector-based semantic search using Qdrant
- Nightly summarization of activities
- Long-term habit and preference learning
- Context-aware responses using past interactions

### 🔐 Security & Privacy
- Row-level security (RLS) in Supabase
- Whitelisted command execution for Desktop Agent
- JWT-based authentication
- Secure credential management

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **Fal AI** - GPT-5 for reasoning and embeddings
- **Supabase** - PostgreSQL database with real-time capabilities
- **Qdrant** - Vector database for semantic search
- **Redis** - Session cache and job queue
- **RQ** - Background job processing

### Frontend
- **Next.js 14** - React framework with TypeScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Beautiful UI components
- **Supabase Auth** - Authentication and authorization

### Desktop Agent
- **Electron** - Cross-platform desktop application
- **TypeScript** - Type-safe development
- **FFmpeg** - Video processing

### DevOps
- **Docker Compose** - Local development environment
- **GitHub Actions** - CI/CD pipeline
- **Sentry** - Error tracking and monitoring

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd zyana-ai
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start infrastructure services**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. **Setup backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -m alembic upgrade head
   uvicorn main:app --reload
   ```

5. **Setup frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

6. **Setup desktop agent** (optional)
   ```bash
   cd desktop-agent
   npm install
   npm run dev
   ```

### Configuration

#### Telegram Bot
1. Create a bot via [@BotFather](https://t.me/botfather)
2. Add token to `.env` as `TELEGRAM_BOT_TOKEN`
3. Set webhook: `POST https://your-backend-url/webhook/message`

#### Google Calendar
1. Create OAuth credentials in Google Cloud Console
2. Add client ID and secret to `.env`
3. Authorize via `/auth/google` endpoint

#### Fal AI
1. Get API key from [fal.ai](https://fal.ai)
2. Add to `.env` as `FAL_API_KEY`

#### Supabase
1. Create project at [supabase.com](https://supabase.com)
2. Add URL and keys to `.env`
3. Run migrations from `backend/migrations/`

## Project Structure

```
zyana-ai/
├── backend/                 # FastAPI backend
│   ├── agents/             # Specialized agent implementations
│   ├── clients/            # External API clients (Fal, Google, etc.)
│   ├── migrations/         # Database migrations
│   ├── models/             # Pydantic schemas
│   ├── prompts/            # AI prompts and templates
│   ├── routers/            # API endpoints
│   ├── services/           # Business logic
│   ├── workers/            # Background jobs
│   └── main.py             # Application entry point
├── frontend/               # Next.js dashboard
│   ├── app/                # App router pages
│   ├── components/         # React components
│   ├── lib/                # Utilities and API client
│   └── public/             # Static assets
├── desktop-agent/          # Electron desktop app
│   ├── src/
│   │   ├── main/          # Main process
│   │   └── renderer/      # Renderer process (UI)
│   └── allowed_commands.json
├── infra/                  # Infrastructure configs
│   └── docker-compose.dev.yml
├── docs/                   # Documentation
│   ├── architecture.md
│   ├── api.md
│   ├── deployment.md
│   └── onboarding.md
├── scripts/                # Utility scripts
└── config/                 # Configuration files
```

## Usage Examples

### Finance Tracking
```
You: "I lent Ahmad Rs 10,000 from Vidify yesterday"
Zyana: "✅ Recorded Rs 10,000 loan to Ahmad for Vidify on 2025-10-20. Anything else?"
```

### Calendar Events
```
You: "Schedule meeting with team tomorrow at 3pm"
Zyana: "✅ Created 'Meeting with team' on 2025-10-22 at 3:00 PM. Google Calendar updated."
```

### Memory Search
```
You: "When did I last pay Ahmad?"
Zyana: "You paid Ahmad Rs 5,000 from Vidify on 2025-10-15 (repayment). Previous loan was Rs 10,000 on 2025-10-10."
```

## Development

### Running Tests
```bash
cd backend
pytest tests/ --cov=. --cov-report=html
```

### Code Quality
```bash
# Format code
black backend/ --line-length 100

# Lint
flake8 backend/ --max-line-length 100

# Type check
mypy backend/
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment

See [docs/deployment.md](docs/deployment.md) for detailed deployment instructions.

### Quick Deploy
- **Backend**: Railway, Render, or VPS with Docker
- **Frontend**: Vercel or Netlify
- **Database**: Supabase (managed) or self-hosted PostgreSQL

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| FAL_API_KEY | Fal AI API key | Yes |
| TELEGRAM_BOT_TOKEN | Telegram bot token | Yes |
| GOOGLE_CLIENT_ID | Google OAuth client ID | Yes |
| GOOGLE_CLIENT_SECRET | Google OAuth client secret | Yes |
| SUPABASE_URL | Supabase project URL | Yes |
| SUPABASE_SERVICE_KEY | Supabase service role key | Yes |
| QDRANT_URL | Qdrant instance URL | Yes |
| REDIS_URL | Redis connection URL | Yes |
| JWT_SECRET | Secret for JWT signing | Yes |

## Contributing

This is a personal project, but suggestions and feedback are welcome!

## License

Private - All Rights Reserved

## Support

For questions or issues, please check the [documentation](docs/) or create an issue.

---

Built with ❤️ by Sami

