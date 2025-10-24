# 🔧 Fix Vercel Secret Reference Error

## ❌ The Error

```
Environment Variable "NEXT_PUBLIC_SUPABASE_URL" references Secret "supabase_url", which does not exist.
```

---

## 🎯 What This Means

Vercel thinks you're trying to **reference a Secret** instead of adding a **plain text value**.

---

## ✅ The Fix: Use Plain Text (Not Secrets)

### **Step-by-Step:**

1. **Delete the incorrect variable:**
   - Find `NEXT_PUBLIC_SUPABASE_URL` in the list
   - Click the trash/delete icon 🗑️
   - Confirm deletion

2. **Add it again correctly:**

   a. Click **"Add Environment Variable"** or **"Add New"**
   
   b. You'll see options:
      - ✅ **Plain Text** ← Choose this!
      - ❌ Secret
      - ❌ Sensitive
   
   c. Fill in:
      - **Name**: `NEXT_PUBLIC_SUPABASE_URL`
      - **Value**: `https://yrwlvurrjzsosfkyaacq.supabase.co`
      - **Type**: Plain Text (default)
   
   d. Select environments:
      - ☑️ Production
      - ☑️ Preview  
      - ☑️ Development
   
   e. Click **"Add"** or **"Save"**

---

## 🔍 How to Know You're Doing It Right

### ✅ Correct (Plain Text):
- You see a single text input field
- You paste the URL directly
- No dropdown saying "Select Secret"
- The value is visible (not hidden with dots)

### ❌ Wrong (Secret Reference):
- You see a dropdown to "Select Secret"
- It says "References Secret"
- You're asked to create a secret first
- The interface looks different

---

## 📋 All 3 Variables (Plain Text)

Add these **one by one** as **Plain Text**:

### Variable 1:
```
Name:  NEXT_PUBLIC_SUPABASE_URL
Value: https://yrwlvurrjzsosfkyaacq.supabase.co
Type:  Plain Text
```

### Variable 2:
```
Name:  NEXT_PUBLIC_SUPABASE_ANON_KEY
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlyd2x2dXJyanpzb3Nma3lhYWNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEwNTY2NDIsImV4cCI6MjA3NjYzMjY0Mn0.6MK8ARbgQS9Oga8UrnhmFY8otvO0PC_3FUJ7izOz008
Type:  Plain Text
```

### Variable 3:
```
Name:  NEXT_PUBLIC_API_URL
Value: https://zyana-backend.onrender.com
Type:  Plain Text
```

---

## 🎨 What the Interface Should Look Like

When adding a variable, you should see:

```
┌─────────────────────────────────────────┐
│ Add Environment Variable                │
├─────────────────────────────────────────┤
│ Name                                    │
│ [NEXT_PUBLIC_SUPABASE_URL            ] │
│                                         │
│ Value                                   │
│ [https://yrwlvurrjzsosfkyaacq...     ] │
│                                         │
│ Environment                             │
│ ☑ Production ☑ Preview ☑ Development   │
│                                         │
│          [Cancel]        [Add]          │
└─────────────────────────────────────────┘
```

**NOT**:
```
┌─────────────────────────────────────────┐
│ Add Environment Variable                │
├─────────────────────────────────────────┤
│ Name                                    │
│ [NEXT_PUBLIC_SUPABASE_URL            ] │
│                                         │
│ ⚠️ References Secret                    │
│ [Select Secret ▼] supabase_url         │  ← WRONG!
│                                         │
└─────────────────────────────────────────┘
```

---

## 💡 Why This Happens

This error occurs when:

1. You accidentally clicked "Use Secret" or "Reference Secret"
2. Vercel auto-detected the name and tried to link it to a secret
3. You're in the wrong section (Secrets vs Environment Variables)

---

## 🚀 After Fixing

Once all 3 variables are added correctly as **Plain Text**:

1. They should all show ✅ green checkmarks
2. Click **"Deploy"** or **"Redeploy"**
3. Wait 3-5 minutes
4. Your frontend will work! 🎉

---

## 🆘 Still Having Issues?

Try this alternative:

### Method 1: Use Simple Interface
Some Vercel UIs have a simpler form. Just fill:
- **Key**: `NEXT_PUBLIC_SUPABASE_URL`
- **Value**: `https://yrwlvurrjzsosfkyaacq.supabase.co`

### Method 2: Edit Project Settings After Creation
1. Create project first (skip env vars)
2. After created, go to **Settings** → **Environment Variables**
3. Add them there (usually simpler interface)

### Method 3: Use Vercel CLI
```bash
vercel env add NEXT_PUBLIC_SUPABASE_URL
# Then paste: https://yrwlvurrjzsosfkyaacq.supabase.co
# Select: Production, Preview, Development
```

---

## ✅ Success Indicators

You'll know it worked when:
- No error about "references Secret"
- All 3 variables show in the list
- Each shows the actual value (or truncated version)
- Deploy button works without errors

---

**Just use Plain Text values, and it will work!** 🎉

