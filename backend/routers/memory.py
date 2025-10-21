"""Memory router for semantic search and vector operations."""
from fastapi import APIRouter, HTTPException
import logging

from models.schemas import MemorySearchRequest, MemorySearchResponse
from memory.embed import memory_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(request: MemorySearchRequest):
    """Search personal memory using semantic search.
    
    Args:
        request: Search query and parameters
        
    Returns:
        Search results with AI-generated summary
    """
    try:
        result = await memory_service.search(
            query=request.query,
            limit=request.limit,
            filters=request.filters
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embed")
async def embed_content(content: str, metadata: dict):
    """Manually embed content into memory.
    
    Args:
        content: Text content to embed
        metadata: Metadata for the memory
        
    Returns:
        Success status
    """
    try:
        await memory_service.add_memory(content, metadata)
        
        return {
            "success": True,
            "message": "✅ Memory embedded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error embedding content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summaries")
async def list_summaries(limit: int = 30):
    """List daily memory summaries.
    
    Args:
        limit: Maximum number of summaries to return
        
    Returns:
        List of daily summaries
    """
    try:
        result = await memory_service.get_summaries(limit=limit)
        return result
        
    except Exception as e:
        logger.error(f"Error listing summaries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

