"""Context retrieval service for querying Qdrant vector memory.

Retrieves relevant calendar events and conversation history from Qdrant
to provide context for AI decision-making.
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from clients.qdrant_client import qdrant_client
from config import settings

logger = logging.getLogger(__name__)


class ContextRetriever:
    """Retrieves relevant context from Qdrant for calendar operations."""
    
    def __init__(self):
        """Initialize context retriever."""
        self.collection_name = "zyana_memory"
        logger.info("✅ ContextRetriever initialized")
    
    async def get_calendar_context(
        self,
        user_id: str,
        query_text: str,
        days_back: int = 90,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Get relevant calendar context from Qdrant.
        
        Args:
            user_id: User identifier
            query_text: Query text to search for
            days_back: Number of days to look back (default: 90)
            limit: Maximum number of results
            
        Returns:
            Dict with:
                - relevant_events: List of similar calendar events
                - context_summary: Text summary for AI
        """
        try:
            # Generate embedding for query using embedding service
            from services.embeddings import embedding_service
            embedding = await embedding_service.embed_single(query_text)
            
            # Search Qdrant with filters (use search_memory method)
            filters = {
                "must": [
                    {"key": "user_id", "match": {"value": user_id}},
                    {"key": "type", "match": {"value": "calendar"}}
                ]
            }
            
            results = await qdrant_client.search_memory(
                query_vector=embedding,
                limit=limit,
                filters=filters
            )
            
            relevant_events = []
            
            for result in results:
                relevant_events.append({
                    'id': result.get('id', ''),
                    'text': result.get('text', ''),
                    'event_title': result.get('event_title', ''),
                    'event_date': result.get('event_date', ''),
                    'attendees': result.get('attendees', []),
                    'score': result.get('score', 0)
                })
            
            # Create context summary
            context_summary = self._create_context_summary(relevant_events)
            
            logger.info(
                f"✅ Retrieved {len(relevant_events)} calendar context items "
                f"for user {user_id}"
            )
            
            return {
                'relevant_events': relevant_events,
                'context_summary': context_summary
            }
            
        except Exception as e:
            logger.error(f"❌ Error retrieving calendar context: {e}", exc_info=True)
            return {
                'relevant_events': [],
                'context_summary': ''
            }
    
    async def get_similar_events(
        self,
        user_id: str,
        event_title: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Find similar calendar events based on title.
        
        Args:
            user_id: User identifier
            event_title: Event title to find similar events for
            limit: Maximum number of results
            
        Returns:
            List of similar events
        """
        try:
            # Generate embedding for event title using embedding service
            from services.embeddings import embedding_service
            embedding = await embedding_service.embed_single(event_title)
            
            # Search Qdrant
            results = qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit,
                query_filter={
                    "must": [
                        {"key": "user_id", "match": {"value": user_id}},
                        {"key": "type", "match": {"value": "calendar"}},
                    ]
                }
            )
            
            similar_events = []
            
            for result in results:
                payload = result.payload
                similar_events.append({
                    'id': result.id,
                    'title': payload.get('event_title', ''),
                    'date': payload.get('event_date', ''),
                    'text': payload.get('text', ''),
                    'similarity_score': result.score
                })
            
            logger.info(
                f"✅ Found {len(similar_events)} similar events "
                f"for '{event_title}'"
            )
            
            return similar_events
            
        except Exception as e:
            logger.error(f"❌ Error finding similar events: {e}", exc_info=True)
            return []
    
    async def store_calendar_event(
        self,
        user_id: str,
        session_id: str,
        raw_text: str,
        resolved_title: str,
        resolved_start_iso: str,
        resolved_end_iso: str,
        attendees: List[str],
        confidence_score: float
    ) -> bool:
        """Store calendar event in Qdrant for future retrieval.
        
        Args:
            user_id: User identifier
            session_id: Session ID
            raw_text: Original user message
            resolved_title: Resolved event title
            resolved_start_iso: ISO start time
            resolved_end_iso: ISO end time
            attendees: List of attendees
            confidence_score: Confidence score
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create text representation for embedding
            text_repr = (
                f"Calendar event: {resolved_title}. "
                f"Original request: {raw_text}. "
                f"Time: {resolved_start_iso} to {resolved_end_iso}."
            )
            
            if attendees:
                text_repr += f" Attendees: {', '.join(attendees)}."
            
            # Generate embedding using embedding service
            from services.embeddings import embedding_service
            embedding = await embedding_service.embed_single(text_repr)
            
            # Prepare payload
            payload = {
                'user_id': user_id,
                'type': 'calendar',
                'session_id': session_id,
                'text': text_repr,
                'raw_text': raw_text,
                'event_title': resolved_title,
                'event_date': resolved_start_iso,
                'start_time': resolved_start_iso,
                'end_time': resolved_end_iso,
                'attendees': attendees,
                'confidence_score': confidence_score,
                'created_at': datetime.now().isoformat()
            }
            
            # Store in Qdrant using add_memory method with UUID point_id (required by Qdrant)
            point_id = str(uuid.uuid4())
            
            await qdrant_client.add_memory(
                point_id=point_id,
                embedding=embedding,
                payload=payload
            )
            
            logger.info(
                f"✅ Stored calendar event in Qdrant: {resolved_title} "
                f"(user: {user_id}, id: {point_id})"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing calendar event in Qdrant: {e}", exc_info=True)
            return False
    
    def _create_context_summary(self, events: List[Dict[str, Any]]) -> str:
        """Create a text summary of relevant events for AI context.
        
        Args:
            events: List of relevant event dicts
            
        Returns:
            Text summary
        """
        if not events:
            return ""
        
        summary_lines = ["Recent calendar context:"]
        
        for i, event in enumerate(events[:3], 1):
            title = event.get('event_title', 'Unknown')
            date = event.get('event_date', '')
            text = event.get('text', '')
            
            summary_lines.append(f"{i}. {title} - {date}")
            if text:
                summary_lines.append(f"   Context: {text[:100]}...")
        
        return "\n".join(summary_lines)


# Global instance
context_retriever = ContextRetriever()

