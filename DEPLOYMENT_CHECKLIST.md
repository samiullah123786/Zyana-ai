# ✅ Zyana AI - Deployment Checklist

## Quick 30-Minute Deployment Guide

Follow these steps in order. Each takes 3-5 minutes.

---

## □ **Step 1: Database (5 min)**

1. Open: https://supabase.com/dashboard/project/yrwlvurrjzsosfkyaacq/sql
2. Open file: `backend/migrations/001_initial_schema.sql`
3. Copy all → Paste → Click RUN
4. ✅ Check: See 10 tables in Table Editor

---

## □ **Step 2: Redis (3 min)**

1. Go to: https://upstash.com
2. Sign up with GitHub
3. Create Database → Name: `zyana-redis`
4. Copy REST URL and TOKEN
5. Save these values

---

## □ **Step 3: Qdrant (3 min)**

1. Go to: https://cloud.qdrant.io
2. Sign up with GitHub  
3. Create Cluster → Free Tier → Name: `zyana-vectors`
4. Copy Cluster URL and create API Key
5. Save these values

---

## □ **Step 4: Backend - Render.com (10 min)**

1. Go to: https://render.com
2. Sign up with GitHub
3. New → Web Service → Connect your repo
4. Configure:
   - Name: `zyana-backend`
   - Runtime: Python 3
   - Build: `cd backend && pip install -r requirements.txt`
   - Start: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Plan: FREE

5. Add ALL environment variables from `.env`
   - **Important**: Update REDIS_URL and QDRANT_URL with values from Steps 2 & 3
   
6. Deploy → Wait 10 minutes
7. Copy your backend URL: `https://zyana-backend-xxx.onrender.com`

---

## □ **Step 5: Telegram Webhook (2 min)**

```powershell
curl -X POST "https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/setWebhook" `
  -H "Content-Type: application/json" `
  -d '{"url": "https://YOUR-BACKEND-URL.onrender.com/webhook/telegram"}'
```

Replace `YOUR-BACKEND-URL` with your Render URL!

---

## □ **Step 6: Frontend - Vercel (5 min)**

1. Go to: https://vercel.com
2. Sign up with GitHub
3. New Project → Import your repo
4. Configure:
   - Root Directory: `frontend`
   - Framework: Next.js
   - Plan: FREE

5. Add environment variables:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://yrwlvurrjzsosfkyaacq.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
   NEXT_PUBLIC_API_URL=https://YOUR-BACKEND-URL.onrender.com
   ```

6. Deploy → Wait 3 minutes
7. Copy your frontend URL: `https://zyana-dashboard.vercel.app`

---

## □ **Step 7: Google OAuth (2 min)**

1. Go to: https://console.cloud.google.com/apis/credentials
2. Edit your OAuth Client
3. Add redirect URI: `https://YOUR-BACKEND-URL.onrender.com/auth/google/callback`
4. Save

---

## ✅ **DONE! Test Your System**

### Test Backend:
```powershell
curl https://YOUR-BACKEND-URL.onrender.com/health
```

### Test Telegram:
Send to your bot: "I received Rs 50,000"

### Test Dashboard:
Open: https://YOUR-FRONTEND-URL.vercel.app

---

## 📝 **Save Your URLs**

Write these down:

- **Backend**: ______________________________
- **Frontend**: ______________________________
- **Telegram Bot**: @your_bot_name

---

## 🎉 **Congratulations!**

Your Zyana AI is now:
- ✅ Online 24/7
- ✅ Accessible from anywhere
- ✅ $0/month cost
- ✅ Auto-deploying on git push

---

## 🚀 **Optional: Keep Backend Always Awake**

Free solution using UptimeRobot:

1. Go to: https://uptimerobot.com
2. Sign up (free)
3. Add Monitor:
   - URL: `https://YOUR-BACKEND-URL.onrender.com/health`
   - Interval: 5 minutes
4. ✅ Backend never sleeps!

---

## 📱 **Access From Anywhere**

Your system works on:
- 💬 Telegram (any device)
- 🌐 Web Dashboard (any browser)
- 📱 Mobile (responsive design)
- 💻 Desktop (electron agent - optional)

---

## 🔄 **How to Update**

```powershell
git add .
git commit -m "Your changes"
git push origin dev
```

⚡ Auto-deploys in 2-3 minutes!

---

## ⚠️ **Important Notes**

1. **Render Free Tier**: Backend sleeps after 15 min of inactivity
   - Solution: Use UptimeRobot (free) or upgrade ($7/month)

2. **First Request**: May take 30 seconds to wake up
   - After that: Fast responses!

3. **Monthly Limits** (all FREE tiers):
   - Render: 750 hours (31 days = 744 hours) ✅
   - Upstash: 10K Redis commands/day ✅
   - Qdrant: 1GB vector storage ✅
   - Vercel: Unlimited deployments ✅

---

## 📞 **Need Help?**

1. Check `PRODUCTION_DEPLOYMENT.md` for detailed guide
2. Check Render logs for backend issues
3. Check Vercel logs for frontend issues
4. Review `docs/` for architecture details

---

**Total Time**: ~30 minutes
**Total Cost**: $0/month
**Result**: Fully functional AI assistant accessible worldwide! 🌍

**Start with Step 1 and work through the checklist!**
