"""Notification scheduling API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from agents.notification_scheduler import notification_scheduler

logger = logging.getLogger(__name__)
router = APIRouter()


class NotificationSchedule(BaseModel):
    """Notification scheduling request."""
    message: str
    scheduled_time: datetime
    telegram_chat_id: Optional[str] = None


@router.post("/schedule")
async def schedule_notification(notification: NotificationSchedule):
    """Schedule a notification for future delivery.
    
    Args:
        notification: Notification scheduling data
        
    Returns:
        Scheduled notification data
    """
    try:
        # TODO: Get user_id from authentication
        user_id = 1
        
        result = await notification_scheduler.schedule_notification(
            user_id=user_id,
            message=notification.message,
            scheduled_time=notification.scheduled_time,
            telegram_chat_id=notification.telegram_chat_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in schedule_notification endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_scheduled_notifications(
    status: Optional[str] = Query("pending")
):
    """List scheduled notifications.
    
    Args:
        status: Filter by status (default: pending)
        
    Returns:
        List of notifications
    """
    try:
        # TODO: Get user_id from authentication
        user_id = 1
        
        notifications = await notification_scheduler.list_scheduled(
            user_id=user_id,
            status=status
        )
        
        return {
            "success": True,
            "data": notifications,
            "count": len(notifications)
        }
        
    except Exception as e:
        logger.error(f"Error in list_scheduled_notifications endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
async def cancel_notification(notification_id: int):
    """Cancel a scheduled notification.
    
    Args:
        notification_id: Notification ID
        
    Returns:
        Success response
    """
    try:
        result = await notification_scheduler.cancel_notification(notification_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in cancel_notification endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

