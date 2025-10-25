"""Redis-based session manager for multi-turn clarification conversations.

Handles storing and retrieving session state for calendar clarifications and
other multi-turn interactions.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import redis
from config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions in Redis for multi-turn conversations."""
    
    def __init__(self):
        """Initialize session manager with Redis connection."""
        try:
            # Parse Redis URL
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ SessionManager connected to Redis: {settings.redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def create_session(
        self,
        user_id: str,
        intent: str,
        pending_fields: List[str],
        partial_data: Dict[str, Any],
        initial_message: str
    ) -> str:
        """Create a new session for multi-turn clarification.
        
        Args:
            user_id: User identifier
            intent: Current intent (e.g., 'schedule_meeting')
            pending_fields: List of fields that need clarification
            partial_data: Partially resolved data
            initial_message: Initial user message
            
        Returns:
            Session ID
        """
        if not self.redis_client:
            logger.warning("⚠️  Redis not available, session not created")
            return f"local_{user_id}_{int(datetime.now().timestamp())}"
        
        try:
            session_id = f"session:{user_id}:{intent}:{int(datetime.now().timestamp())}"
            
            session_data = {
                'user_id': user_id,
                'intent': intent,
                'pending_fields': pending_fields,
                'partial_data': partial_data,
                'conversation_history': [
                    {
                        'role': 'user',
                        'message': initial_message,
                        'timestamp': datetime.now().isoformat()
                    }
                ],
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=settings.redis_session_ttl)).isoformat()
            }
            
            # Store in Redis with TTL
            self.redis_client.setex(
                session_id,
                settings.redis_session_ttl,
                json.dumps(session_data)
            )
            
            logger.info(
                f"✅ Created session {session_id} for user {user_id} "
                f"(intent: {intent}, pending: {pending_fields})"
            )
            
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Error creating session: {e}", exc_info=True)
            return f"local_{user_id}_{int(datetime.now().timestamp())}"
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dict or None if not found
        """
        if not self.redis_client:
            logger.warning("⚠️  Redis not available")
            return None
        
        try:
            session_json = self.redis_client.get(session_id)
            
            if not session_json:
                logger.info(f"ℹ️  Session not found: {session_id}")
                return None
            
            session_data = json.loads(session_json)
            
            logger.info(f"✅ Retrieved session {session_id}")
            
            return session_data
            
        except Exception as e:
            logger.error(f"❌ Error retrieving session: {e}", exc_info=True)
            return None
    
    def get_active_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent active session for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Session data dict or None if no active session
        """
        if not self.redis_client:
            return None
        
        try:
            # Search for sessions matching pattern
            pattern = f"session:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            if not keys:
                return None
            
            # Get the most recent session (highest timestamp)
            keys.sort(reverse=True)
            
            for key in keys:
                session_data = self.get_session(key)
                if session_data and session_data.get('status') == 'pending':
                    session_data['session_id'] = key
                    return session_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting active session: {e}", exc_info=True)
            return None
    
    def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any],
        add_message: Optional[str] = None,
        message_role: str = 'assistant'
    ) -> bool:
        """Update session data.
        
        Args:
            session_id: Session identifier
            updates: Dict of fields to update
            add_message: Optional message to append to conversation history
            message_role: Role of the message ('user' or 'assistant')
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            logger.warning("⚠️  Redis not available")
            return False
        
        try:
            session_data = self.get_session(session_id)
            
            if not session_data:
                logger.warning(f"⚠️  Session not found for update: {session_id}")
                return False
            
            # Apply updates
            session_data.update(updates)
            
            # Add message to conversation history if provided
            if add_message:
                session_data['conversation_history'].append({
                    'role': message_role,
                    'message': add_message,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Update timestamp
            session_data['updated_at'] = datetime.now().isoformat()
            
            # Get remaining TTL
            ttl = self.redis_client.ttl(session_id)
            if ttl <= 0:
                ttl = settings.redis_session_ttl
            
            # Store updated session
            self.redis_client.setex(
                session_id,
                ttl,
                json.dumps(session_data)
            )
            
            logger.info(f"✅ Updated session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating session: {e}", exc_info=True)
            return False
    
    def clear_session(self, session_id: str) -> bool:
        """Clear/delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(session_id)
            
            if result > 0:
                logger.info(f"✅ Cleared session {session_id}")
                return True
            else:
                logger.warning(f"⚠️  Session not found: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error clearing session: {e}", exc_info=True)
            return False
    
    def mark_session_complete(self, session_id: str) -> bool:
        """Mark a session as completed.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_session(
            session_id,
            {
                'status': 'completed',
                'completed_at': datetime.now().isoformat()
            }
        )
    
    def mark_session_cancelled(self, session_id: str) -> bool:
        """Mark a session as cancelled.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_session(
            session_id,
            {
                'status': 'cancelled',
                'cancelled_at': datetime.now().isoformat()
            }
        )
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of conversation messages
        """
        session_data = self.get_session(session_id)
        
        if not session_data:
            return []
        
        history = session_data.get('conversation_history', [])
        
        # Return last N messages
        return history[-limit:] if len(history) > limit else history


# Global instance
session_manager = SessionManager()

