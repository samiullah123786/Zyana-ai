"""
JARVIS-Level Intelligence Engine for Zyana
===========================================
This module provides advanced AI capabilities including:
- Context-aware conversations
- Pattern learning and prediction
- Proactive suggestions
- Multi-turn conversation support
- User preference learning
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from clients.supabase_client import supabase_client
from memory.embed import memory_service

logger = logging.getLogger(__name__)


class IntelligenceEngine:
    """Advanced AI engine for context-aware, learning-based interactions."""
    
    def __init__(self):
        """Initialize the intelligence engine."""
        self.conversation_memory = {}  # In-memory conversation context
        self.user_patterns = defaultdict(list)
        
    async def enhance_context(
        self,
        user_id: str,
        message: str,
        parsed_intent: str
    ) -> Dict[str, Any]:
        """Enhance message understanding with learned context.
        
        Args:
            user_id: User identifier
            message: Current message
            parsed_intent: Detected intent
            
        Returns:
            Enhanced context dict with:
            - conversation_history: Recent messages
            - learned_patterns: User habits
            - related_memories: Relevant past interactions
            - suggestions: Proactive suggestions
        """
        context = {
            "conversation_history": await self._get_conversation_history(user_id),
            "learned_patterns": await self._get_user_patterns(user_id),
            "related_memories": await self._find_related_memories(message, user_id),
            "user_preferences": await self._get_user_preferences(user_id),
            "suggestions": []
        }
        
        # Generate proactive suggestions based on patterns
        context["suggestions"] = await self._generate_suggestions(
            user_id, parsed_intent, context
        )
        
        return context
    
    async def learn_from_interaction(
        self,
        user_id: str,
        message: str,
        intent: str,
        entities: Dict[str, Any],
        outcome: str
    ):
        """Learn from user interaction to improve future responses.
        
        Args:
            user_id: User identifier
            message: User message
            intent: Detected intent
            entities: Extracted entities
            outcome: Result of interaction
        """
        try:
            # Store interaction in learning database
            interaction = {
                "user_id": user_id,
                "message": message,
                "intent": intent,
                "entities": entities,
                "outcome": outcome,
                "timestamp": datetime.now().isoformat()
            }
            
            # Save to database
            supabase_client.admin.table("ai_learning_log").insert(interaction).execute()
            
            # Update in-memory patterns
            self._update_patterns(user_id, intent, entities)
            
            # Update conversation context
            await self._store_conversation(user_id, message, intent)
            
            logger.info(f"Learned from interaction: {intent} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error learning from interaction: {e}")
    
    async def _get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history."""
        try:
            result = supabase_client.admin.table("conversation_history").select(
                "message, intent, timestamp"
            ).eq("user_id", user_id).order(
                "timestamp", desc=True
            ).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching conversation history: {e}")
            return []
    
    async def _get_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get learned user patterns and habits."""
        try:
            # Get most frequent business
            business_result = supabase_client.admin.table("transactions").select(
                "business_id"
            ).eq("user_id", 1).execute()  # TODO: Map real user_id
            
            if business_result.data:
                from collections import Counter
                business_counts = Counter([t.get("business_id") for t in business_result.data])
                most_common_business = business_counts.most_common(1)
                
                if most_common_business:
                    biz_id = most_common_business[0][0]
                    biz_result = supabase_client.admin.table("businesses").select(
                        "name"
                    ).eq("id", biz_id).execute()
                    default_business = biz_result.data[0]["name"] if biz_result.data else None
                else:
                    default_business = None
            else:
                default_business = None
            
            # Get preferred currency
            currency_result = supabase_client.admin.table("transactions").select(
                "currency"
            ).eq("user_id", 1).execute()
            
            if currency_result.data:
                from collections import Counter
                currency_counts = Counter([t.get("currency", "PKR") for t in currency_result.data])
                preferred_currency = currency_counts.most_common(1)[0][0]
            else:
                preferred_currency = "PKR"
            
            # Get common transaction times
            time_result = supabase_client.admin.table("transactions").select(
                "date, type, amount"
            ).eq("user_id", 1).limit(100).execute()
            
            patterns = {
                "default_business": default_business,
                "preferred_currency": preferred_currency,
                "common_categories": await self._get_common_categories(user_id),
                "transaction_patterns": await self._analyze_transaction_patterns(time_result.data if time_result.data else [])
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error getting user patterns: {e}")
            return {
                "default_business": None,
                "preferred_currency": "PKR",
                "common_categories": [],
                "transaction_patterns": {}
            }
    
    async def _get_common_categories(self, user_id: str) -> List[str]:
        """Get user's most common transaction categories."""
        try:
            result = supabase_client.admin.table("transactions").select(
                "category"
            ).eq("user_id", 1).execute()
            
            if result.data:
                from collections import Counter
                category_counts = Counter([t.get("category", "general") for t in result.data])
                return [cat for cat, _ in category_counts.most_common(5)]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting common categories: {e}")
            return []
    
    async def _analyze_transaction_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze transaction patterns for insights."""
        if not transactions:
            return {}
        
        try:
            # Calculate average transaction amount
            amounts = [t.get("amount", 0) for t in transactions if t.get("amount")]
            avg_amount = sum(amounts) / len(amounts) if amounts else 0
            
            # Find recurring transactions
            from collections import defaultdict
            date_amounts = defaultdict(list)
            
            for t in transactions:
                if t.get("date") and t.get("amount"):
                    date_amounts[t["date"]].append(t["amount"])
            
            return {
                "average_amount": avg_amount,
                "total_transactions": len(transactions),
                "active_days": len(date_amounts)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return {}
    
    async def _find_related_memories(self, message: str, user_id: str, limit: int = 5) -> List[Dict]:
        """Find related past memories using semantic search."""
        try:
            result = await memory_service.search(message, limit=limit)
            return result.results if hasattr(result, 'results') else []
            
        except Exception as e:
            logger.error(f"Error finding related memories: {e}")
            return []
    
    async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences and settings."""
        try:
            result = supabase_client.admin.table("user_preferences").select(
                "*"
            ).eq("user_id", user_id).execute()
            
            if result.data:
                return result.data[0]
            
            return {
                "timezone": "UTC",
                "language": "en",
                "notification_preferences": {}
            }
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}
    
    async def _generate_suggestions(
        self,
        user_id: str,
        intent: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate proactive suggestions based on context."""
        suggestions = []
        
        try:
            # Suggest default business if missing
            if intent in ["transaction", "loan"]:
                default_biz = context["learned_patterns"].get("default_business")
                if default_biz:
                    suggestions.append(f"💡 Use {default_biz} (your most frequent business)?")
            
            # Suggest currency
            if intent == "transaction":
                pref_currency = context["learned_patterns"].get("preferred_currency", "PKR")
                if pref_currency != "PKR":
                    suggestions.append(f"💡 Currency: {pref_currency}?")
            
            # Check for pending loans
            loans = await self._get_pending_loans(user_id)
            if loans and intent == "query":
                total_pending = sum(loan.get("remaining_amount", 0) for loan in loans)
                suggestions.append(f"💰 You have {len(loans)} pending loans (Total: Rs {total_pending:,.0f})")
            
            # Suggest reporting if many transactions
            patterns = context["learned_patterns"].get("transaction_patterns", {})
            if patterns.get("total_transactions", 0) > 10:
                suggestions.append("📊 Want to see your financial summary? Just ask!")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []
    
    async def _get_pending_loans(self, user_id: str) -> List[Dict]:
        """Get pending loans."""
        try:
            result = supabase_client.admin.table("loans").select(
                "*"
            ).eq("user_id", 1).in_("status", ["active", "partially_paid"]).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting pending loans: {e}")
            return []
    
    def _update_patterns(self, user_id: str, intent: str, entities: Dict[str, Any]):
        """Update in-memory user patterns."""
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = []
        
        self.user_patterns[user_id].append({
            "intent": intent,
            "entities": entities,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 100 patterns in memory
        if len(self.user_patterns[user_id]) > 100:
            self.user_patterns[user_id] = self.user_patterns[user_id][-100:]
    
    async def _store_conversation(self, user_id: str, message: str, intent: str):
        """Store conversation in database."""
        try:
            supabase_client.admin.table("conversation_history").insert({
                "user_id": user_id,
                "message": message,
                "intent": intent,
                "timestamp": datetime.now().isoformat()
            }).execute()
            
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
    
    async def generate_insights(self, user_id: str) -> Dict[str, Any]:
        """Generate intelligent insights about user's data.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with insights and recommendations
        """
        try:
            # Get all transactions
            trans_result = supabase_client.admin.table("transactions").select(
                "*"
            ).eq("user_id", 1).execute()
            
            transactions = trans_result.data if trans_result.data else []
            
            if not transactions:
                return {
                    "message": "No transactions yet. Start tracking to get insights!",
                    "insights": []
                }
            
            # Calculate insights
            total_income = sum(t["amount"] for t in transactions if t.get("type") == "income")
            total_expense = sum(t["amount"] for t in transactions if t.get("type") == "expense")
            net_balance = total_income - total_expense
            
            # Get top categories
            from collections import Counter
            expense_by_category = defaultdict(float)
            for t in transactions:
                if t.get("type") == "expense":
                    expense_by_category[t.get("category", "general")] += t.get("amount", 0)
            
            top_expenses = sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Generate insights
            insights = []
            
            if net_balance > 0:
                insights.append(f"✅ Great! You're in profit by Rs {net_balance:,.0f}")
            else:
                insights.append(f"⚠️ Expenses exceed income by Rs {abs(net_balance):,.0f}")
            
            if top_expenses:
                top_cat, top_amount = top_expenses[0]
                insights.append(f"🏷️ Top expense category: {top_cat} (Rs {top_amount:,.0f})")
            
            # Check for loans
            loans_result = supabase_client.admin.table("loans").select(
                "remaining_amount"
            ).eq("user_id", 1).in_("status", ["active", "partially_paid"]).execute()
            
            if loans_result.data:
                total_loans = sum(l["remaining_amount"] for l in loans_result.data)
                insights.append(f"💰 Outstanding loans: Rs {total_loans:,.0f}")
            
            return {
                "message": "Here's your intelligent analysis",
                "summary": {
                    "total_income": total_income,
                    "total_expense": total_expense,
                    "net_balance": net_balance,
                    "transaction_count": len(transactions)
                },
                "insights": insights,
                "recommendations": await self._generate_recommendations(transactions, loans_result.data if loans_result.data else [])
            }
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                "message": "Unable to generate insights at this time",
                "insights": []
            }
    
    async def _generate_recommendations(self, transactions: List[Dict], loans: List[Dict]) -> List[str]:
        """Generate smart recommendations."""
        recommendations = []
        
        try:
            # Check if spending is increasing
            if len(transactions) >= 10:
                recent_expenses = [
                    t["amount"] for t in transactions[-5:]
                    if t.get("type") == "expense"
                ]
                older_expenses = [
                    t["amount"] for t in transactions[-10:-5]
                    if t.get("type") == "expense"
                ]
                
                if recent_expenses and older_expenses:
                    recent_avg = sum(recent_expenses) / len(recent_expenses)
                    older_avg = sum(older_expenses) / len(older_expenses)
                    
                    if recent_avg > older_avg * 1.2:
                        recommendations.append("📈 Your expenses are increasing. Consider reviewing your spending.")
            
            # Check for unpaid loans
            if loans:
                total_due = sum(l.get("remaining_amount", 0) for l in loans)
                if total_due > 0:
                    recommendations.append(f"💸 You have Rs {total_due:,.0f} in pending loans. Consider setting reminders.")
            
            # Encourage regular tracking
            from datetime import datetime, timedelta
            if transactions:
                latest = transactions[-1]
                if latest.get("date"):
                    last_date = datetime.fromisoformat(latest["date"])
                    days_since = (datetime.now() - last_date).days
                    
                    if days_since > 3:
                        recommendations.append("📝 Keep your records up to date! Log today's transactions.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []


# Global intelligence engine instance
intelligence_engine = IntelligenceEngine()

