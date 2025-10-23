# 🚀 GitHub Repository Setup for Zyana AI

## Quick Guide to Push Your Code to GitHub

---

## 📋 **Step 1: Create GitHub Repository (2 minutes)**

### Option A: Via GitHub Website (Recommended)

1. Go to: https://github.com/new

2. **Repository Settings**:
   - Repository name: `Zyana` (or `zyana-ai`)
   - Description: `Multi-agent AI assistant with natural language processing`
   - Visibility: **Private** (recommended) or Public
   - ❌ **DO NOT** initialize with README, .gitignore, or license
   - Click **Create repository**

3. **Copy your repository URL**: 
   - Will look like: `https://github.com/YOUR_USERNAME/Zyana.git`
   - Keep this page open!

---

## 📋 **Step 2: Push Your Code to GitHub**

I'll help you run these commands automatically, or you can run them manually:

```powershell
# 1. Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/Zyana.git

# 2. Verify remote was added
git remote -v

# 3. Push your code to GitHub
git push -u origin dev

# 4. (Optional) Also push to main branch
git checkout -b main
git push -u origin main
git checkout dev
```

---

## ✅ **After Pushing to GitHub**

Your code is now on GitHub! You can proceed with:

1. ✅ **Deploy Backend to Render.com** (10 min)
2. ✅ **Deploy Frontend to Vercel** (5 min)

Both platforms will connect to your GitHub repository automatically!

---

## 🔐 **Important: Protect Your Secrets**

Your `.env` file is already in `.gitignore`, so your secrets are safe! ✅

Never commit:
- `.env`
- Any files with API keys
- Credentials

---

## 📝 **Quick Reference**

After creating the GitHub repo, you'll need:
- Repository URL: `https://github.com/YOUR_USERNAME/Zyana.git`
- Branch to deploy: `dev`

---

**Next**: Follow `PRODUCTION_DEPLOYMENT.md` Phase 4 to deploy to Render!

