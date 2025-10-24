# 🔧 Vercel Environment Variables Setup

## ❌ The Issue

You pasted all variables together in one field. You need to add them **one by one**.

---

## ✅ Correct Method: Add ONE Variable at a Time

### **Step 1: Add First Variable**

1. In Vercel, find **"Environment Variables"** section
2. Click **"Add Environment Variable"** or **"Add Another"**
3. Fill in:
   - **Key**: `NEXT_PUBLIC_SUPABASE_URL`
   - **Value**: `https://yrwlvurrjzsosfkyaacq.supabase.co`
4. Click **"Add"** or checkmark

### **Step 2: Add Second Variable**

1. Click **"Add Another"** or **"+"** button
2. Fill in:
   - **Key**: `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **Value**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlyd2x2dXJyanpzb3Nma3lhYWNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEwNTY2NDIsImV4cCI6MjA3NjYzMjY0Mn0.6MK8ARbgQS9Oga8UrnhmFY8otvO0PC_3FUJ7izOz008`
3. Click **"Add"**

### **Step 3: Add Third Variable**

1. Click **"Add Another"** or **"+"** button
2. Fill in:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://zyana-backend.onrender.com`
3. Click **"Add"**

---

## 📋 **Summary: 3 Separate Variables**

You should have **3 separate entries**:

| # | Key | Value |
|---|-----|-------|
| 1 | `NEXT_PUBLIC_SUPABASE_URL` | `https://yrwlvurrjzsosfkyaacq.supabase.co` |
| 2 | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| 3 | `NEXT_PUBLIC_API_URL` | `https://zyana-backend.onrender.com` |

---

## 🔍 **What It Should Look Like**

In Vercel's Environment Variables section, you should see:

```
✅ NEXT_PUBLIC_SUPABASE_URL = https://yrwlvurrjzsosfkyaacq.supabase.co

✅ NEXT_PUBLIC_SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

✅ NEXT_PUBLIC_API_URL = https://zyana-backend.onrender.com
```

**NOT**:
```
❌ NEXT_PUBLIC_SUPABASE_URL = https://yrwlvurrjzsosfkyaacq.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🛠️ **If You Already Added It Wrong**

### Method 1: Delete and Re-add
1. Find the incorrect variable
2. Click the **trash/delete** icon
3. Add them correctly one by one (as above)

### Method 2: Edit Each One
1. Click **Edit** on the variable
2. Fix the Key and Value
3. Save

---

## ✅ **Environment Selection**

For each variable, make sure to select:
- ☑️ **Production**
- ☑️ **Preview**
- ☑️ **Development**

(Or at least check "Production")

---

## 🚀 **After Adding All 3 Variables**

1. Click **"Deploy"** button
2. Wait 3-5 minutes
3. Your frontend will be live!

---

## 🧪 **Verify Variables Are Set**

After deployment, you can check if they're working:

1. Open your deployed site
2. Open browser console (F12)
3. Type: `console.log(process.env.NEXT_PUBLIC_SUPABASE_URL)`
4. Should show the URL

---

## 📝 **Quick Checklist**

Before deploying:

- [ ] Variable 1: `NEXT_PUBLIC_SUPABASE_URL` added
- [ ] Variable 2: `NEXT_PUBLIC_SUPABASE_ANON_KEY` added  
- [ ] Variable 3: `NEXT_PUBLIC_API_URL` added
- [ ] All are separate entries (not combined)
- [ ] Production environment selected
- [ ] Values don't have extra spaces or quotes

---

## 💡 **Common Mistakes**

### ❌ Don't do this:
- Pasting all in one field
- Adding quotes around values
- Including the variable name in the value field
- Copy-pasting with line breaks

### ✅ Do this:
- Add one variable at a time
- Just the value, no quotes
- Key in key field, value in value field
- Trim any extra whitespace

---

**Add them separately and you're good to go!** 🚀

