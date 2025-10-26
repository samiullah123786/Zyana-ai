"""Nightly summarization worker for memory consolidation.

Runs daily to:
1. Summarize each user's daily conversations
2. Embed summaries in Qdrant
3. Optionally compact old conversations
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from clients.openai_client import openai_client
from clients.qdrant_client import qdrant_client
from clients.supabase_client import supabase_client
from services.embeddings import embedding_service
from config import settings

logger = logging.getLogger(__name__)


class NightlySummarizer:
    """Worker for nightly memory summarization and consolidation."""
    
    def __init__(self):
        """Initialize nightly summarizer."""
        self.summary_days = settings.memory_summary_days
        logger.info("✅ NightlySummarizer initialized")
    
    async def summarize_user_day(
        self,
        user_id: str,
        date: datetime
    ) -> Dict[str, Any]:
        """Summarize a user's conversations for a specific day.
        
        Args:
            user_id: User identifier
            date: Date to summarize
            
        Returns:
            Dict with summary_id, summary_text, embedding_id
        """
        try:
            # Get conversations for the day
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            
            result = supabase_client.admin.table("conversations").select(
                "message, role, timestamp"
            ).eq("user_id", user_id).gte(
                "timestamp", start_date.isoformat()
            ).lt(
                "timestamp", end_date.isoformat()
            ).order("timestamp", desc=False).execute()
            
            if not result.data or len(result.data) == 0:
                logger.info(f"No conversations for user {user_id} on {date.date()}")
                return None
            
            # Format conversations
            conversation_text = self._format_conversations(result.data)
            
            # Generate summary using Fal AI
            summary = await self._generate_summary(conversation_text, user_id, date)
            
            if not summary:
                logger.warning(f"Failed to generate summary for user {user_id} on {date.date()}")
                return None
            
            # Store summary in memory_summaries table
            summary_result = supabase_client.admin.table("memory_summaries").insert({
                "user_id": user_id,
                "summary": summary,
                "date": date.date().isoformat(),
                "conversation_count": len(result.data)
            }).execute()
            
            if not summary_result.data:
                logger.error(f"Failed to store summary for user {user_id}")
                return None
            
            summary_id = summary_result.data[0]['id']
            
            # Generate embedding for summary
            embedding = await embedding_service.embed_single(summary)
            
            # Store in Qdrant
            point_id = f"summary_{summary_id}"
            
            await qdrant_client.add_memory(
                content=summary,
                embedding=embedding,
                metadata={
                    'user_id': user_id,
                    'table': 'memory_summaries',
                    'row_id': summary_id,
                    'date': date.isoformat(),
                    'snippet': summary[:200],
                    'type': 'daily_summary',
                    'conversation_count': len(result.data)
                },
                point_id=point_id
            )
            
            logger.info(
                f"✅ Created daily summary for user {user_id} on {date.date()} "
                f"({len(result.data)} conversations)"
            )
            
            return {
                'summary_id': summary_id,
                'summary_text': summary,
                'embedding_id': point_id,
                'conversation_count': len(result.data)
            }
            
        except Exception as e:
            logger.error(f"❌ Error summarizing day for user {user_id}: {e}", exc_info=True)
            return None
    
    def _format_conversations(self, conversations: List[Dict[str, Any]]) -> str:
        """Format conversations for summarization.
        
        Args:
            conversations: List of conversation records
            
        Returns:
            Formatted conversation text
        """
        lines = []
        for conv in conversations:
            role = conv.get('role', 'user')
            message = conv.get('message', '')
            timestamp = conv.get('timestamp', '')
            
            prefix = "User:" if role == 'user' else "Assistant:"
            lines.append(f"{prefix} {message}")
        
        return "\n".join(lines)
    
    async def _generate_summary(
        self,
        conversation_text: str,
        user_id: str,
        date: datetime
    ) -> str:
        """Generate summary using Fal AI.
        
        Args:
            conversation_text: Formatted conversations
            user_id: User identifier
            date: Date being summarized
            
        Returns:
            Summary text
        """
        try:
            prompt = f"""Summarize the following conversation from {date.date()} in 3-5 concise bullet points.
