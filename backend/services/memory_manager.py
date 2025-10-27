"""Memory Manager - Multi-layer memory system for context-aware AI.

Implements three layers of memory:
1. Short-term: Recent conversation history (chat_sessions table)
2. Long-term: Persistent facts and preferences (user_memory table)
3. Semantic: Vector embeddings for similarity search (Qdrant)
"""
import logging
import json
import re
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pytz

from clients.supabase_client import supabase_client
from clients.qdrant_client import qdrant_client
from services.embeddings import embedding_service
from config import settings

logger = logging.getLogger(__name__)

PAKISTAN_TZ = pytz.timezone(settings.default_timezone)


class MemoryManager:
    """Manages all layers of AI memory for context-aware conversations."""
    
    def __init__(self):
        """Initialize Memory Manager."""
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = getattr(settings, 'memory_ttl', 3600)  # 1 hour default
        logger.info("✅ MemoryManager initialized")
    
    async def save_session_message(
        self,
        user_id: str,
        role: str,
        content: str,
        intent: Optional[str] = None,
        success: bool = True
    ) -> Dict[str, Any]:
        """Save a message to short-term memory (chat_sessions).
        
        Args:
            user_id: User identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            intent: Detected intent (optional)
            success: Whether the interaction was successful
            
        Returns:
            Dict with saved message data
        """
        try:
            result = supabase_client.admin.table("chat_sessions").insert({
                "user_id": user_id,
                "role": role,
                "content": content,
                "intent": intent,
                "success": success,
                "timestamp": datetime.now(PAKISTAN_TZ).isoformat()
            }).execute()
            
            logger.debug(f"💾 Saved message to chat_sessions: {role} ({len(content)} chars)")
            
            return {
                "success": True,
                "data": result.data[0] if result.data else {}
            }
            
        except Exception as e:
            logger.error(f"Error saving session message: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def get_recent_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch recent conversation history from short-term memory.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of recent messages (oldest first for context)
        """
        try:
            # Check cache first
            cache_key = f"history:{user_id}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    logger.debug(f"📦 Retrieved history from cache for user {user_id}")
                    return cached_data
            
            # Fetch from database
            result = supabase_client.admin.table("chat_sessions").select(
                "role, content, intent, timestamp"
            ).eq("user_id", user_id).order(
                "timestamp", desc=True
            ).limit(limit).execute()
            
            # Reverse to get chronological order (oldest first)
            messages = list(reversed(result.data)) if result.data else []
            
            # Cache the result
            self.cache[cache_key] = (messages, datetime.now())
            
            logger.debug(f"🔍 Retrieved {len(messages)} messages from chat_sessions")
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting recent history: {e}", exc_info=True)
            return []
    
    async def save_long_term_fact(
        self,
        user_id: str,
        fact_text: str
    ) -> Dict[str, Any]:
        """Save a fact to long-term memory (user_memory).
        
        Args:
            user_id: User identifier
            fact_text: Fact to store
            
        Returns:
            Dict with success status
        """
        try:
            # Get existing facts
            result = supabase_client.admin.table("user_memory").select(
                "facts"
            ).eq("user_id", user_id).execute()
            
            if result.data:
                # Append to existing facts
                existing_facts = result.data[0].get("facts", [])
                existing_facts.append({
                    "text": fact_text,
                    "timestamp": datetime.now(PAKISTAN_TZ).isoformat()
                })
                
                supabase_client.admin.table("user_memory").update({
                    "facts": existing_facts,
                    "last_updated": datetime.now(PAKISTAN_TZ).isoformat()
                }).eq("user_id", user_id).execute()
            else:
                # Create new entry
                supabase_client.admin.table("user_memory").insert({
                    "user_id": user_id,
                    "facts": [{
                        "text": fact_text,
                        "timestamp": datetime.now(PAKISTAN_TZ).isoformat()
                    }],
                    "last_updated": datetime.now(PAKISTAN_TZ).isoformat()
                }).execute()
            
            logger.info(f"💡 Saved long-term fact for user {user_id}: {fact_text[:50]}...")
            
            # Clear cache
            cache_key = f"facts:{user_id}"
            if cache_key in self.cache:
                del self.cache[cache_key]
            
            return {"success": True, "fact": fact_text}
            
        except Exception as e:
            logger.error(f"Error saving long-term fact: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def get_long_term_facts(
        self,
        user_id: str
    ) -> List[str]:
        """Retrieve all long-term facts for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of fact strings
        """
        try:
            # Check cache first
            cache_key = f"facts:{user_id}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    logger.debug(f"📦 Retrieved facts from cache for user {user_id}")
                    return cached_data
            
            # Fetch from database
            result = supabase_client.admin.table("user_memory").select(
                "facts"
            ).eq("user_id", user_id).execute()
            
            if result.data and result.data[0].get("facts"):
                facts = [fact["text"] for fact in result.data[0]["facts"]]
                
                # Cache the result
                self.cache[cache_key] = (facts, datetime.now())
                
                logger.debug(f"📚 Retrieved {len(facts)} long-term facts")
                return facts
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting long-term facts: {e}", exc_info=True)
            return []
    
    async def update_user_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ) -> Dict[str, Any]:
        """Update a user preference in long-term memory.
        
        Args:
            user_id: User identifier
            key: Preference key
            value: Preference value
            
        Returns:
            Dict with success status
        """
        try:
            # Get existing preferences
            result = supabase_client.admin.table("user_memory").select(
                "preferences"
            ).eq("user_id", user_id).execute()
            
            if result.data:
                # Update existing preferences
                preferences = result.data[0].get("preferences", {})
                preferences[key] = value
                
                supabase_client.admin.table("user_memory").update({
                    "preferences": preferences,
                    "last_updated": datetime.now(PAKISTAN_TZ).isoformat()
                }).eq("user_id", user_id).execute()
            else:
                # Create new entry
                supabase_client.admin.table("user_memory").insert({
                    "user_id": user_id,
                    "preferences": {key: value},
                    "last_updated": datetime.now(PAKISTAN_TZ).isoformat()
                }).execute()
            
            logger.info(f"⚙️  Updated preference for user {user_id}: {key} = {value}")
            
            return {"success": True, "preference": {key: value}}
            
        except Exception as e:
            logger.error(f"Error updating user preference: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def embed_and_store_memory(
        self,
        user_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create embedding and store in vector memory (Qdrant).
        
        Args:
            user_id: User identifier
            text: Text to embed
            metadata: Optional metadata to store with embedding
            
        Returns:
            Dict with success status
        """
        try:
            if not qdrant_client.initialized:
                logger.warning("⚠️  Qdrant not initialized, skipping vector storage")
                return {"success": False, "error": "Qdrant not available"}
            
            # Generate embedding
            embedding = await embedding_service.embed_single(text)
            
            # Prepare payload
            payload = {
                "user_id": user_id,
                "text": text,
                "type": "conversation",
                "timestamp": datetime.now(PAKISTAN_TZ).isoformat()
            }
            
            if metadata:
                payload.update(metadata)
            
            # Store in Qdrant with UUID point_id (required by Qdrant)
            point_id = str(uuid.uuid4())
            
            await qdrant_client.add_memory(
                point_id=point_id,
                embedding=embedding,
                payload=payload
            )
            
            logger.debug(f"🧠 Stored memory in Qdrant: {text[:50]}...")
            
            return {"success": True, "point_id": point_id}
            
        except Exception as e:
            logger.error(f"Error embedding and storing memory: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def search_similar_memories(
        self,
        user_id: str,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for similar memories using semantic search (Qdrant).
        
        Args:
            user_id: User identifier
            query: Query text
            top_k: Number of results to return
            
        Returns:
            List of similar memories
        """
        try:
            if not qdrant_client.initialized:
                logger.warning("⚠️  Qdrant not initialized, skipping semantic search")
                return []
            
            # Generate query embedding
            query_embedding = await embedding_service.embed_single(query)
            
            # Search in Qdrant
            filters = {
                "must": [
                    {"key": "user_id", "match": {"value": user_id}}
                ]
            }
            
            results = await qdrant_client.search_memory(
                query_vector=query_embedding,
                limit=top_k,
                filters=filters
            )
            
            logger.debug(f"🔍 Found {len(results)} similar memories for query: {query[:50]}...")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar memories: {e}", exc_info=True)
            return []
    
    async def build_context_for_ai(
        self,
        user_id: str,
        current_message: str
    ) -> Dict[str, Any]:
        """Build comprehensive context by combining all memory layers.
        
        Args:
            user_id: User identifier
            current_message: Current user message
            
        Returns:
            Dict with all context layers
        """
        try:
            # Fetch all memory layers in parallel
            history = await self.get_recent_history(
                user_id,
                limit=getattr(settings, 'max_chat_history', 10)
            )
            facts = await self.get_long_term_facts(user_id)
            semantic_results = await self.search_similar_memories(
                user_id,
                current_message,
                top_k=getattr(settings, 'semantic_search_k', 3)
            )
            
            # Format history for prompt
            chat_history = []
            for msg in history:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                chat_history.append(f"{role.capitalize()}: {content}")
            
            # Format facts for prompt
            user_facts = facts if facts else ["No long-term facts stored yet."]
            
            # Format semantic results for prompt
            semantic_context = []
            for result in semantic_results:
                text = result.get("text", "")
                score = result.get("score", 0)
                semantic_context.append(f"[Relevance: {score:.2f}] {text}")
            
            logger.info(f"📝 Built context: {len(chat_history)} messages, {len(facts)} facts, {len(semantic_results)} semantic results")
            
            return {
                "chat_history": "\n".join(chat_history) if chat_history else "No recent conversation history.",
                "user_facts": "\n- ".join(user_facts),
                "semantic_context": "\n".join(semantic_context) if semantic_context else "No relevant past context found."
            }
            
        except Exception as e:
            logger.error(f"Error building context for AI: {e}", exc_info=True)
            return {
                "chat_history": "",
                "user_facts": "",
                "semantic_context": ""
            }
    
    async def extract_facts_from_response(
        self,
        user_id: str,
        message: str,
        response: str
    ) -> None:
        """Intelligently extract facts from assistant response and save them.
        
        Detects patterns like:
        - "I've saved that..."
        - "I'll remember that..."
        - "Got it, your favorite..."
        
        Args:
            user_id: User identifier
            message: User's original message
            response: Assistant's response
        """
        try:
            # Patterns indicating fact storage
            fact_indicators = [
                "i've saved", "i'll remember", "noted that", "got it,", 
                "i've recorded", "logged that", "storing that", "saved it"
            ]
            
            response_lower = response.lower()
            
            if any(indicator in response_lower for indicator in fact_indicators):
                # Extract potential fact from user message
                # Simple extraction: use the user's message as the fact
                fact = message
                
                # Try to extract more specific fact from response
                # Look for quotes or specific details
                quote_pattern = r'"([^"]+)"'
                quotes = re.findall(quote_pattern, response)
                if quotes:
                    fact = quotes[0]
                
                await self.save_long_term_fact(user_id, fact)
                logger.info(f"🤖 Auto-extracted fact from conversation: {fact[:50]}...")
            
        except Exception as e:
            logger.error(f"Error extracting facts from response: {e}", exc_info=True)
    
    def clear_cache(self, user_id: Optional[str] = None):
        """Clear memory cache.
        
        Args:
            user_id: Optional user ID to clear specific user's cache. If None, clears all.
        """
        if user_id:
            # Clear specific user's cache
            keys_to_delete = [k for k in self.cache.keys() if user_id in k]
            for key in keys_to_delete:
                del self.cache[key]
            logger.debug(f"🗑️  Cleared cache for user {user_id}")
        else:
            # Clear all cache
            self.cache = {}
            logger.debug("🗑️  Cleared all memory cache")


# Global instance
memory_manager = MemoryManager()

