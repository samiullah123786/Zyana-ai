# 🔧 Render Deployment - Correct Method

## ❌ The Problem

Render is looking for a Dockerfile because you're using the **manual deployment** method instead of the **Blueprint** method.

---

## ✅ Solution: Use Manual Configuration (Easier)

Since the Blueprint method is having issues, let's deploy manually with the correct settings:

---

## 🚀 **Step-by-Step: Manual Deployment on Render**

### **Step 1: Start Fresh**

1. Go to your Render dashboard: https://dashboard.render.com/
2. If you have a failed service, delete it
3. Click **New +** → **Web Service**

---

### **Step 2: Connect Your Repository**

1. Click **Connect a repository**
2. Find: `samiullah123786/Zyana-ai`
3. Click **Connect**

---

### **Step 3: Configure Service (IMPORTANT!)**

Fill in these EXACT values:

| Field | Value |
|-------|-------|
| **Name** | `zyana-backend` |
| **Region** | Choose closest to you |
| **Branch** | `dev` |
| **Root Directory** | `backend` ⚠️ IMPORTANT! |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | `Free` |

---

### **Step 4: Add Environment Variables**

Click **Advanced** → **Add Environment Variable**

Add these ONE BY ONE (copy from `ENV_VALUES_FOR_RENDER.md`):

**Critical ones first:**

```
FAL_API_KEY=e6f8df20-14bf-4ac4-bb36-d2f04ec664dd:935918035b5a881d42db9ecb1147893c
```

```
TELEGRAM_BOT_TOKEN=7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU
```

```
SUPABASE_URL=https://yrwlvurrjzsosfkyaacq.supabase.co
```

```
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlyd2x2dXJyanpzb3Nma3lhYWNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEwNTY2NDIsImV4cCI6MjA3NjYzMjY0Mn0.6MK8ARbgQS9Oga8UrnhmFY8otvO0PC_3FUJ7izOz008
```

```
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlyd2x2dXJyanpzb3Nma3lhYWNxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTA1NjY0MiwiZXhwIjoyMDc2NjMyNjQyfQ.GSotk1NrrrBXRuUxstnSbZTrAisdcIBTLGFaJAnRdp0
```

```
QDRANT_URL=https://f4fab578-ab34-48aa-b411-b54bf9fd02c1.europe-west3-0.gcp.cloud.qdrant.io
```

```
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.BIArqqrc50qJzCT6dXYA_LcZM1IpPgoe9ZCPEuWYT2g
```

```
REDIS_URL=https://prepared-swan-28344.upstash.io
```

```
UPSTASH_REDIS_REST_TOKEN=AW64AAIncDI2NTFkYjcyN2Q5NTU0MDFmYmUzYmU1M2EzMGRkMzU5OXAyMjgzNDQ
```

```
ENVIRONMENT=production
```

```
JWT_SECRET=zyana-secret-key-production-2024-change-this-to-random
```

**Optional (for Google Calendar):**

```
GOOGLE_CLIENT_ID=711714603933-p5ffenv2uumnmnapu98el3ahktdssbu0.apps.googleusercontent.com
```

```
GOOGLE_CLIENT_SECRET=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
```

```
GOOGLE_PROJECT_ID=zyana-475803
```

---

### **Step 5: Deploy!**

1. Click **Create Web Service**
2. Wait 5-10 minutes for deployment
3. Watch the logs!

---

## 🎯 **What to Watch in Logs**

You should see:
```
==> Cloning from https://github.com/samiullah123786/Zyana-ai
==> Checking out commit xxx in branch dev
==> Using Python version 3.11.0
==> Running 'pip install -r requirements.txt'
==> Installing dependencies...
==> Build successful!
==> Starting service...
==> Uvicorn running on http://0.0.0.0:10000
```

---

## ✅ **Success Indicators**

1. **Build logs show**: "Build successful"
2. **Deploy logs show**: "Uvicorn running"
3. **Service status**: Green/Active
4. **Your URL**: `https://zyana-backend-xxx.onrender.com`

---

## 🔍 **Testing Your Deployment**

Once it's live, test:

```powershell
curl https://YOUR-RENDER-URL.onrender.com/health
```

Should return:
```json
{"status":"healthy"}
```

---

## ⚠️ **Common Issues & Fixes**

### Issue: "No module named 'main'"
**Fix**: Make sure Root Directory is set to `backend`

### Issue: "Port already in use"
**Fix**: Use `$PORT` in start command (not hardcoded port)

### Issue: "Requirements not found"
**Fix**: Root Directory should be `backend` where requirements.txt is

### Issue: "Supabase connection failed"
**Fix**: Check all SUPABASE_* environment variables are set

---

## 📝 **Quick Checklist**

Before clicking "Create Web Service":

- [ ] Root Directory = `backend`
- [ ] Build Command = `pip install -r requirements.txt`
- [ ] Start Command = `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] All environment variables added (minimum 10)
- [ ] Branch = `dev`
- [ ] Plan = `Free`

---

## 🎉 **After Successful Deployment**

1. Copy your Render URL
2. Update `GOOGLE_REDIRECT_URI` in Render env vars
3. Set Telegram webhook (see PRODUCTION_DEPLOYMENT.md Phase 5)
4. Deploy frontend to Vercel (Phase 6)

---

**The KEY is setting Root Directory to `backend`!** 🔑
