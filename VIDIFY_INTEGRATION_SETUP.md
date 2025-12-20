# Zyana + Vidify HQ Dashboard Integration

This guide explains how to connect Zyana AI to your Vidify HQ Dashboard so you can manage your agency using natural language commands.

## 🎯 What You Can Do

Once connected, you can tell Zyana things like:

| Command | What Zyana Does |
|---------|-----------------|
| "Add client Ahmad Khan to Vidify" | Creates a new client in Vidify HQ |
| "Create project Website for Ahmad - 50000" | Adds a project linked to the client |
| "Log income 25000 from Ahmad in Vidify" | Records income transaction |
| "Add expense 5000 for equipment in Vidify" | Records expense |
| "Pay Hamza salary 30000" | Records salary payment |
| "Show Vidify dashboard" | Gets dashboard statistics |
| "List Vidify clients" | Shows all clients |
| "Show Vidify projects" | Lists all projects |

## 🔧 Setup Instructions

### Step 1: Get Firebase Service Account Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your **vidify-hq** project
3. Click the gear icon ⚙️ → **Project settings**
4. Go to **Service accounts** tab
5. Click **Generate new private key**
6. Save the downloaded JSON file

### Step 2: Configure Zyana Backend

You have two options:

#### Option A: Environment Variable (Recommended for Production)

1. Open the downloaded JSON file
2. Copy its entire contents
3. Add to your `.env` file:

```env
FIREBASE_CREDENTIALS={"type":"service_account","project_id":"vidify-hq",...}
```

Make sure the entire JSON is on one line!

#### Option B: File Path (Good for Local Development)

1. Save the JSON file to a secure location, e.g., `D:\Apps\Zyana\backend\vidify-hq-credentials.json`
2. Add to your `.env` file:

```env
FIREBASE_CREDENTIALS_PATH=D:\Apps\Zyana\backend\vidify-hq-credentials.json
```

### Step 3: Install Dependencies

```bash
cd backend
pip install google-cloud-firestore==2.14.0
```

Or if using requirements.txt:
```bash
pip install -r requirements.txt
```

### Step 4: Restart Zyana Backend

```bash
# Windows
cd D:\Apps\Zyana\backend
python main.py

# Or using the batch file
START_BACKEND.bat
```

### Step 5: Test the Connection

Send a message to Zyana via Telegram:
```
Show Vidify dashboard
```

If connected successfully, you'll see your dashboard stats!

## 📁 Files Created

The integration adds these files to Zyana:

```
backend/
├── clients/
│   └── firebase_client.py      # Firebase Firestore connection
├── agents/
│   └── vidify_dashboard.py     # Vidify dashboard agent
├── routers/
│   └── vidify.py               # REST API endpoints
```

## 🔌 API Endpoints

The integration also exposes REST API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/vidify/status` | GET | Check Firebase connection |
| `/vidify/stats` | GET | Get dashboard statistics |
| `/vidify/clients` | GET/POST | List or add clients |
| `/vidify/projects` | GET/POST | List or add projects |
| `/vidify/transactions` | POST | Add income/expense |
| `/vidify/team` | POST | Add team member |
| `/vidify/team/pay-salary` | POST | Pay salary |
| `/vidify/command` | POST | Natural language command |

## 🔒 Security Notes

1. **Never commit** your Firebase credentials JSON file to git
2. Add to `.gitignore`:
   ```
   *-credentials.json
   vidify-hq-*.json
   ```
3. For production, use environment variables instead of file paths

## 🐛 Troubleshooting

### "Firebase not connected" error

1. Check if `FIREBASE_CREDENTIALS` or `FIREBASE_CREDENTIALS_PATH` is set correctly
2. Verify the JSON file is valid
3. Check the backend logs for detailed error messages

### "Permission denied" error

1. Make sure the Firebase service account has Firestore access
2. In Firebase Console → Firestore → Rules, ensure rules allow access

### Commands not recognized

Make sure to include "Vidify" in your command:
- ✅ "Add client Ahmad to **Vidify**"
- ❌ "Add client Ahmad" (might be confused with other finance features)

## 🚀 Next Steps

1. Test all commands with Zyana
2. Add your existing clients/projects through Zyana
3. Track all income and expenses through voice/text commands
4. Pay team salaries with a simple message!

---

Made with ❤️ for Sami's agency workflow automation

