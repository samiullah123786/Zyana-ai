# 🚀 Zyana Deployment Guide

This guide will walk you through deploying Zyana completely FREE on the cloud, accessible from anywhere!

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Step 1: Setup Supabase (Database)](#step-1-setup-supabase-database)
4. [Step 2: Setup Qdrant Cloud (Vector Database)](#step-2-setup-qdrant-cloud-vector-database)
5. [Step 3: Setup Upstash Redis (Queue)](#step-3-setup-upstash-redis-queue)
6. [Step 4: Deploy Backend on Render](#step-4-deploy-backend-on-render)
7. [Step 5: Deploy Frontend on Vercel](#step-5-deploy-frontend-on-vercel)
8. [Step 6: Setup Telegram Bot Webhook](#step-6-setup-telegram-bot-webhook)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, make sure you have:

- ✅ GitHub account
- ✅ Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- ✅ Google Cloud Project (for Calendar API - optional)
- ✅ Fal.ai API Key (for image generation)

---

## Architecture Overview

```
┌─────────────────┐
│   User/Telegram │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Frontend       │      │   Backend        │
│  (Vercel)       │─────▶│   (Render)       │
│  Next.js        │      │   FastAPI        │
└─────────────────┘      └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
            ┌───────────┐  ┌──────────┐  ┌──────────┐
            │ Supabase  │  │  Qdrant  │  │  Upstash │
            │ (Database)│  │ (Vector) │  │  (Redis) │
            └───────────┘  └──────────┘  └──────────┘
```

**Cost: $0/month** ✨

---

## Step 1: Setup Supabase (Database)

### 1.1 Create Account & Project

1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project" and sign in with GitHub
3. Click "New Project"
4. Fill in:
   - **Name**: `zyana`
   - **Database Password**: (generate a strong password - save it!)
   - **Region**: Choose closest to you
   - **Pricing Plan**: Free
5. Click "Create new project" (takes ~2 minutes)

### 1.2 Run Database Migrations

1. In your Supabase dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy the contents of `backend/migrations/001_initial_schema.sql`
4. Paste and click "Run"
5. You should see "Success. No rows returned"

### 1.3 Get Your API Keys

1. Go to **Settings** → **API**
2. Copy these values (you'll need them later):
   - `URL`: Your Supabase URL
   - `anon public`: Your anon key
   - `service_role`: Your service key (keep this secret!)

---

## Step 2: Setup Qdrant Cloud (Vector Database)

### 2.1 Create Free Cluster

1. Go to [cloud.qdrant.io](https://cloud.qdrant.io)
2. Sign up with GitHub
3. Click "Create Cluster"
4. Fill in:
   - **Cluster name**: `zyana`
   - **Cloud Provider**: Any (AWS/GCP/Azure)
   - **Region**: Choose closest to you
   - **Plan**: Free (1GB)
5. Click "Create"

### 2.2 Get API Key

1. Once cluster is created, click on it
2. Go to **API Keys** tab
3. Click "Create API Key"
4. Copy and save:
   - **Cluster URL**: `https://xxx.cloud.qdrant.io`
   - **API Key**: Your generated key

---

## Step 3: Setup Upstash Redis (Queue)

### 3.1 Create Free Redis Database

1. Go to [upstash.com](https://upstash.com)
2. Sign up with GitHub
3. Click "Create Database"
4. Fill in:
   - **Name**: `zyana-queue`
   - **Type**: Regional
   - **Region**: Choose closest to you
5. Click "Create"

### 3.2 Get Connection URL

1. In your database dashboard, scroll to **REST API** section
2. Copy the **UPSTASH_REDIS_REST_URL**
3. Format it as: `redis://default:password@host:port`
   - Or just use the connection string provided

---

## Step 4: Deploy Backend on Render

### 4.1 Push Code to GitHub

If you haven't already:

```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 4.2 Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New +" → "Web Service"

### 4.3 Connect Repository

1. Click "Connect GitHub account"
2. Select your Zyana repository
3. Click "Connect"

### 4.4 Configure Service

Fill in the following:

- **Name**: `zyana-backend`
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: `backend`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Plan**: Free

### 4.5 Add Environment Variables

Click "Advanced" → "Add Environment Variable" and add each of these:

| Key | Value | Notes |
|-----|-------|-------|
| `ENVIRONMENT` | `production` | |
| `FAL_API_KEY` | `your_fal_api_key` | From fal.ai |
| `TELEGRAM_BOT_TOKEN` | `your_bot_token` | From @BotFather |
| `GOOGLE_CLIENT_ID` | `your_google_client_id` | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | `your_google_client_secret` | From Google Cloud Console |
| `GOOGLE_PROJECT_ID` | `your_google_project_id` | From Google Cloud Console |
| `GOOGLE_REDIRECT_URI` | `https://zyana-backend.onrender.com/auth/google/callback` | Update with your Render URL |
| `SUPABASE_URL` | `your_supabase_url` | From Step 1.3 |
| `SUPABASE_ANON_KEY` | `your_supabase_anon_key` | From Step 1.3 |
| `SUPABASE_SERVICE_KEY` | `your_supabase_service_key` | From Step 1.3 |
| `QDRANT_URL` | `your_qdrant_url` | From Step 2.2 |
| `QDRANT_API_KEY` | `your_qdrant_api_key` | From Step 2.2 |
| `REDIS_URL` | `your_redis_url` | From Step 3.2 |
| `JWT_SECRET` | `generate_random_32_char_string` | Use a password generator |
| `WEBHOOK_URL` | `https://zyana-backend.onrender.com` | Your Render URL |
| `BACKEND_HOST` | `0.0.0.0` | |
| `BACKEND_PORT` | `$PORT` | |

### 4.6 Deploy

1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes first time)
3. Once live, your backend will be at: `https://zyana-backend.onrender.com`
4. Test it by visiting: `https://zyana-backend.onrender.com/health`

**⚠️ Important**: On the free plan, your backend will sleep after 15 minutes of inactivity. It takes ~30 seconds to wake up. For always-on service, upgrade to $7/month plan.

---

## Step 5: Deploy Frontend on Vercel

### 5.1 Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Click "Add New..." → "Project"

### 5.2 Import Repository

1. Find your Zyana repository
2. Click "Import"
3. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

### 5.3 Add Environment Variables

Click "Environment Variables" and add:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | `your_supabase_url` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `your_supabase_anon_key` |
| `NEXT_PUBLIC_API_URL` | `https://zyana-backend.onrender.com` |

### 5.4 Deploy

1. Click "Deploy"
2. Wait for deployment (2-3 minutes)
3. Your frontend will be live at: `https://zyana.vercel.app` (or your custom domain)

### 5.5 Update CORS in Backend

Go back to your Render dashboard:

1. Go to your `zyana-backend` service
2. Go to "Environment"
3. Update the `WEBHOOK_URL` if needed
4. Your backend already allows your Vercel domain in CORS!

---

## Step 6: Setup Telegram Bot Webhook

### 6.1 Automatic Setup (Recommended)

The webhook is automatically set when your backend starts! Just verify it:

1. Open Telegram
2. Send `/start` to your bot
3. You should get a welcome message
4. If it works, you're done! 🎉

### 6.2 Manual Setup (If Needed)

If the automatic setup didn't work:

1. Visit this URL in your browser (replace with your details):

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://zyana-backend.onrender.com/webhook/telegram
```

2. You should see:
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

### 6.3 Verify Webhook

Check webhook status:

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

You should see your webhook URL and no errors.

---

## 🎉 You're Live!

Your Zyana AI is now fully deployed and accessible from anywhere!

### Access Points:

- **Web App**: `https://zyana.vercel.app`
- **Backend API**: `https://zyana-backend.onrender.com`
- **Telegram Bot**: Open Telegram and message your bot
- **API Docs**: `https://zyana-backend.onrender.com/docs` (only in development)

---

## Troubleshooting

### Backend Issues

#### "Application failed to respond"

- Check if all environment variables are set
- Check deployment logs in Render dashboard
- Verify your Python dependencies in `requirements.txt`

#### "Database connection failed"

- Verify Supabase credentials
- Check if your database migrations ran successfully
- Ensure Supabase project is not paused

### Frontend Issues

#### "Error connecting to API"

- Verify `NEXT_PUBLIC_API_URL` is correct
- Check if backend is running: visit `/health` endpoint
- Check browser console for CORS errors

#### "Authentication not working"

- Verify Supabase credentials match between frontend and backend
- Check if Supabase project is active
- Clear browser cache and try again

### Telegram Bot Issues

#### "Bot not responding"

- Check webhook status using the URL in Step 6.3
- Verify `TELEGRAM_BOT_TOKEN` in Render environment variables
- Check backend logs for webhook errors
- Try manually setting webhook again

#### "Webhook certificate verify failed"

- Your Render URL should use HTTPS automatically
- Verify webhook URL doesn't have typos
- Try deleting and re-creating webhook

### Performance Issues

#### "Backend is slow to respond"

- Free tier sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- Solution: Upgrade to paid plan ($7/month) for always-on service
- Or: Set up a cron job to ping your backend every 10 minutes

---

## Monitoring & Maintenance

### Check Service Health

Visit these endpoints regularly:

- `https://zyana-backend.onrender.com/health` - Backend health
- `https://zyana.vercel.app` - Frontend status

### View Logs

- **Render**: Dashboard → Your Service → Logs
- **Vercel**: Dashboard → Your Project → Deployments → View Function Logs
- **Supabase**: Dashboard → Logs

### Update Your Deployment

When you push changes to GitHub:

- **Render**: Auto-deploys from `main` branch
- **Vercel**: Auto-deploys from `main` branch

To disable auto-deploy, go to service settings.

---

## Upgrading to Paid Plans (Optional)

### When to Upgrade:

- Backend needs to be always-on (no sleep)
- More than 100k monthly requests
- Need faster response times
- Professional custom domain

### Recommended Plans:

- **Render**: Starter ($7/month) - Always-on, 512MB RAM
- **Vercel**: Pro ($20/month) - Enhanced analytics, priority support
- **Supabase**: Pro ($25/month) - More database storage, daily backups
- **Upstash Redis**: Pay as you go - Only if you exceed free tier

**Total for paid tier**: ~$32/month (only if you need it)

---

## Security Best Practices

1. ✅ Never commit `.env` files to GitHub
2. ✅ Use strong, unique JWT_SECRET
3. ✅ Rotate API keys periodically
4. ✅ Enable Supabase RLS (Row Level Security)
5. ✅ Use environment variables for all secrets
6. ✅ Enable 2FA on all service accounts
7. ✅ Monitor logs for suspicious activity

---

## Support & Resources

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)
- **Qdrant Docs**: [qdrant.tech/documentation](https://qdrant.tech/documentation)
- **Telegram Bot API**: [core.telegram.org/bots](https://core.telegram.org/bots)

---

## 🎊 Congratulations!

You've successfully deployed Zyana to the cloud! Your AI assistant is now:

- ✅ Accessible from anywhere
- ✅ Running 24/7 (with wake-up delay on free tier)
- ✅ Scalable and production-ready
- ✅ 100% FREE (with free tier limitations)

Enjoy your deployed Zyana AI! 🚀✨

