# 🧪 Test Backend Locally Before Deploying

## Quick Local Test (5 minutes)

This ensures everything works before deploying to Render.

---

## Step 1: Install Dependencies (2 minutes)

```powershell
cd D:\Apps\Zyana\backend
pip install -r requirements.txt
```

---

## Step 2: Start the Backend (1 second)

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Step 3: Test Health Endpoint (1 second)

Open new terminal:

```powershell
curl http://localhost:8000/health
```

**Expected:** `{"status":"healthy"}`

---

## Step 4: Check API Docs

Open browser: http://localhost:8000/docs

You should see Swagger UI with all endpoints!

---

## ✅ If It Works Locally:

Your code is good! Deploy to Render with confidence!

---

## ❌ If It Fails Locally:

Fix the error, then deploy. This saves deployment time!

