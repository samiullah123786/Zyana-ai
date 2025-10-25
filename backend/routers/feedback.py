"""Feedback router for collecting user ratings and comments."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

from clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""
    user_id: str
    source_type: str = Field(..., description="Type: message, calendar, transaction, general")
    source_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    comment: Optional[str] = None
    metadata: Optional[dict] = None


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: int
    user_id: str
    source_type: str
    source_id: Optional[str]
    rating: int
    comment: Optional[str]
    reviewed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/", response_model=dict)
async def submit_feedback(feedback: FeedbackCreate):
    """Submit user feedback.
    
    Args:
        feedback: Feedback data
        
    Returns:
        Success message and feedback ID
    """
    try:
        result = supabase_client.admin.table("feedback").insert({
            "user_id": feedback.user_id,
            "source_type": feedback.source_type,
            "source_id": feedback.source_id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "metadata": feedback.metadata or {}
        }).execute()
        
        feedback_id = result.data[0]["id"] if result.data else None
        
        logger.info(f"✅ Feedback submitted: {feedback_id} (rating: {feedback.rating})")
        
        return {
            "success": True,
            "message": "Thank you for your feedback!",
            "feedback_id": feedback_id
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=List[dict])
async def get_recent_feedback(
    limit: int = Query(default=50, le=100),
    reviewed: Optional[bool] = None,
    min_rating: Optional[int] = Query(default=None, ge=1, le=5),
    max_rating: Optional[int] = Query(default=None, ge=1, le=5)
):
    """Get recent feedback (admin only).
    
    Args:
        limit: Maximum number of results
        reviewed: Filter by reviewed status
        min_rating: Minimum rating filter
        max_rating: Maximum rating filter
        
    Returns:
        List of feedback entries
    """
    try:
        query = supabase_client.admin.table("feedback").select("*")
        
        if reviewed is not None:
            query = query.eq("reviewed", reviewed)
        
        if min_rating is not None:
            query = query.gte("rating", min_rating)
        
        if max_rating is not None:
            query = query.lte("rating", max_rating)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        
        return {
            "success": True,
            "feedback": result.data or [],
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=dict)
async def get_feedback_stats():
    """Get feedback statistics (admin only).
    
    Returns:
        Statistics about feedback
    """
    try:
        # Get all feedback
        result = supabase_client.admin.table("feedback").select("rating, reviewed").execute()
        
        if not result.data:
            return {
                "success": True,
                "stats": {
                    "total": 0,
                    "avg_rating": 0,
                    "rating_distribution": {},
                    "reviewed_count": 0,
                    "unreviewed_count": 0
                }
            }
        
        feedback_list = result.data
        total = len(feedback_list)
        
        # Calculate statistics
        ratings = [f["rating"] for f in feedback_list]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Rating distribution
        rating_dist = {i: ratings.count(i) for i in range(1, 6)}
        
        # Reviewed count
        reviewed_count = sum(1 for f in feedback_list if f.get("reviewed"))
        unreviewed_count = total - reviewed_count
        
        return {
            "success": True,
            "stats": {
                "total": total,
                "avg_rating": round(avg_rating, 2),
                "rating_distribution": rating_dist,
                "reviewed_count": reviewed_count,
                "unreviewed_count": unreviewed_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{feedback_id}", response_model=dict)
async def update_feedback(feedback_id: int, reviewed: bool):
    """Update feedback reviewed status (admin only).
    
    Args:
        feedback_id: Feedback ID
        reviewed: New reviewed status
        
    Returns:
        Success message
    """
    try:
        result = supabase_client.admin.table("feedback").update({
            "reviewed": reviewed
        }).eq("id", feedback_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        logger.info(f"✅ Updated feedback {feedback_id}: reviewed={reviewed}")
        
        return {
            "success": True,
            "message": f"Feedback marked as {'reviewed' if reviewed else 'unreviewed'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{feedback_id}", response_model=dict)
async def delete_feedback(feedback_id: int):
    """Delete feedback entry (admin only).
    
    Args:
        feedback_id: Feedback ID
        
    Returns:
        Success message
    """
    try:
        result = supabase_client.admin.table("feedback").delete().eq("id", feedback_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        logger.info(f"✅ Deleted feedback {feedback_id}")
        
        return {
            "success": True,
            "message": "Feedback deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

