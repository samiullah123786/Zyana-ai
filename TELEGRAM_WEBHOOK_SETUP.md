# 🔧 Telegram Webhook Setup Guide

## Issue: PowerShell Network Connectivity

If you're getting "Unable to connect to the remote server", try these methods:

---

## ✅ Method 1: Use Browser (EASIEST)

Simply open this URL in your web browser:

```
https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/setWebhook?url=https://zyana-backend.onrender.com/webhook/telegram
```

**Expected Response in Browser:**
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

---

## ✅ Method 2: Use Postman or Insomnia

### Using Postman:
1. Open Postman
2. Create new **GET** request
3. URL: `https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/setWebhook`
4. Add Query Parameter:
   - Key: `url`
   - Value: `https://zyana-backend.onrender.com/webhook/telegram`
5. Send

---

## ✅ Method 3: Use Git Bash or WSL

If you have Git Bash or WSL installed:

```bash
curl "https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/setWebhook?url=https://zyana-backend.onrender.com/webhook/telegram"
```

---

## ✅ Method 4: Run Provided Scripts

### PowerShell Script:
```powershell
.\SET_TELEGRAM_WEBHOOK.ps1
```

### Batch File:
Double-click: `SET_WEBHOOK_SIMPLE.bat`

---

## 🔍 Verify Webhook is Set

### Method A: Browser
Open:
```
https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/getWebhookInfo
```

### Method B: PowerShell
```powershell
Invoke-RestMethod "https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/getWebhookInfo"
```

**Expected Response:**
```json
{
  "ok": true,
  "result": {
    "url": "https://zyana-backend.onrender.com/webhook/telegram",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

---

## 🧪 Test Your Bot

1. Open Telegram app
2. Find your bot
3. Send: `/start`
4. Try: "I received Rs 50,000 from milk sales"

**Your bot should respond!** 🎉

---

## ⚠️ Troubleshooting Network Issues

If PowerShell commands fail with "Unable to connect":

### Check 1: Internet Connection
```powershell
Test-Connection google.com
```

### Check 2: DNS Resolution
```powershell
Resolve-DnsName api.telegram.org
```

### Check 3: Firewall
- Check if Windows Firewall is blocking PowerShell
- Check corporate proxy settings

### Check 4: Use VPN
- If on restricted network, try VPN
- Or use mobile hotspot temporarily

---

## 💡 Alternative: Set Webhook From Server

You can also set the webhook from your Render backend:

1. Add an admin endpoint to your backend
2. Call it once to set webhook
3. Then remove the endpoint

**Example code to add to backend:**
```python
@app.get("/admin/set-webhook")
async def set_webhook():
    import httpx
    bot_token = settings.telegram_bot_token
    webhook_url = f"{settings.webhook_url}/webhook/telegram"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            json={"url": webhook_url}
        )
        return response.json()
```

Then visit: `https://zyana-backend.onrender.com/admin/set-webhook`

---

## ✅ Summary

**Easiest Method:** Just open the URL in your browser! 🌐

**URL to open:**
```
https://api.telegram.org/bot7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU/setWebhook?url=https://zyana-backend.onrender.com/webhook/telegram
```

**That's it!** No scripts needed! 🎉

