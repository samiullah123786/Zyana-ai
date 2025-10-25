"""Invoice Tracker Agent for managing client invoices and payments."""
import logging
from datetime import date, datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal

from clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class InvoiceTrackerAgent:
    """Agent for invoice and payment tracking."""
    
    async def create_invoice(
        self,
        client_id: int,
        amount: float,
        due_date: date,
        business_id: int,
        user_id: int,
        currency: str = "PKR",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new invoice.
        
        Args:
            client_id: Client ID
            amount: Invoice amount
            due_date: Payment due date
            business_id: Business ID
            user_id: User ID
            currency: Currency code
            notes: Optional notes
            
        Returns:
            Response dict with invoice data
        """
        try:
            # Generate invoice number
            invoice_number = await self._generate_invoice_number(business_id)
            
            # Insert invoice
            result = supabase_client.admin.table("invoices").insert({
                "invoice_number": invoice_number,
                "client_id": client_id,
                "business_id": business_id,
                "user_id": user_id,
                "amount": amount,
                "currency": currency,
                "due_date": due_date.isoformat(),
                "status": "pending",
                "notes": notes
            }).execute()
            
            invoice = result.data[0] if result.data else {}
            
            # Get client name
            client = await self._get_client(client_id)
            client_name = client.get("name", "Unknown") if client else "Unknown"
            
            logger.info(f"Created invoice {invoice_number} for client {client_name}")
            
            return {
                "success": True,
                "message": f"✅ Invoice #{invoice_number} created\nClient: {client_name}\nAmount: {currency} {amount:,.0f}\nDue: {due_date}",
                "data": invoice
            }
            
        except Exception as e:
            logger.error(f"Error creating invoice: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to create invoice: {str(e)}",
                "data": None
            }
    
    async def record_payment(
        self,
        invoice_id: int,
        payment_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Mark invoice as paid.
        
        Args:
            invoice_id: Invoice ID
            payment_date: Payment date (defaults to today)
            
        Returns:
            Response dict
        """
        try:
            if payment_date is None:
                payment_date = date.today()
            
            # Update invoice
            result = supabase_client.admin.table("invoices").update({
                "status": "paid",
                "payment_date": payment_date.isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", invoice_id).execute()
            
            if not result.data:
                return {
                    "success": False,
                    "message": f"Invoice #{invoice_id} not found",
                    "data": None
                }
            
            invoice = result.data[0]
            
            logger.info(f"Marked invoice {invoice['invoice_number']} as paid")
            
            return {
                "success": True,
                "message": f"✅ Invoice #{invoice['invoice_number']} marked as paid\nPayment date: {payment_date}",
                "data": invoice
            }
            
        except Exception as e:
            logger.error(f"Error recording payment: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to record payment: {str(e)}",
                "data": None
            }
    
    async def get_overdue_invoices(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of overdue invoices.
        
        Args:
            user_id: Optional user filter
            
        Returns:
            List of overdue invoices
        """
        try:
            # First update statuses
            await self._update_overdue_statuses()
            
            # Query overdue invoices
            query = supabase_client.admin.table("invoices").select(
                "*, clients(name, contact), businesses(name)"
            ).eq("status", "overdue")
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.order("due_date", desc=False).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting overdue invoices: {e}", exc_info=True)
            return []
    
    async def list_invoices(
        self,
        business_id: Optional[int] = None,
        status: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List invoices with optional filters.
        
        Args:
            business_id: Filter by business
            status: Filter by status
            user_id: Filter by user
            
        Returns:
            List of invoices
        """
        try:
            query = supabase_client.admin.table("invoices").select(
                "*, clients(name, contact, company), businesses(name)"
            )
            
            if business_id:
                query = query.eq("business_id", business_id)
            if status:
                query = query.eq("status", status)
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.order("created_at", desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error listing invoices: {e}", exc_info=True)
            return []
    
    async def get_invoice(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get single invoice by ID.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Invoice dict or None
        """
        try:
            result = supabase_client.admin.table("invoices").select(
                "*, clients(name, contact, email, company), businesses(name)"
            ).eq("id", invoice_id).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting invoice: {e}", exc_info=True)
            return None
    
    async def generate_monthly_report(
        self,
        user_id: int,
        month: int,
        year: int
    ) -> Dict[str, Any]:
        """Generate monthly financial report.
        
        Args:
            user_id: User ID
            month: Month (1-12)
            year: Year
            
        Returns:
            Report dict
        """
        try:
            # Date range
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            
            # Get invoices for the month
            result = supabase_client.admin.table("invoices").select(
                "*, clients(name), businesses(name)"
            ).eq("user_id", user_id).gte(
                "created_at", start_date.isoformat()
            ).lt(
                "created_at", end_date.isoformat()
            ).execute()
            
            invoices = result.data if result.data else []
            
            # Calculate stats
            total_invoiced = sum(float(inv["amount"]) for inv in invoices)
            total_paid = sum(float(inv["amount"]) for inv in invoices if inv["status"] == "paid")
            total_pending = sum(float(inv["amount"]) for inv in invoices if inv["status"] in ["pending", "overdue"])
            
            paid_count = len([inv for inv in invoices if inv["status"] == "paid"])
            pending_count = len([inv for inv in invoices if inv["status"] == "pending"])
            overdue_count = len([inv for inv in invoices if inv["status"] == "overdue"])
            
            report = {
                "month": month,
                "year": year,
                "total_invoices": len(invoices),
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "total_pending": total_pending,
                "paid_count": paid_count,
                "pending_count": pending_count,
                "overdue_count": overdue_count,
                "invoices": invoices
            }
            
            # Format message
            month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            message = (
                f"📊 Monthly Report - {month_names[month]} {year}\n\n"
                f"Total Invoices: {len(invoices)}\n"
                f"Total Invoiced: PKR {total_invoiced:,.0f}\n"
                f"Paid: PKR {total_paid:,.0f} ({paid_count} invoices)\n"
                f"Pending: PKR {total_pending:,.0f} ({pending_count + overdue_count} invoices)\n"
            )
            
            if overdue_count > 0:
                message += f"⚠️ Overdue: {overdue_count} invoices\n"
            
            return {
                "success": True,
                "message": message,
                "data": report
            }
            
        except Exception as e:
            logger.error(f"Error generating monthly report: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to generate report: {str(e)}",
                "data": None
            }
    
    async def _generate_invoice_number(self, business_id: int) -> str:
        """Generate unique invoice number.
        
        Args:
            business_id: Business ID
            
        Returns:
            Invoice number
        """
        # Get business prefix
        business = supabase_client.admin.table("businesses").select("slug").eq(
            "id", business_id
        ).execute()
        
        prefix = "INV"
        if business.data:
            prefix = business.data[0]["slug"][:3].upper()
        
        # Get count of invoices for this business
        count_result = supabase_client.admin.table("invoices").select(
            "id", count="exact"
        ).eq("business_id", business_id).execute()
        
        count = count_result.count + 1 if count_result.count else 1
        
        return f"{prefix}-{count:04d}"
    
    async def _get_client(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Get client by ID.
        
        Args:
            client_id: Client ID
            
        Returns:
            Client dict or None
        """
        result = supabase_client.admin.table("clients").select("*").eq(
            "id", client_id
        ).execute()
        
        return result.data[0] if result.data else None
    
    async def _update_overdue_statuses(self):
        """Update invoice statuses to overdue if past due date."""
        try:
            supabase_client.admin.table("invoices").update({
                "status": "overdue"
            }).eq("status", "pending").lt("due_date", date.today().isoformat()).execute()
        except Exception as e:
            logger.error(f"Error updating overdue statuses: {e}")


# Global instance
invoice_tracker = InvoiceTrackerAgent()

