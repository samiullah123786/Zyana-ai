"""Habit Learning Agent - learns user preferences and patterns."""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

from models.schemas import ParsedMessage
from clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class HabitLearner:
    """Agent for learning and suggesting user habits."""
    
    CONFIRMATION_THRESHOLD = 3  # Number of occurrences before suggesting
    CONFIDENCE_THRESHOLD = 0.7  # Confidence score threshold
    
    async def observe_interaction(self, parsed: ParsedMessage, user_id: str):
        """Observe user interaction and learn patterns.
        
        Args:
            parsed: Parsed message
            user_id: User identifier
        """
        try:
            # Learn currency preference
            if parsed.currency:
                await self._update_pattern("preferred_currency", parsed.currency, user_id)
            
            # Learn business association with categories
            if parsed.business and parsed.category:
                await self._update_pattern(
                    f"business_category_{parsed.business}",
                    parsed.category,
                    user_id
                )
            
            # Learn frequent contacts
            if parsed.person:
                await self._update_pattern("frequent_contact", parsed.person, user_id)
            
            # Learn default business if not specified
            if parsed.business:
                await self._update_pattern("default_business", parsed.business, user_id)
            
        except Exception as e:
            logger.error(f"Error in habit learning: {e}")
    
    async def _update_pattern(self, key: str, value: str, user_id: str):
        """Update a pattern occurrence.
        
        Args:
            key: Pattern key
            value: Pattern value
            user_id: User identifier
        """
        # Get existing habit
        result = supabase_client.admin.table("habit_profiles").select("*").eq(
            "user_id", 1  # TODO: Map user_id
        ).eq("key", key).execute()
        
        if result.data:
            # Update existing
            habit = result.data[0]
            
            # If same value, increment occurrences
            if habit["value"] == value:
                new_occurrences = habit["occurrences"] + 1
                new_confidence = min(0.95, habit["confidence_score"] + 0.05)
                
                supabase_client.admin.table("habit_profiles").update({
                    "occurrences": new_occurrences,
                    "confidence_score": new_confidence,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", habit["id"]).execute()
                
                logger.debug(f"Updated habit: {key}={value} (occurrences: {new_occurrences})")
            else:
                # Different value - this might be a change
                # Only update if new pattern has occurred enough
                pass
        else:
            # Create new habit
            supabase_client.admin.table("habit_profiles").insert({
                "user_id": 1,  # TODO: Map user_id
                "key": key,
                "value": value,
                "confidence_score": 0.3,
                "occurrences": 1
            }).execute()
            
            logger.debug(f"Created new habit pattern: {key}={value}")
    
    async def get_suggestions(self, user_id: str) -> Dict[str, Any]:
        """Get habit suggestions that need confirmation.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with suggestions
        """
        # Get habits with low-medium confidence that have enough occurrences
        result = supabase_client.admin.table("habit_profiles").select("*").eq(
            "user_id", 1  # TODO: Map user_id
        ).gte("occurrences", self.CONFIRMATION_THRESHOLD).lt(
            "confidence_score", self.CONFIDENCE_THRESHOLD
        ).execute()
        
        suggestions = []
        for habit in result.data:
            suggestions.append({
                "key": habit["key"],
                "value": habit["value"],
                "occurrences": habit["occurrences"],
                "message": self._generate_confirmation_message(habit)
            })
        
        return {"suggestions": suggestions}
    
    def _generate_confirmation_message(self, habit: Dict) -> str:
        """Generate a confirmation message for a habit.
        
        Args:
            habit: Habit dict
            
        Returns:
            Confirmation message
        """
        key = habit["key"]
        value = habit["value"]
        
        if key == "preferred_currency":
            return f"I noticed you usually use {value}. Should I default to {value} for amounts?"
        
        elif key == "default_business":
            return f"You seem to work mostly with {value}. Should I assume {value} when you don't specify?"
        
        elif key.startswith("business_category_"):
            business = key.replace("business_category_", "")
            return f"For {business}, you often use category '{value}'. Make this the default?"
        
        elif key == "frequent_contact":
            return f"You interact frequently with {value}. Should I prioritize them in suggestions?"
        
        else:
            return f"Confirm preference: {key} = {value}?"
    
    async def confirm_habit(self, key: str, user_id: str):
        """Confirm a habit suggestion (increase confidence).
        
        Args:
            key: Habit key
            user_id: User identifier
        """
        supabase_client.admin.table("habit_profiles").update({
            "confidence_score": 0.95
        }).eq("user_id", 1).eq("key", key).execute()
        
        logger.info(f"Confirmed habit: {key}")
    
    async def reject_habit(self, key: str, user_id: str):
        """Reject a habit suggestion (delete it).
        
        Args:
            key: Habit key
            user_id: User identifier
        """
        supabase_client.admin.table("habit_profiles").delete().eq(
            "user_id", 1
        ).eq("key", key).execute()
        
        logger.info(f"Rejected habit: {key}")


# Global instance
habit_learner = HabitLearner()

