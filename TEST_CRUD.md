# 🧪 CRUD Operations Testing Guide

## API Endpoints Available

### 📊 Businesses

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/finance/businesses` | List all businesses with stats |
| POST | `/finance/businesses` | Create new business |
| PUT | `/finance/businesses/{id}` | Update business |
| DELETE | `/finance/businesses/{id}` | Delete business |

### 💰 Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/finance/transactions` | List transactions (with filters) |
| GET | `/finance/transactions/{id}` | Get single transaction |
| POST | `/finance/transactions` | Create transaction |
| PUT | `/finance/transactions/{id}` | Update transaction |
| DELETE | `/finance/transactions/{id}` | Delete transaction |

### 📈 Loans

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/finance/loans` | List loans |
| POST | `/finance/loans` | Create loan |
| POST | `/finance/loans/{id}/repay` | Record repayment |

---

## 🧪 Manual Testing with cURL

### Test 1: Get All Businesses

```bash
curl https://zyana-backend.onrender.com/finance/businesses
```

**Expected Response**:
```json
[
  {
    "id": 1,
    "name": "Vidify",
    "slug": "vidify",
    "type": "video_production",
    "balance": 0,
    "revenue": 0,
    "expenses": 0
  },
  ...
]
```

### Test 2: Create a Business

```bash
curl -X POST "https://zyana-backend.onrender.com/finance/businesses?name=TestBusiness&slug=test-business&type=retail&description=Test%20Description"
```

**Expected Response**:
```json
{
  "success": true,
  "message": "✅ Created business: TestBusiness",
  "data": { ... }
}
```

### Test 3: Create a Transaction

```bash
curl -X POST "https://zyana-backend.onrender.com/finance/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": 1,
    "type": "income",
    "amount": 50000,
    "currency": "PKR",
    "category": "Sales",
    "person": "Ahmad",
    "date": "2024-01-20",
    "description": "Video production payment"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "✅ Recorded PKR 50000.0 income",
  "data": { ... }
}
```

### Test 4: Get Transactions with Filters

```bash
# Get all income transactions
curl "https://zyana-backend.onrender.com/finance/transactions?type=income&limit=10"

# Get transactions for specific business
curl "https://zyana-backend.onrender.com/finance/transactions?business_id=1"

# Get transactions by person
curl "https://zyana-backend.onrender.com/finance/transactions?person=Ahmad"
```

### Test 5: Update a Business

```bash
curl -X PUT "https://zyana-backend.onrender.com/finance/businesses/1?name=Vidify%20Studio&type=video_production&description=Updated%20description"
```

### Test 6: Delete a Transaction

```bash
curl -X DELETE "https://zyana-backend.onrender.com/finance/transactions/1"
```

---

## 🌐 Testing with Browser Console

Visit https://zyana-dashboard.vercel.app/ and open Console (F12), then run:

### Test Backend Connection

```javascript
const API_URL = 'https://zyana-backend.onrender.com';

// Test 1: Health check
fetch(`${API_URL}/health`)
  .then(r => r.json())
  .then(d => console.log('✅ Health:', d))
  .catch(e => console.error('❌ Error:', e));

// Test 2: Get businesses
fetch(`${API_URL}/finance/businesses`)
  .then(r => r.json())
  .then(d => console.log('✅ Businesses:', d))
  .catch(e => console.error('❌ Error:', e));

// Test 3: Create a transaction
fetch(`${API_URL}/finance/transactions`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    business_id: 1,
    type: 'income',
    amount: 25000,
    currency: 'PKR',
    category: 'Sales',
    date: '2024-01-25',
    description: 'Test transaction'
  })
})
  .then(r => r.json())
  .then(d => console.log('✅ Created:', d))
  .catch(e => console.error('❌ Error:', e));
