# Zyana Architecture

## System Overview

Zyana is a multi-agent AI assistant system designed to help manage finances, calendar events, video processing, and personal memory across multiple businesses.

## Architecture Diagram

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

## Components

### 1. User Interfaces

#### Telegram Bot
- Natural language message input
- Webhook-based updates
- Command support (/start, /status, /report)
- Conversational follow-ups for missing information

#### Next.js Dashboard
- Business overview and management
- Transaction tracking and visualization
- Calendar event management
- Semantic memory search
- Agent console for direct commands

#### Desktop Agent (Electron)
- File system monitoring for video files
- Automated job submission to backend
- Secure command whitelisting
- Local configuration management

### 2. Backend (FastAPI)

#### Main Core Agent (Router)
- Routes parsed messages to appropriate specialized agents
- Maintains session context (last 20 messages in Redis)
- Coordinates multi-agent workflows
- Handles fallback with Fal AI for unknown intents

#### Specialized Agents

**Finance Agent**
- Transaction creation and management
- Loan tracking and repayment
- P&L calculations and reporting
- Business balance management

**Calendar Agent**
- Google Calendar integration (OAuth2)
- Bi-directional sync (hourly cron)
- Event creation and management
- Conflict detection

**Memory Agent**
- Semantic search across all data
- Vector embedding generation
- Nightly summarization
- Context retrieval for conversations

**Video Agent**
- Job submission from desktop agent
- Metadata extraction
- FFmpeg script execution (whitelisted)
- Processing status tracking

**Habit Learner**
- Pattern detection (currency, business, contacts)
- Confidence scoring
- User confirmation workflow
- Preference application

### 3. Data Layer

#### Supabase (PostgreSQL)
- Businesses, users, transactions
- Loans, repayments, goals
- Calendar events
- Agent logs
- Habit profiles
- Memory summaries
- Row-level security (RLS)

#### Qdrant (Vector Database)
- Embeddings for transactions, events, notes
- Semantic search capabilities
- Payload: {row_id, table, snippet, date, business}
- COSINE distance metric

#### Redis
- Session memory (last 20 messages)
- Job queue (RQ)
- Rate limiting
- Caching

### 4. External Services

#### Fal AI
- GPT-5 for reasoning and generation
- Embeddings (text-embedding-ada-002)
- Two-stage parsing: classification → extraction
- Function calling support

#### Google Calendar API
- OAuth2 authentication
- Event CRUD operations
- Webhook notifications (optional)

## Data Flow

### 1. Message Processing Flow

```
User Message (Telegram/Web)
    ↓
Webhook Endpoint
    ↓
Message Parser (Fal AI)
    ├→ Stage 1: Intent Classification
    └→ Stage 2: Structured Extraction
    ↓
Validation (Pydantic)
    ↓
Main Core Agent (Router)
    ↓
Specialized Agent
    ├→ Database Operations
    ├→ External API Calls
    └→ Memory Embedding
    ↓
Response Generation
    ↓
Send to User (Telegram/Web)
```

### 2. Habit Learning Flow

```
User Interaction
    ↓
Habit Learner Observes
    ├→ Currency preference
    ├→ Business associations
    ├→ Frequent contacts
    └→ Default business
    ↓
Update Occurrence Count
    ↓
Confidence > Threshold?
    ├→ Yes: Suggest to User
    └→ No: Continue observing
    ↓
User Confirms?
    ├→ Yes: Apply as default
    └→ No: Reset pattern
```

### 3. Memory Embedding Flow

```
New Data (Transaction/Event)
    ↓
Generate Summary Text
    ↓
Fal AI Embedding
    ↓
Store in Qdrant
    ├→ Vector
    └→ Payload (metadata)
    ↓
Available for Semantic Search
```

## Security

### Authentication
- Supabase Auth for frontend
- JWT tokens for API access
- Row-level security (RLS) in database

### Desktop Agent Security
- Whitelisted commands only (ffmpeg, convert)
- No arbitrary shell execution
- User confirmation required
- Secure token storage (electron-store)

### API Security
- Rate limiting
- Input validation (Pydantic)
- CORS configuration
- Environment-based secrets

## Scalability

### Horizontal Scaling
- Stateless backend (session in Redis)
- Multiple worker instances (RQ)
- Load balancer ready

### Performance
- Database indexes on key columns
- Materialized views for aggregations
- Redis caching
- Async operations (FastAPI)

### Monitoring
- Health check endpoints
- Agent action logging
- Error tracking (Sentry)
- Metrics collection

## Deployment

### Development
- Docker Compose for local services
- Hot reload for backend/frontend
- Local Qdrant, Redis, Postgres

### Production
- Backend: Railway/Render/VPS (Docker)
- Frontend: Vercel/Netlify
- Database: Supabase (managed)
- Qdrant: Cloud or self-hosted
- Redis: Upstash or self-hosted

## Technology Stack

### Backend
- Python 3.11
- FastAPI
- Supabase Python Client
- Qdrant Client
- RQ (Redis Queue)
- Google API Client

### Frontend
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Recharts

### Desktop
- Electron
- TypeScript
- Chokidar (file watching)
- Axios

### Infrastructure
- Docker
- PostgreSQL 15
- Redis 7
- Qdrant
- GitHub Actions

## Future Enhancements

1. **Multi-user support** - Full user management and isolation
2. **Mobile apps** - React Native for iOS/Android
3. **Voice interface** - Integrate speech-to-text
4. **Advanced analytics** - ML-powered insights
5. **Third-party integrations** - Stripe, QuickBooks, etc.
6. **Real-time collaboration** - WebSocket support
7. **Backup and export** - Automated backups, data export

