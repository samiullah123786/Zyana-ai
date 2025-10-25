"""Finance router for transaction and loan management."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import date, datetime
import logging

from models.schemas import (
    TransactionCreate, TransactionResponse,
    LoanCreate, LoanResponse
)
from clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/transactions", response_model=dict)
async def create_transaction(transaction: TransactionCreate):
    """Create a new transaction.
    
    Args:
        transaction: Transaction data
        
    Returns:
        Created transaction with ID
    """
    try:
        # Insert transaction
        result = supabase_client.admin.table("transactions").insert({
            "business_id": transaction.business_id,
            "type": transaction.type,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "category": transaction.category,
            "person": transaction.person,
            "date": transaction.date.isoformat(),
            "description": transaction.description,
            "tags": transaction.tags,
            "user_id": 1  # TODO: Get from auth context
        }).execute()
        
        logger.info(f"Created transaction: {result.data}")
        
        return {
            "success": True,
            "message": f"✅ Recorded {transaction.currency} {transaction.amount} {transaction.type}",
            "data": result.data[0] if result.data else {}
        }
        
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_model=List[dict])
async def list_transactions(
    business_id: Optional[int] = None,
    type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    person: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """List transactions with optional filters.
    
    Args:
        business_id: Filter by business
        type: Filter by transaction type
        start_date: Filter from date
        end_date: Filter to date
        person: Filter by person
        limit: Maximum results
        
    Returns:
        List of transactions
    """
    try:
        query = supabase_client.admin.table("transactions").select(
            "*, businesses(name)"
        )
        
        if business_id:
            query = query.eq("business_id", business_id)
        if type:
            query = query.eq("type", type)
        if start_date:
            query = query.gte("date", start_date.isoformat())
        if end_date:
            query = query.lte("date", end_date.isoformat())
        if person:
            query = query.ilike("person", f"%{person}%")
        
        result = query.order("date", desc=True).limit(limit).execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"Error listing transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{transaction_id}", response_model=dict)
async def get_transaction(transaction_id: int):
    """Get a specific transaction by ID.
    
    Args:
        transaction_id: Transaction ID
        
    Returns:
        Transaction details
    """
    try:
        result = supabase_client.admin.table("transactions").select(
            "*, businesses(name)"
        ).eq("id", transaction_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return result.data
        
    except Exception as e:
        logger.error(f"Error getting transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/transactions/{transaction_id}", response_model=dict)
async def update_transaction(transaction_id: int, transaction: TransactionCreate):
    """Update a transaction.
    
    Args:
        transaction_id: Transaction ID
        transaction: Updated transaction data
        
    Returns:
        Updated transaction
    """
    try:
        result = supabase_client.admin.table("transactions").update({
            "business_id": transaction.business_id,
            "type": transaction.type,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "category": transaction.category,
            "person": transaction.person,
            "date": transaction.date.isoformat(),
            "description": transaction.description,
            "tags": transaction.tags
        }).eq("id", transaction_id).execute()
        
        logger.info(f"Updated transaction {transaction_id}")
        
        return {
            "success": True,
            "message": "✅ Transaction updated",
            "data": result.data[0] if result.data else {}
        }
        
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/transactions/{transaction_id}", response_model=dict)
async def delete_transaction(transaction_id: int):
    """Delete a transaction.
    
    Args:
        transaction_id: Transaction ID
        
    Returns:
        Success status
    """
    try:
        supabase_client.admin.table("transactions").delete().eq("id", transaction_id).execute()
        
        logger.info(f"Deleted transaction {transaction_id}")
        
        return {
            "success": True,
            "message": "✅ Transaction deleted"
        }
        
    except Exception as e:
        logger.error(f"Error deleting transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loans", response_model=dict)
async def create_loan(loan: LoanCreate):
    """Create a new loan record.
    
    Args:
        loan: Loan data
        
    Returns:
        Created loan with ID
    """
    try:
        result = supabase_client.admin.table("loans").insert({
            "business_id": loan.business_id,
            "person": loan.person,
            "amount": float(loan.amount),
            "currency": loan.currency,
            "date": loan.date.isoformat(),
            "status": loan.status,
            "remaining_amount": float(loan.amount),
            "description": loan.description,
            "user_id": 1  # TODO: Get from auth context
        }).execute()
        
        logger.info(f"Created loan: {result.data}")
        
        return {
            "success": True,
            "message": f"✅ Recorded loan: {loan.currency} {loan.amount} to {loan.person}",
            "data": result.data[0] if result.data else {}
        }
        
    except Exception as e:
        logger.error(f"Error creating loan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans", response_model=List[dict])
async def list_loans(
    business_id: Optional[int] = None,
    person: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """List loans with optional filters.
    
    Args:
        business_id: Filter by business
        person: Filter by person
        status: Filter by status (active, partially_paid, paid)
        limit: Maximum results
        
    Returns:
        List of loans
    """
    try:
        query = supabase_client.admin.table("loans").select(
            "*, businesses(name)"
        )
        
        if business_id:
            query = query.eq("business_id", business_id)
        if person:
            query = query.ilike("person", f"%{person}%")
        if status:
            query = query.eq("status", status)
        
        result = query.order("date", desc=True).limit(limit).execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"Error listing loans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loans/{loan_id}/repay", response_model=dict)
async def record_repayment(loan_id: int, amount: float, repayment_date: Optional[date] = None):
    """Record a loan repayment.
    
    Args:
        loan_id: Loan ID
        amount: Repayment amount
        repayment_date: Date of repayment (defaults to today)
        
    Returns:
        Updated loan details
    """
    try:
        # Get loan
        loan_result = supabase_client.admin.table("loans").select("*").eq(
            "id", loan_id
        ).single().execute()
        
        if not loan_result.data:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        loan = loan_result.data
        
        # Create repayment record
        repayment_result = supabase_client.admin.table("loan_repayments").insert({
            "loan_id": loan_id,
            "amount": amount,
            "date": (repayment_date or date.today()).isoformat()
        }).execute()
        
        # Update loan
        new_remaining = loan["remaining_amount"] - amount
        new_status = "paid" if new_remaining <= 0 else "partially_paid"
        
        update_result = supabase_client.admin.table("loans").update({
            "remaining_amount": max(0, new_remaining),
            "status": new_status
        }).eq("id", loan_id).execute()
        
        logger.info(f"Recorded repayment: {amount} for loan {loan_id}")
        
        return {
            "success": True,
            "message": f"✅ Repayment recorded: {loan['currency']} {amount}. Remaining: {max(0, new_remaining)}",
            "data": update_result.data[0] if update_result.data else {}
        }
        
    except Exception as e:
        logger.error(f"Error recording repayment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/businesses", response_model=List[dict])
async def list_businesses():
    """Get all businesses with their financial summaries.
    
    Returns:
        List of businesses with balance, revenue, expenses
    """
    try:
        # Get all businesses
        businesses_result = supabase_client.admin.table("businesses").select("*").execute()
        
        if not businesses_result.data:
            return []
        
        businesses_with_stats = []
        
        for business in businesses_result.data:
            # Get transactions for this business
            transactions_result = supabase_client.admin.table("transactions").select(
                "type, amount"
            ).eq("business_id", business["id"]).execute()
            
            total_income = sum(
                t["amount"] for t in transactions_result.data if t["type"] == "income"
            )
            total_expenses = sum(
                t["amount"] for t in transactions_result.data if t["type"] == "expense"
            )
            
            businesses_with_stats.append({
                "id": business["id"],
                "name": business["name"],
                "slug": business["slug"],
                "type": business.get("type"),
                "description": business.get("description"),
                "balance": total_income - total_expenses,
                "revenue": total_income,
                "expenses": total_expenses,
                "created_at": business.get("created_at")
            })
        
        return businesses_with_stats
        
    except Exception as e:
        logger.error(f"Error listing businesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/businesses", response_model=dict)
async def create_business(
    name: str = Query(..., description="Business name"),
    slug: str = Query(..., description="URL-friendly slug"),
    type: str = Query(default="general", description="Business type"),
    description: Optional[str] = Query(default=None, description="Business description")
):
    """Create a new business.
    
    Args:
        name: Business name
        slug: URL-friendly slug
        type: Business type
        description: Business description
        
    Returns:
        Created business
    """
    try:
        logger.info(f"Creating business: name={name}, slug={slug}, type={type}, description={description}")
        
        # Check if slug already exists
        existing = supabase_client.admin.table("businesses").select("id").eq("slug", slug).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail=f"Business with slug '{slug}' already exists")
        
        insert_data = {
            "name": name,
            "slug": slug,
            "type": type,
        }
        
        if description is not None:
            insert_data["description"] = description
        
        result = supabase_client.admin.table("businesses").insert(insert_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create business - no data returned")
        
        logger.info(f"Created business: {name} (ID: {result.data[0].get('id')})")
        
        return {
            "success": True,
            "message": f"✅ Created business: {name}",
            "data": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating business: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/businesses/{business_id}", response_model=dict)
async def update_business(
    business_id: int,
    name: Optional[str] = Query(default=None, description="New business name"),
    type: Optional[str] = Query(default=None, description="New business type"),
    description: Optional[str] = Query(default=None, description="New description")
):
    """Update a business.
    
    Args:
        business_id: Business ID
        name: New business name
        type: New business type
        description: New description
        
    Returns:
        Updated business
    """
    try:
        logger.info(f"Updating business {business_id}: name={name}, type={type}, description={description}")
        
        # Check if business exists
        existing = supabase_client.admin.table("businesses").select("id").eq("id", business_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail=f"Business with ID {business_id} not found")
        
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if type is not None:
            update_data["type"] = type
        if description is not None:
            update_data["description"] = description
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided to update")
        
        result = supabase_client.admin.table("businesses").update(
            update_data
        ).eq("id", business_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update business - no data returned")
        
        logger.info(f"Updated business {business_id} successfully")
        
        return {
            "success": True,
            "message": "✅ Business updated",
            "data": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating business: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/businesses/{business_id}", response_model=dict)
async def delete_business(business_id: int):
    """Delete a business and all associated transactions.
    
    Args:
        business_id: Business ID
        
    Returns:
        Success status
    """
    try:
        logger.info(f"Deleting business {business_id}")
        
        # Check if business exists
        existing = supabase_client.admin.table("businesses").select("id, name").eq("id", business_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail=f"Business with ID {business_id} not found")
        
        business_name = existing.data[0].get("name")
        
        # Delete associated transactions first (if cascade delete is not set up)
        try:
            supabase_client.admin.table("transactions").delete().eq("business_id", business_id).execute()
            logger.info(f"Deleted transactions for business {business_id}")
        except Exception as e:
            logger.warning(f"Could not delete transactions: {e}")
        
        # Delete the business
        result = supabase_client.admin.table("businesses").delete().eq("id", business_id).execute()
        
        logger.info(f"Deleted business {business_id} ({business_name})")
        
        return {
            "success": True,
            "message": f"✅ Business '{business_name}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting business: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/summary/{business_id}", response_model=dict)
async def get_business_summary(
    business_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """Get financial summary for a business.
    
    Args:
        business_id: Business ID
        start_date: Start date for summary
        end_date: End date for summary
        
    Returns:
        Summary with income, expenses, and balance
    """
    try:
        query = supabase_client.admin.table("transactions").select(
            "type, amount"
        ).eq("business_id", business_id)
        
        if start_date:
            query = query.gte("date", start_date.isoformat())
        if end_date:
            query = query.lte("date", end_date.isoformat())
        
        result = query.execute()
        
        total_income = sum(
            t["amount"] for t in result.data if t["type"] == "income"
        )
        total_expenses = sum(
            t["amount"] for t in result.data if t["type"] == "expense"
        )
        
        return {
            "business_id": business_id,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": total_income - total_expenses,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/monthly-trend", response_model=List[dict])
async def get_monthly_trend(
    business_id: Optional[int] = None,
    months: int = Query(default=6, le=24, description="Number of months to include")
):
    """Get monthly revenue and expenses trend.
    
    Args:
        business_id: Optional business ID filter
        months: Number of months to include (default 6, max 24)
        
    Returns:
        List of monthly data with revenue and expenses
    """
    try:
        from datetime import datetime, timedelta
        from collections import defaultdict
        import calendar
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        # Fetch transactions
        query = supabase_client.admin.table("transactions").select(
            "type, amount, date"
        ).gte("date", start_date.isoformat()).lte("date", end_date.isoformat())
        
        if business_id:
            query = query.eq("business_id", business_id)
        
        result = query.execute()
        
        # Group by month
        monthly_data = defaultdict(lambda: {"revenue": 0, "expenses": 0})
        
        for transaction in result.data:
            trans_date = datetime.fromisoformat(transaction["date"])
            month_key = trans_date.strftime("%b")
            
            if transaction["type"] == "income":
                monthly_data[month_key]["revenue"] += transaction["amount"]
            elif transaction["type"] == "expense":
                monthly_data[month_key]["expenses"] += transaction["amount"]
        
        # Format response
        response = []
        for i in range(months):
            month_date = end_date - timedelta(days=(months - i - 1) * 30)
            month_name = month_date.strftime("%b")
            response.append({
                "month": month_name,
                "revenue": monthly_data[month_name]["revenue"],
                "expenses": monthly_data[month_name]["expenses"]
            })
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting monthly trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/by-category", response_model=List[dict])
async def get_category_breakdown(
    business_id: Optional[int] = None,
    type: str = Query(default="income", regex="^(income|expense)$")
):
    """Get transaction breakdown by category.
    
    Args:
        business_id: Optional business ID filter
        type: Transaction type (income or expense)
        
    Returns:
        List of categories with totals
    """
    try:
        query = supabase_client.admin.table("transactions").select(
            "category, amount"
        ).eq("type", type)
        
        if business_id:
            query = query.eq("business_id", business_id)
        
        result = query.execute()
        
        # Group by category
        from collections import defaultdict
        category_totals = defaultdict(float)
        
        for transaction in result.data:
            category = transaction.get("category") or "Other"
            category_totals[category] += transaction["amount"]
        
        # Format response
        colors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444", "#06b6d4"]
        response = []
        for i, (category, value) in enumerate(category_totals.items()):
            response.append({
                "name": category,
                "value": value,
                "color": colors[i % len(colors)]
            })
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting category breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/recent-activities", response_model=List[dict])
async def get_recent_activities(
    business_id: Optional[int] = None,
    limit: int = Query(default=10, le=50)
):
    """Get recent financial activities.
    
    Args:
        business_id: Optional business ID filter
        limit: Maximum number of activities
        
    Returns:
        List of recent activities
    """
    try:
        from datetime import datetime
        
        query = supabase_client.admin.table("transactions").select(
            "*, businesses(name)"
        )
        
        if business_id:
            query = query.eq("business_id", business_id)
        
        result = query.order("date", desc=True).limit(limit).execute()
        
        # Format activities
        activities = []
        for transaction in result.data:
            time_diff = datetime.now() - datetime.fromisoformat(transaction["date"])
            
            if time_diff.days == 0:
                time_ago = f"{time_diff.seconds // 3600} hours ago" if time_diff.seconds >= 3600 else f"{time_diff.seconds // 60} minutes ago"
            elif time_diff.days == 1:
                time_ago = "1 day ago"
            else:
                time_ago = f"{time_diff.days} days ago"
            
            activities.append({
                "id": transaction["id"],
                "type": transaction["type"],
                "message": transaction["description"] or f"{transaction['type'].title()} transaction",
                "amount": f"{'+'if transaction['type'] == 'income' else '-'}PKR {transaction['amount']:,.0f}",
                "time": time_ago,
                "color": "text-green-600" if transaction["type"] == "income" else "text-red-600"
            })
        
        return activities
        
    except Exception as e:
        logger.error(f"Error getting recent activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/business-performance", response_model=List[dict])
async def get_business_performance():
    """Get performance comparison across all businesses.
    
    Returns:
        List of businesses with their total revenue
    """
    try:
        # Get all businesses
        businesses = supabase_client.admin.table("businesses").select("*").execute()
        
        # Calculate revenue for each business
        response = []
        for business in businesses.data:
            transactions = supabase_client.admin.table("transactions").select(
                "amount"
            ).eq("business_id", business["id"]).eq("type", "income").execute()
            
            total_revenue = sum(t["amount"] for t in transactions.data)
            
            response.append({
                "name": business["name"],
                "value": total_revenue
            })
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting business performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/dashboard-stats", response_model=dict)
async def get_dashboard_stats():
    """Get dashboard statistics with period comparisons.
    
    Returns:
        Dashboard stats with percentage changes compared to previous period
    """
    try:
        from datetime import datetime, timedelta
        
        # Calculate date ranges
        today = datetime.now()
        month_ago = today - timedelta(days=30)
        two_months_ago = today - timedelta(days=60)
        
        # Current period (last 30 days)
        current_transactions = supabase_client.admin.table("transactions").select(
            "type, amount"
        ).gte("date", month_ago.isoformat()).execute()
        
        # Previous period (30-60 days ago)
        previous_transactions = supabase_client.admin.table("transactions").select(
            "type, amount"
        ).gte("date", two_months_ago.isoformat()).lte(
            "date", month_ago.isoformat()
        ).execute()
        
        # Calculate current totals
        current_income = sum(t["amount"] for t in current_transactions.data if t["type"] == "income")
        current_expenses = sum(t["amount"] for t in current_transactions.data if t["type"] == "expense")
        
        # Calculate previous totals
        prev_income = sum(t["amount"] for t in previous_transactions.data if t["type"] == "income")
        prev_expenses = sum(t["amount"] for t in previous_transactions.data if t["type"] == "expense")
        
        # Calculate percentage changes
        revenue_change = ((current_income - prev_income) / prev_income * 100) if prev_income > 0 else 0
        expense_change = ((current_expenses - prev_expenses) / prev_expenses * 100) if prev_expenses > 0 else 0
        
        logger.info(f"Dashboard stats - Revenue: {current_income} ({revenue_change:+.1f}%), Expenses: {current_expenses} ({expense_change:+.1f}%)")
        
        return {
            "total_balance": current_income - current_expenses,
            "total_revenue": current_income,
            "total_expenses": current_expenses,
            "revenue_change": round(revenue_change, 1),
            "expense_change": round(expense_change, 1),
            "balance_change": round(revenue_change, 1)  # Simplified
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/business-stats/{business_id}", response_model=dict)
async def get_business_stats(business_id: int):
    """Get business statistics with period comparisons.
    
    Args:
        business_id: Business ID
        
    Returns:
        Business stats with percentage changes compared to previous period
    """
    try:
        from datetime import datetime, timedelta
        
        today = datetime.now()
        month_ago = today - timedelta(days=30)
        two_months_ago = today - timedelta(days=60)
        
        # Current period (last 30 days)
        current = supabase_client.admin.table("transactions").select(
            "type, amount"
        ).eq("business_id", business_id).gte("date", month_ago.isoformat()).execute()
        
        # Previous period (30-60 days ago)
        previous = supabase_client.admin.table("transactions").select(
            "type, amount"
        ).eq("business_id", business_id).gte(
            "date", two_months_ago.isoformat()
        ).lte("date", month_ago.isoformat()).execute()
        
        current_income = sum(t["amount"] for t in current.data if t["type"] == "income")
        current_expenses = sum(t["amount"] for t in current.data if t["type"] == "expense")
        prev_income = sum(t["amount"] for t in previous.data if t["type"] == "income")
        prev_expenses = sum(t["amount"] for t in previous.data if t["type"] == "expense")
        
        revenue_change = ((current_income - prev_income) / prev_income * 100) if prev_income > 0 else 0
        expense_change = ((current_expenses - prev_expenses) / prev_expenses * 100) if prev_expenses > 0 else 0
        profit_change = revenue_change - expense_change
        
        logger.info(f"Business {business_id} stats - Revenue: {revenue_change:+.1f}%, Expenses: {expense_change:+.1f}%, Profit: {profit_change:+.1f}%")
        
        return {
            "revenue_change": round(revenue_change, 1),
            "expense_change": round(expense_change, 1),
            "profit_change": round(profit_change, 1),
            "balance_change": round(revenue_change, 1)
        }
        
    except Exception as e:
        logger.error(f"Error getting business stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
