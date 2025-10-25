"""Intelligent Intent Router - Zyana's Core Brain.

This module uses ChatGPT-5 via Fal AI to intelligently route messages
to the appropriate sub-agent or respond conversationally.
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from clients.fal_client import fal_client
from clients.supabase_client import supabase_client
from config import settings

logger = logging.getLogger(__name__)


class IntentRouter:
    """Core brain that routes intents and maintains conversation context."""
    
    def __init__(self):
        """Initialize intent router with Fal AI (ChatGPT-5)."""
        self.model = "gpt-5-chat"  # ChatGPT-5 via Fal AI
        logger.info(f"✅ Intelligent Intent Router initialized with model: {self.model}")
    
    async def route_intent(
        self,
        message: str,
        user_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze message and route to appropriate handler.
        
        Args:
            message: User's natural language message
            user_id: User identifier
            user_context: Optional user context from memory
            
        Returns:
            Dict with:
                - intent: Detected intent type
                - parameters: Extracted parameters for sub-agent
                - response: Text response to user
                - route_to: Sub-agent to route to (or None for chat)
        """
        try:
            # Load user context if not provided
            if user_context is None:
                user_context = await self._load_user_context(user_id)
            
            # Build AI prompt
            system_prompt = self._build_system_prompt(user_context)
            
            # Call ChatGPT-5 via Fal AI
            ai_response = await self._call_chatgpt5(message, system_prompt)
            
            # Parse AI response
            result = self._parse_ai_response(ai_response)
            
            # Update user context
            await self._update_user_context(user_id, message, result)
            
            logger.info(f"🧠 Intent routed: {result['intent']} for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in intent routing: {e}", exc_info=True)
            # Fallback to safe chat response
            return {
                "intent": "chat",
                "parameters": {},
                "response": "I'm here! How can I help you today?",
                "route_to": None,
                "confidence": 0.5
            }
    
    def _build_system_prompt(self, user_context: Dict[str, Any]) -> str:
        """Build system prompt for ChatGPT-5.
        
        Args:
            user_context: User's context and preferences
            
        Returns:
            System prompt string
        """
        last_intent = user_context.get("last_intent", "none")
        preferences = user_context.get("preferences", {})
        tone = user_context.get("tone", "friendly")
        
        return f"""You are Zyana's core brain - an intelligent, friendly AI assistant.

Your job: Analyze user messages and decide if they contain actionable tasks or are casual conversation.

**Available Actions:**
- schedule_meeting: Book calendar events (e.g., "meeting at 5pm tomorrow")
- record_expense: Log financial transactions (e.g., "spent 5000 on software")
- record_income: Log income (e.g., "received 10k from client")
- loan: Track loans given/received (e.g., "lent Ali 5000")
- set_reminder: Set notifications (e.g., "remind me to call John")
- note_idea: Save notes/memories (e.g., "remember my password is xyz")
- create_invoice: Generate invoices (e.g., "invoice ABC Corp for $5000")
- track_client: Add/update clients (e.g., "add client XYZ Company")
- query_status: Check balances, summaries (e.g., "how much did I spend?")
- chat: Casual conversation, no specific action

**User Context:**
- Last intent: {last_intent}
- Preferences: {json.dumps(preferences)}
- Tone: {tone}

**Your Response Format (JSON):**
{{
  "intent": "one of the actions above",
  "parameters": {{
    "title": "extracted event/transaction name",
    "amount": extracted number,
    "person": "person's name",
    "datetime": "extracted date/time",
    "description": "any additional details",
    "business": "business name if mentioned"
  }},
  "response": "friendly text response to user",
  "confidence": 0.0 to 1.0
}}

**Examples:**

User: "Schedule meeting with Ali at 5pm tomorrow"
{{
  "intent": "schedule_meeting",
  "parameters": {{"title": "Meeting with Ali", "datetime": "tomorrow 5pm", "person": "Ali"}},
  "response": "Got it! I'll schedule a meeting with Ali tomorrow at 5pm.",
  "confidence": 0.95
}}

User: "Bro I'm tired today"
{{
  "intent": "chat",
  "parameters": {{}},
  "response": "I feel you! Take it easy and rest up. You've earned it. 💪",
  "confidence": 0.9
}}

User: "Note that I spent 5000 on editing software"
{{
  "intent": "record_expense",
  "parameters": {{"amount": 5000, "description": "editing software", "category": "software"}},
  "response": "✅ Recorded expense of 5000 for editing software!",
  "confidence": 0.95
}}

**Rules:**
1. Be friendly and casual
2. Use emojis appropriately
3. If unsure, default to "chat" intent
4. Extract ALL relevant parameters
5. Respond in user's language/tone
6. Be context-aware based on user preferences

Now analyze this message:"""
    
    async def _call_chatgpt5(
        self,
        message: str,
        system_prompt: str
    ) -> str:
        """Call ChatGPT-5 via Fal AI.
        
        Args:
            message: User message
            system_prompt: System instructions
            
        Returns:
            AI response as JSON string
        """
        try:
            # Use Fal AI client
            response = await fal_client.chat_simple(
                prompt=message,
                system_prompt=system_prompt,
                model=self.model,
                temperature=0.3,  # Lower for more consistent JSON
                max_tokens=500
            )
            
            logger.info(f"🤖 ChatGPT-5 response received ({len(response)} chars)")
            return response
            
        except Exception as e:
            logger.error(f"❌ ChatGPT-5 API error: {e}")
            raise
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response into structured format.
        
        Args:
            ai_response: Raw AI response (should be JSON)
            
        Returns:
            Parsed intent dict
        """
        try:
            # Try to parse as JSON
            result = json.loads(ai_response)
            
            # Map intent to route_to
            intent = result.get("intent", "chat")
            route_to = self._map_intent_to_agent(intent)
            
            result["route_to"] = route_to
            
            # Ensure required fields
            result.setdefault("parameters", {})
            result.setdefault("response", "I'm here to help!")
            result.setdefault("confidence", 0.5)
            
            return result
            
        except json.JSONDecodeError:
            # AI returned non-JSON, treat as chat response
            logger.warning(f"⚠️  Non-JSON response from AI, treating as chat")
            return {
                "intent": "chat",
                "parameters": {},
                "response": ai_response,
                "route_to": None,
                "confidence": 0.3
            }
    
    def _map_intent_to_agent(self, intent: str) -> Optional[str]:
        """Map intent to sub-agent name.
        
        Args:
            intent: Detected intent
            
        Returns:
            Agent name or None for chat
        """
        mapping = {
            "schedule_meeting": "calendar",
            "record_expense": "finance",
            "record_income": "finance",
            "loan": "finance",
            "set_reminder": "notification",
            "note_idea": "memory",
            "create_invoice": "invoice",
            "track_client": "client",
            "query_status": "finance",
            "chat": None
        }
        
        return mapping.get(intent)
    
    async def _load_user_context(self, user_id: str) -> Dict[str, Any]:
        """Load user context from Supabase.
        
        Args:
            user_id: User identifier
            
        Returns:
            User context dict
        """
        try:
            # Try to load from user_preferences table
            result = supabase_client.admin.table("user_preferences").select("*").eq(
                "user_id", user_id
            ).limit(1).execute()
            
            if result.data:
                prefs = result.data[0]
                return {
                    "last_intent": prefs.get("last_intent", "none"),
                    "preferences": prefs.get("preferences", {}),
                    "tone": prefs.get("preferred_tone", "friendly")
                }
            
            # Default context for new users
            return {
                "last_intent": "none",
                "preferences": {},
                "tone": "friendly"
            }
            
        except Exception as e:
            logger.error(f"Error loading user context: {e}")
            return {"last_intent": "none", "preferences": {}, "tone": "friendly"}
    
    async def _update_user_context(
        self,
        user_id: str,
        message: str,
        result: Dict[str, Any]
    ):
        """Update user context in Supabase.
        
        Args:
            user_id: User identifier
            message: User message
            result: Intent routing result
        """
        try:
            # Update user_preferences with last intent
            update_data = {
                "user_id": user_id,
                "last_intent": result["intent"],
                "last_message": message[:200],  # Store snippet
                "updated_at": datetime.now().isoformat()
            }
            
            # Upsert (insert or update)
            supabase_client.admin.table("user_preferences").upsert(
                update_data,
                on_conflict="user_id"
            ).execute()
            
            logger.info(f"💾 Updated context for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user context: {e}")


# Global instance
intent_router = IntentRouter()

