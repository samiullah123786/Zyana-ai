# 🔐 Environment Variables for Render.com Deployment

## Copy-Paste These EXACT Values into Render

When deploying to Render.com, add these environment variables one by one:

---

## ✅ **Core API Keys**

```
FAL_API_KEY=e6f8df20-14bf-4ac4-bb36-d2f04ec664dd:935918035b5a881d42db9ecb1147893c
```

```
TELEGRAM_BOT_TOKEN=7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU
```

---

## ✅ **Google OAuth (from Phase 3)**

```
GOOGLE_CLIENT_ID=711714603933-p5ffenv2uumnmnapu98el3ahktdssbu0.apps.googleusercontent.com
```

```
GOOGLE_CLIENT_SECRET=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
```

```
GOOGLE_PROJECT_ID=zyana-475803
```

```
GOOGLE_REDIRECT_URI=https://your-render-app.onrender.com/auth/google/callback
```
**Note**: Replace `your-render-app` with your actual Render URL after deployment!

---

## ✅ **Supabase (Database)**

```
SUPABASE_URL=https://yrwlvurrjzsosfkyaacq.supabase.co
```

```
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlyd2x2dXJyanpzb3Nma3lhYWNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEwNTY2NDIsImV4cCI6MjA3NjYzMjY0Mn0.6MK8ARbgQS9Oga8UrnhmFY8otvO0PC_3FUJ7izOz008
```

```
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlyd2x2dXJyanpzb3Nma3lhYWNxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTA1NjY0MiwiZXhwIjoyMDc2NjMyNjQyfQ.GSotk1NrrrBXRuUxstnSbZTrAisdcIBTLGFaJAnRdp0
```

---

## ✅ **Qdrant (Vector Database) - YOUR VALUES**

```
QDRANT_URL=https://f4fab578-ab34-48aa-b411-b54bf9fd02c1.europe-west3-0.gcp.cloud.qdrant.io
```

```
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.BIArqqrc50qJzCT6dXYA_LcZM1IpPgoe9ZCPEuWYT2g
```

---

## ✅ **Redis (Upstash) - YOUR VALUES**

For REDIS_URL, use the REST URL:

```
REDIS_URL=https://prepared-swan-28344.upstash.io
```

**ALSO ADD** (Your backend needs this token):

```
UPSTASH_REDIS_REST_TOKEN=AW64AAIncDI2NTFkYjcyN2Q5NTU0MDFmYmUzYmU1M2EzMGRkMzU5OXAyMjgzNDQ
```

---

## ✅ **Security & Environment**

```
JWT_SECRET=change-this-to-random-string-minimum-32-characters-long
```
**Note**: Change this to a secure random string! Generate one with: `openssl rand -hex 32`

```
ENVIRONMENT=production
```

```
BACKEND_HOST=0.0.0.0
```

```
BACKEND_PORT=10000
```

---

## 📋 **Quick Copy - All Variables**

If Render asks for a bulk input, copy this entire block:

```env
FAL_API_KEY=e6f8df20-14bf-4ac4-bb36-d2f04ec664dd:935918035b5a881d42db9ecb1147893c
TELEGRAM_BOT_TOKEN=7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU
GOOGLE_CLIENT_ID=711714603933-p5ffenv2uumnmnapu98el3ahktdssbu0.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_PROJECT_ID=zyana-475803
GOOGLE_REDIRECT_URI=https://your-render-app.onrender.com/auth/google/callback
SUPABASE_URL=https://yrwlvurrjzsosfkyaacq.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlyd2x2dXJyanpzb3Nma3lhYWNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEwNTY2NDIsImV4cCI6MjA3NjYzMjY0Mn0.6MK8ARbgQS9Oga8UrnhmFY8otvO0PC_3FUJ7izOz008
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlyd2x2dXJyanpzb3Nma3lhYWNxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTA1NjY0MiwiZXhwIjoyMDc2NjMyNjQyfQ.GSotk1NrrrBXRuUxstnSbZTrAisdcIBTLGFaJAnRdp0
QDRANT_URL=https://f4fab578-ab34-48aa-b411-b54bf9fd02c1.europe-west3-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.BIArqqrc50qJzCT6dXYA_LcZM1IpPgoe9ZCPEuWYT2g
REDIS_URL=https://prepared-swan-28344.upstash.io
UPSTASH_REDIS_REST_TOKEN=AW64AAIncDI2NTFkYjcyN2Q5NTU0MDFmYmUzYmU1M2EzMGRkMzU5OXAyMjgzNDQ
JWT_SECRET=change-this-to-random-string-minimum-32-characters-long
ENVIRONMENT=production
BACKEND_HOST=0.0.0.0
BACKEND_PORT=10000
```

---

## ⚠️ **Important Notes**

1. **REDIS_URL**: Use the HTTPS URL from Upstash (not a redis:// URL)
2. **UPSTASH_REDIS_REST_TOKEN**: Add this as a separate variable!
3. **JWT_SECRET**: Generate a secure one before deploying
4. **GOOGLE_REDIRECT_URI**: Update after you get your Render URL

---

## 🎯 **How to Add in Render**

### Method 1: One by One (Recommended)
1. In Render deployment form
2. Click "Advanced" → "Add Environment Variable"
3. Copy variable name (e.g., `FAL_API_KEY`)
4. Paste value from above
5. Repeat for each variable

### Method 2: Bulk Add
1. Some Render forms have "Add from .env"
2. Copy the entire block from "Quick Copy" section
3. Paste it in
4. Verify all variables loaded

---

## ✅ **Checklist Before Deploying**

- [ ] All 17 environment variables added
- [ ] REDIS_URL is the HTTPS URL (not redis://)
- [ ] UPSTASH_REDIS_REST_TOKEN is added separately
- [ ] QDRANT_URL includes full cluster URL
- [ ] QDRANT_API_KEY is the JWT token
- [ ] JWT_SECRET is changed from default
- [ ] GOOGLE_REDIRECT_URI will be updated after deployment

---

**You're Ready to Deploy!** 🚀

