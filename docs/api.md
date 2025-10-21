# Zyana API Documentation

Base URL: `http://localhost:8000`

API documentation is also available via Swagger UI at: `http://localhost:8000/docs`

## Authentication

Most endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_token>
```

For development, you can use the service key or create a test token.

## Endpoints

### Health & Status

#### GET /
Root endpoint - API health check

**Response:**
```json
{
  "status": "online",
  "service": "Zyana AI Backend",
  "version": "1.0.0",
  "environment": "development"
}
```

#### GET /health
Detailed health check

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "redis": "ok",
    "qdrant": "ok",
    "fal_ai": "ok"
  }
}
```

---

### Webhook

#### POST /webhook/message
Receive messages from any platform

**Request Body:**
```json
{
  "user_id": "string",
  "message": "I lent Ahmad Rs 10,000 from Vidify",
  "platform": "telegram",
  "metadata": {}
}
```

**Response:**
```json
{
  "status": "success",
  "message": "✅ Recorded loan: PKR 10,000 to Ahmad\nBusiness: Vidify\nDate: 2025-10-21",
  "data": {
    "id": 123,
    "amount": 10000,
    "person": "Ahmad"
  }
}
```

#### POST /webhook/telegram
Telegram-specific webhook

**Request Body:** Telegram Update object

**Response:**
```json
{
  "ok": true
}
```

---

### Finance

#### POST /finance/transactions
Create a new transaction

**Request Body:**
```json
{
  "business_id": 1,
  "type": "expense",
  "amount": 15000,
  "currency": "PKR",
  "category": "software",
  "person": null,
  "date": "2025-10-21",
  "description": "Adobe subscription",
  "tags": ["expense", "software"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "✅ Recorded expense: PKR 15,000",
  "data": {
    "id": 456,
    "business_id": 1,
    "type": "expense",
    "amount": 15000,
    "currency": "PKR",
    "created_at": "2025-10-21T12:00:00Z"
  }
}
```

#### GET /finance/transactions
List transactions with optional filters

**Query Parameters:**
- `business_id` (optional): Filter by business
- `type` (optional): Filter by type (income/expense/transfer)
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `person` (optional): Filter by person name
- `limit` (optional): Max results (default: 50, max: 200)

**Response:**
```json
[
  {
    "id": 1,
    "business_id": 1,
    "business_name": "Vidify",
    "type": "income",
    "amount": 50000,
    "currency": "PKR",
    "category": "sales",
    "person": null,
    "date": "2025-10-20",
    "description": "Client payment",
    "tags": ["income"],
    "created_at": "2025-10-20T10:00:00Z"
  }
]
```

#### GET /finance/transactions/{transaction_id}
Get a specific transaction

**Response:** Single transaction object

#### POST /finance/loans
Create a loan record

**Request Body:**
```json
{
  "business_id": 1,
  "person": "Ahmad",
  "amount": 10000,
  "currency": "PKR",
  "date": "2025-10-21",
  "description": "Loan to Ahmad",
  "status": "active"
}
```

**Response:**
```json
{
  "success": true,
  "message": "✅ Recorded loan: PKR 10,000 to Ahmad",
  "data": {
    "id": 789,
    "person": "Ahmad",
    "amount": 10000,
    "remaining_amount": 10000,
    "status": "active"
  }
}
```

#### GET /finance/loans
List loans

**Query Parameters:**
- `business_id` (optional)
- `person` (optional)
- `status` (optional): active/partially_paid/paid
- `limit` (optional)

**Response:** Array of loan objects

#### POST /finance/loans/{loan_id}/repay
Record a loan repayment

**Query Parameters:**
- `amount`: Repayment amount
- `repayment_date` (optional): Date of repayment

**Response:**
```json
{
  "success": true,
  "message": "✅ Repayment recorded: PKR 5,000 from Ahmad\nRemaining: PKR 5,000",
  "data": {
    "id": 999,
    "loan_id": 789,
    "amount": 5000,
    "date": "2025-10-21"
  }
}
```

#### GET /finance/summary/{business_id}
Get financial summary for a business

**Query Parameters:**
- `start_date` (optional)
- `end_date` (optional)

**Response:**
```json
{
  "business_id": 1,
  "total_income": 150000,
  "total_expenses": 45000,
  "balance": 105000,
  "period": {
    "start": "2025-10-01",
    "end": "2025-10-31"
  }
}
```

---

### Calendar

#### POST /calendar/events
Create a calendar event

**Request Body:**
```json
{
  "user_id": 1,
  "title": "Team Meeting",
  "start_time": "2025-10-22T15:00:00Z",
  "end_time": "2025-10-22T16:00:00Z",
  "description": "Weekly team standup",
  "location": "Office"
}
```

**Response:**
```json
{
  "success": true,
  "message": "✅ Created 'Team Meeting' on 2025-10-22 at 3:00 PM",
  "data": {
    "id": 111,
    "title": "Team Meeting",
    "google_event_id": "abc123",
    "created_at": "2025-10-21T12:00:00Z"
  }
}
```

#### GET /calendar/events
List calendar events

