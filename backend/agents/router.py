"""Main Core Agent Router - orchestrates all specialized agents."""
import logging
from typing import Dict, Any

from models.schemas import ParsedMessage, AgentResponse
from agents.finance import finance_agent
from agents.calendar import calendar_agent
from agents.habit_learner import habit_learner
from clients.fal_client import fal_client
from services.prompts import get_prompt

logger = logging.getLogger(__name__)


class MainCoreAgent:
    """Main agent that routes to specialized agents based on intent."""
    
    def __init__(self):
        """Initialize main agent."""
        self.system_prompt = get_prompt("system_zyana")
    
    async def route(self, parsed: ParsedMessage, user_id: str) -> AgentResponse:
        """Route parsed message to appropriate agent.
        
        Args:
            parsed: Parsed message with intent
            user_id: User identifier
            
        Returns:
            AgentResponse with result
        """
        logger.info(f"Routing intent: {parsed.intent} for user: {user_id}")
        
        try:
            # Route based on intent
            if parsed.intent in ["transaction", "loan", "repayment", "query", "report"]:
                result = await finance_agent.process(parsed, user_id)
            
            elif parsed.intent == "calendar":
                result = await calendar_agent.process(parsed, user_id)
            
            elif parsed.intent == "create_business":
                result = await self._create_business(parsed, user_id)
            
            elif parsed.intent == "status":
                result = await self._get_status(user_id)
            
            elif parsed.intent == "goal":
                result = await self._create_goal(parsed, user_id)
            
            else:
                result = await self._handle_other(parsed, user_id)
            
            # Learn from interaction
            await habit_learner.observe_interaction(parsed, user_id)
            
            # Create AgentResponse
            return AgentResponse(
                success=result.get("success", True),
                message=result.get("message", "Done"),
                data=result.get("data"),
                next_action=result.get("next_action")
            )
            
        except Exception as e:
            logger.error(f"Error routing message: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                message=f"Sorry, I encountered an error: {str(e)}",
                data=None
            )
    
    async def _create_business(self, parsed: ParsedMessage, user_id: str) -> Dict[str, Any]:
        """Create a new business.
        
        Args:
            parsed: Parsed message
            user_id: User identifier
            
        Returns:
            Response dict
        """
        from clients.supabase_client import supabase_client
        
        business_name = parsed.business or parsed.description
        if not business_name:
            return {
                "success": False,
                "message": "Please provide a business name"
            }
        
        # Create slug
        slug = business_name.lower().replace(" ", "-")
        
        result = supabase_client.admin.table("businesses").insert({
            "name": business_name,
            "slug": slug,
            "type": "general",
            "description": parsed.description
        }).execute()
        
        return {
            "success": True,
            "message": f"✅ Created business: {business_name}",
            "data": result.data[0] if result.data else {}
        }
    
    async def _get_status(self, user_id: str) -> Dict[str, Any]:
        """Get status summary of all businesses.
        
        Args:
            user_id: User identifier
            
        Returns:
            Response dict with status
        """
        from clients.supabase_client import supabase_client
        
        # Get all businesses
        businesses = supabase_client.admin.table("businesses").select("*").execute()
        
        status_lines = ["📊 Your Business Status:\n"]
        
        for business in businesses.data:
            # Get balance
            transactions = supabase_client.admin.table("transactions").select(
                "type, amount"
            ).eq("business_id", business["id"]).execute()
            
            income = sum(t["amount"] for t in transactions.data if t["type"] == "income")
            expenses = sum(t["amount"] for t in transactions.data if t["type"] == "expense")
            balance = income - expenses
            
            status_lines.append(f"\n{business['name']}: PKR {balance:,.0f}")
        
        return {
            "success": True,
            "message": "\n".join(status_lines)
        }
    
    async def _create_goal(self, parsed: ParsedMessage, user_id: str) -> Dict[str, Any]:
        """Create a goal.
        
        Args:
            parsed: Parsed message
            user_id: User identifier
            
        Returns:
            Response dict
        """
        from clients.supabase_client import supabase_client
        from agents.finance import finance_agent
        
        business_id = await finance_agent._get_business_id(parsed.business)
        if not business_id:
            return {
                "success": False,
                "message": f"Business '{parsed.business}' not found"
            }
        
        result = supabase_client.admin.table("goals").insert({
            "business_id": business_id,
            "user_id": 1,
            "title": parsed.description or f"Target for {parsed.business}",
            "target_amount": parsed.amount,
            "current_amount": 0,
            "currency": parsed.currency or "PKR",
            "deadline": parsed.date.isoformat() if parsed.date else None,
            "status": "active"
        }).execute()
        
        return {
            "success": True,
            "message": f"✅ Goal set: {parsed.currency} {parsed.amount:,.0f} for {parsed.business}",
            "data": result.data[0] if result.data else {}
        }
    
    async def _handle_other(self, parsed: ParsedMessage, user_id: str) -> Dict[str, Any]:
        """Handle other intents using Fal AI.
        
        Args:
            parsed: Parsed message
            user_id: User identifier
            
        Returns:
            Response dict
        """
        # Use Fal to generate a helpful response
        response = await fal_client.chat_simple(
            prompt=parsed.raw_text,
            system_prompt=self.system_prompt,
            temperature=0.7
        )
        
        return {
            "success": True,
            "message": response or "I'm not sure how to help with that. Can you rephrase?"
        }


# Global instance
main_agent = MainCoreAgent()

