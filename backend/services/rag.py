"""RAG (Retrieval-Augmented Generation) service for memory-enhanced responses.

Integrates:
- Semantic memory retrieval from Qdrant
- User preference and habit profiles
- Mirror Mode style samples
- Prompt building with retrieved context
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from clients.qdrant_client import qdrant_client
from clients.supabase_client import supabase_client
from services.embeddings import embedding_service
from services.mirror_mode import mirror_mode_service
from config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Retrieval-Augmented Generation service for context-aware responses."""
    
    def __init__(self):
        """Initialize RAG service."""
        self.memory_collection = "zyana_memory"
        self.mirror_collection = "mirror_samples"
        logger.info("✅ RAG Service initialized")
    
    async def retrieve_relevant_memories(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        timeframe_days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories from Qdrant.
        
        Args:
            query: Search query
            user_id: User identifier
            top_k: Number of results to return
            timeframe_days: Optional time window (days back)
            
        Returns:
            List of relevant memory dicts with source, snippet, score
        """
        try:
            # Generate query embedding
            query_embedding = await embedding_service.embed_single(query)
            
            # Build filter
            filters = None
            if timeframe_days:
                cutoff_date = (datetime.now() - timedelta(days=timeframe_days)).isoformat()
                filters = {
                    "must": [
                        {"key": "user_id", "match": {"value": user_id}},
                        {"key": "date", "range": {"gte": cutoff_date}}
                    ]
                }
            else:
                filters = {
                    "must": [
                        {"key": "user_id", "match": {"value": user_id}}
                    ]
                }
            
            # Search Qdrant
            results = await qdrant_client.search_memory(
                query_vector=query_embedding,
                limit=top_k,
                filters=filters
            )
            
            logger.info(f"🔍 Retrieved {len(results)} relevant memories for user {user_id}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error retrieving memories: {e}", exc_info=True)
            return []
    
    async def build_rag_prompt(
        self,
        query: str,
        user_context: Dict[str, Any],
        retrieved_memories: List[Dict[str, Any]]
    ) -> str:
        """Build RAG-enhanced prompt with retrieved context.
        
        Args:
            query: User query
            user_context: User preferences and habits
            retrieved_memories: Retrieved memory results
            
        Returns:
            Formatted context string for system prompt
        """
        prompt_parts = []
        
        # Add retrieved memories
        if retrieved_memories:
            prompt_parts.append("**Relevant Memories:**")
            for i, memory in enumerate(retrieved_memories[:5], 1):
                snippet = memory.get('snippet', '')
                table = memory.get('table', 'unknown')
                date = memory.get('date', 'unknown')
                score = memory.get('score', 0)
                
                prompt_parts.append(
                    f"{i}. [{table}] {snippet[:100]}... "
                    f"(Date: {date}, Relevance: {score:.2f})"
                )
            prompt_parts.append("")
        
        # Add user habits/preferences
        if user_context:
            prompt_parts.append("**User Preferences:**")
            
            if user_context.get('default_business'):
                prompt_parts.append(f"• Preferred business: {user_context['default_business']}")
            
            if user_context.get('preferred_currency'):
                prompt_parts.append(f"• Currency: {user_context['preferred_currency']}")
            
            if user_context.get('common_categories'):
                cats = user_context['common_categories'][:3]
                prompt_parts.append(f"• Common categories: {', '.join(cats)}")
            
            prompt_parts.append("")
        
        return "\n".join(prompt_parts)
    
    async def get_user_memory_context(
        self,
        user_id: str,
        query: str,
        include_mirror: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive memory context for a user.
        
        Combines:
        - Semantic memories from Qdrant
        - Mirror Mode style samples (if enabled)
        - User preferences and habits
        
        Args:
            user_id: User identifier
            query: Current query/message
            include_mirror: Whether to include Mirror Mode samples
            
        Returns:
            Dict with:
                - memories: List of relevant memories
                - mirror_samples: List of style samples (if enabled)
                - user_preferences: User prefs dict
                - formatted_context: Pre-formatted string for prompt
        """
        try:
            # Retrieve semantic memories
            memories = await self.retrieve_relevant_memories(
                query=query,
                user_id=user_id,
                top_k=5,
                timeframe_days=settings.memory_summary_days
            )
            
            # Get Mirror Mode samples if enabled and requested
            mirror_samples = []
            if include_mirror:
                mirror_enabled = await mirror_mode_service.is_mirror_mode_enabled(int(user_id) if user_id.isdigit() else 1)
                
                if mirror_enabled:
                    mirror_samples = await self._retrieve_mirror_samples(
                        user_id=user_id,
                        top_k=settings.mirror_embed_k
                    )
            
            # Get user preferences/habits
            user_prefs = await self._get_user_preferences(user_id)
            
            # Build formatted context
            formatted_context = await self.build_rag_prompt(
                query=query,
                user_context=user_prefs,
                retrieved_memories=memories
            )
            
            # Add mirror samples to context if present
            if mirror_samples:
                mirror_context = self._format_mirror_samples(mirror_samples)
                formatted_context = formatted_context + "\n" + mirror_context
            
            return {
                'memories': memories,
                'mirror_samples': mirror_samples,
                'user_preferences': user_prefs,
                'formatted_context': formatted_context,
                'has_context': bool(memories or mirror_samples)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user memory context: {e}", exc_info=True)
            return {
                'memories': [],
                'mirror_samples': [],
                'user_preferences': {},
                'formatted_context': '',
                'has_context': False
            }
    
    async def _retrieve_mirror_samples(
        self,
        user_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve Mirror Mode style samples.
        
        Args:
            user_id: User identifier
            top_k: Number of samples to retrieve
            
        Returns:
            List of mirror sample dicts
        """
        try:
            # Get recent samples from database
            result = supabase_client.admin.table("user_message_samples").select(
                "message, timestamp"
            ).eq("user_id", int(user_id) if user_id.isdigit() else 1).order(
                "timestamp", desc=True
            ).limit(top_k).execute()
            
            samples = []
            if result.data:
                for sample in result.data:
                    samples.append({
                        'message': sample['message'],
                        'timestamp': sample['timestamp']
                    })
            
            logger.debug(f"✅ Retrieved {len(samples)} mirror samples for user {user_id}")
            return samples
            
        except Exception as e:
            logger.error(f"❌ Error retrieving mirror samples: {e}")
            return []
    
    async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences and learned patterns.
        
        Args:
            user_id: User identifier
            
        Returns:
            User preferences dict
        """
        try:
            # Get from user_preferences table
            result = supabase_client.admin.table("user_preferences").select(
                "*"
            ).eq("user_id", user_id).limit(1).execute()
            
            if result.data:
                return result.data[0]
            
            # Fallback: Try to infer from patterns
            return {
                'default_business': None,
                'preferred_currency': 'PKR',
                'timezone': settings.default_timezone,
                'language': 'en'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user preferences: {e}")
            return {}
    
    def _format_mirror_samples(self, samples: List[Dict[str, Any]]) -> str:
        """Format mirror samples for prompt inclusion.
        
        Args:
            samples: List of mirror sample dicts
            
        Returns:
            Formatted string
        """
        if not samples:
            return ""
        
        lines = ["**Communication Style Examples:**"]
        lines.append(f"Write in a style similar to {settings.owner_name}'s messages:")
        
        for i, sample in enumerate(samples[:3], 1):
            message = sample['message']
            lines.append(f"{i}. \"{message}\"")
        
        lines.append("")
        return "\n".join(lines)


# Global instance
rag_service = RAGService()

