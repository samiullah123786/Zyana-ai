"""User mapping service to convert Telegram IDs to internal user IDs.

Telegram IDs can be very large (>2 billion), exceeding PostgreSQL INTEGER limits.
This service maps them to internal user IDs safely.
"""
import logging
from typing import Optional
from clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class UserMapper:
    """Maps external user IDs (like Telegram IDs) to internal user IDs."""
    
    def __init__(self):
        """Initialize user mapper."""
        self._cache = {}  # Simple in-memory cache
    
    async def get_internal_user_id(self, telegram_id: str) -> int:
        """Get or create internal user ID from Telegram ID.
        
        Args:
            telegram_id: Telegram user ID (string to handle large numbers)
            
        Returns:
            Internal integer user ID (safe for PostgreSQL INTEGER)
        """
        # Check cache first
        if telegram_id in self._cache:
            return self._cache[telegram_id]
        
        try:
            # Try to find existing user by telegram_id
            result = supabase_client.admin.table("users").select(
                "id"
            ).eq("telegram_id", telegram_id).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                internal_id = result.data[0]["id"]
                logger.debug(f"Found existing user: telegram_id={telegram_id} -> id={internal_id}")
                self._cache[telegram_id] = internal_id
                return internal_id
            
            # User doesn't exist, create new one
            logger.info(f"Creating new user for telegram_id={telegram_id}")
            new_user = supabase_client.admin.table("users").insert({
                "telegram_id": telegram_id,
                "name": f"User {telegram_id[:8]}",
                "created_at": "now()"
            }).execute()
            
            if new_user.data and len(new_user.data) > 0:
                internal_id = new_user.data[0]["id"]
                logger.info(f"✅ Created new user: telegram_id={telegram_id} -> id={internal_id}")
                self._cache[telegram_id] = internal_id
                return internal_id
            
            # Fallback if insert somehow failed
            logger.error(f"Failed to create user for telegram_id={telegram_id}, using fallback")
            return 1  # Fallback to default user
            
        except Exception as e:
            logger.error(f"Error mapping telegram_id={telegram_id}: {e}", exc_info=True)
            # Fallback to user_id=1 to prevent crashes
            return 1
    
    def clear_cache(self):
        """Clear the user mapping cache."""
        self._cache = {}


# Global instance
user_mapper = UserMapper()

