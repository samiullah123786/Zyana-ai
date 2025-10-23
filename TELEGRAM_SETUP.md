# 🤖 Telegram Bot Setup Guide

## Option 1: Setup Ngrok (For Local Testing) ⏱️ 3 minutes

### Step 1: Download Ngrok
1. Go to: https://ngrok.com/download
2. Download the Windows version
3. Extract `ngrok.exe` to a folder (e.g., `C:\ngrok\`)

### Step 2: Sign Up & Get Auth Token
1. Create free account at: https://dashboard.ngrok.com/signup
2. Go to: https://dashboard.ngrok.com/get-started/your-authtoken
3. Copy your authtoken (looks like: `2abc123def456_7GHI890jklMNO123pqrSTU`)

### Step 3: Configure Ngrok
Run this command (replace with YOUR authtoken):
```powershell
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

Example:
```powershell
ngrok config add-authtoken 2abc123def456_7GHI890jklMNO123pqrSTU
```

### Step 4: Start Ngrok Tunnel
```powershell
ngrok http 8000
```

You'll see output like:
```
Forwarding  https://abcd-123-456.ngrok-free.app -> http://localhost:8000
```

**Copy the https URL!**

### Step 5: Set Telegram Webhook
Replace `YOUR_NGROK_URL` with the https URL from step 4:

```powershell
curl -X POST "https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/setWebhook" `
  -H "Content-Type: application/json" `
  -d "{`"url`": `"https://YOUR_NGROK_URL/webhook/telegram`"}"
```

Example:
```powershell
curl -X POST "https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/setWebhook" `
  -H "Content-Type: application/json" `
  -d "{`"url`": `"https://abcd-123-456.ngrok-free.app/webhook/telegram`"}"
```

### Step 6: Verify Webhook
```powershell
curl "https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/getWebhookInfo"
```

You should see your ngrok URL in the response.

---

## Option 2: Use Polling (No Ngrok Needed) ⏱️ 1 minute

**Simpler for local testing - no tunnel required!**

I'll create a polling script that checks for Telegram messages every few seconds.

### Step 1: Create Polling Script

File already created: `backend/run_telegram_polling.py`

### Step 2: Run Polling Mode
```powershell
cd backend
python run_telegram_polling.py
```

This will:
- ✅ Check for new messages every 2 seconds
- ✅ Process messages through Zyana
- ✅ Send responses back
- ✅ No webhook or ngrok needed!

**Note:** Keep this script running while testing locally.

---

## Option 3: Deploy to Production (Recommended) ⏱️ 10 minutes

For production use, deploy to a service with a public URL:

### Railway (Easiest)
1. Go to: https://railway.app
2. Connect your GitHub repo
3. Deploy backend
4. Copy the public URL (e.g., `https://zyana-backend.railway.app`)
5. Set webhook:
```powershell
curl -X POST "https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/setWebhook" `
  -d "{`"url`": `"https://zyana-backend.railway.app/webhook/telegram`"}"
```

### Render
1. Go to: https://render.com
2. Connect GitHub repo
3. Deploy as Web Service
4. Copy the public URL
5. Set webhook (same as Railway)

---

## 🧪 Testing Your Setup

### Test 1: Check Bot is Running
Open Telegram and send to your bot:
```
/start
```

You should get a welcome message.

### Test 2: Send a Transaction
```
I received Rs 50,000 from milk sales today
```

Expected response:
```
✅ Recorded income: PKR 50,000
Business: MilkBusiness
Category: sales
```

### Test 3: Check Backend Logs
Look at your backend terminal - you should see:
```
INFO: POST /webhook/telegram - 200 OK
```

---

## 🔧 Troubleshooting

### "Webhook failed"
- ✅ Use **Option 2 (Polling)** instead - much easier!
- Or check ngrok is running
- Verify webhook URL in Telegram

### "Bot not responding"
- Check backend is running on port 8000
- Look for errors in backend logs
- Try polling mode (Option 2)

### "Connection refused"
- Backend must be running first
- Check `http://localhost:8000/health`

---

## 📝 Quick Commands Reference

### Check Webhook Status
```powershell
curl "https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/getWebhookInfo"
```

### Remove Webhook (switch to polling)
```powershell
curl "https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/deleteWebhook"
```

### Test Bot Connection
```powershell
curl "https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/getMe"
```

---

## ✅ Recommended Approach

**For Local Development:**
👍 **Use Option 2 (Polling)** - Simplest, no configuration needed

**For Production:**
👍 **Deploy to Railway/Render** - Get public URL, set webhook

**Skip Ngrok** unless you specifically need to test webhooks locally.

---

## 🚀 Quick Start (Polling Mode)

1. Make sure backend is running
2. Open NEW terminal:
```powershell
cd D:\Apps\Zyana\backend
python run_telegram_polling.py
```
3. Send message to your Telegram bot
4. ✅ Done!

---

**Polling mode is recommended for local testing - it's simpler and works perfectly!** 🎉

