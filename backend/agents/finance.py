"""Finance Agent for transaction and loan management."""
import logging
from datetime import date
from typing import Dict, Any

from models.schemas import ParsedMessage, TransactionCreate, LoanCreate
from clients.supabase_client import supabase_client
from memory.embed import memory_service

logger = logging.getLogger(__name__)


class FinanceAgent:
    """Agent for handling financial transactions and loans."""
    
    async def process(self, parsed: ParsedMessage, user_id: str) -> Dict[str, Any]:
        """Process finance-related intents.
        
        Args:
            parsed: Parsed message with financial intent
            user_id: User identifier
            
        Returns:
            Response dict with success status and message
        """
        try:
            if parsed.intent == "transaction":
                return await self._create_transaction(parsed, user_id)
            
            elif parsed.intent == "loan":
                return await self._create_loan(parsed, user_id)
            
            elif parsed.intent == "repayment":
                return await self._record_repayment(parsed, user_id)
            
            elif parsed.intent == "query":
                return await self._handle_query(parsed, user_id)
            
            else:
                return {
                    "success": False,
                    "message": "Unknown finance intent",
                    "data": None
                }
                
        except Exception as e:
            logger.error(f"Finance agent error: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error processing financial action: {str(e)}",
                "data": None
            }
    
    async def _create_transaction(self, parsed: ParsedMessage, user_id: str) -> Dict[str, Any]:
        """Create a transaction from parsed message.
        
        Args:
            parsed: Parsed message
            user_id: User identifier
            
        Returns:
            Response dict
        """
        # Get business ID
        business_id = await self._get_business_id(parsed.business)
        if not business_id:
            return {
                "success": False,
                "message": f"Business '{parsed.business}' not found. Please create it first.",
                "data": None
            }
        
        # Map telegram_id to internal user_id (create user if doesn't exist)
        internal_user_id = await self._get_or_create_user(user_id)
        
        # Insert transaction
        result = supabase_client.admin.table("transactions").insert({
            "business_id": business_id,
            "user_id": internal_user_id,
            "type": parsed.type,
            "amount": parsed.amount,
            "currency": parsed.currency or "PKR",
            "category": parsed.category or "general",
            "person": parsed.person,
            "date": (parsed.date or date.today()).isoformat(),
            "description": parsed.description or parsed.raw_text,
            "tags": parsed.tags
        }).execute()
        
        # Log action
        await self._log_action("transaction", "create", parsed.raw_text, result.data)
        
        # Embed in memory
        await memory_service.add_memory(
            content=f"Transaction: {parsed.type} {parsed.currency} {parsed.amount} - {parsed.description}",
            metadata={
                "table": "transactions",
                "row_id": result.data[0]["id"],
                "business": parsed.business,
                "date": (parsed.date or date.today()).isoformat()
            }
        )
        
        # Format response
        transaction = result.data[0] if result.data else {}
        message = (
            f"✅ Recorded {parsed.type}: {parsed.currency} {parsed.amount:,.0f}\n"
            f"Business: {parsed.business}\n"
            f"Category: {parsed.category or 'general'}"
        )
        
        if parsed.person:
            message += f"\nPerson: {parsed.person}"
        
        return {
            "success": True,
            "message": message,
            "data": transaction
        }
    
    async def _create_loan(self, parsed: ParsedMessage, user_id: str) -> Dict[str, Any]:
        """Create a loan record.
        
        Args:
            parsed: Parsed message
            user_id: User identifier
            
        Returns:
            Response dict
        """
        business_id = await self._get_business_id(parsed.business)
        if not business_id:
            return {
                "success": False,
                "message": f"Business '{parsed.business}' not found.",
                "data": None
            }
        
        # Map telegram_id to internal user_id
        internal_user_id = await self._get_or_create_user(user_id)
        
        result = supabase_client.admin.table("loans").insert({
            "business_id": business_id,
            "user_id": internal_user_id,
            "person": parsed.person,
            "amount": parsed.amount,
            "currency": parsed.currency or "PKR",
            "date": (parsed.date or date.today()).isoformat(),
            "status": "active",
            "remaining_amount": parsed.amount,
            "description": parsed.description or f"Loan to {parsed.person}"
        }).execute()
        
        await self._log_action("loan", "create", parsed.raw_text, result.data)
        
        loan = result.data[0] if result.data else {}
        message = (
            f"✅ Recorded loan: {parsed.currency} {parsed.amount:,.0f} to {parsed.person}\n"
            f"Business: {parsed.business}\n"
            f"Date: {parsed.date or date.today()}"
        )
        
        return {
            "success": True,
            "message": message,
            "data": loan
        }
    
    async def _record_repayment(self, parsed: ParsedMessage, user_id: str) -> Dict[str, Any]:
        """Record a loan repayment.
        
        Args:
            parsed: Parsed message
            user_id: User identifier
            
        Returns:
            Response dict
        """
        # Find active loan for this person
        loans_result = supabase_client.admin.table("loans").select("*").eq(
            "person", parsed.person
        ).eq("status", "active").execute()
        
        if not loans_result.data:
            return {
                "success": False,
                "message": f"No active loan found for {parsed.person}",
                "data": None
            }
        
        loan = loans_result.data[0]
        
        # Record repayment
        repayment_result = supabase_client.admin.table("loan_repayments").insert({
            "loan_id": loan["id"],
            "amount": parsed.amount,
            "date": (parsed.date or date.today()).isoformat()
        }).execute()
        
        # Update loan
        new_remaining = loan["remaining_amount"] - parsed.amount
        new_status = "paid" if new_remaining <= 0 else "partially_paid"
        
        supabase_client.admin.table("loans").update({
            "remaining_amount": max(0, new_remaining),
            "status": new_status
        }).eq("id", loan["id"]).execute()
        
        message = (
            f"✅ Repayment recorded: {loan['currency']} {parsed.amount:,.0f} from {parsed.person}\n"
            f"Remaining: {loan['currency']} {max(0, new_remaining):,.0f}"
        )
        
        if new_status == "paid":
            message += "\n🎉 Loan fully repaid!"
        
        return {
            "success": True,
            "message": message,
            "data": repayment_result.data[0] if repayment_result.data else {}
        }
    
    async def _handle_query(self, parsed: ParsedMessage, user_id: str) -> Dict[str, Any]:
        """Handle financial queries.
        
        Args:
            parsed: Parsed message
            user_id: User identifier
            
        Returns:
            Response dict
        """
        # Use memory search for queries
        from memory.embed import memory_service
        
        result = await memory_service.search(parsed.raw_text, limit=5)
        
        return {
            "success": True,
            "message": result.summary if hasattr(result, 'summary') else "Query processed",
            "data": result.results if hasattr(result, 'results') else []
        }
    
    async def _get_or_create_user(self, telegram_id: str) -> int:
        """Get or create user by telegram_id.
        
        Args:
            telegram_id: Telegram user ID (string)
            
        Returns:
            Internal user ID (integer)
        """
        try:
            # Check if user exists
            result = supabase_client.admin.table("users").select("id").eq(
                "telegram_id", telegram_id
            ).limit(1).execute()
            
            if result.data:
                return result.data[0]["id"]
            
            # Create new user
            new_user = supabase_client.admin.table("users").insert({
                "telegram_id": telegram_id,
                "name": f"User {telegram_id[:8]}"  # Default name
            }).execute()
            
            logger.info(f"✅ Created new user: {telegram_id}")
            return new_user.data[0]["id"] if new_user.data else 1
            
        except Exception as e:
            logger.error(f"Error getting/creating user: {e}")
            return 1  # Fallback to user_id=1
    
    async def _get_business_id(self, business_name: str) -> int:
        """Get business ID by name.
        
        Args:
            business_name: Business name
            
        Returns:
            Business ID or None
        """
        if not business_name:
            return None
        
        result = supabase_client.admin.table("businesses").select("id").ilike(
            "name", business_name
        ).limit(1).execute()
        
        return result.data[0]["id"] if result.data else None
    
    async def _log_action(self, agent_type: str, action: str, input_text: str, output_data: Any):
        """Log agent action.
        
        Args:
            agent_type: Type of agent
            action: Action performed
            input_text: Input text
            output_data: Output data
        """
        try:
            supabase_client.admin.table("agent_logs").insert({
                "user_id": 1,
                "agent_type": agent_type,
                "action": action,
                "input_data": {"text": input_text},
                "output_data": output_data,
                "status": "success"
            }).execute()
        except Exception as e:
            logger.error(f"Error logging action: {e}")


# Global instance
finance_agent = FinanceAgent()

