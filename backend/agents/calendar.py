"""Calendar Agent for event management and Google Calendar sync."""
import logging
import json
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional
from pathlib import Path
import pytz

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from models.schemas import ParsedMessage, EventCreate
from clients.supabase_client import supabase_client
from config import settings

logger = logging.getLogger(__name__)

# Pakistan timezone
PAKISTAN_TZ = pytz.timezone('Asia/Karachi')

TOKEN_FILE = Path("config/google_token.json")
SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarAgent:
    """Agent for handling calendar events and Google Calendar sync."""
    
    def __init__(self):
        """Initialize Calendar Agent."""
        self.credentials = None
        self.user_id = 1  # Default user (personal bot)
        self._load_credentials()
    
    def _load_credentials(self, user_id: int = 1):
        """Load Google OAuth credentials from Supabase (persistent storage).
        
        Args:
            user_id: User ID to load credentials for
        """
        try:
            # Load from Supabase instead of file system (survives Render restarts)
            result = supabase_client.admin.table("users").select(
                "google_credentials, google_calendar_connected"
            ).eq("id", user_id).execute()
            
            if result.data and result.data[0].get("google_credentials"):
                creds_json = result.data[0]["google_credentials"]
                self.credentials = Credentials.from_authorized_user_info(
                    json.loads(creds_json), SCOPES
                )
                logger.info(f"✅ Loaded Google Calendar credentials from Supabase for user {user_id}")
            else:
                logger.info(f"ℹ️  No Google Calendar credentials found for user {user_id}")
                self.credentials = None
        except Exception as e:
            logger.error(f"Error loading credentials from Supabase: {e}")
            self.credentials = None
    
    def _save_credentials(self, creds: Credentials, user_id: int = 1):
        """Save credentials to Supabase (persistent across restarts).
        
        Args:
            creds: Google OAuth credentials
            user_id: User ID to save credentials for
        """
        try:
            # Save to Supabase instead of file system
            creds_json = creds.to_json()
            
            supabase_client.admin.table("users").update({
                "google_credentials": creds_json,
                "google_calendar_connected": True,
                "google_calendar_email": creds.to_json()  # Extract email if available
            }).eq("id", user_id).execute()
            
            self.credentials = creds
            logger.info(f"✅ Saved Google Calendar credentials to Supabase for user {user_id}")
        except Exception as e:
            logger.error(f"Error saving credentials to Supabase: {e}")
    
    def get_auth_url(self) -> str:
        """Get Google OAuth authorization URL.
        
        Returns:
            Authorization URL
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_redirect_uri]
                }
            },
            scopes=SCOPES,
            redirect_uri=settings.google_redirect_uri
        )
        
        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url
    
    async def handle_oauth_callback(self, code: str, user_id: int = 1):
        """Handle OAuth callback and save credentials.
        
        Args:
            code: Authorization code from Google
            user_id: User ID to associate credentials with (default: 1 for personal bot)
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_redirect_uri]
                }
            },
            scopes=SCOPES,
            redirect_uri=settings.google_redirect_uri
        )
        
        flow.fetch_token(code=code)
        self._save_credentials(flow.credentials, user_id=user_id)
    
    async def process(self, parsed: ParsedMessage, user_id: str) -> Dict[str, Any]:
        """Process calendar-related intents.
        
        Args:
            parsed: Parsed message with calendar intent
            user_id: User identifier
            
        Returns:
            Response dict
        """
        try:
            if parsed.intent == "calendar":
                return await self._create_event_from_parsed(parsed, user_id)
            else:
                return {
                    "success": False,
                    "message": "Unknown calendar intent",
                    "data": None
                }
        except Exception as e:
            logger.error(f"Calendar agent error: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error processing calendar action: {str(e)}",
                "data": None
            }
    
    async def _create_event_from_parsed(self, parsed: ParsedMessage, user_id: str) -> Dict[str, Any]:
        """Create event from parsed message.
        
        Args:
            parsed: Parsed message
            user_id: User identifier
            
        Returns:
            Response dict
        """
        # Map Telegram user ID to internal user_id
        internal_user_id = await self._get_or_create_user(user_id)
        
        # Reload credentials for this specific user (fixes multi-user bug)
        self._load_credentials(user_id=internal_user_id)
        
        # Extract date and time from message
        event_date, event_time = self._extract_datetime_from_message(parsed.raw_text)
        
        # Create datetime objects in Pakistan timezone
        naive_datetime = datetime.combine(event_date, event_time)
        start_time = PAKISTAN_TZ.localize(naive_datetime)
        end_time = start_time + timedelta(hours=1)
        
        # Extract title (person name or description)
        title = parsed.person if parsed.person else "Meeting"
        if "with" in parsed.raw_text.lower():
            title = f"Meeting with {parsed.person or 'someone'}"
        
        event = EventCreate(
            user_id=internal_user_id,  # Always 1 for personal bot (su8352282@gmail.com)
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=parsed.raw_text
        )
        
        return await self.create_event(event)
    
    def _extract_datetime_from_message(self, message: str) -> tuple:
        """Extract date and time from calendar message.
        
        Args:
            message: User message
            
        Returns:
            Tuple of (date, time)
        """
        from datetime import time as datetime_time
        import re
        
        message_lower = message.lower()
        
        # Get current time in Pakistan timezone
        now_pk = datetime.now(PAKISTAN_TZ)
        today = now_pk.date()
        
        # Handle "in X minutes/hours" patterns
        if "in" in message_lower and ("minute" in message_lower or "hour" in message_lower):
            # Extract number
            match = re.search(r'in\s+(\d+)\s+(minute|hour)', message_lower)
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
                
                if unit == "minute":
                    future_time = now_pk + timedelta(minutes=amount)
                else:  # hour
                    future_time = now_pk + timedelta(hours=amount)
                
                return future_time.date(), future_time.time()
        
        # Extract date
        event_date = today
        if "tomorrow" in message_lower:
            event_date = today + timedelta(days=1)
        elif "today" in message_lower:
            event_date = today
        elif "yesterday" in message_lower:
            event_date = today - timedelta(days=1)
        elif any(day in message_lower for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
            # Simple day extraction (could be enhanced)
            event_date = today + timedelta(days=1)
        
        # Natural language time words
        if "morning" in message_lower:
            event_time = datetime_time(hour=9, minute=0)
        elif "noon" in message_lower or "midday" in message_lower:
            event_time = datetime_time(hour=12, minute=0)
        elif "afternoon" in message_lower:
            event_time = datetime_time(hour=14, minute=0)  # 2pm
        elif "evening" in message_lower:
            event_time = datetime_time(hour=18, minute=0)  # 6pm
        elif "night" in message_lower:
            event_time = datetime_time(hour=20, minute=0)  # 8pm
        else:
            # Extract time - look for patterns like "10am", "3pm", "10:30am", "15:00", "10 o'clock"
            time_patterns = [
                r'(\d{1,2}):(\d{2})\s*(am|pm)',  # 10:30am
                r'(\d{1,2})\s*o\'?clock\s*(am|pm|in the morning|in the afternoon|in the evening)?',  # 10 o'clock
                r'(\d{1,2})\s*(am|pm)',           # 10am
                r'(\d{1,2}):(\d{2})',             # 15:00
            ]
            
            event_time = datetime_time(hour=9, minute=0)  # Default 9am
            
            for pattern in time_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    if len(match.groups()) == 3:  # With minutes and am/pm
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        period = match.group(3)
                        if period == 'pm' and hour < 12:
                            hour += 12
                        elif period == 'am' and hour == 12:
                            hour = 0
                        event_time = datetime_time(hour=hour, minute=minute)
                        break
                    elif len(match.groups()) == 2 and match.group(2) in ['am', 'pm']:  # Just hour with am/pm
                        hour = int(match.group(1))
                        period = match.group(2)
                        if period == 'pm' and hour < 12:
                            hour += 12
                        elif period == 'am' and hour == 12:
                            hour = 0
                        event_time = datetime_time(hour=hour, minute=0)
                        break
                    elif len(match.groups()) == 2:  # 24-hour format
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        event_time = datetime_time(hour=hour, minute=minute)
                        break
        
        return event_date, event_time
    
    def _generate_google_calendar_link(self, event: EventCreate) -> str:
        """Generate a Google Calendar "Add Event" link.
        
        Args:
            event: Event data
            
        Returns:
            Google Calendar link
        """
        from urllib.parse import quote
        
        # Convert to UTC for Google Calendar link (it expects UTC)
        start_time_utc = event.start_time.astimezone(pytz.UTC)
        end_time_utc = event.end_time.astimezone(pytz.UTC)
        
        # Format datetime for Google Calendar (YYYYMMDDTHHmmssZ)
        start_str = start_time_utc.strftime('%Y%m%dT%H%M%SZ')
        end_str = end_time_utc.strftime('%Y%m%dT%H%M%SZ')
        
        # Build Google Calendar URL
        base_url = "https://calendar.google.com/calendar/render"
        params = [
            f"action=TEMPLATE",
            f"text={quote(event.title)}",
            f"dates={start_str}/{end_str}",
            f"ctz=Asia/Karachi",  # Set timezone to Pakistan
        ]
        
        if event.description:
            params.append(f"details={quote(event.description)}")
        
        if event.location:
            params.append(f"location={quote(event.location)}")
        
        return f"{base_url}?{'&'.join(params)}"
    
    async def create_event(self, event: EventCreate) -> Dict[str, Any]:
        """Create calendar event in DB and Google Calendar.
        
        Args:
            event: Event data
            
        Returns:
            Response dict
        """
        google_event_id = None
        
        # Create in Google Calendar if authenticated
        if self.credentials:
            try:
                logger.info(f"📅 Syncing to Google Calendar...")
                google_event_id = await self._create_google_event(event)
                logger.info(f"✅ Synced to Google Calendar: {google_event_id}")
            except Exception as e:
                logger.error(f"❌ Error creating Google event: {e}", exc_info=True)
        else:
            logger.warning(f"⚠️  Google Calendar not connected - event only saved to database. Click the link in the message to add to Google Calendar manually.")
        
        # Create in database
        result = supabase_client.admin.table("events").insert({
            "user_id": event.user_id,
            "title": event.title,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "description": event.description,
            "location": event.location,
            "google_event_id": google_event_id
        }).execute()
        
        db_event = result.data[0] if result.data else {}
        
        # Generate Google Calendar Add Link
        calendar_link = self._generate_google_calendar_link(event)
        
        # Build user-friendly message based on sync status
        if google_event_id:
            # Successfully synced
            message = (
                f"✅ Event created: {event.title}\n"
                f"📅 {event.start_time.strftime('%Y-%m-%d at %I:%M %p')} (Pakistan Time)\n"
                f"🔗 Synced to your Google Calendar!\n\n"
                f"If you don't see it, add manually:\n"
                f"{calendar_link}"
            )
        else:
            # Not synced (not authenticated)
            message = (
                f"✅ Event created: {event.title}\n"
                f"📅 {event.start_time.strftime('%Y-%m-%d at %I:%M %p')} (Pakistan Time)\n\n"
                f"⚠️  Google Calendar not connected.\n"
                f"➕ Click to add to Google Calendar:\n"
                f"{calendar_link}\n\n"
                f"💡 To auto-sync future events, authenticate at:\n"
                f"{settings.backend_url}/calendar/auth/google"
            )
        
        return {
            "success": True,
            "message": message,
            "data": db_event,
            "calendar_link": calendar_link
        }
    
    async def _create_google_event(self, event: EventCreate) -> Optional[str]:
        """Create event in Google Calendar.
        
        Args:
            event: Event data
            
        Returns:
            Google event ID
        """
        if not self.credentials:
            return None
        
        # Refresh credentials if needed
        if self.credentials.expired and self.credentials.refresh_token:
            self.credentials.refresh(Request())
            self._save_credentials(self.credentials)
        
        service = build('calendar', 'v3', credentials=self.credentials)
        
        google_event = {
            'summary': event.title,
            'description': event.description,
            'start': {
                'dateTime': event.start_time.isoformat(),
                'timeZone': 'Asia/Karachi',
            },
            'end': {
                'dateTime': event.end_time.isoformat(),
                'timeZone': 'Asia/Karachi',
            },
        }
        
        if event.location:
            google_event['location'] = event.location
        
        created_event = service.events().insert(
            calendarId='primary',
            body=google_event
        ).execute()
        
        return created_event['id']
    
    async def sync_from_google(self) -> Dict[str, Any]:
        """Sync events from Google Calendar.
        
        Returns:
            Sync result
        """
        if not self.credentials:
            return {
                "success": False,
                "message": "Google Calendar not connected. Please authorize first.",
                "data": None
            }
        
        try:
            # Refresh credentials if needed
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                self._save_credentials(self.credentials)
            
            service = build('calendar', 'v3', credentials=self.credentials)
            
            # Get events from the next 30 days
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            synced_count = 0
            
            for event in events:
                google_event_id = event['id']
                
                # Check if already exists
                existing = supabase_client.admin.table("events").select("id").eq(
                    "google_event_id", google_event_id
                ).execute()
                
                if not existing.data:
                    # Insert new event
                    supabase_client.admin.table("events").insert({
                        "user_id": 1,
                        "title": event.get('summary', 'Untitled'),
                        "start_time": event['start'].get('dateTime', event['start'].get('date')),
                        "end_time": event['end'].get('dateTime', event['end'].get('date')),
                        "description": event.get('description'),
                        "location": event.get('location'),
                        "google_event_id": google_event_id
                    }).execute()
                    synced_count += 1
            
            return {
                "success": True,
                "message": f"✅ Synced {synced_count} new events from Google Calendar",
                "data": {"synced_count": synced_count}
            }
            
        except Exception as e:
            logger.error(f"Error syncing from Google: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error syncing: {str(e)}",
                "data": None
            }
    
    async def _get_or_create_user(self, telegram_id: str) -> int:
        """Get or create user by telegram_id, always returning user_id=1 for personal bot.
        
        Args:
            telegram_id: Telegram user identifier
            
        Returns:
            Internal user_id (always 1 for personal bot)
        """
        try:
            # Check if user exists
            result = supabase_client.admin.table("users").select("id").eq(
                "telegram_id", telegram_id
            ).limit(1).execute()
            
            if result.data:
                user_id = result.data[0]["id"]
                logger.info(f"✅ Found existing user: telegram_id={telegram_id} -> user_id={user_id}")
                return user_id
            
            # Create new user (should be user_id=1 for personal bot)
            new_user = supabase_client.admin.table("users").insert({
                "telegram_id": telegram_id,
                "name": f"User {telegram_id[:8]}"
            }).execute()
            
            user_id = new_user.data[0]["id"] if new_user.data else 1
            logger.info(f"✅ Created new user: telegram_id={telegram_id} -> user_id={user_id}")
            return user_id
            
        except Exception as e:
            logger.error(f"Error getting/creating user: {e}")
            return 1  # Fallback to user_id=1 for personal bot


# Global instance
calendar_agent = CalendarAgent()

