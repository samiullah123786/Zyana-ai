# Calendar Intelligence Upgrade - Verification Checklist

## ✅ Pre-Deployment Verification

### 1. Environment Variables
- [ ] `DEFAULT_TIMEZONE=Asia/Karachi` set in .env
- [ ] `CONFIDENCE_THRESHOLD=0.7` set in .env
- [ ] `REDIS_SESSION_TTL=604800` set in .env
- [ ] `OWNER_NAME=Sami` set in .env
- [ ] `FAL_API_KEY` set and valid
- [ ] `REDIS_URL` set and Redis accessible
- [ ] `SUPABASE_URL` and keys configured
- [ ] `QDRANT_URL` set and Qdrant accessible

### 2. Dependencies
```bash
cd backend
pip install -r requirements.txt
# Verify dateparser installed:
python -c "import dateparser; print('✅ dateparser installed')"
```

### 3. Database Migration
```bash
cd backend
python scripts/apply_migrations.py
# Verify tables created:
# - sessions
# - calendar_events
# - conversations
# - agent_profile
```

### 4. Services Running
```bash
# Check Redis
redis-cli ping
# Expected: PONG

# Check Qdrant
curl http://localhost:6333/collections
# Expected: JSON response

# Check Supabase
# Visit your Supabase dashboard and verify connection
```

---

## 🧪 Functional Tests

### Test 1: Explicit Time Scheduling (No Clarification)
```
Input: "Schedule meeting tomorrow at 3pm with Zain"
Expected Output:
✅ "Got it, Sami! I'll schedule a meeting with Zain tomorrow at 3pm."
✅ Event created in Google Calendar
✅ ISO timestamp: 2025-10-26T15:00:00+05:00
✅ No clarification session created
```

**Verification:**
```sql
SELECT * FROM calendar_events ORDER BY created_at DESC LIMIT 1;
-- Check: resolved_start_iso has +05:00 timezone
```

### Test 2: Ambiguous Request (Should Clarify)
```
Input: "Schedule a meeting"
Expected Output:
✅ "I'd be happy to schedule that, Sami! When would you like it?"
✅ Session created in Redis
✅ needs_clarification = True

Follow-up Input: "Tomorrow at 3pm"
Expected Output:
✅ "Perfect, Sami! I'll create that event now."
✅ Event created
✅ Session marked complete
```

**Verification:**
```bash
# Check Redis for sessions (before completion)
redis-cli --scan --pattern "session:*"

# Check calendar_events table
SELECT session_id, raw_user_text, resolved_title, confidence_score 
FROM calendar_events 
WHERE session_id IS NOT NULL 
ORDER BY created_at DESC LIMIT 1;
```

### Test 3: Partial Info (Datetime Only, Need Title)
```
Input: "Schedule something tomorrow at 3pm"
Expected:
✅ May ask for title or default to "Meeting"
✅ Creates event with provided time
```

### Test 4: Natural Language Variations
Test these inputs:
```
✅ "meeting in 2 hours"
✅ "call with Ali next Friday afternoon"
✅ "lunch tomorrow"
✅ "appointment on Monday at 10:30am"
✅ "remind me to call John in 30 minutes"
```

### Test 5: Timezone Verification
```sql
-- All timestamps should include +05:00
SELECT 
    resolved_title,
    resolved_start_iso,
    resolved_end_iso,
    CASE 
        WHEN resolved_start_iso::text LIKE '%+05:00' THEN '✅ Correct TZ'
        ELSE '❌ Wrong TZ'
    END as timezone_check
FROM calendar_events
ORDER BY created_at DESC
LIMIT 5;
```

### Test 6: Qdrant Memory Storage
```python
# Test in Python shell
from services.context_retriever import context_retriever
import asyncio

async def test():
    context = await context_retriever.get_calendar_context(
        user_id="test_user",
        query_text="meeting with Ali",
        limit=5
    )
    print(f"Found {len(context['relevant_events'])} relevant events")
    print(context['context_summary'])

asyncio.run(test())
# Expected: Returns similar past events
```

### Test 7: Session Expiry
```python
from services.session_manager import session_manager
import time

# Create session
session_id = session_manager.create_session(
    user_id="test_expiry",
    intent="schedule_meeting",
    pending_fields=["datetime"],
    partial_data={},
    initial_message="test"
)

# Check TTL
import redis
r = redis.from_url("redis://localhost:6379")
ttl = r.ttl(session_id)
print(f"Session TTL: {ttl} seconds")
# Expected: ~604800 (7 days)
```

### Test 8: Agent Self-Description
```sql
SELECT name, owner, capabilities, default_timezone 
FROM agent_profile;

-- Expected:
-- name: Zyana
-- owner: Sami
-- default_timezone: Asia/Karachi
-- capabilities: [array of features]
```

---

## 🔍 Integration Tests

