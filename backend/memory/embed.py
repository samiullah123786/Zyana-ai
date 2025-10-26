"""Memory and embedding service for semantic search."""
import logging
from typing import Dict, Any, List, Optional
from datetime import date
import uuid

from clients.openai_client import openai_client
from clients.qdrant_client import qdrant_client
from clients.supabase_client import supabase_client
from models.schemas import MemorySearchResponse, MemorySearchResult
from services.prompts import get_prompt, format_prompt
from services.embeddings import embedding_service

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for embedding and searching memories."""
    
    async def add_memory(self, content: str, metadata: Dict[str, Any]):
        """Add a memory to the vector database.
        
        Args:
            content: Text content to embed
            metadata: Metadata (table, row_id, business, date, etc.)
        """
        try:
            # Generate embedding using new pluggable service
            embedding = await embedding_service.embed_single(content)
            
            # Create unique ID
            vector_id = metadata.get("vector_id") or str(uuid.uuid4())
            
            # Prepare payload
            payload = {
                "snippet": content,
                "table": metadata.get("table", "unknown"),
                "row_id": metadata.get("row_id"),
                "date": metadata.get("date"),
                "business": metadata.get("business")
            }
            
            # Add to Qdrant
            await qdrant_client.add_memory(vector_id, embedding, payload)
            
            logger.info(f"Added memory: {vector_id}")
            
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict] = None
    ) -> MemorySearchResponse:
        """Search memories using semantic search.
        
        Args:
            query: Search query
            limit: Number of results
            filters: Optional filters
            
        Returns:
            MemorySearchResponse with results and summary
        """
        try:
            # Generate query embedding using new pluggable service
            query_embedding = await embedding_service.embed_single(query)
            
            # Search in Qdrant
            results = await qdrant_client.search_memory(
                query_vector=query_embedding,
                limit=limit,
                filters=filters
            )
            
            # Convert to MemorySearchResult objects
            search_results = [
                MemorySearchResult(
                    id=str(r.get("id", "")),
                    snippet=r.get("snippet", ""),
                    table=r.get("table", ""),
                    date=r.get("date"),
                    business=r.get("business"),
                    score=r.get("score", 0.0)
                )
                for r in results
            ]
            
            # Generate AI summary
            summary = await self._generate_summary(query, search_results)
            
            return MemorySearchResponse(
                query=query,
                results=search_results,
                summary=summary,
                total_found=len(search_results)
            )
            
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return MemorySearchResponse(
                query=query,
                results=[],
                summary="Sorry, I encountered an error searching your memory.",
                total_found=0
            )
    
    async def _generate_summary(self, query: str, results: List[MemorySearchResult]) -> str:
        """Generate AI summary from search results.
        
        Args:
            query: Original query
            results: Search results
            
        Returns:
            Summary text
        """
        if not results:
            return "I don't have specific information about that. Would you like me to search for something else?"
        
        # Format results for prompt
        results_text = "\n\n".join([
            f"[Score: {r.score:.2f}] {r.snippet}\n"
            f"  From: {r.table}, Date: {r.date}, Business: {r.business}"
            for r in results
        ])
        
        # Get prompt template
        prompt_template = get_prompt("memory_search")
        
        # Format prompt
        prompt = format_prompt(
            prompt_template,
            query=query,
            results=results_text
        )
        
        # Generate summary with OpenAI
        summary = await openai_client.chat_simple(
            prompt=prompt,
            temperature=0.3
        )
        
        return summary.strip()
    
    async def get_summaries(self, limit: int = 30) -> List[Dict]:
        """Get daily memory summaries.
        
        Args:
            limit: Number of summaries to return
            
        Returns:
            List of summaries
        """
        try:
            result = supabase_client.admin.table("memory_summaries").select(
                "*"
            ).order("date", desc=True).limit(limit).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting summaries: {e}")
            return []
    
    async def create_daily_summary(self, target_date: date, user_id: int = 1):
        """Create a daily summary of activities.
        
        Args:
            target_date: Date to summarize
            user_id: User ID
        """
        try:
            # Get all activities for the day
            transactions = supabase_client.admin.table("transactions").select(
                "*"
            ).eq("date", target_date.isoformat()).execute()
            
            events = supabase_client.admin.table("events").select(
                "*"
            ).gte("start_time", f"{target_date}T00:00:00").lte(
                "start_time", f"{target_date}T23:59:59"
            ).execute()
            
            # Format activities
            activities = []
            
            for t in transactions.data:
                activities.append(
                    f"{t['type']}: {t['currency']} {t['amount']} - {t['description']}"
                )
            
            for e in events.data:
                activities.append(f"Event: {e['title']}")
            
            if not activities:
                logger.info(f"No activities for {target_date}")
                return
            
            # Generate summary
            activities_text = "\n".join(activities)
            summary_prompt = f"""Summarize the following activities for {target_date} in 2-3 sentences:

{activities_text}

Summary:"""
            
            summary = await openai_client.chat_simple(
                prompt=summary_prompt,
                temperature=0.3
            )
            
            # Embed summary with OpenAI
            embedding = await openai_client.embed_single(summary)
            embedding_id = str(uuid.uuid4())
            
            await qdrant_client.add_memory(
                embedding_id,
                embedding,
                {
                    "snippet": summary,
                    "table": "daily_summary",
                    "date": target_date.isoformat(),
                    "row_id": None,
                    "business": None
                }
            )
            
            # Save summary
            supabase_client.admin.table("memory_summaries").insert({
                "user_id": user_id,
                "date": target_date.isoformat(),
                "summary": summary,
                "embedding_id": embedding_id
            }).execute()
            
            logger.info(f"Created daily summary for {target_date}")
            
        except Exception as e:
            logger.error(f"Error creating daily summary: {e}")


# Global instance
memory_service = MemoryService()

