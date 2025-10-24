# ⚡ Quick Deploy - 30 Minutes to Production

Your Zyana AI can be fully deployed in 30 minutes, 100% FREE!

## 🎯 What You'll Deploy

- ✅ **Backend API** (FastAPI) → Render.com  
- ✅ **Frontend Dashboard** (Next.js) → Vercel  
- ✅ **Telegram Bot** (Webhooks)  
- ✅ **Database** → Supabase (PostgreSQL)  
- ✅ **Vector DB** → Qdrant Cloud  
- ✅ **Redis Queue** → Upstash  

**Total Cost: $0/month**

---

## 📋 Before You Start

Have these ready:

1. ✅ GitHub account
2. ✅ Telegram Bot Token ([Get from @BotFather](https://t.me/botfather))
3. ✅ Fal.ai API Key ([Sign up here](https://fal.ai))
4. ✅ 30 minutes of time

---

## 🚀 Deploy in 6 Steps

### Step 1: Database (5 min)
```
1. Go to: https://supabase.com
2. Create project: "zyana"
3. SQL Editor → Paste backend/migrations/001_initial_schema.sql
4. RUN → Save your credentials
```

### Step 2: Vector DB (3 min)
```
1. Go to: https://cloud.qdrant.io
2. Create cluster: "zyana-vectors" (Free tier)
3. Save Cluster URL & API Key
```

### Step 3: Redis (3 min)
```
1. Go to: https://upstash.com
2. Create database: "zyana-redis"
3. Save REST URL & Token
```

### Step 4: Backend (10 min)
```
1. Go to: https://render.com
2. New Web Service → Connect GitHub → Select zyana repo
3. Configure:
   - Root: backend
   - Build: pip install -r requirements.txt
   - Start: uvicorn main:app --host 0.0.0.0 --port $PORT
4. Add environment variables (see DEPLOYMENT_CHECKLIST.md)
5. Deploy → Wait 10 min
6. Save your backend URL
```

### Step 5: Frontend (5 min)
```
1. Go to: https://vercel.com
2. Import Project → Select zyana repo
3. Configure:
   - Root: frontend
   - Framework: Next.js
4. Add 3 environment variables:
   - NEXT_PUBLIC_SUPABASE_URL
   - NEXT_PUBLIC_SUPABASE_ANON_KEY
   - NEXT_PUBLIC_API_URL
5. Deploy → Wait 3 min
```

### Step 6: Telegram Webhook (2 min)
```powershell
# Run this in PowerShell (replace YOUR_BOT_TOKEN and YOUR_BACKEND_URL):
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" `
  -H "Content-Type: application/json" `
  -d '{"url": "https://YOUR_BACKEND_URL.onrender.com/webhook/telegram"}'
```

---

## ✅ Test Your Deployment

### Test Backend:
```powershell
curl https://your-backend.onrender.com/health
```
Should return: `{"status": "healthy"}`

### Test Telegram:
1. Open Telegram
2. Find your bot
3. Send: `/start`
4. Should get welcome message!

### Test Frontend:
Visit: `https://your-app.vercel.app`

---

## 🎉 Done!

Your AI is now:
- 🌍 Accessible from anywhere
- 💰 Costing $0/month
- ⚡ Auto-deploying on git push
- 🔒 Secure with HTTPS

---

## 📖 Detailed Guides

- **Step-by-step**: See `DEPLOYMENT_GUIDE.md`
- **Checklist**: See `DEPLOYMENT_CHECKLIST.md`
- **Environment vars**: See `ENV_SETUP.md`
- **Troubleshooting**: See `DEPLOYMENT_GUIDE.md#troubleshooting`

---

## 🆘 Having Issues?

1. Check Render logs for backend errors
2. Check Vercel deployment logs
3. Verify all environment variables are set
4. Read the troubleshooting section in DEPLOYMENT_GUIDE.md

---

**Ready? Start with Step 1!** 🚀

