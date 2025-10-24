# 🎯 Quick Start: Connect Vercel Frontend to Supabase

## 🚨 Current Status

- ✅ **Frontend Deployed**: https://zyana-dashboard.vercel.app/
- ⚠️ **Backend**: Needs Supabase connection
- ⚠️ **Database**: Tables need to be created

## 📋 Quick Setup (5 Minutes)

### Step 1️⃣: Create Database Tables (2 min)

1. Open **Supabase Dashboard**: https://supabase.com/dashboard
2. Go to **SQL Editor** (left sidebar)
3. Click **New Query**
4. Copy the entire content from **`SUPABASE_SETUP.sql`** file
5. Click **Run** (or press Ctrl+Enter)

✅ **Done!** You now have all tables, businesses, and triggers set up.

---

### Step 2️⃣: Get Supabase Credentials (1 min)

From your Supabase Dashboard:

1. Go to **Settings** → **API**
2. Copy these 3 values:

```
Project URL: https://xxxxx.supabase.co
anon public key: eyJh...
service_role key: eyJh...
```

---

### Step 3️⃣: Configure Backend on Render (1 min)

Go to: https://dashboard.render.com → Your Backend Service

Add these environment variables:

```bash
SUPABASE_URL=<paste your project URL>
SUPABASE_ANON_KEY=<paste your anon key>
SUPABASE_SERVICE_KEY=<paste your service role key>
```

Click **Save** → Render will auto-redeploy your backend.

---

### Step 4️⃣: Configure Frontend on Vercel (1 min)

Go to: https://vercel.com/dashboard → Your Project → **Settings** → **Environment Variables**

Add:

```bash
NEXT_PUBLIC_API_URL=https://zyana-backend.onrender.com
```

Click **Save** → Go to **Deployments** → Click ⋯ → **Redeploy**

---

### Step 5️⃣: Test Everything (30 sec)

1. **Open**: https://zyana-backend.onrender.com/finance/businesses
   - ✅ Should see JSON with 3 businesses

2. **Open**: https://zyana-dashboard.vercel.app/
   - ✅ Should see 3 businesses loaded (not "Loading...")

3. **Test CRUD**:
   - Visit: https://zyana-dashboard.vercel.app/businesses
   - Click "Add Business" → Create a new business
   - ✅ Should save to database successfully!

---

## 🎉 You're Done!

Your full-stack app is now connected:

- ✅ **Frontend** (Vercel) → **Backend** (Render) → **Database** (Supabase)
- ✅ All CRUD operations working
- ✅ Real-time data from database

---

## 📚 Need More Info?

- **Detailed Setup**: Read `VERCEL_SUPABASE_CONNECTION.md`
- **Testing Guide**: Read `TEST_CRUD.md`
- **SQL Schema**: Check `SUPABASE_SETUP.sql`

---

## 🐛 Troubleshooting

### Problem: Still showing "Loading..."

**Solution**:
1. Check browser console (F12) for errors
2. Verify `NEXT_PUBLIC_API_URL` is set in Vercel
3. Test backend directly: https://zyana-backend.onrender.com/health

### Problem: Backend returns 500 error

**Solution**:
1. Check Render logs for errors
2. Verify Supabase credentials are correct
3. Make sure you ran the SQL script in Supabase

### Problem: Database connection failed

**Solution**:
1. Verify Supabase project is active
2. Check credentials are copied correctly (no extra spaces)
3. Make sure service_role key is used (not just anon key)

---

## 🚀 What's Working Now

After setup, you can:

✅ **View Dashboard** with real business data  
✅ **Add/Edit/Delete Businesses** at `/businesses`  
✅ **Add/View Transactions** at `/transactions`  
✅ **See Live Stats** (balance, revenue, expenses)  
✅ **Filter and Search** transactions  
✅ **Real-time Updates** across all pages  

---

## 📝 Next Steps (Optional)

Want to add more features?

1. **Authentication**: Add user login with Supabase Auth
2. **More CRUD Pages**: Loans, Goals, Events
3. **Reports**: Generate PDF reports
4. **Charts**: Add more data visualizations
5. **Mobile App**: Connect the same backend to a mobile app

---

**Questions?** Check the detailed guides or open an issue! 🚀

