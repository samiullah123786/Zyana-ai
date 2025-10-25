"""Client Manager Agent for managing business clients."""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class ClientManagerAgent:
    """Agent for client management operations."""
    
    async def create_client(
        self,
        name: str,
        business_id: int,
        contact: Optional[str] = None,
        email: Optional[str] = None,
        company: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new client.
        
        Args:
            name: Client name
            business_id: Associated business ID
            contact: Contact phone/info
            email: Email address
            company: Company name
            notes: Additional notes
            
        Returns:
            Response dict with client data
        """
        try:
            # Insert client
            result = supabase_client.admin.table("clients").insert({
                "name": name,
                "business_id": business_id,
                "contact": contact,
                "email": email,
                "company": company,
                "notes": notes
            }).execute()
            
            client = result.data[0] if result.data else {}
            
            # Get business name
            business = await self._get_business(business_id)
            business_name = business.get("name", "Unknown") if business else "Unknown"
            
            logger.info(f"Created client: {name} for business {business_name}")
            
            message = f"✅ Client added: {name}\n"
            if contact:
                message += f"Contact: {contact}\n"
            if company:
                message += f"Company: {company}\n"
            message += f"Business: {business_name}"
            
            return {
                "success": True,
                "message": message,
                "data": client
            }
            
        except Exception as e:
            logger.error(f"Error creating client: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to create client: {str(e)}",
                "data": None
            }
    
    async def list_clients(
        self,
        business_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List clients with optional business filter.
        
        Args:
            business_id: Filter by business
            
        Returns:
            List of clients
        """
        try:
            query = supabase_client.admin.table("clients").select(
                "*, businesses(name)"
            )
            
            if business_id:
                query = query.eq("business_id", business_id)
            
            result = query.order("name").execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error listing clients: {e}", exc_info=True)
            return []
    
    async def get_client(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Get client by ID with related data.
        
        Args:
            client_id: Client ID
            
        Returns:
            Client dict with invoices
        """
        try:
            # Get client
            client_result = supabase_client.admin.table("clients").select(
                "*, businesses(name)"
            ).eq("id", client_id).execute()
            
            if not client_result.data:
                return None
            
            client = client_result.data[0]
            
            # Get client's invoices
            invoices_result = supabase_client.admin.table("invoices").select(
                "*"
            ).eq("client_id", client_id).order("created_at", desc=True).execute()
            
            client["invoices"] = invoices_result.data if invoices_result.data else []
            
            return client
            
        except Exception as e:
            logger.error(f"Error getting client: {e}", exc_info=True)
            return None
    
    async def get_client_by_name(self, name: str, business_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get client by name (case-insensitive).
        
        Args:
            name: Client name
            business_id: Optional business filter
            
        Returns:
            Client dict or None
        """
        try:
            query = supabase_client.admin.table("clients").select("*").ilike("name", f"%{name}%")
            
            if business_id:
                query = query.eq("business_id", business_id)
            
            result = query.limit(1).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting client by name: {e}", exc_info=True)
            return None
    
    async def get_client_status(self, client_id: int) -> Dict[str, Any]:
        """Get comprehensive client status including invoices and payments.
        
        Args:
            client_id: Client ID
            
        Returns:
            Status dict
        """
        try:
            client = await self.get_client(client_id)
            
            if not client:
                return {
                    "success": False,
                    "message": "Client not found",
                    "data": None
                }
            
            invoices = client.get("invoices", [])
            
            # Calculate stats
            total_invoiced = sum(float(inv["amount"]) for inv in invoices)
            total_paid = sum(float(inv["amount"]) for inv in invoices if inv["status"] == "paid")
            total_pending = sum(float(inv["amount"]) for inv in invoices if inv["status"] in ["pending", "overdue"])
            
            paid_count = len([inv for inv in invoices if inv["status"] == "paid"])
            pending_count = len([inv for inv in invoices if inv["status"] == "pending"])
            overdue_count = len([inv for inv in invoices if inv["status"] == "overdue"])
            
            # Last invoice date
            last_invoice = invoices[0] if invoices else None
            last_invoice_date = last_invoice["created_at"][:10] if last_invoice else "N/A"
            
            message = (
                f"📊 {client['name']} Status\n\n"
                f"Total Invoices: {len(invoices)}\n"
                f"Total Invoiced: PKR {total_invoiced:,.0f}\n"
                f"Paid: PKR {total_paid:,.0f} ({paid_count} invoices)\n"
                f"Pending: PKR {total_pending:,.0f} ({pending_count + overdue_count} invoices)\n"
            )
            
            if overdue_count > 0:
                message += f"⚠️ Overdue: {overdue_count} invoices\n"
            
            message += f"\nLast Invoice: {last_invoice_date}"
            
            return {
                "success": True,
                "message": message,
                "data": {
                    "client": client,
                    "total_invoices": len(invoices),
                    "total_invoiced": total_invoiced,
                    "total_paid": total_paid,
                    "total_pending": total_pending,
                    "paid_count": paid_count,
                    "pending_count": pending_count,
                    "overdue_count": overdue_count,
                    "last_invoice_date": last_invoice_date
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting client status: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to get client status: {str(e)}",
                "data": None
            }
    
    async def update_client(
        self,
        client_id: int,
        name: Optional[str] = None,
        contact: Optional[str] = None,
        email: Optional[str] = None,
        company: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update client information.
        
        Args:
            client_id: Client ID
            name: New name
            contact: New contact
            email: New email
            company: New company
            notes: New notes
            
        Returns:
            Response dict
        """
        try:
            # Build update dict
            update_data = {"updated_at": datetime.utcnow().isoformat()}
            
            if name is not None:
                update_data["name"] = name
            if contact is not None:
                update_data["contact"] = contact
            if email is not None:
                update_data["email"] = email
            if company is not None:
                update_data["company"] = company
            if notes is not None:
                update_data["notes"] = notes
            
            # Update
            result = supabase_client.admin.table("clients").update(
                update_data
            ).eq("id", client_id).execute()
            
            if not result.data:
                return {
                    "success": False,
                    "message": "Client not found",
                    "data": None
                }
            
            client = result.data[0]
            
            logger.info(f"Updated client: {client['name']}")
            
            return {
                "success": True,
                "message": f"✅ Client {client['name']} updated",
                "data": client
            }
            
        except Exception as e:
            logger.error(f"Error updating client: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to update client: {str(e)}",
                "data": None
            }
    
    async def delete_client(self, client_id: int) -> Dict[str, Any]:
        """Delete a client.
        
        Args:
            client_id: Client ID
            
        Returns:
            Response dict
        """
        try:
            # Check if client has invoices
            invoices = supabase_client.admin.table("invoices").select(
                "id", count="exact"
            ).eq("client_id", client_id).execute()
            
            if invoices.count and invoices.count > 0:
                return {
                    "success": False,
                    "message": f"Cannot delete client with {invoices.count} invoices. Delete invoices first.",
                    "data": None
                }
            
            # Delete client
            result = supabase_client.admin.table("clients").delete().eq(
                "id", client_id
            ).execute()
            
            logger.info(f"Deleted client ID: {client_id}")
            
            return {
                "success": True,
                "message": "✅ Client deleted",
                "data": None
            }
            
        except Exception as e:
            logger.error(f"Error deleting client: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to delete client: {str(e)}",
                "data": None
            }
    
    async def _get_business(self, business_id: int) -> Optional[Dict[str, Any]]:
        """Get business by ID.
        
        Args:
            business_id: Business ID
            
        Returns:
            Business dict or None
        """
        result = supabase_client.admin.table("businesses").select("*").eq(
            "id", business_id
        ).execute()
        
        return result.data[0] if result.data else None


# Global instance
client_manager = ClientManagerAgent()

