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
async def create_business(name: str, slug: str, type: str = "general", description: str = None):
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
        result = supabase_client.admin.table("businesses").insert({
            "name": name,
            "slug": slug,
            "type": type,
            "description": description
        }).execute()
        
        logger.info(f"Created business: {name}")
        
        return {
            "success": True,
            "message": f"✅ Created business: {name}",
            "data": result.data[0] if result.data else {}
        }
        
    except Exception as e:
        logger.error(f"Error creating business: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/businesses/{business_id}", response_model=dict)
async def update_business(business_id: int, name: str = None, type: str = None, description: str = None):
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
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if type is not None:
            update_data["type"] = type
        if description is not None:
            update_data["description"] = description
        
        result = supabase_client.admin.table("businesses").update(
            update_data
        ).eq("id", business_id).execute()
        
        logger.info(f"Updated business {business_id}")
        
        return {
            "success": True,
            "message": "✅ Business updated",
            "data": result.data[0] if result.data else {}
        }
        
    except Exception as e:
        logger.error(f"Error updating business: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/businesses/{business_id}", response_model=dict)
async def delete_business(business_id: int):
    """Delete a business.
    
    Args:
        business_id: Business ID
        
    Returns:
        Success status
    """
    try:
        supabase_client.admin.table("businesses").delete().eq("id", business_id).execute()
        
        logger.info(f"Deleted business {business_id}")
        
        return {
            "success": True,
            "message": "✅ Business deleted"
        }
        
    except Exception as e:
        logger.error(f"Error deleting business: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

