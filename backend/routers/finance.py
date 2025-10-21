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

