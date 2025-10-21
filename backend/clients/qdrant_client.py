"""Qdrant client wrapper for vector storage."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import settings
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ZyanaQdrantClient:
    """Wrapper for Qdrant vector database client."""
    
    COLLECTION_NAME = "zyana_memory"
    VECTOR_DIMENSION = 1536  # OpenAI ada-002 dimension
    
    def __init__(self):
        """Initialize Qdrant client."""
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
        self._ensure_collection()
        logger.info(f"Qdrant client initialized: {settings.qdrant_url}")
    
    def _ensure_collection(self):
        """Ensure the Zyana memory collection exists."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.COLLECTION_NAME not in collection_names:
                logger.info(f"Creating collection: {self.COLLECTION_NAME}")
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.VECTOR_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection created: {self.COLLECTION_NAME}")
            else:
                logger.debug(f"Collection already exists: {self.COLLECTION_NAME}")
                
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    async def add_memory(
        self,
        vector_id: str,
        embedding: List[float],
        payload: Dict[str, Any]
    ):
        """Add a memory vector to Qdrant.
        
        Args:
            vector_id: Unique ID for the vector
            embedding: Vector embedding
            payload: Metadata (row_id, table, snippet, date, business)
        """
        try:
            point = PointStruct(
                id=vector_id,
                vector=embedding,
                payload=payload
            )
            
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[point]
            )
            
            logger.debug(f"Added memory vector: {vector_id}")
            
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise
    
    async def search_memory(
        self,
        query_vector: List[float],
        limit: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar memories.
        
        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            filters: Optional filters for metadata
            
        Returns:
            List of search results with payload and score
        """
        try:
            search_result = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_vector,
                limit=limit,
                query_filter=filters
            )
            
            results = [
                {
                    "id": hit.id,
                    "score": hit.score,
                    **hit.payload
                }
                for hit in search_result
            ]
            
            logger.debug(f"Found {len(results)} memory results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []
    
    async def delete_memory(self, vector_id: str):
        """Delete a memory vector.
        
        Args:
            vector_id: ID of vector to delete
        """
        try:
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=[vector_id]
            )
            logger.debug(f"Deleted memory vector: {vector_id}")
            
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            raise


# Global Qdrant client instance
qdrant_client = ZyanaQdrantClient()

