"""Intelligent Intent Router - Zyana's Core Brain.

This module uses ChatGPT-5 via Fal AI to intelligently route messages
to the appropriate sub-agent or respond conversationally.

Enhanced with:
- Strict function calling for calendar intents
- Multi-turn clarification support
- Session-based conversation management
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from clients.fal_client import fal_client
from clients.supabase_client import supabase_client
from services.session_manager import session_manager
from services.datetime_parser import datetime_parser
from services.context_retriever import context_retriever
from services.rag import rag_service
from services.mirror_mode import mirror_mode_service
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
        """Analyze message and route to appropriate handler with clarification support.
        
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
                - needs_clarification: True if clarification needed
                - session_id: Session ID for multi-turn clarification
        """
        try:
            # Check for active session (user replying to clarification)
            active_session = session_manager.get_active_session(user_id)
            
            if active_session:
                logger.info(f"📝 Continuing active session for user {user_id}")
                return await self._handle_clarification_response(
                    message,
                    user_id,
                    active_session
                )
            
            # Load user context if not provided
            if user_context is None:
                user_context = await self._load_user_context(user_id)
            
            # Get relevant calendar context from Qdrant
            calendar_context = await context_retriever.get_calendar_context(
                user_id,
                message,
                days_back=90,
                limit=3
            )
            
            # Get RAG memory context (semantic memories + mirror mode + preferences)
            memory_context = await rag_service.get_user_memory_context(
                user_id,
                message,
                include_mirror=True
            )
            
            # Build AI prompt with enhanced context
            system_prompt = self._build_system_prompt(user_context, calendar_context, memory_context)
            
            # Call ChatGPT-5 via Fal AI
            ai_response = await self._call_chatgpt5(message, system_prompt)
            
            # Parse AI response
            result = self._parse_ai_response(ai_response)
            
            # Validate and check for clarification needs
            if result['intent'] in ['schedule_meeting', 'reschedule_meeting', 'set_reminder']:
                validated = await self._validate_calendar_intent(result, message, user_id)
                result.update(validated)
            
            # Update user context
            await self._update_user_context(user_id, message, result)
            
            # Apply Mirror Mode style transformation to response
            if result.get('response'):
                try:
                    # Convert user_id to int for mirror_mode_service
                    internal_user_id = int(user_id) if user_id.isdigit() else 1
                    transformed_response = await mirror_mode_service.apply_style_transformation(
                        result['response'],
                        internal_user_id
                    )
                    result['response'] = transformed_response
                    logger.debug(f"✨ Applied Mirror Mode transformation for user {user_id}")
                except Exception as mirror_error:
                    logger.warning(f"⚠️  Mirror Mode transformation failed: {mirror_error}")
                    # Keep original response if transformation fails
            
            logger.info(
                f"🧠 Intent routed: {result['intent']} for user {user_id} "
                f"(confidence: {result.get('confidence', 0):.2f})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in intent routing: {e}", exc_info=True)
            # Fallback to safe chat response
            return {
                "intent": "chat",
                "parameters": {},
                "response": "I'm here! How can I help you today?",
                "route_to": None,
                "confidence": 0.5,
                "needs_clarification": False
            }
    
    def _build_system_prompt(
        self,
        user_context: Dict[str, Any],
        calendar_context: Optional[Dict[str, Any]] = None,
        memory_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build system prompt for ChatGPT-5 with strict function calling and RAG context.
        
        Args:
            user_context: User's context and preferences
            calendar_context: Recent calendar events and context
            memory_context: RAG memory context (semantic memories + mirror mode)
            
        Returns:
            System prompt string
        """
        last_intent = user_context.get("last_intent", "none")
        preferences = user_context.get("preferences", {})
        tone = user_context.get("tone", "friendly")
        owner_name = settings.owner_name
        
        # Add calendar context if available
        calendar_context_text = ""
        if calendar_context and calendar_context.get('context_summary'):
            calendar_context_text = f"\n\n**Recent Calendar Context:**\n{calendar_context['context_summary']}"
        
        # Add RAG memory context if available
        memory_context_text = ""
        if memory_context and memory_context.get('has_context'):
            memory_context_text = f"\n\n{memory_context.get('formatted_context', '')}"
        
        return f"""You are Zyana - {owner_name}'s intelligent, friendly AI assistant.

Your job: Analyze user messages and decide if they contain actionable tasks or are casual conversation.

**Available Actions:**
- schedule_meeting: Book calendar events (e.g., "meeting at 5pm tomorrow")
- reschedule_meeting: Change existing event time
- cancel_meeting: Cancel scheduled event
- set_reminder: Set notifications (e.g., "remind me to call John")
- record_expense: Log financial transactions (e.g., "spent 5000 on software")
- record_income: Log income (e.g., "received 10k from client")
- loan: Track loans given/received (e.g., "lent Ali 5000")
- note_idea: Save notes/memories (e.g., "remember my password is xyz")
- create_invoice: Generate invoices (e.g., "invoice ABC Corp for $5000")
- track_client: Add/update clients (e.g., "add client XYZ Company")
- query_status: Check balances, summaries (e.g., "how much did I spend?")
- chat: Casual conversation, no specific action

**User Context:**
- Owner: {owner_name}
- Last intent: {last_intent}
- Preferences: {json.dumps(preferences)}
- Tone: {tone}
- Timezone: {settings.default_timezone}{calendar_context_text}{memory_context_text}

**STRICT OUTPUT FORMAT (JSON ONLY - NO EXTRA TEXT):**

For calendar intents (schedule_meeting, reschedule_meeting, set_reminder):
{{
  "intent": "schedule_meeting",
  "title": "Meeting with Ali" or null,
  "start_iso": "2025-10-26T17:00:00+05:00" or null,
  "end_iso": "2025-10-26T18:00:00+05:00" or null,
  "duration_minutes": 60 or null,
  "attendees": ["Ali", "someone@example.com"] or [],
  "location": "Office" or null,
  "confidence": 0.0-1.0,
  "response": "friendly text response"
}}

For other intents:
{{
  "intent": "record_expense|record_income|loan|chat|etc",
  "parameters": {{
    "amount": number or null,
    "person": "name" or null,
    "description": "text" or null,
    "business": "business name" or null
  }},
  "response": "friendly text response",
  "confidence": 0.0-1.0
}}

**Calendar Intent Rules:**
1. If user mentions specific time (3pm, tomorrow, etc), try to parse to ISO8601 with timezone +05:00 (Asia/Karachi)
2. If time is unclear/missing, return null for start_iso and set confidence < 0.7
3. If date is missing, return null for start_iso
4. Always extract attendees from phrases like "with Ali", "call John"
5. Default duration: 60 minutes for meetings, 15 minutes for reminders

**Examples:**

User: "Schedule meeting with Ali tomorrow at 3pm"
{{
  "intent": "schedule_meeting",
  "title": "Meeting with Ali",
  "start_iso": "2025-10-26T15:00:00+05:00",
  "end_iso": "2025-10-26T16:00:00+05:00",
  "duration_minutes": 60,
  "attendees": ["Ali"],
  "location": null,
  "confidence": 0.95,
  "response": "Got it, {owner_name}! I'll schedule a meeting with Ali tomorrow at 3pm."
}}

User: "Schedule lunch with team next Friday"
{{
  "intent": "schedule_meeting",
  "title": "Lunch with team",
  "start_iso": null,
  "end_iso": null,
  "duration_minutes": 60,
  "attendees": ["team"],
  "location": null,
  "confidence": 0.6,
  "response": "Sure! What time works for lunch next Friday?"
}}

User: "Schedule a meeting"
{{
  "intent": "schedule_meeting",
  "title": "Meeting",
  "start_iso": null,
  "end_iso": null,
  "duration_minutes": 60,
  "attendees": [],
  "location": null,
  "confidence": 0.4,
  "response": "I'd be happy to schedule a meeting! When would you like it?"
}}

User: "Hey Zyana, what's up?"
{{
  "intent": "chat",
  "parameters": {{}},
  "response": "Hey {owner_name}! All good here. What can I help you with? 😊",
  "confidence": 1.0
}}

**Critical Rules:**
1. Output ONLY valid JSON, no markdown or extra text
2. Use owner name "{owner_name}" when appropriate
3. For calendar intents, prefer ISO timestamps when possible
4. If uncertain (confidence < 0.7), be honest and ask for clarification
5. Be friendly, casual, and helpful

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
    
    async def _validate_calendar_intent(
        self,
        result: Dict[str, Any],
        message: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Validate calendar intent and check if clarification is needed.
        
        Args:
            result: Parsed intent result
            message: Original user message
            user_id: User identifier
            
        Returns:
            Dict with validation results and clarification needs
        """
        needs_clarification = False
        pending_fields = []
        partial_data = {}
        
        # Extract calendar-specific fields
        title = result.get('title') or result.get('parameters', {}).get('title')
        start_iso = result.get('start_iso')
        end_iso = result.get('end_iso')
        duration_minutes = result.get('duration_minutes', 60)
        attendees = result.get('attendees', [])
        location = result.get('location')
        confidence = result.get('confidence', 0.5)
        
        # If start_iso is missing or null, try datetime parser
        if not start_iso:
            parsed_datetime = datetime_parser.parse_datetime(message)
            
            if parsed_datetime['iso_start']:
                start_iso = parsed_datetime['iso_start']
                end_iso = parsed_datetime['iso_end']
                confidence = max(confidence, parsed_datetime['confidence'])
            
            # Check if ambiguous
            if parsed_datetime['is_ambiguous'] or confidence < settings.confidence_threshold:
                needs_clarification = True
                pending_fields.append('datetime')
        
        # Check required fields
        if not title:
            # Try to extract from message
            if any(word in message.lower() for word in ['meeting', 'call', 'appointment']):
                title = "Meeting"
            else:
                needs_clarification = True
                pending_fields.append('title')
        
        # Build partial data
        partial_data = {
            'title': title,
            'start_iso': start_iso,
            'end_iso': end_iso,
            'duration_minutes': duration_minutes,
            'attendees': attendees,
            'location': location
        }
        
        # If clarification needed, create session
        session_id = None
        clarification_question = None
        
        if needs_clarification:
            # Generate clarification question
            clarification_question = self._generate_clarification_question(
                pending_fields,
                partial_data,
                message
            )
            
            # Create session
            session_id = session_manager.create_session(
                user_id=user_id,
                intent=result['intent'],
                pending_fields=pending_fields,
                partial_data=partial_data,
                initial_message=message
            )
            
            logger.info(
                f"📝 Created clarification session {session_id} "
                f"(pending: {pending_fields})"
            )
        
        return {
            'needs_clarification': needs_clarification,
            'pending_fields': pending_fields,
            'partial_data': partial_data,
            'session_id': session_id,
            'clarification_question': clarification_question,
            'response': clarification_question if needs_clarification else result.get('response')
        }
    
    def _generate_clarification_question(
        self,
        pending_fields: List[str],
        partial_data: Dict[str, Any],
        original_message: str
    ) -> str:
        """Generate a clarification question for missing fields.
        
        Args:
            pending_fields: List of fields that need clarification
            partial_data: Partially resolved data
            original_message: Original user message
            
        Returns:
            Clarification question string
        """
        owner_name = settings.owner_name
        
        if 'datetime' in pending_fields:
            if partial_data.get('title'):
                return f"Sure, {owner_name}! What time should I schedule \"{partial_data['title']}\"?"
            else:
                return f"I'd be happy to schedule that, {owner_name}! When would you like it?"
        
        if 'title' in pending_fields:
            return f"Got it, {owner_name}! What should I call this event?"
        
        # Default clarification
        return f"Could you provide a bit more detail, {owner_name}? 😊"
    
    async def _handle_clarification_response(
        self,
        message: str,
        user_id: str,
        session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle user's response to a clarification question.
        
        Args:
            message: User's clarification response
            user_id: User identifier
            session: Active session data
            
        Returns:
            Updated intent result
        """
        try:
            session_id = session.get('session_id')
            pending_fields = session.get('pending_fields', [])
            partial_data = session.get('partial_data', {})
            original_intent = session.get('intent', 'schedule_meeting')
            
            logger.info(f"📝 Processing clarification response for session {session_id}")
            
            # Update session with new message
            session_manager.update_session(
                session_id,
                {},
                add_message=message,
                message_role='user'
            )
            
            # Try to resolve pending fields
            resolved_fields = []
            
            if 'datetime' in pending_fields:
                # Parse datetime from clarification
                parsed_datetime = datetime_parser.parse_datetime(message)
                
                if parsed_datetime['iso_start'] and not parsed_datetime['is_ambiguous']:
                    partial_data['start_iso'] = parsed_datetime['iso_start']
                    partial_data['end_iso'] = parsed_datetime['iso_end']
                    partial_data['duration_minutes'] = parsed_datetime['duration_minutes']
                    resolved_fields.append('datetime')
                elif parsed_datetime['confidence'] >= settings.confidence_threshold:
                    # Accept if confidence is good enough
                    partial_data['start_iso'] = parsed_datetime['iso_start']
                    partial_data['end_iso'] = parsed_datetime['iso_end']
                    resolved_fields.append('datetime')
            
            if 'title' in pending_fields:
                # Use the message as title if it's short enough
                if len(message.split()) <= 10:
                    partial_data['title'] = message
                    resolved_fields.append('title')
            
            # Update pending fields
            for field in resolved_fields:
                if field in pending_fields:
                    pending_fields.remove(field)
            
            # Check if all fields resolved
            if not pending_fields:
                # Mark session complete
                session_manager.mark_session_complete(session_id)
                
                # Return completed intent
                return {
                    'intent': original_intent,
                    'parameters': partial_data,
                    'response': f"Perfect, {settings.owner_name}! I'll create that event now.",
                    'route_to': 'calendar',
                    'confidence': 0.95,
                    'needs_clarification': False,
                    'session_id': session_id,
                    **partial_data
                }
            else:
                # Still need more clarification
                clarification_question = self._generate_clarification_question(
                    pending_fields,
                    partial_data,
                    message
                )
                
                # Update session
                session_manager.update_session(
                    session_id,
                    {
                        'pending_fields': pending_fields,
                        'partial_data': partial_data
                    },
                    add_message=clarification_question,
                    message_role='assistant'
                )
                
                return {
                    'intent': original_intent,
                    'parameters': partial_data,
                    'response': clarification_question,
                    'route_to': None,
                    'confidence': 0.5,
                    'needs_clarification': True,
                    'session_id': session_id,
                    'pending_fields': pending_fields
                }
                
        except Exception as e:
            logger.error(f"❌ Error handling clarification response: {e}", exc_info=True)
            # Clear session and return error
            if session_id:
                session_manager.clear_session(session_id)
            
            return {
                'intent': 'chat',
                'parameters': {},
                'response': "Sorry, I got confused. Could you start over? 😅",
                'route_to': None,
                'confidence': 0.3,
                'needs_clarification': False
            }


# Global instance
intent_router = IntentRouter()

