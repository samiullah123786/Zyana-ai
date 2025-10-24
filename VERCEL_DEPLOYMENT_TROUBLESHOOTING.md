# 🔧 Vercel Deployment Troubleshooting

## Issue: Project Created But Doesn't Deploy

---

## ✅ Method 1: Start Fresh (Recommended)

The easiest way is to **delete and recreate** with correct settings:

### Step 1: Delete Current Project
1. Go to your Vercel dashboard
2. Find the project
3. Go to **Settings** → **General**
4. Scroll to bottom
5. Click **"Delete Project"**
6. Confirm deletion

### Step 2: Create New Project Correctly

1. Go to: https://vercel.com/new

2. **Import Repository:**
   - Click **"Add New"** → **"Project"**
   - Find: `samiullah123786/Zyana-ai`
   - Click **"Import"**

3. **Configure Build Settings:**

   **IMPORTANT:** Set these EXACTLY:

   | Setting | Value | Notes |
   |---------|-------|-------|
   | **Framework Preset** | Next.js | Auto-detected |
   | **Root Directory** | `frontend` | ⚠️ Type: `frontend` (no slash!) |
   | **Build Command** | `npm run build` | Default |
   | **Output Directory** | `.next` | Default |
   | **Install Command** | `npm install` | Default |

4. **Add Environment Variables:**

   Click **"Environment Variables"** section

   **Variable 1:**
   - Click **"Add New"**
   - Name: `NEXT_PUBLIC_SUPABASE_URL`
   - Value: `https://yrwlvurrjzsosfkyaacq.supabase.co`
   - Environment: All (Production, Preview, Development)
   - **Important:** Make sure it's Plain Text, NOT a secret reference
   - Click **"Add"**

   **Variable 2:**
   - Click **"Add New"** again
   - Name: `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - Value: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlyd2x2dXJyanpzb3Nma3lhYWNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEwNTY2NDIsImV4cCI6MjA3NjYzMjY0Mn0.6MK8ARbgQS9Oga8UrnhmFY8otvO0PC_3FUJ7izOz008`
   - Environment: All
   - Click **"Add"**

   **Variable 3:**
   - Click **"Add New"** again
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://zyana-backend.onrender.com`
   - Environment: All
   - Click **"Add"**

5. **Deploy:**
   - Click **"Deploy"** button
   - Wait 3-5 minutes
   - Should work! ✅

---

## ✅ Method 2: Fix Existing Project

If you don't want to delete, try fixing the current one:

### Fix 1: Correct Root Directory

1. Go to project in Vercel
2. Click **"Settings"**
3. Go to **"General"** tab
4. Find **"Root Directory"** section
5. Click **"Edit"**
6. Enter: `frontend` (no leading `/`, no trailing `/`)
7. Click **"Save"**
8. Go to **"Deployments"** tab
9. Click **"Redeploy"**

### Fix 2: Fix Environment Variables

1. Go to **"Settings"** → **"Environment Variables"**
2. **Delete ALL existing variables** that have errors
3. Add them fresh, one by one:

   For each variable:
   - Click **"Add New"**
   - Fill Name and Value
   - **DON'T check "Sensitive"**
   - **DON'T use secrets**
   - Just plain text values
   - Select all environments
   - Click **"Add"**

### Fix 3: Check Build Settings

1. Go to **"Settings"** → **"Build & Development Settings"**
2. Verify:
   - **Framework Preset**: Next.js
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`
3. If anything is wrong, click **"Override"** and set correctly
4. Click **"Save"**

### Fix 4: Manual Redeploy

1. Go to **"Deployments"** tab
2. Click on the latest deployment
3. Click the **"..."** (three dots) menu
4. Select **"Redeploy"**
5. Check **"Use existing Build Cache"**: OFF
6. Click **"Redeploy"**

---

## 🔍 Check Deployment Logs

If it still fails:

1. Go to **"Deployments"** tab
2. Click on the failed deployment
3. Check the logs for errors
4. Look for:
   - ❌ "Cannot find package.json" → Root directory is wrong
   - ❌ "References Secret" → Environment variables wrong
   - ❌ "Build failed" → Check error message

---

## 🎯 Common Mistakes

### Mistake 1: Wrong Root Directory Format
❌ `/frontend` (has leading slash)
❌ `frontend/` (has trailing slash)
❌ `./frontend` (has dot slash)
✅ `frontend` (correct!)

### Mistake 2: Environment Variables as Secrets
When adding a variable, you should see:
```
[Name field]
[Value field] ← Paste value here!
```

NOT:
```
[Name field]
[Reference Secret ▼] ← Don't use this!
```

### Mistake 3: Wrong Branch
- Make sure Vercel is deploying from: `dev` branch
- Check in Settings → Git → Production Branch

---

## ✅ Success Indicators

You'll know it worked when:

1. **During Build:**
   - ✅ "Cloning repository..."
   - ✅ "Installing dependencies..."
   - ✅ "Building..."
   - ✅ "Build completed"

2. **After Deploy:**
   - ✅ Green checkmark on deployment
   - ✅ Live URL works
   - ✅ No errors in logs

---

## 🆘 If Still Failing

### Try This: Deploy From CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Go to frontend directory
cd D:\Apps\Zyana\frontend

# Deploy
vercel

# Follow prompts:
# - Link to existing project
# - Confirm settings
# - Deploy!
```

---

## 📝 Checklist Before Deploying

- [ ] Root Directory = `frontend` (no slashes)
- [ ] Framework = Next.js (detected)
- [ ] Build Command = `npm run build`
- [ ] Output Directory = `.next`
- [ ] 3 environment variables added (as plain text)
- [ ] No "References Secret" errors
- [ ] Branch = `dev`
- [ ] Repository connected correctly

---

## 💡 Pro Tip

The simplest way:

1. **Delete the project**
2. **Start fresh**
3. **Follow Method 1 exactly**
4. **Takes 5 minutes**
5. **Works first time!** ✨

---

**Try Method 1 (start fresh) - it's the quickest solution!** 🚀

