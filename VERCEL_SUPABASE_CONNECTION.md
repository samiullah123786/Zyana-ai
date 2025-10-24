# 🚀 Vercel + Supabase Connection Guide

Your frontend is deployed at: **https://zyana-dashboard.vercel.app/**

## ⚠️ Current Issue

The dashboard shows "Loading your businesses..." because either:
1. The backend API URL is not set in Vercel environment variables
2. The Supabase database tables don't exist yet
3. The backend is not deployed/running

## ✅ Step-by-Step Fix

### Step 1: Set Up Supabase Database

1. **Go to your Supabase Dashboard**: https://supabase.com/dashboard
2. **Select your project** (or create one if you haven't)
3. **Go to SQL Editor** (left sidebar)
4. **Copy and paste the entire content** from `SUPABASE_SETUP.sql` file
5. **Click "Run"** to execute the script

This will create:
- ✅ All required tables (businesses, transactions, loans, etc.)
- ✅ Indexes for performance
- ✅ Row Level Security policies
- ✅ Sample businesses (Vidify, MilkBusiness, Yazman Express)

### Step 2: Get Your Supabase Credentials

From your Supabase Dashboard:
1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **Project API Key** (`anon public` key)
   - **Service Role Key** (for backend admin access)

### Step 3: Configure Backend Environment Variables

Your backend should be deployed at: **https://zyana-backend.onrender.com**

Go to Render.com → Your Backend Service → Environment Variables:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ENVIRONMENT=production
WEBHOOK_URL=https://zyana-backend.onrender.com

# Other required variables
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
OPENAI_API_KEY=your-openai-api-key
QDRANT_URL=your-qdrant-url
QDRANT_API_KEY=your-qdrant-api-key
UPSTASH_REDIS_REST_URL=your-upstash-redis-url
UPSTASH_REDIS_REST_TOKEN=your-upstash-redis-token
```

**After adding these, Render will automatically redeploy your backend.**

### Step 4: Configure Frontend Environment Variables (Vercel)

1. Go to **Vercel Dashboard**: https://vercel.com/dashboard
2. Select your **zyana-dashboard** project
3. Go to **Settings** → **Environment Variables**
4. Add this variable:

```bash
NEXT_PUBLIC_API_URL=https://zyana-backend.onrender.com
```

5. **Redeploy** your frontend:
   - Go to **Deployments** tab
   - Click the three dots (⋯) on the latest deployment
   - Click **Redeploy**

### Step 5: Verify the Connection

1. **Test Backend API Directly**:
   Open: https://zyana-backend.onrender.com/health
   
   ✅ You should see: `{"status": "healthy"}`

2. **Test Businesses Endpoint**:
   Open: https://zyana-backend.onrender.com/finance/businesses
   
   ✅ You should see JSON with 3 businesses (Vidify, MilkBusiness, Yazman Express)

3. **Test Frontend**:
   Open: https://zyana-dashboard.vercel.app/
   
   ✅ You should see the 3 businesses loaded in the dashboard

### Step 6: Test CRUD Operations

Once everything is connected:

1. **Add a Business**:
   - Visit: https://zyana-dashboard.vercel.app/businesses
   - Click "Add Business"
   - Fill in the form and save

2. **Add a Transaction**:
   - Visit: https://zyana-dashboard.vercel.app/transactions
   - Click "Add Transaction"
   - Fill in the form and save

3. **View Dashboard**:
   - Visit: https://zyana-dashboard.vercel.app/
   - You should see real data from your database

## 🔍 Troubleshooting

### Problem: Backend returns 500 error
**Solution**: Check that all Supabase environment variables are correctly set in Render.

### Problem: Frontend shows CORS error
**Solution**: The backend already has CORS enabled. Check browser console for exact error.

### Problem: "Loading..." never stops
**Solution**: 
1. Open browser console (F12)
2. Check for error messages
3. Verify `NEXT_PUBLIC_API_URL` is set in Vercel
4. Verify backend is running at the URL

### Problem: Database connection failed
**Solution**: 
1. Check Supabase credentials are correct
2. Verify Supabase project is active
3. Check if tables exist in Supabase SQL Editor

## 📝 Quick Test Script

Run this in your browser console on https://zyana-dashboard.vercel.app/:

```javascript
// Test API connection
fetch('https://zyana-backend.onrender.com/finance/businesses')
  .then(r => r.json())
  .then(d => console.log('✅ Businesses:', d))
  .catch(e => console.error('❌ Error:', e))
```

## 🎯 Expected Results

After completing all steps, you should have:

✅ **Dashboard**: Shows real business data  
✅ **Add/Edit/Delete**: All CRUD operations work  
✅ **Transactions**: Can add and view transactions  
✅ **Real-time Updates**: Changes reflect immediately  
✅ **No Loading Errors**: Everything loads smoothly  

## 🆘 Need Help?

If you still see issues:

1. **Check Backend Logs** (Render Dashboard → Logs tab)
2. **Check Supabase Logs** (Supabase Dashboard → Logs)
3. **Check Browser Console** (F12 → Console tab)
4. Share the error messages for debugging

---

## 📋 Checklist

- [ ] Run `SUPABASE_SETUP.sql` in Supabase SQL Editor
- [ ] Copy Supabase credentials (URL, anon key, service key)
- [ ] Add credentials to Render backend environment variables
- [ ] Add `NEXT_PUBLIC_API_URL` to Vercel environment variables
- [ ] Redeploy backend on Render
- [ ] Redeploy frontend on Vercel
- [ ] Test backend health endpoint
- [ ] Test businesses endpoint
- [ ] Test frontend dashboard
- [ ] Test CRUD operations (create/edit/delete)

Once all items are checked, your full-stack application should be working perfectly! 🎉

