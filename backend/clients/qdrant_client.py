"""Qdrant client wrapper for vector storage."""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct,
    PayloadSchemaType
)
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
        """Ensure the Zyana memory collection exists with proper indexes."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.COLLECTION_NAME not in collection_names:
                logger.info(f"Creating collection: {self.COLLECTION_NAME}")
                
                # Create collection with vector config
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.VECTOR_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                
                # Create payload indexes for efficient filtering
                logger.info(f"Creating payload indexes for {self.COLLECTION_NAME}")
                self.client.create_payload_index(
                    collection_name=self.COLLECTION_NAME,
                    field_name="user_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                
                self.client.create_payload_index(
                    collection_name=self.COLLECTION_NAME,
                    field_name="type",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                
                logger.info(f"Collection and indexes created: {self.COLLECTION_NAME}")
            else:
                logger.debug(f"Collection already exists: {self.COLLECTION_NAME}")
                
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    def recreate_collection_with_indexes(self):
        """Recreate collection with proper indexes (for migration).
        
        WARNING: This will delete all existing vectors in the collection!
        """
        try:
            # Delete existing collection
            try:
                self.client.delete_collection(collection_name=self.COLLECTION_NAME)
                logger.info(f"Deleted existing collection: {self.COLLECTION_NAME}")
            except Exception as e:
                logger.warning(f"Could not delete collection (may not exist): {e}")
            
            # Recreate with indexes
            self._ensure_collection()
            logger.info("Collection recreated with proper indexes")
            
        except Exception as e:
            logger.error(f"Error recreating collection: {e}")
            raise
    
    async def add_memory(
        self,
        content: str = None,  # For backwards compatibility
        embedding: List[float] = None,
        metadata: Dict[str, Any] = None,
        vector_id: str = None,
        payload: Dict[str, Any] = None,
        point_id: str = None,
        collection_name: str = None
    ):
        """Add a memory vector to Qdrant (flexible signature for compatibility).
        
        Args:
            content: Content text (for reference)
            embedding: Vector embedding
            metadata: Metadata dict
            vector_id: Unique ID (deprecated, use point_id)
            payload: Metadata (deprecated, use metadata)
            point_id: Unique ID for the vector
            collection_name: Optional collection name (defaults to COLLECTION_NAME)
        """
        try:
            # Handle different parameter styles
            final_id = point_id or vector_id
            if not final_id:
                import uuid
                final_id = str(uuid.uuid4())
            
            final_payload = metadata or payload or {}
            final_collection = collection_name or self.COLLECTION_NAME
            
            point = PointStruct(
                id=final_id,
                vector=embedding,
                payload=final_payload
            )
            
            self.client.upsert(
                collection_name=final_collection,
                points=[point]
            )
            
            logger.debug(f"Added memory vector: {final_id} to {final_collection}")
            
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
    
    async def delete_memory(self, vector_id: str, collection_name: str = None):
        """Delete a memory vector.
        
        Args:
            vector_id: ID of vector to delete
            collection_name: Optional collection name (defaults to COLLECTION_NAME)
        """
        try:
            final_collection = collection_name or self.COLLECTION_NAME
            
            self.client.delete(
                collection_name=final_collection,
                points_selector=[vector_id]
            )
            logger.debug(f"Deleted memory vector: {vector_id} from {final_collection}")
            
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            raise
    
    def ensure_collection(self, collection_name: str, dimension: int = 1536):
        """Ensure a specific collection exists.
        
        Args:
            collection_name: Name of the collection
            dimension: Vector dimension
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if collection_name not in collection_names:
                logger.info(f"Creating collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Collection created: {collection_name}")
            else:
                logger.debug(f"Collection already exists: {collection_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about all collections.
        
        Returns:
            Dict with collection names and counts
        """
        try:
            collections = self.client.get_collections().collections
            
            info = {}
            for col in collections:
                try:
                    count = self.client.count(collection_name=col.name)
                    info[col.name] = {
                        'count': count.count,
                        'vectors_config': str(col.config)
                    }
                except Exception as e:
                    logger.warning(f"Error getting count for {col.name}: {e}")
                    info[col.name] = {'count': 'unknown', 'error': str(e)}
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    async def delete_user_memories(self, user_id: str, collection: str = None):
        """Delete all memories for a specific user (for "Forget" feature).
        
        Args:
            user_id: User identifier
            collection: Optional collection name (defaults to all)
        """
        try:
            collections_to_process = [collection] if collection else [self.COLLECTION_NAME]
            
            for coll_name in collections_to_process:
                # Delete points with matching user_id in payload
                self.client.delete(
                    collection_name=coll_name,
                    points_selector={
                        "filter": {
                            "must": [
                                {
                                    "key": "user_id",
                                    "match": {"value": user_id}
                                }
                            ]
                        }
                    }
                )
                logger.info(f"✅ Deleted memories for user {user_id} from {coll_name}")
            
        except Exception as e:
            logger.error(f"Error deleting user memories: {e}")
            raise


# Global Qdrant client instance
qdrant_client = ZyanaQdrantClient()

