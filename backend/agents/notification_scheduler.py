"""Notification Scheduler Agent for managing scheduled reminders and notifications."""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

from clients.supabase_client import supabase_client
from services.telegram_bot import send_telegram_message

logger = logging.getLogger(__name__)


class NotificationSchedulerAgent:
    """Agent for scheduling and managing notifications."""
    
    async def schedule_notification(
        self,
        user_id: int,
        message: str,
        scheduled_time: datetime,
        telegram_chat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Schedule a notification for future delivery.
        
        Args:
            user_id: User ID
            message: Notification message
            scheduled_time: When to send the notification
            telegram_chat_id: Telegram chat ID
            
        Returns:
            Response dict with scheduled notification data
        """
        try:
            # Insert scheduled notification
            result = supabase_client.admin.table("scheduled_notifications").insert({
                "user_id": user_id,
                "message": message,
                "scheduled_time": scheduled_time.isoformat(),
                "status": "pending",
                "telegram_chat_id": telegram_chat_id
            }).execute()
            
            notification = result.data[0] if result.data else {}
            
            logger.info(f"Scheduled notification for user {user_id} at {scheduled_time}")
            
            # Format scheduled time
            time_str = scheduled_time.strftime("%b %d, %I:%M %p")
            
            return {
                "success": True,
                "message": f"✅ Reminder set for {time_str}\nMessage: \"{message}\"\nID: #{notification['id']}",
                "data": notification
            }
            
        except Exception as e:
            logger.error(f"Error scheduling notification: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to schedule notification: {str(e)}",
                "data": None
            }
    
    async def list_scheduled(
        self,
        user_id: int,
        status: str = "pending"
    ) -> List[Dict[str, Any]]:
        """List scheduled notifications for a user.
        
        Args:
            user_id: User ID
            status: Filter by status (default: pending)
            
        Returns:
            List of scheduled notifications
        """
        try:
            query = supabase_client.admin.table("scheduled_notifications").select(
                "*"
            ).eq("user_id", user_id)
            
            if status:
                query = query.eq("status", status)
            
            result = query.order("scheduled_time").execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error listing scheduled notifications: {e}", exc_info=True)
            return []
    
    async def cancel_notification(self, notification_id: int) -> Dict[str, Any]:
        """Cancel a scheduled notification.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            Response dict
        """
        try:
            # Update status to cancelled
            result = supabase_client.admin.table("scheduled_notifications").update({
                "status": "cancelled",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", notification_id).eq("status", "pending").execute()
            
            if not result.data:
                return {
                    "success": False,
                    "message": f"Reminder #{notification_id} not found or already processed",
                    "data": None
                }
            
            logger.info(f"Cancelled notification ID: {notification_id}")
            
            return {
                "success": True,
                "message": f"✅ Reminder #{notification_id} cancelled",
                "data": result.data[0]
            }
            
        except Exception as e:
            logger.error(f"Error cancelling notification: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to cancel notification: {str(e)}",
                "data": None
            }
    
    async def process_pending(self):
        """Process all pending notifications that are due.
        
        This method should be called periodically (e.g., every minute).
        """
        try:
            # Get pending notifications that are due
            now = datetime.utcnow()
            result = supabase_client.admin.table("scheduled_notifications").select(
                "*"
            ).eq("status", "pending").lte("scheduled_time", now.isoformat()).execute()
            
            notifications = result.data if result.data else []
            
            logger.info(f"Processing {len(notifications)} pending notifications")
            
            for notification in notifications:
                await self._send_notification(notification)
            
        except Exception as e:
            logger.error(f"Error processing pending notifications: {e}", exc_info=True)
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send a single notification.
        
        Args:
            notification: Notification dict
        """
        try:
            notification_id = notification["id"]
            message = f"🔔 Reminder: {notification['message']}"
            telegram_chat_id = notification.get("telegram_chat_id")
            
            if not telegram_chat_id:
                logger.warning(f"No telegram_chat_id for notification {notification_id}")
                # Mark as failed
                supabase_client.admin.table("scheduled_notifications").update({
                    "status": "failed",
                    "error_message": "No telegram_chat_id",
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", notification_id).execute()
                return
            
            # Send Telegram message
            await send_telegram_message(telegram_chat_id, message)
            
            # Mark as sent
            supabase_client.admin.table("scheduled_notifications").update({
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", notification_id).execute()
            
            logger.info(f"Sent notification {notification_id} to {telegram_chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending notification {notification.get('id')}: {e}", exc_info=True)
            
            # Mark as failed
            try:
                supabase_client.admin.table("scheduled_notifications").update({
                    "status": "failed",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", notification["id"]).execute()
            except Exception as update_error:
                logger.error(f"Failed to update notification status: {update_error}")
    
    def parse_schedule_time(self, text: str, reference_time: Optional[datetime] = None) -> Optional[datetime]:
        """Parse natural language time expressions.
        
        Args:
            text: Text containing time expression
            reference_time: Reference time (defaults to now)
            
        Returns:
            Parsed datetime or None
        """
        if reference_time is None:
            reference_time = datetime.now()
        
        text_lower = text.lower()
        
        # Specific times: "at 5 PM", "at 17:00"
        time_patterns = [
            (r"at (\d{1,2})\s*(am|pm)", self._parse_12hour),
            (r"at (\d{1,2}):(\d{2})\s*(am|pm)?", self._parse_time),
        ]
        
        for pattern, parser in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result = parser(match, reference_time)
                if result:
                    return result
        
        # Relative times: "in 30 minutes", "in 2 hours"
        relative_patterns = [
            (r"in (\d+)\s*minutes?", lambda m, ref: ref + timedelta(minutes=int(m.group(1)))),
            (r"in (\d+)\s*hours?", lambda m, ref: ref + timedelta(hours=int(m.group(1)))),
            (r"in (\d+)\s*days?", lambda m, ref: ref + timedelta(days=int(m.group(1)))),
        ]
        
        for pattern, calculator in relative_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return calculator(match, reference_time)
        
        # Named times: "tomorrow", "next week"
        if "tomorrow" in text_lower:
            tomorrow = reference_time + timedelta(days=1)
            # Default to 9 AM
            return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        
        if "next week" in text_lower:
            next_week = reference_time + timedelta(days=7)
            return next_week.replace(hour=9, minute=0, second=0, microsecond=0)
        
        return None
    
    def _parse_12hour(self, match, reference_time):
        """Parse 12-hour time (e.g., '3 PM')."""
        hour = int(match.group(1))
        period = match.group(2)
        
        if period == "pm" and hour != 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0
        
        result = reference_time.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # Check if time is in the future
        if "tomorrow" in match.string.lower():
            result += timedelta(days=1)
        elif result < reference_time:
            # If time has passed today, schedule for tomorrow
            result += timedelta(days=1)
        
        return result
    
    def _parse_time(self, match, reference_time):
        """Parse time with minutes (e.g., '14:30' or '2:30 PM')."""
        hour = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3) if len(match.groups()) > 2 else None
        
        if period:
            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
        
        result = reference_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Check if time is in the future
        if "tomorrow" in match.string.lower():
            result += timedelta(days=1)
        elif result < reference_time:
            result += timedelta(days=1)
        
        return result


# Global instance
notification_scheduler = NotificationSchedulerAgent()

