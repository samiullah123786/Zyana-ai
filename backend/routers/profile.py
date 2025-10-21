"""Profile router for user preferences and habit profiles."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import logging

from clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/habits")
async def get_habit_profile(user_id: int = 1):
    """Get user's habit profile.
    
    Args:
        user_id: User ID
        
    Returns:
        User habit profile entries
    """
    try:
        result = supabase_client.admin.table("habit_profiles").select("*").eq(
            "user_id", user_id
        ).execute()
        
        # Convert to dict format
        habits = {item["key"]: item["value"] for item in result.data}
        
        return {
            "user_id": user_id,
            "habits": habits,
            "details": result.data
        }
        
    except Exception as e:
        logger.error(f"Error getting habit profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/habits")
async def update_habit(key: str, value: str, user_id: int = 1):
    """Update or create a habit profile entry.
    
    Args:
        key: Habit key (e.g., 'preferred_currency')
        value: Habit value (e.g., 'PKR')
        user_id: User ID
        
    Returns:
        Updated habit entry
    """
    try:
        # Upsert habit
        result = supabase_client.admin.table("habit_profiles").upsert({
            "user_id": user_id,
            "key": key,
            "value": value,
            "confidence_score": 0.9,
            "occurrences": 1
        }).execute()
        
        logger.info(f"Updated habit: {key}={value}")
        
        return {
            "success": True,
            "message": f"✅ Updated preference: {key}",
            "data": result.data[0] if result.data else {}
        }
        
    except Exception as e:
        logger.error(f"Error updating habit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/habits/{key}")
async def delete_habit(key: str, user_id: int = 1):
    """Delete a habit profile entry.
    
    Args:
        key: Habit key to delete
        user_id: User ID
        
    Returns:
        Success status
    """
    try:
        supabase_client.admin.table("habit_profiles").delete().eq(
            "user_id", user_id
        ).eq("key", key).execute()
        
        return {
            "success": True,
            "message": f"✅ Deleted preference: {key}"
        }
        
    except Exception as e:
        logger.error(f"Error deleting habit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences")
async def get_user_preferences(user_id: int = 1):
    """Get user preferences.
    
    Args:
        user_id: User ID
        
    Returns:
        User preferences
    """
    try:
        result = supabase_client.admin.table("users").select("preferences").eq(
            "id", user_id
        ).single().execute()
        
        return result.data.get("preferences", {}) if result.data else {}
        
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences")
async def update_preferences(preferences: dict, user_id: int = 1):
    """Update user preferences.
    
    Args:
        preferences: Preferences dict
        user_id: User ID
        
    Returns:
        Success status
    """
    try:
        result = supabase_client.admin.table("users").update({
            "preferences": preferences
        }).eq("id", user_id).execute()
        
        return {
            "success": True,
            "message": "✅ Preferences updated",
            "data": result.data[0] if result.data else {}
        }
        
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

