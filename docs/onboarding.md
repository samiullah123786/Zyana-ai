# Zyana Onboarding Guide

Welcome to Zyana! This guide will help you get started with your personal AI assistant.

## Step 1: Initial Setup

### 1.1 Verify Installation

Make sure you have completed the installation:
- Backend is running at `http://localhost:8000`
- Frontend is accessible at `http://localhost:3000`
- Database migrations have been applied

Check health:
```bash
curl http://localhost:8000/health
```

### 1.2 Verify Credentials

Ensure these are set in your `.env`:
- ✅ `FAL_API_KEY`
- ✅ `TELEGRAM_BOT_TOKEN`
- ✅ `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`
- ✅ `SUPABASE_URL` & `SUPABASE_SERVICE_KEY`

## Step 2: Connect Telegram Bot

### 2.1 Find Your Bot

1. Open Telegram
2. Search for your bot (the name you gave to @BotFather)
3. Send `/start` to your bot

Expected response:
```
👋 Welcome to Zyana!

I'm your personal AI assistant. I can help you:
• Track finances across your businesses
• Manage calendar events
• Search your personal memory
• And much more!
```

### 2.2 Test Basic Interaction

Try sending:
```
I received Rs 50,000 from milk sales today
```

Zyana should respond with a confirmation like:
```
✅ Recorded income: PKR 50,000
Business: MilkBusiness
Category: sales
```

## Step 3: Connect Google Calendar

### 3.1 Authorize Google Account

1. Visit: `http://localhost:8000/calendar/auth/google`
2. Copy the authorization URL
3. Open it in your browser
4. Log in with your Google account
5. Grant Calendar permissions
6. You'll be redirected back with a success message

### 3.2 Test Calendar Integration

Send to Zyana:
```
Schedule meeting with team tomorrow at 3pm
```

Check your Google Calendar - the event should appear!

## Step 4: Explore the Dashboard

### 4.1 Access the Dashboard

Open http://localhost:3000 in your browser

You should see:
- Overview of all your businesses
- Current balances
- Quick actions

### 4.2 Navigate Business Details

1. Click on any business card (e.g., "Vidify")
2. View recent transactions
3. See income vs. expenses
4. Check current balance

### 4.3 Try Memory Search

1. Click "Memory Search" on the dashboard
2. Try queries like:
   - "Show me all payments to Ahmad"
   - "What were my expenses last week?"
   - "When did I last meet the team?"

## Step 5: Setup Desktop Agent (Optional)

### 5.1 Install Desktop Agent

```bash
cd desktop-agent
npm install
npm run dev
```

### 5.2 Configure Desktop Agent

1. Enter API URL: `http://localhost:8000`
2. Enter Auth Token: (get from backend or use test token)
3. Add watch folders:
   - Click "Add Folder"
   - Enter path to folder with videos
   - Click "Add"

### 5.3 Test File Watching

1. Copy a video file (.mp4, .mov) to the watched folder
2. Check Desktop Agent logs
3. Video job should be created in backend

## Step 6: Customize Your Experience

### 6.1 Habit Learning

Zyana will learn your preferences automatically:

After using the same currency 3+ times:
```
Zyana: I noticed you usually use PKR. Should I default to PKR for amounts?
You: Yes
Zyana: ✅ Updated preference: preferred_currency
```

### 6.2 Add More Businesses

Tell Zyana:
```
Start new business called TechConsulting
```

Or via dashboard:
1. Go to dashboard
2. Click "Add Business" (coming soon)

### 6.3 Set Goals

Set revenue targets:
```
Target to earn 500k from Vidify by December
```

## Common Use Cases

### Track Daily Expenses

```
Paid 2500 for fuel for Yazman Express
Bought office supplies 15000
Lunch meeting expense 3000 from Vidify
```

### Manage Loans

```
Lent Ahmad Rs 10,000 from Vidify
Ahmad repaid 5,000
How much does Ahmad still owe me?
```

### Schedule Events

```
Meeting with client next Monday at 10am
Reminder to call supplier tomorrow
Team standup every weekday at 9am
```

### Generate Reports

```
Show me this month's expenses for Vidify
What's my current balance?
/status
```

## Tips & Tricks

### 1. Be Natural

Zyana understands natural language:
```
✅ "I lent Ahmad 10k yesterday from Vidify"
✅ "Received 50,000 from milk sales today"
✅ "Paid for Adobe subscription $299"
```

### 2. Specify Details

More details = better records:
```
Better: "Paid Ahmad Rs 10,000 from Vidify for video editing work"
vs
Basic: "Paid Ahmad 10000"
```

### 3. Use Commands

Quick actions via commands:
- `/status` - Check all balances
- `/report` - Generate report
- `/help` - Show help

### 4. Leverage Memory

Ask questions about past transactions:
```
When did I last pay Ahmad?
Show me all video-related expenses
What were my top expenses last month?
```

### 5. Multi-language Support

Zyana understands multiple languages:
```
آج دودھ کی فروخت سے 50000 روپے ملے
(Received 50,000 from milk sales today)
```

## Troubleshooting

### Zyana doesn't respond

1. Check backend is running: `curl http://localhost:8000/health`
2. Verify Telegram webhook is set
3. Check backend logs for errors

### Transactions not appearing

1. Verify database migrations were applied
2. Check Supabase dashboard
3. Look for errors in agent logs

### Calendar sync not working

1. Re-authorize Google account
2. Check credentials in `.env`
3. Verify redirect URI matches Google Console

### Desktop Agent not detecting files

1. Verify folder path is correct
2. Check file permissions
3. Look at Desktop Agent logs

## Next Steps

### Customize Zyana Further

1. **Add more businesses** - Track multiple income streams
2. **Set goals** - Revenue targets, savings goals
3. **Train with your data** - Feed past transactions for better insights
4. **Invite team members** (coming soon)

### Explore Advanced Features

1. **Weekly/Monthly reports** - Automated via email
2. **Budget alerts** - Get notified when exceeding limits
3. **Recurring transactions** - Automate regular expenses
4. **Custom categories** - Organize your way

### Integrate More Services

1. **Bank sync** (coming soon) - Auto-import transactions
2. **Invoice generation** - Create invoices from transactions
3. **Tax reporting** - Export for tax filing
4. **Third-party apps** - Stripe, QuickBooks, etc.

## Getting Help

### Resources

- 📚 Documentation: `docs/`
- 🏗️ Architecture: `docs/architecture.md`
- 🚀 Deployment: `docs/deployment.md`
- 💻 API Docs: `http://localhost:8000/docs`

### Support

- GitHub Issues: Report bugs or request features
- Email: (add your contact)
- Community: (add Discord/Slack if applicable)

## Feedback

We'd love to hear from you!

What works well?
What could be better?
What features do you need?

Share your feedback to help make Zyana even better!

---

**Welcome to the Zyana family! 🎉**

Start chatting with your AI assistant and let Zyana help you manage your businesses effortlessly.

