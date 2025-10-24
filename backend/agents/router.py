"""Main Core Agent Router - orchestrates all specialized agents with JARVIS-level intelligence."""
import logging
from typing import Dict, Any

from models.schemas import ParsedMessage, AgentResponse
from agents.finance import finance_agent
from agents.calendar import calendar_agent
from agents.habit_learner import habit_learner
from services.prompts import get_prompt
from services.intelligence_engine import intelligence_engine

logger = logging.getLogger(__name__)


class MainCoreAgent:
    """Main agent that routes to specialized agents based on intent."""
    
    def __init__(self):
        """Initialize main agent."""
        self.system_prompt = get_prompt("system_zyana")
    
    async def route(self, parsed: ParsedMessage, user_id: str) -> AgentResponse:
        """Route parsed message to appropriate agent with JARVIS-level intelligence.
        
        Args:
            parsed: Parsed message with intent
            user_id: User identifier
            
        Returns:
            AgentResponse with result
        """
        logger.info(f"🧠 Routing intent: {parsed.intent} for user: {user_id}")
        
        try:
            # 🚀 JARVIS UPGRADE: Enhance context with learned patterns and memories
            context = await intelligence_engine.enhance_context(
                user_id, parsed.raw_text, parsed.intent
            )
            
            logger.info(f"Enhanced context: {len(context.get('related_memories', []))} memories found")
            
            # Apply learned patterns to missing fields
            if parsed.missing_fields and context.get("learned_patterns"):
                parsed = self._apply_learned_patterns(parsed, context["learned_patterns"])
            
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
            
            elif parsed.intent == "insights":
                # 🧠 NEW: Generate intelligent insights
                result = await self._generate_insights(user_id)
            
            else:
                result = await self._handle_other(parsed, user_id, context)
            
            # 🧠 JARVIS UPGRADE: Learn from this interaction
            await intelligence_engine.learn_from_interaction(
                user_id,
                parsed.raw_text,
                parsed.intent,
                {
                    "business": parsed.business,
                    "amount": parsed.amount,
                    "person": parsed.person
                },
                "success" if result.get("success") else "failure"
            )
            
            # Learn habits
            await habit_learner.observe_interaction(parsed, user_id)
            
            # 🚀 Add proactive suggestions to response
            message = result.get("message", "Done")
            if context.get("suggestions"):
                message += "\n\n" + "\n".join(context["suggestions"][:2])
            
            # Create AgentResponse
            return AgentResponse(
                success=result.get("success", True),
                message=message,
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
    
    def _apply_learned_patterns(self, parsed: ParsedMessage, patterns: Dict[str, Any]) -> ParsedMessage:
        """Apply learned patterns to fill missing fields.
        
        Args:
            parsed: ParsedMessage with missing fields
            patterns: Learned user patterns
            
        Returns:
            Enhanced ParsedMessage
        """
        # Apply default business
        if not parsed.business and patterns.get("default_business"):
            parsed.business = patterns["default_business"]
            if "business" in parsed.missing_fields:
                parsed.missing_fields.remove("business")
            logger.info(f"🧠 Applied learned default business: {parsed.business}")
        
        # Apply preferred currency
        if not parsed.currency and patterns.get("preferred_currency"):
            parsed.currency = patterns["preferred_currency"]
            logger.info(f"🧠 Applied learned currency: {parsed.currency}")
        
        return parsed
    
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
    
    async def _generate_insights(self, user_id: str) -> Dict[str, Any]:
        """Generate intelligent insights and analysis.
        
        Args:
            user_id: User identifier
            
        Returns:
            Response dict with insights
        """
        insights_data = await intelligence_engine.generate_insights(user_id)
        
        # Format insights as message
        message = insights_data.get("message", "")
        
        if insights_data.get("insights"):
            message += "\n\n" + "\n".join(insights_data["insights"])
        
        if insights_data.get("recommendations"):
            message += "\n\n🎯 Recommendations:\n" + "\n".join(insights_data["recommendations"])
        
        return {
            "success": True,
            "message": message,
            "data": insights_data.get("summary")
        }
    
    async def _handle_other(self, parsed: ParsedMessage, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle other intents with helpful response.
        
        PRODUCTION-GRADE: No external AI calls, instant response.
        
        Args:
            parsed: Parsed message
            user_id: User identifier
            context: Enhanced context from intelligence engine
            
        Returns:
            Response dict
        """
        # Provide helpful, instant response
        message = parsed.raw_text.lower()
        
        # Check for common patterns
        if any(word in message for word in ['hi', 'hello', 'hey', 'greetings']):
            response = (
                "👋 Hello! I'm Zyana, your AI assistant.\n\n"
                "I can help you:\n"
                "• Track finances: 'I lent Ahmad Rs 10,000 from Vidify'\n"
                "• Check status: /status\n"
                "• View insights: /insights\n"
                "• Book calendar: 'Meeting tomorrow at 3pm'\n\n"
                "How can I assist you?"
            )
        elif any(word in message for word in ['thanks', 'thank you', 'thx']):
            response = "You're welcome! 😊 Let me know if you need anything else."
        elif any(word in message for word in ['help', 'what can you do', 'commands']):
            response = (
                "🤖 I can help with:\n\n"
                "💰 Finance:\n"
                "• 'I lent Ahmad Rs 10,000'\n"
                "• 'Received 50k from sales'\n"
                "• 'Paid 3000 for software'\n\n"
                "📊 Reports:\n"
                "• /status - Check balances\n"
                "• /insights - AI analysis\n\n"
                "📅 Calendar:\n"
                "• 'Meeting tomorrow at 3pm'\n"
                "• 'Call with client Friday 10am'\n\n"
                "Just talk to me naturally!"
            )
        else:
            response = (
                "I'm here to help! I can track your finances, manage calendar events, and provide insights.\n\n"
                "Try:\n"
                "• 'I gave someone Rs 5000'\n"
                "• /insights for AI analysis\n"
                "• /help for commands"
            )
        
        return {
            "success": True,
            "message": response
        }


# Global instance
main_agent = MainCoreAgent()

