# Zyana 7-Feature Expansion - Deployment Guide

This guide covers deploying all 7 new features to production.

## Prerequisites

- Supabase project with admin access
- Render.com account (backend hosting)
- Vercel account (frontend hosting)
- Redis instance (for background jobs)
- Telegram Bot Token

## Step 1: Database Migrations

Run all 4 new migrations on your Supabase SQL Editor:

1. **005_invoices_and_clients.sql**
   - Creates `clients` and `invoices` tables
   - Adds indexes and RLS policies
   
2. **006_scheduled_notifications.sql**
   - Creates `scheduled_notifications` table
   - Adds scheduling support
   
3. **007_work_sessions.sql**
   - Creates `work_sessions` table
   - Extends `habit_profiles` with work pattern fields
   
4. **008_mirror_mode.sql**
   - Creates `user_message_samples` table
   - Adds mirror mode fields to `users` table
   - Sets first user as admin

### Migration Commands

```sql
-- Run these in order in Supabase SQL Editor:
-- 1. Copy contents of backend/migrations/005_invoices_and_clients.sql and execute
-- 2. Copy contents of backend/migrations/006_scheduled_notifications.sql and execute
-- 3. Copy contents of backend/migrations/007_work_sessions.sql and execute
-- 4. Copy contents of backend/migrations/008_mirror_mode.sql and execute
```

### Verification

After running migrations, verify tables exist:

```sql
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('clients', 'invoices', 'scheduled_notifications', 'work_sessions', 'user_message_samples');
```

## Step 2: Install Backend Dependencies

Add to your existing virtual environment:

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install new dependencies
pip install faster-whisper==1.0.1
pip install pydub==0.25.1

# Or reinstall from requirements.txt
pip install -r requirements.txt
```

### Note on faster-whisper

faster-whisper requires additional system dependencies:

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download ffmpeg from https://ffmpeg.org/download.html and add to PATH

## Step 3: Environment Variables

No new environment variables needed! All features use existing configuration:
- `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` - Database
- `REDIS_URL` - Background jobs
- `TELEGRAM_BOT_TOKEN` - Telegram integration
- `WEBHOOK_URL` - Telegram webhook

## Step 4: Deploy Backend to Render

### Update Build Command

In your Render dashboard, update build command:

```bash
pip install -r backend/requirements.txt
```

### Update Start Command

Ensure you're running both the API server and background workers:

**Option A: Use Procfile (Recommended)**

Create/update `Procfile` in project root:

```
web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
worker: cd backend && python -m workers.worker
scheduler: cd backend && python workers/scheduler.py
```

**Option B: Single Process (for development)**

```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

Then separately run workers:

```bash
python -m workers.worker
python workers/scheduler.py
```

### Verify Deployment

After deployment, test endpoints:

```bash
# Check health
curl https://your-backend-url.onrender.com/health

# Check invoices endpoint
curl https://your-backend-url.onrender.com/invoice/list

# Check admin stats
curl https://your-backend-url.onrender.com/admin/stats
```

## Step 5: Deploy Frontend to Vercel

### Environment Variables

Ensure `NEXT_PUBLIC_BACKEND_URL` points to your Render backend:

```
NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.onrender.com
```

### Deploy

```bash
cd frontend
vercel --prod
```

Or push to your connected GitHub repo for automatic deployment.

### Verify Deployment

Visit your Vercel URL and check:
- ✅ /invoices page loads
- ✅ /clients page loads
- ✅ /admin page loads
- ✅ Navbar shows new links

## Step 6: Start Background Workers

Background jobs handle:
- Processing scheduled notifications (every minute)
- Checking overdue payments (daily 9 AM)
- Analyzing routines (daily midnight)
- Weekly/monthly reports
- Google Calendar sync

### On Render

If using Procfile, workers start automatically.

If not, add separate background worker services in Render:

1. Create new "Background Worker" service
2. Connect same repo
3. Build command: `pip install -r backend/requirements.txt`
4. Start command: `cd backend && python -m workers.worker`

5. Create another for scheduler:
6. Start command: `cd backend && python workers/scheduler.py`

### Local Testing

```bash
# Terminal 1: API Server
cd backend
python main.py

# Terminal 2: Worker
cd backend
python -m workers.worker

# Terminal 3: Scheduler
cd backend
python workers/scheduler.py
```

## Step 7: Configure Telegram Bot

Update bot commands with BotFather:

```
/setcommands

start - Welcome message
help - Command list
status - Balance check
insights - AI insights
list_invoices - Show invoices
list_clients - Show clients
client_status - Client invoice status
list_reminders - Show scheduled notifications
cancel_reminder - Cancel notification
mirror_mode_on - Enable mirror mode
mirror_mode_off - Disable mirror mode
my_style - Show learned style profile
```

## Step 8: Testing Checklist

### Invoice System
- [ ] Create invoice via dashboard
- [ ] List invoices with filters
- [ ] Mark invoice as paid
- [ ] View overdue invoices
- [ ] Test `/list_invoices` Telegram command

### Client Management
- [ ] Create client via dashboard
- [ ] List clients
- [ ] View client details
- [ ] Test `/list_clients` Telegram command
- [ ] Test `/client_status [name]` Telegram command

### Scheduled Notifications
- [ ] Schedule notification via natural language: "Remind me to X at Y"
- [ ] List pending reminders with `/list_reminders`
- [ ] Cancel reminder with `/cancel_reminder [id]`
- [ ] Wait for scheduled time and verify notification is sent

### Voice Commands
- [ ] Send voice message via Telegram
- [ ] Verify transcription feedback message
- [ ] Verify voice is processed as text
- [ ] Test with different languages (English, Urdu)