```

---

## 🎨 Testing with Frontend UI

### 1. Test Business Management

1. **Visit**: https://zyana-dashboard.vercel.app/businesses
2. **Actions to Test**:
   - ✅ View existing businesses
   - ✅ Click "Add Business" and create new one
   - ✅ Click edit icon and update a business
   - ✅ Click delete icon and remove a business
   - ✅ Click "View Details" to see business page

### 2. Test Transaction Management

1. **Visit**: https://zyana-dashboard.vercel.app/transactions
2. **Actions to Test**:
   - ✅ View transaction list
   - ✅ Filter by type (income/expense)
   - ✅ Filter by business
   - ✅ Add new transaction
   - ✅ View transaction details

### 3. Test Dashboard Integration

1. **Visit**: https://zyana-dashboard.vercel.app/
2. **Verify**:
   - ✅ Stats cards show real data (not N/A)
   - ✅ Business list shows your businesses
   - ✅ Clicking business opens detail page
   - ✅ Quick actions work

---

## ✅ Test Scenarios

### Scenario 1: Complete Business Lifecycle

```
1. Create business "Coffee Shop"
2. Add income transaction: "Coffee Sales" +5000 PKR
3. Add expense transaction: "Coffee Beans" -1500 PKR
4. Check dashboard → Balance should be 3500 PKR
5. Edit business name to "Coffee House"
6. Delete the expense transaction
7. Check dashboard → Balance should be 5000 PKR
8. Delete the business
```

### Scenario 2: Multiple Businesses

```
1. Create 3 businesses: Shop1, Shop2, Shop3
2. Add 2 transactions to each business
3. Dashboard should show total across all businesses
4. Filter transactions by business_id
5. Verify each business shows correct balance
```

### Scenario 3: Transaction Filters

```
1. Add 10 transactions (5 income, 5 expense)
2. Filter by type: income → should show only 5
3. Filter by type: expense → should show only 5
4. Filter by date range
5. Filter by person
```

---

## 🐛 Common Issues & Solutions

### Issue: 404 Not Found
**Cause**: Endpoint URL is wrong or backend is down  
**Solution**: Verify backend URL and check Render deployment status

### Issue: 500 Internal Server Error
**Cause**: Database not configured or query failed  
**Solution**: Check Supabase connection and run `SUPABASE_SETUP.sql`

### Issue: CORS Error
**Cause**: Backend CORS not configured  
**Solution**: Already configured in backend, check browser console for details

### Issue: Data Not Showing
**Cause**: Frontend env variable not set  
**Solution**: Add `NEXT_PUBLIC_API_URL` in Vercel and redeploy

### Issue: RLS Policy Block
**Cause**: Row Level Security blocking access  
**Solution**: SQL script already has public policies for development

---

## 📈 Performance Testing

### Test Database Performance

```sql
-- Run in Supabase SQL Editor

-- Check table counts
SELECT 'businesses' as table_name, COUNT(*) as count FROM businesses
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'loans', COUNT(*) FROM loans;

-- Check business balances view
SELECT * FROM business_balances;

-- Test transaction query performance
EXPLAIN ANALYZE
SELECT * FROM transactions 
WHERE business_id = 1 
ORDER BY date DESC 
LIMIT 50;
```

---

## 🎯 Success Criteria

Your CRUD operations are working perfectly when:

- ✅ All GET requests return data (not empty arrays)
- ✅ POST requests create new records
- ✅ PUT requests update existing records
- ✅ DELETE requests remove records
- ✅ Dashboard shows real data from database
- ✅ No console errors in browser
- ✅ All UI buttons and forms work
- ✅ Data persists after page refresh
- ✅ Multiple users can access the same data

---

## 🚀 Next Steps

Once CRUD is working:

1. **Add Authentication**: Implement user login with Supabase Auth
2. **Add Validation**: Server-side validation for all inputs
3. **Add Error Handling**: Better error messages for users
4. **Add Loading States**: Show spinners during API calls
5. **Add Pagination**: Handle large datasets efficiently
6. **Add Search**: Full-text search on transactions
7. **Add Reports**: Generate PDF/Excel reports
8. **Add Notifications**: Real-time updates via webhooks

Happy Testing! 🎉

