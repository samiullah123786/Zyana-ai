# Deployment Guide

## Prerequisites

- Git
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Supabase account
- Fal AI API key
- Telegram Bot token
- Google Cloud Project (for Calendar)

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd zyana-ai
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `FAL_API_KEY` - Your Fal AI API key
- `TELEGRAM_BOT_TOKEN` - From @BotFather
- `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET` - From Google Cloud Console
- `SUPABASE_URL` & `SUPABASE_SERVICE_KEY` - From Supabase dashboard
- `JWT_SECRET` - Generate a secure random string

## Local Development

### 1. Start Infrastructure Services

```bash
docker-compose -f docker-compose.dev.yml up -d postgres redis qdrant
```

### 2. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Apply database migrations:
```bash
python scripts/apply_migrations.py
```

Start backend:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

Access at: http://localhost:3000

### 4. Setup Desktop Agent (Optional)

```bash
cd desktop-agent
npm install
npm run dev
```

## Production Deployment

### Option 1: Docker Deployment (Recommended)

#### 1. Build Images

```bash
# Build backend
cd backend
docker build -t zyana-backend:latest .

# Build frontend (if using Docker)
cd ../frontend
docker build -t zyana-frontend:latest .
```

#### 2. Deploy with Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: "3.8"
services:
  backend:
    image: zyana-backend:latest
    env_file: .env
    ports:
      - "8000:8000"
    restart: unless-stopped
  
  worker:
    image: zyana-backend:latest
    env_file: .env
    command: rq worker --url redis://redis:6379 zyana-queue
    restart: unless-stopped
  
  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data
    restart: unless-stopped
  
  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrantdata:/qdrant/storage
    restart: unless-stopped

volumes:
  redisdata:
  qdrantdata:
```

Deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Option 2: Platform-as-a-Service

#### Backend on Railway

1. Create new project on [Railway](https://railway.app)
2. Connect GitHub repository
3. Add PostgreSQL, Redis services
4. Set environment variables
5. Deploy from `main` branch

#### Frontend on Vercel

1. Import project on [Vercel](https://vercel.com)
2. Set root directory to `frontend/`
3. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_URL`
4. Deploy

### Option 3: VPS Deployment

#### On Ubuntu/Debian Server

1. **Install Dependencies**

```bash
sudo apt update
sudo apt install -y python3.11 python3-pip nginx certbot python3-certbot-nginx
```

2. **Setup Application**

```bash
git clone <repository-url> /opt/zyana
cd /opt/zyana
```

3. **Configure Systemd Services**

Create `/etc/systemd/system/zyana-backend.service`:

```ini
[Unit]
Description=Zyana Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/zyana/backend
Environment="PATH=/opt/zyana/backend/venv/bin"
ExecStart=/opt/zyana/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/zyana-worker.service`:

```ini
[Unit]
Description=Zyana RQ Worker
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/zyana/backend
Environment="PATH=/opt/zyana/backend/venv/bin"
ExecStart=/opt/zyana/backend/venv/bin/rq worker --url redis://localhost:6379 zyana-queue
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Start Services**

```bash
sudo systemctl daemon-reload
sudo systemctl enable zyana-backend zyana-worker
sudo systemctl start zyana-backend zyana-worker
```

5. **Configure Nginx**

Create `/etc/nginx/sites-available/zyana`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/zyana /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

6. **Setup SSL**

```bash
sudo certbot --nginx -d api.yourdomain.com
```

## Database Migrations

### Apply to Supabase

1. Go to your Supabase project: `https://app.supabase.com/project/<project-id>/sql`
2. Copy contents of `backend/migrations/001_initial_schema.sql`
3. Paste and run in SQL Editor
4. Verify tables were created

### Verify Migration

```bash
cd backend
python scripts/apply_migrations.py
```

## Telegram Bot Setup

1. Set webhook URL:

```bash
curl -X POST https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-api-domain.com/webhook/telegram"}'
```

2. Verify webhook:

```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

## Google Calendar Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project or select existing
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `https://your-api-domain.com/auth/google/callback`
6. Download credentials and update `.env`

## Monitoring

### Health Checks

```bash
# Backend health
curl https://your-api-domain.com/health

# Check specific services
curl https://your-api-domain.com/agent/status
```

### Logs

```bash
# Backend logs (systemd)
sudo journalctl -u zyana-backend -f

# Worker logs
sudo journalctl -u zyana-worker -f

# Docker logs
docker-compose logs -f backend worker
```

### Sentry Integration (Optional)

1. Create project on [Sentry](https://sentry.io)
2. Add DSN to `.env`:
   ```
   SENTRY_DSN=your_sentry_dsn
   ```
3. Install Sentry SDK:
   ```bash
   pip install sentry-sdk[fastapi]
   ```

## Backup

### Database Backup

```bash
# Supabase (automated backups included)
# Manual export via dashboard

# Self-hosted Postgres
pg_dump -h localhost -U postgres zyana_dev > backup.sql
```

### Qdrant Backup

```bash
# Copy data directory
docker cp zyana-qdrant:/qdrant/storage ./qdrant-backup
```

## Troubleshooting

### Backend won't start
- Check environment variables are set
- Verify database connection
- Check logs for errors

### Frontend can't connect to backend
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS settings in backend
- Verify backend is accessible

### Telegram webhook not working
- Check webhook URL is set correctly
- Verify backend is accessible from internet
- Check webhook info for errors

### Database connection issues
- Verify credentials
- Check network connectivity
- Ensure RLS policies don't block admin access

## Maintenance

### Update Application

```bash
git pull origin main
cd backend && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
sudo systemctl restart zyana-backend zyana-worker
```

### Rotate Secrets

1. Generate new secret
2. Update environment variables
3. Restart services
4. Update clients (Telegram webhook, etc.)

### Scale Workers

```bash
# Add more worker instances
for i in {2..4}; do
  sudo systemctl start zyana-worker@$i
done
```

## Security Checklist

- [ ] All secrets in environment variables
- [ ] SSL/TLS enabled (HTTPS)
- [ ] Firewall configured
- [ ] Database RLS enabled
- [ ] Regular backups scheduled
- [ ] Monitoring and alerts set up
- [ ] Rate limiting enabled
- [ ] Input validation in place
- [ ] CORS properly configured
- [ ] Logs reviewed regularly

