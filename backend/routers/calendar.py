"""Calendar router for event management and Google Calendar sync."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import logging

from models.schemas import EventCreate, EventResponse
from clients.supabase_client import supabase_client
from agents.calendar import calendar_agent

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/events", response_model=dict)
async def create_event(event: EventCreate):
    """Create a new calendar event and sync with Google Calendar.
    
    Args:
        event: Event data
        
    Returns:
        Created event with ID
    """
    try:
        result = await calendar_agent.create_event(event)
        return result
        
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events", response_model=List[dict])
async def list_events(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 50
):
    """List calendar events.
    
    Args:
        start_time: Filter events after this time
        end_time: Filter events before this time
        limit: Maximum results
        
    Returns:
        List of events
    """
    try:
        query = supabase_client.admin.table("events").select("*")
        
        if start_time:
            query = query.gte("start_time", start_time.isoformat())
        if end_time:
            query = query.lte("end_time", end_time.isoformat())
        
        result = query.order("start_time", desc=False).limit(limit).execute()
        
        return {
            "success": True,
            "events": result.data or [],
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}", response_model=dict)
async def get_event(event_id: int):
    """Get a specific event by ID.
    
    Args:
        event_id: Event ID
        
    Returns:
        Event details
    """
    try:
        result = supabase_client.admin.table("events").select("*").eq(
            "id", event_id
        ).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return result.data
        
    except Exception as e:
        logger.error(f"Error getting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync", response_model=dict)
async def sync_google_calendar():
    """Trigger Google Calendar synchronization.
    
    Returns:
        Sync status
    """
    try:
        result = await calendar_agent.sync_from_google()
        return result
        
    except Exception as e:
        logger.error(f"Error syncing calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/google")
async def google_auth():
    """Initiate Google OAuth flow.
    
    Returns:
        Authorization URL
    """
    try:
        auth_url = calendar_agent.get_auth_url()
        return {"auth_url": auth_url}
        
    except Exception as e:
        logger.error(f"Error getting auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/google/callback")
async def google_auth_callback(code: str, state: str = None):
    """Handle Google OAuth callback.
    
    Args:
        code: Authorization code from Google
        state: Optional user identifier from OAuth state
        
    Returns:
        Success message
    """
    try:
        # Extract user_id from state if provided, otherwise default to 1
        user_id = int(state) if state and state.isdigit() else 1
        
        await calendar_agent.handle_oauth_callback(code, user_id=user_id)
        
        return {
            "success": True,
            "message": f"✅ Google Calendar connected successfully for user {user_id}!"
        }
        
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