### Run Automated Tests
```bash
cd backend

# Test datetime parser
pytest tests/test_datetime_parser.py -v
# Expected: All tests pass

# Test session manager
pytest tests/test_session_manager.py -v
# Expected: All tests pass (if Redis available)

# Test clarification flow
pytest tests/test_clarification_flow.py -v -s
# Expected: Integration tests pass
```

---

## 📊 Production Readiness Checklist

### Code Quality
- [ ] No linting errors
- [ ] All tests passing
- [ ] No hardcoded credentials
- [ ] Proper error handling
- [ ] Logging with emoji indicators

### Performance
- [ ] Redis connection pooling working
- [ ] Qdrant queries < 200ms
- [ ] Session lookups < 50ms
- [ ] Datetime parsing < 100ms

### Security
- [ ] API keys not logged
- [ ] Sessions expire automatically
- [ ] SQL injection prevented
- [ ] Input validation present

### Monitoring
- [ ] Check logs for:
  - ✅ Success indicators
  - ❌ Error indicators
  - ⚠️  Warning indicators
  - 📝 Session indicators
  - 🧠 Intent indicators

### Deployment
- [ ] Environment variables documented
- [ ] Migration script tested
- [ ] Rollback plan prepared
- [ ] Health check endpoints working

```bash
# Health check
curl http://localhost:8000/health
# Expected: All services "ok"
```

---

## 🐛 Common Issues & Solutions

### Issue: "Redis connection failed"
**Solution:**
```bash
docker-compose -f docker-compose.dev.yml up redis -d
# Wait 5 seconds, then retry
```

### Issue: "Qdrant collection not found"
**Solution:**
```bash
# Qdrant creates collections automatically
# Just ensure Qdrant is running:
docker-compose -f docker-compose.dev.yml up qdrant -d
```

### Issue: "Migration failed"
**Solution:**
```bash
# Check Supabase connection
python -c "from clients.supabase_client import supabase_client; print(supabase_client.admin.table('users').select('id').limit(1).execute())"

# If works, re-run migration:
cd backend && python scripts/apply_migrations.py
```

### Issue: "Datetime parser returns wrong timezone"
**Solution:**
```bash
# Verify env var:
echo $DEFAULT_TIMEZONE
# Should be: Asia/Karachi

# Restart backend after setting
```

### Issue: "Sessions not persisting"
**Solution:**
```bash
# Check Redis TTL setting:
echo $REDIS_SESSION_TTL
# Should be: 604800 (or your custom value)

# Test Redis write:
redis-cli SET test_key test_value EX 10
redis-cli GET test_key
# Should return: test_value
```

### Issue: "Clarification not working"
**Solution:**
```python
# Test confidence threshold:
from config import settings
print(settings.confidence_threshold)
# Should be: 0.7

# Lower threshold if needed:
# CONFIDENCE_THRESHOLD=0.5 in .env
```

---

## 📈 Success Metrics

After deployment, monitor:

1. **Clarification Rate**
   ```sql
   SELECT 
       COUNT(CASE WHEN session_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as clarification_rate
   FROM calendar_events
   WHERE created_at > NOW() - INTERVAL '24 hours';
   -- Target: < 30% need clarification
   ```

2. **Parse Confidence**
   ```sql
   SELECT 
       AVG(confidence_score) as avg_confidence,
       MIN(confidence_score) as min_confidence,
       MAX(confidence_score) as max_confidence
   FROM calendar_events
   WHERE created_at > NOW() - INTERVAL '24 hours';
   -- Target: avg > 0.8
   ```

3. **Session Completion Rate**
   ```sql
   SELECT 
       COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as completion_rate
   FROM sessions
   WHERE created_at > NOW() - INTERVAL '24 hours';
   -- Target: > 85% complete
   ```

4. **Response Time**
   - Monitor logs for processing times
   - Target: < 2 seconds end-to-end

---

## ✅ Final Sign-Off

Before deploying to production:

- [ ] All functional tests passing
- [ ] Integration tests passing
- [ ] Environment variables set in production
- [ ] Migrations run successfully
- [ ] Redis and Qdrant accessible
- [ ] Monitoring and logging configured
- [ ] Rollback plan documented
- [ ] Team trained on new features

---

## 📞 Post-Deployment Support

**Monitor these for 48 hours:**
1. Error rates in logs
2. Session creation/completion rates
3. User feedback on clarifications
4. Timezone correctness
5. Google Calendar sync success rate

**Key Log Patterns to Watch:**
```bash
# Success pattern
grep "✅ Stored resolved calendar event" logs/backend.log

# Error pattern
grep "❌" logs/backend.log

# Clarification pattern
grep "📝 Created clarification session" logs/backend.log

# Session issues
grep "⚠️" logs/backend.log | grep -i session
```

---

**Verification Date:** _____________

**Verified By:** _____________

**Production Deploy Date:** _____________

**Status:** ⬜ Ready for Production | ⬜ Issues Found | ⬜ Needs Review