Focus on:
- Key topics discussed
- Important decisions or actions
- Notable information shared

Keep it brief and actionable.

Conversation:
{conversation_text[:2000]}  # Limit to avoid token limits

Summary:"""
            
            response = await openai_client.chat_simple(
                prompt,
                system_prompt="You are a helpful assistant that creates concise summaries.",
                temperature=0.3
            )
            
            summary = response.strip()
            
            # Basic validation
            if len(summary) < 20:
                logger.warning(f"Summary too short for user {user_id}: {summary}")
                return f"Brief conversation on {date.date()}"
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating summary: {e}")
            return f"Conversation on {date.date()} (summary generation failed)"
    
    async def run_daily_summarization(self) -> Dict[str, Any]:
        """Run daily summarization for all users.
        
        Returns:
            Dict with results
        """
        try:
            logger.info("🌙 Starting nightly summarization...")
            
            # Get yesterday's date
            yesterday = datetime.now() - timedelta(days=1)
            
            # Get all users with conversations
            result = supabase_client.admin.table("conversations").select(
                "user_id"
            ).gte(
                "timestamp", yesterday.replace(hour=0, minute=0, second=0).isoformat()
            ).execute()
            
            if not result.data:
                logger.info("No conversations to summarize")
                return {'users_processed': 0, 'summaries_created': 0}
            
            # Get unique user IDs
            user_ids = list(set(record['user_id'] for record in result.data))
            
            logger.info(f"Found {len(user_ids)} users with conversations from {yesterday.date()}")
            
            # Process each user
            results = {
                'users_processed': 0,
                'summaries_created': 0,
                'errors': 0
            }
            
            for user_id in user_ids:
                summary = await self.summarize_user_day(user_id, yesterday)
                results['users_processed'] += 1
                
                if summary:
                    results['summaries_created'] += 1
                else:
                    results['errors'] += 1
            
            logger.info(
                f"✅ Nightly summarization complete: "
                f"{results['summaries_created']} summaries created for "
                f"{results['users_processed']} users"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in nightly summarization: {e}", exc_info=True)
            return {'users_processed': 0, 'summaries_created': 0, 'errors': 1}
    
    async def consolidate_old_memories(
        self,
        user_id: str,
        days_old: int = 90
    ) -> Dict[str, Any]:
        """Consolidate old memories for a user (optional future feature).
        
        Args:
            user_id: User identifier
            days_old: Age threshold in days
            
        Returns:
            Dict with consolidation results
        """
        # TODO: Implement memory consolidation
        # This could merge multiple daily summaries into weekly/monthly summaries
        logger.info(f"Memory consolidation not yet implemented for user {user_id}")
        return {'consolidated': 0}
    
    async def cleanup_old_conversations(
        self,
        retention_days: int = 30
    ) -> int:
        """Delete or archive old conversations (optional).
        
        Args:
            retention_days: Number of days to retain
            
        Returns:
            Number of conversations deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # For now, just log - don't actually delete
            result = supabase_client.admin.table("conversations").select(
                "id"
            ).lt("timestamp", cutoff_date.isoformat()).execute()
            
            count = len(result.data) if result.data else 0
            
            logger.info(
                f"Found {count} conversations older than {retention_days} days "
                f"(not deleting - feature disabled)"
            )
            
            # To enable deletion, uncomment:
            # supabase_client.admin.table("conversations").delete().lt(
            #     "timestamp", cutoff_date.isoformat()
            # ).execute()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error in cleanup: {e}")
            return 0


# Global instance
nightly_summarizer = NightlySummarizer()


async def run_nightly_summarization():
    """Run the nightly summarization job."""
    logger.info("🚀 Starting nightly summarization job...")
    results = await nightly_summarizer.run_daily_summarization()
    logger.info(f"✅ Nightly summarization finished: {results}")
    return results