**Query Parameters:**
- `start_time` (optional): Filter events after this time
- `end_time` (optional): Filter events before this time
- `limit` (optional): Max results (default: 50)

**Response:** Array of event objects

#### GET /calendar/events/{event_id}
Get a specific event

**Response:** Single event object

#### POST /calendar/sync
Trigger Google Calendar sync

**Response:**
```json
{
  "success": true,
  "message": "Synced 5 events from Google Calendar",
  "data": {
    "imported": 5,
    "updated": 2,
    "skipped": 0
  }
}
```

#### GET /calendar/auth/google
Get Google OAuth authorization URL

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

#### GET /calendar/auth/google/callback
Handle Google OAuth callback

**Query Parameters:**
- `code`: Authorization code from Google

**Response:**
```json
{
  "success": true,
  "message": "✅ Google Calendar connected successfully!"
}
```

---

### Memory

#### POST /memory/search
Search personal memory using semantic search

**Request Body:**
```json
{
  "query": "When did I last pay Ahmad?",
  "limit": 5,
  "filters": {}
}
```

**Response:**
```json
{
  "query": "When did I last pay Ahmad?",
  "results": [
    {
      "id": "uuid-123",
      "snippet": "Repayment from Ahmad: PKR 5,000",
      "table": "loan_repayments",
      "date": "2025-10-21",
      "business": "Vidify",
      "score": 0.95
    }
  ],
  "summary": "You received a repayment of PKR 5,000 from Ahmad on October 21, 2025 for Vidify. The previous loan was PKR 10,000 on October 15.",
  "total_found": 1
}
```

#### POST /memory/embed
Manually embed content into memory

**Request Body:**
```json
{
  "content": "Important note about project deadline",
  "metadata": {
    "table": "notes",
    "date": "2025-10-21",
    "business": "Vidify"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "✅ Memory embedded successfully"
}
```

#### GET /memory/summaries
List daily memory summaries

**Query Parameters:**
- `limit` (optional): Max results (default: 30)

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "date": "2025-10-21",
    "summary": "Today you recorded income of PKR 50,000 from Vidify and scheduled a team meeting for tomorrow.",
    "created_at": "2025-10-22T02:00:00Z"
  }
]
```

---

### Profile

#### GET /profile/habits
Get user's habit profile

**Query Parameters:**
- `user_id` (optional): User ID (default: 1)

**Response:**
```json
{
  "user_id": 1,
  "habits": {
    "preferred_currency": "PKR",
    "default_business": "Vidify",
    "frequent_contact": "Ahmad"
  },
  "details": [
    {
      "id": 1,
      "key": "preferred_currency",
      "value": "PKR",
      "confidence_score": 0.95,
      "occurrences": 15
    }
  ]
}
```

#### POST /profile/habits
Update or create a habit

**Query Parameters:**
- `key`: Habit key
- `value`: Habit value
- `user_id` (optional): User ID

**Response:**
```json
{
  "success": true,
  "message": "✅ Updated preference: preferred_currency",
  "data": {
    "id": 1,
    "key": "preferred_currency",
    "value": "PKR"
  }
}
```

#### DELETE /profile/habits/{key}
Delete a habit

**Query Parameters:**
- `user_id` (optional): User ID

**Response:**
```json
{
  "success": true,
  "message": "✅ Deleted preference: preferred_currency"
}
```

#### GET /profile/preferences
Get user preferences

**Response:**
```json
{
  "language": "en",
  "timezone": "Asia/Karachi",
  "currency": "PKR",
  "notifications": true
}
```

#### POST /profile/preferences
Update user preferences

**Request Body:**
```json
{
  "language": "en",
  "timezone": "Asia/Karachi",
  "currency": "PKR"
}
```

**Response:**
```json
{
  "success": true,
  "message": "✅ Preferences updated"
}
```

---

### Agent

#### POST /agent/execute
Execute an agent action

**Request Body:**
```json
{
  "intent": "transaction",
  "business": "Vidify",
  "type": "expense",
  "amount": 15000,
  "currency": "PKR",
  "raw_text": "Paid 15000 for software"
}
```

**Response:**
```json
{
  "success": true,
  "message": "✅ Recorded expense: PKR 15,000",
  "data": {},
  "next_action": null
}
```

#### GET /agent/status
Get agent system status

**Response:**
```json
{
  "status": "online",
  "agents": {
    "finance": "active",
    "calendar": "active",
    "memory": "active",
    "video": "active",
    "habit_learner": "active"
  }
}
```

---

## Error Responses

All endpoints may return error responses in this format:

```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting

Current limits (subject to change):
- 100 requests per minute per user
- 1000 requests per hour per user

Exceeded limits return `429 Too Many Requests`.

## Webhooks

Zyana can send webhooks to your endpoints for:
- Transaction created
- Goal achieved
- Report generated

Configure webhooks in user preferences.

## SDKs & Libraries

- **Python**: Use `requests` or `httpx`
- **JavaScript**: Use `axios` or `fetch`
- **TypeScript**: See `frontend/lib/api.ts` for reference implementation

## Support

For API questions or issues:
- Check Swagger docs: `/docs`
- Review examples in codebase
- Open GitHub issue

