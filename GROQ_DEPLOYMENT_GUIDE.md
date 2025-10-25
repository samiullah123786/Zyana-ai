# 🚀 Groq Whisper - Quick Deployment Guide

**Time to Deploy:** ~10 minutes  
**Prerequisites:** Render account, Supabase access, GROQ_API_KEY

---

## Step 1: Apply Database Migration (2 min)

### Option A: Supabase Dashboard
1. Go to: https://supabase.com/dashboard
2. Select your project
3. Click **SQL Editor**
4. Copy contents of `backend/migrations/009_add_voice_logs.sql`
5. Paste and click **Run**
6. Verify: `voice_logs` table appears in Table Editor

### Option B: psql Command Line
```bash
psql $POSTGRES_CONN < backend/migrations/009_add_voice_logs.sql
```

---

## Step 2: Set Environment Variables in Render (3 min)

1. Go to: https://dashboard.render.com
2. Select your **zyana-backend** service
3. Click **Environment** tab
4. Add these variables:

```
GROQ_API_KEY = your_groq_api_key_here
GROQ_TRANSCRIBE_MODEL = whisper-large-v3-turbo
MAX_CHUNK_SECONDS = 180
WHISPER_LOCAL_ENABLED = false
VOICE_STORAGE_PROVIDER = supabase
```

5. Click **Save Changes**

---

## Step 3: Deploy Code (2 min)

```bash
# Stage all changes
git add .

# Commit
git commit -m "feat: Add Groq Whisper voice transcription

- Replace local faster-whisper with Groq cloud API
- Add voice_logs table and admin endpoints
- 15+ unit tests, full documentation
- No ffmpeg dependency required

Migration: 009_add_voice_logs.sql
Requires: GROQ_API_KEY env var"

# Push to dev branch (Render auto-deploys)
git push origin dev
```

---

## Step 4: Verify Deployment (3 min)

### A. Check Render Deployment
- Watch Render dashboard: Deployment should succeed in ~2-3 minutes
- Check logs for: `✅ Groq Transcriber initialized`

### B. Check Health Endpoint
```bash
curl https://zyana-backend.onrender.com/health
```

Expected:
```json
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "qdrant": "ok",
    ...
  }
}
```

### C. Test Voice Transcription
1. Open Telegram and send a voice message to your bot
2. Expected response:
   ```
   ✅ I transcribed your voice note:

   "[your spoken text here]"

   Processing your request...
   ```
3. Bot should then process the command normally

### D. Check Voice Logs
```bash
curl https://zyana-backend.onrender.com/admin/voice_logs
```

Expected:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "transcription": "your voice message text",
      "language": "en",
      ...
    }
  ]
}
```

---

## ✅ Success Criteria

All of these should be TRUE:

- [x] Migration 009 applied successfully
- [x] GROQ_API_KEY set in Render
- [x] Render deployment succeeded
- [x] Health check returns 200 OK
- [x] Voice message gets transcribed
- [x] Bot processes transcribed text
- [x] Entry appears in `/admin/voice_logs`
- [x] No errors in Render logs

---

## 🐛 Quick Troubleshooting

### "GROQ_API_KEY is required"
→ Check Render Environment Variables tab, ensure key is set exactly as shown

### "relation 'voice_logs' does not exist"
→ Migration 009 not applied. Run SQL in Supabase Dashboard

### "Failed to transcribe voice message"
→ Check Render logs for detailed error. Verify GROQ_API_KEY is valid

### Voice logs endpoint returns empty array
→ Send a voice message first, then check again

---

## 🔄 Rollback (If Needed)

```bash
# Revert to previous commit
git revert HEAD
git push origin dev

# Render will auto-deploy previous version
```

---

## 📊 Monitoring

### Check Groq API Usage
- Go to: https://console.groq.com
- View usage dashboard
- Free tier: 30 req/min, 14,400 req/day

### Check Voice Logs in Production
```bash
# Get today's logs
curl "https://zyana-backend.onrender.com/admin/voice_logs?limit=10"

# Filter by user
curl "https://zyana-backend.onrender.com/admin/voice_logs?user_id=1"
```

---

## 🎉 You're Done!

Voice transcription is now powered by Groq's cloud API. Users can send voice messages and the bot will:

1. ✅ Transcribe with high accuracy
2. ✅ Process as regular text command  
3. ✅ Store in audit log
4. ✅ Return instant responses

**Enjoy your upgraded voice capabilities!** 🎙️

---

*Deployment time: ~10 minutes | Status: Production Ready*