### Mirror Mode
- [ ] Enable with `/mirror_mode_on`
- [ ] Send 20+ messages
- [ ] Check style with `/my_style`
- [ ] Verify responses match your style
- [ ] Disable with `/mirror_mode_off`

### Routine Optimization
- [ ] Send messages throughout the day for 7 days
- [ ] Wait for daily midnight analysis
- [ ] Check for break suggestions during work hours
- [ ] Verify busy period detection

### Admin Dashboard
- [ ] Access `/admin` page
- [ ] View system stats
- [ ] Check activity logs
- [ ] View scheduled notifications
- [ ] Test canceling notifications

### Background Jobs
- [ ] Verify overdue payment reminders sent at 9 AM
- [ ] Verify routine analysis runs at midnight
- [ ] Verify scheduled notifications process every minute
- [ ] Check logs in admin dashboard

## Step 9: Monitoring

### Backend Logs

Monitor Render logs for:
- `✅ All scheduled jobs set up successfully`
- `🔄 Starting RQ worker...`
- `📨 Telegram webhook received`
- `Running scheduled notifications processing job`

### Database Monitoring

Check Supabase for table growth:

```sql
-- Check recent invoices
SELECT COUNT(*) FROM invoices WHERE created_at > NOW() - INTERVAL '24 hours';

-- Check scheduled notifications
SELECT COUNT(*) FROM scheduled_notifications WHERE status = 'pending';

-- Check work sessions
SELECT COUNT(*) FROM work_sessions WHERE timestamp > NOW() - INTERVAL '7 days';

-- Check message samples for mirror mode
SELECT COUNT(*) FROM user_message_samples;
```

### Redis Monitoring

Check Redis for active jobs:

```bash
# Connect to Redis
redis-cli -h your-redis-host -p 6379

# Check queues
LLEN zyana-queue

# Check scheduled jobs
ZCARD rq:scheduler:scheduled_jobs
```

## Step 10: Performance Optimization

### Database Indexes

All necessary indexes are created by migrations. Verify:

```sql
SELECT tablename, indexname FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename IN ('clients', 'invoices', 'scheduled_notifications', 'work_sessions');
```

### Whisper Model

The default "base" model (74MB) provides good balance. For better accuracy:

Edit `backend/services/voice_transcriber.py`:

```python
# Change from "base" to "small"
model_size = "small"  # 244MB, better accuracy
```

### Redis Connection Pooling

Already configured in `workers/scheduler.py` and `workers/worker.py`.

## Troubleshooting

### Issue: Voice transcription fails

**Solution:**
- Ensure ffmpeg is installed on server
- Check Render build logs for installation errors
- Verify faster-whisper installed: `pip show faster-whisper`

### Issue: Scheduled notifications not sending

**Solution:**
- Verify scheduler is running (check Render logs for "Scheduler is running...")
- Check Redis connection
- Verify cron job registered: Check logs for "✓ Scheduled: Process scheduled notifications"
- Test manually: Call `/notification/schedule` API endpoint

### Issue: Mirror mode not working

**Solution:**
- Verify user sent 20+ messages (check `user_message_samples` table)
- Check if mirror mode enabled: `SELECT mirror_mode_enabled FROM users WHERE id = 1;`
- Verify style profile exists: `SELECT * FROM habit_profiles WHERE key = 'communication_style';`

### Issue: Admin dashboard shows errors

**Solution:**
- Check backend health: `curl https://your-backend-url.onrender.com/health`
- Verify migrations ran successfully
- Check Supabase table permissions

### Issue: Overdue payment reminders not sending

**Solution:**
- Verify invoices exist with overdue status: `SELECT * FROM invoices WHERE status = 'overdue';`
- Check scheduler running (should log "Running overdue payments check job")
- Verify Telegram chat_id stored (needed for sending reminders)

## Success Criteria

All features deployed successfully when:

1. ✅ All 4 migrations applied
2. ✅ Backend health check returns "healthy"
3. ✅ Frontend pages load (invoices, clients, admin)
4. ✅ Telegram commands respond correctly
5. ✅ Voice messages transcribe successfully
6. ✅ Scheduled notifications send at correct time
7. ✅ Admin dashboard shows real-time stats
8. ✅ Background jobs run on schedule
9. ✅ Mirror mode learns and applies style
10. ✅ Overdue payment reminders sent daily

## Rollback Plan

If issues occur:

1. **Backend Rollback:** Redeploy previous Render commit
2. **Frontend Rollback:** Revert Vercel deployment
3. **Database Rollback:** Drop new tables (keep backups!)

```sql
-- CAUTION: Only if absolutely necessary
DROP TABLE IF EXISTS user_message_samples CASCADE;
DROP TABLE IF EXISTS work_sessions CASCADE;
DROP TABLE IF EXISTS scheduled_notifications CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS clients CASCADE;
```

## Support & Maintenance

### Regular Tasks

- **Daily:** Check overdue payment reminders sent
- **Weekly:** Review admin logs for errors
- **Monthly:** Analyze usage patterns and optimize

### Backup Strategy

- Supabase automatic backups enabled
- Export important data weekly:

```sql
COPY invoices TO '/tmp/invoices_backup.csv' CSV HEADER;
COPY clients TO '/tmp/clients_backup.csv' CSV HEADER;
```

## Conclusion

All 7 features are now deployed and operational:

1. ✅ Invoice & Payment Tracker
2. ✅ Routine Optimization  
3. ✅ Mirror Mode
4. ✅ Auto-Notifications
5. ✅ Client Management
6. ✅ Voice Commands
7. ✅ Admin Dashboard

Your Zyana assistant is now enterprise-ready! 🚀

