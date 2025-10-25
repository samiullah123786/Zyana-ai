"""Invoice management API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
import logging

from agents.invoice_tracker import invoice_tracker

logger = logging.getLogger(__name__)
router = APIRouter()


class InvoiceCreate(BaseModel):
    """Invoice creation request."""
    client_id: int
    business_id: int
    amount: float = Field(gt=0)
    due_date: date
    currency: str = "PKR"
    notes: Optional[str] = None


class InvoicePayment(BaseModel):
    """Invoice payment recording request."""
    payment_date: Optional[date] = None


@router.post("/create")
async def create_invoice(invoice: InvoiceCreate):
    """Create a new invoice.
    
    Args:
        invoice: Invoice creation data
        
    Returns:
        Created invoice data
    """
    try:
        # TODO: Get user_id from authentication
        user_id = 1
        
        result = await invoice_tracker.create_invoice(
            client_id=invoice.client_id,
            amount=invoice.amount,
            due_date=invoice.due_date,
            business_id=invoice.business_id,
            user_id=user_id,
            currency=invoice.currency,
            notes=invoice.notes
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in create_invoice endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_invoices(
    business_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
):
    """List invoices with optional filters.
    
    Args:
        business_id: Filter by business
        status: Filter by status (pending, paid, overdue)
        
    Returns:
        List of invoices
    """
    try:
        # TODO: Get user_id from authentication
        user_id = 1
        
        invoices = await invoice_tracker.list_invoices(
            business_id=business_id,
            status=status,
            user_id=user_id
        )
        
        return {
            "success": True,
            "data": invoices,
            "count": len(invoices)
        }
        
    except Exception as e:
        logger.error(f"Error in list_invoices endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overdue")
async def get_overdue_invoices():
    """Get list of overdue invoices.
    
    Returns:
        List of overdue invoices
    """
    try:
        # TODO: Get user_id from authentication
        user_id = 1
        
        invoices = await invoice_tracker.get_overdue_invoices(user_id=user_id)
        
        return {
            "success": True,
            "data": invoices,
            "count": len(invoices)
        }
        
    except Exception as e:
        logger.error(f"Error in get_overdue_invoices endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: int):
    """Get single invoice by ID.
    
    Args:
        invoice_id: Invoice ID
        
    Returns:
        Invoice data
    """
    try:
        invoice = await invoice_tracker.get_invoice(invoice_id)
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return {
            "success": True,
            "data": invoice
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_invoice endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{invoice_id}/pay")
async def mark_invoice_paid(invoice_id: int, payment: InvoicePayment):
    """Mark invoice as paid.
    
    Args:
        invoice_id: Invoice ID
        payment: Payment data
        
    Returns:
        Updated invoice
    """
    try:
        result = await invoice_tracker.record_payment(
            invoice_id=invoice_id,
            payment_date=payment.payment_date
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mark_invoice_paid endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{year}/{month}")
async def get_monthly_report(year: int, month: int):
    """Generate monthly financial report.
    
    Args:
        year: Year
        month: Month (1-12)
        
    Returns:
        Monthly report
    """
    try:
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        # TODO: Get user_id from authentication
        user_id = 1
        
        result = await invoice_tracker.generate_monthly_report(
            user_id=user_id,
            month=month,
            year=year
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_monthly_report endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

