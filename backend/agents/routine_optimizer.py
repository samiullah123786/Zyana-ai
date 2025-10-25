"""Routine Optimizer Agent for learning work patterns and suggesting breaks."""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class RoutineOptimizerAgent:
    """Agent for learning user routines and optimizing work patterns."""
    
    ACTIVITY_THRESHOLD = 3  # Minimum activities per hour to consider it work time
    ANALYSIS_DAYS = 7  # Days to analyze for pattern detection
    
    async def observe_activity(
        self,
        user_id: int,
        timestamp: Optional[datetime] = None,
        activity_type: str = "message"
    ):
        """Log a user activity for pattern learning.
        
        Args:
            user_id: User ID
            timestamp: Activity timestamp (defaults to now)
            activity_type: Type of activity
        """
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            # Insert work session
            supabase_client.admin.table("work_sessions").insert({
                "user_id": user_id,
                "activity_type": activity_type,
                "timestamp": timestamp.isoformat()
            }).execute()
            
            logger.debug(f"Logged activity for user {user_id} at {timestamp}")
            
        except Exception as e:
            logger.error(f"Error observing activity: {e}", exc_info=True)
    
    async def analyze_work_patterns(self, user_id: int) -> Dict[str, Any]:
        """Analyze user's work patterns and update habit profile.
        
        Args:
            user_id: User ID
            
        Returns:
            Analysis results
        """
        try:
            # Get activities from last N days
            cutoff_date = datetime.utcnow() - timedelta(days=self.ANALYSIS_DAYS)
            
            result = supabase_client.admin.table("work_sessions").select(
                "*"
            ).eq("user_id", user_id).gte(
                "timestamp", cutoff_date.isoformat()
            ).execute()
            
            sessions = result.data if result.data else []
            
            if len(sessions) < 10:
                logger.info(f"Insufficient data for user {user_id}: {len(sessions)} sessions")
                return {
                    "success": False,
                    "message": "Not enough activity data yet",
                    "data": None
                }
            
            # Analyze patterns
            hour_activity = defaultdict(int)  # Hour of day -> activity count
            day_hour_activity = defaultdict(lambda: defaultdict(int))  # Day -> Hour -> count
            
            for session in sessions:
                timestamp = datetime.fromisoformat(session["timestamp"].replace('Z', '+00:00'))
                hour = timestamp.hour
                day = timestamp.weekday()
                
                hour_activity[hour] += 1
                day_hour_activity[day][hour] += 1
            
            # Detect work hours (hours with activity above threshold)
            work_hours = []
            for hour, count in hour_activity.items():
                avg_per_day = count / self.ANALYSIS_DAYS
                if avg_per_day >= self.ACTIVITY_THRESHOLD:
                    work_hours.append(hour)
            
            if not work_hours:
                logger.info(f"No clear work pattern for user {user_id}")
                return {
                    "success": False,
                    "message": "No clear work pattern detected yet",
                    "data": None
                }
            
            work_hours.sort()
            work_hours_start = work_hours[0]
            work_hours_end = work_hours[-1]
            
            # Detect busy periods (consecutive hours with high activity)
            busy_periods = []
            current_period = None
            
            for hour in work_hours:
                if current_period is None:
                    current_period = {"start": hour, "end": hour}
                elif hour == current_period["end"] + 1:
                    current_period["end"] = hour
                else:
                    if current_period["end"] - current_period["start"] >= 2:
                        busy_periods.append(current_period)
                    current_period = {"start": hour, "end": hour}
            
            if current_period and current_period["end"] - current_period["start"] >= 2:
                busy_periods.append(current_period)
            
            # Suggest break times (gaps between busy periods or mid-period)
            break_suggestions = []
            if len(busy_periods) >= 2:
                # Between busy periods
                for i in range(len(busy_periods) - 1):
                    break_hour = busy_periods[i]["end"] + 1
                    break_suggestions.append(break_hour)
            elif busy_periods:
                # Mid-period breaks for long busy periods
                period = busy_periods[0]
                if period["end"] - period["start"] >= 4:
                    # Suggest break at mid-point
                    mid = (period["start"] + period["end"]) // 2
                    break_suggestions.append(mid)
            
            # Update habit profile
            await self._update_habit_profile(
                user_id,
                work_hours_start,
                work_hours_end,
                busy_periods,
                break_suggestions
            )
            
            logger.info(f"Analyzed work patterns for user {user_id}: {work_hours_start}-{work_hours_end}")
            
            return {
                "success": True,
                "message": "Work pattern analysis complete",
                "data": {
                    "work_hours_start": work_hours_start,
                    "work_hours_end": work_hours_end,
                    "busy_periods": busy_periods,
                    "break_suggestions": break_suggestions,
                    "total_sessions": len(sessions)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing work patterns: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to analyze patterns: {str(e)}",
                "data": None
            }
    
    async def suggest_break(self, user_id: int) -> Optional[str]:
        """Check if user should take a break based on current time.
        
        Args:
            user_id: User ID
            
        Returns:
            Break suggestion message or None
        """
        try:
            # Get user's habit profile
            profile = await self._get_habit_profile(user_id)
            
            if not profile:
                return None
            
            break_suggestions = profile.get("break_suggestions", [])
            if not break_suggestions:
                return None
            
            # Check if current time is a suggested break time
            current_hour = datetime.now().hour
            
            if current_hour in break_suggestions:
                return f"☕ It's your usual break time ({current_hour}:00). Taking a break?"
            
            return None
            
        except Exception as e:
            logger.error(f"Error suggesting break: {e}", exc_info=True)
            return None
    
    async def get_optimal_notification_times(self, user_id: int) -> List[int]:
        """Get optimal hours for sending non-urgent notifications.
        
        Args:
            user_id: User ID
            
        Returns:
            List of hour values (0-23)
        """
        try:
            profile = await self._get_habit_profile(user_id)
            
            if not profile:
                # Default to typical work hours
                return [9, 12, 15, 18]
            
            work_start = profile.get("work_hours_start")
            work_end = profile.get("work_hours_end")
            busy_periods = profile.get("busy_periods", [])
            
            if work_start is None or work_end is None:
                return [9, 12, 15, 18]
            
            # Suggest times outside busy periods but within work hours
            optimal_times = []
            
            for hour in range(work_start, work_end + 1):
                # Check if hour is in a busy period
                in_busy_period = False
                for period in busy_periods:
                    if period["start"] <= hour <= period["end"]:
                        in_busy_period = True
                        break
                
                if not in_busy_period:
                    optimal_times.append(hour)
            
            # If no optimal times found, use work hours
            if not optimal_times:
                optimal_times = list(range(work_start, work_end + 1, 3))
            
            return optimal_times[:4]  # Return top 4
            
        except Exception as e:
            logger.error(f"Error getting optimal notification times: {e}", exc_info=True)
            return [9, 12, 15, 18]
    
    async def is_busy_time(self, user_id: int, check_time: Optional[datetime] = None) -> bool:
        """Check if given time falls in user's busy period.
        
        Args:
            user_id: User ID
            check_time: Time to check (defaults to now)
            
        Returns:
            True if busy time
        """
        try:
            if check_time is None:
                check_time = datetime.now()
            
            profile = await self._get_habit_profile(user_id)
            
            if not profile:
                return False
            
            busy_periods = profile.get("busy_periods", [])
            hour = check_time.hour
            
            for period in busy_periods:
                if period["start"] <= hour <= period["end"]:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking busy time: {e}", exc_info=True)
            return False
    
    async def generate_weekly_insight(self, user_id: int) -> str:
        """Generate weekly work pattern insight.
        
        Args:
            user_id: User ID
            
        Returns:
            Insight message
        """
        try:
            # Analyze patterns
            analysis = await self.analyze_work_patterns(user_id)
            
            if not analysis["success"]:
                return "📊 Not enough activity data yet. Keep using Zyana to learn your patterns!"
            
            data = analysis["data"]
            work_start = data["work_hours_start"]
            work_end = data["work_hours_end"]
            busy_periods = data["busy_periods"]
            break_suggestions = data["break_suggestions"]
            
            # Format time
            def format_hour(h):
                return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"
            
            message = (
                f"📊 Weekly Insight:\n\n"
                f"Your work pattern: Most active {format_hour(work_start)} - {format_hour(work_end)}\n"
            )
            
            if busy_periods:
                message += f"Focus zones: "
                message += ", ".join([f"{format_hour(p['start'])}-{format_hour(p['end'])}" for p in busy_periods])
                message += "\n"
            
            if break_suggestions:
                message += f"Suggested break times: "
                message += ", ".join([format_hour(h) for h in break_suggestions])
                message += "\n"
            
            message += f"\nTotal activity sessions: {data['total_sessions']}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating weekly insight: {e}", exc_info=True)
            return "📊 Unable to generate insight at this time."
    
    async def _update_habit_profile(
        self,
        user_id: int,
        work_hours_start: int,
        work_hours_end: int,
        busy_periods: List[Dict[str, int]],
        break_suggestions: List[int]
    ):
        """Update user's habit profile with work pattern data.
        
        Args:
            user_id: User ID
            work_hours_start: Work start hour
            work_hours_end: Work end hour
            busy_periods: List of busy period dicts
            break_suggestions: List of suggested break hours
        """
        try:
            # Check if profile exists
            result = supabase_client.admin.table("habit_profiles").select("*").eq(
                "user_id", user_id
            ).eq("key", "work_pattern").execute()
            
            data = {
                "work_hours_start": work_hours_start,
                "work_hours_end": work_hours_end,
                "busy_periods": busy_periods,
                "break_suggestions": break_suggestions,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if result.data:
                # Update existing
                supabase_client.admin.table("habit_profiles").update(data).eq(
                    "user_id", user_id
                ).eq("key", "work_pattern").execute()
            else:
                # Create new
                data.update({
                    "user_id": user_id,
                    "key": "work_pattern",
                    "value": "analyzed",
                    "confidence_score": 0.8
                })
                supabase_client.admin.table("habit_profiles").insert(data).execute()
            
            logger.info(f"Updated work pattern for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating habit profile: {e}", exc_info=True)
    
    async def _get_habit_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's habit profile.
        
        Args:
            user_id: User ID
            
        Returns:
            Profile dict or None
        """
        result = supabase_client.admin.table("habit_profiles").select("*").eq(
            "user_id", user_id
        ).eq("key", "work_pattern").execute()
        
        return result.data[0] if result.data else None


# Global instance
routine_optimizer = RoutineOptimizerAgent()

