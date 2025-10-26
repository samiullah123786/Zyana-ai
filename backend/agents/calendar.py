"""Calendar Agent for event management and Google Calendar sync.

Enhanced with:
- Robust datetime parsing via dateparser
- ISO8601 validation with timezone
- Memory persistence to Qdrant
- Full conversation context storage
"""
import logging
import json
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List
from pathlib import Path
import pytz

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from models.schemas import ParsedMessage, EventCreate
from clients.supabase_client import supabase_client
from services.datetime_parser import datetime_parser
from services.context_retriever import context_retriever
from config import settings

logger = logging.getLogger(__name__)

# Default timezone
PAKISTAN_TZ = pytz.timezone(settings.default_timezone)

TOKEN_FILE = Path("config/google_token.json")
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]


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
                return
            
            # FALLBACK: If this user doesn't have credentials, try to find ANY user with credentials
            # This is for personal bot usage where all users share the same Google Calendar
            logger.warning(f"⚠️  No credentials for user {user_id}, checking for any available credentials...")
            fallback_result = supabase_client.admin.table("users").select(
                "id, google_credentials, google_calendar_connected"
            ).eq("google_calendar_connected", True).limit(1).execute()
            
            if fallback_result.data and fallback_result.data[0].get("google_credentials"):
                creds_json = fallback_result.data[0]["google_credentials"]
                self.credentials = Credentials.from_authorized_user_info(
                    json.loads(creds_json), SCOPES
                )
                fallback_user_id = fallback_result.data[0]["id"]
                logger.info(f"✅ Using fallback credentials from user {fallback_user_id} (personal bot mode)")
            else:
                logger.info(f"ℹ️  No Google Calendar credentials found in system")
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
        
        # Extract date and time using datetime_parser
        parsed_datetime = datetime_parser.parse_datetime(parsed.raw_text)
        
        if parsed_datetime['iso_start']:
            start_time = datetime.fromisoformat(parsed_datetime['iso_start'])
            end_time = datetime.fromisoformat(parsed_datetime['iso_end'])
        else:
            # Fallback to current approach
            now = datetime.now(PAKISTAN_TZ)
            start_time = now + timedelta(hours=1)
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
    
    def _extract_datetime_from_parsed_result(
        self,
        parsed_result: Dict[str, Any]
    ) -> tuple[datetime, datetime]:
        """Extract start and end datetimes from intent router result.
        
        Args:
            parsed_result: Result from intent router with calendar data
            
        Returns:
            Tuple of (start_time, end_time) as timezone-aware datetimes
        """
        start_iso = parsed_result.get('start_iso')
        end_iso = parsed_result.get('end_iso')
        duration_minutes = parsed_result.get('duration_minutes', 60)
        
        if start_iso:
            # Parse ISO timestamp
            start_time = datetime.fromisoformat(start_iso)
            
            if end_iso:
                end_time = datetime.fromisoformat(end_iso)
            else:
                # Calculate end time from duration
                end_time = start_time + timedelta(minutes=duration_minutes)
        else:
            # Fallback: use current time + 1 hour
            now = datetime.now(PAKISTAN_TZ)
            start_time = now + timedelta(hours=1)
            end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Ensure timezone-aware
        if start_time.tzinfo is None:
            start_time = PAKISTAN_TZ.localize(start_time)
        if end_time.tzinfo is None:
            end_time = PAKISTAN_TZ.localize(end_time)
        
        return start_time, end_time
    
    def _validate_iso_timestamps(self, start_iso: str, end_iso: str) -> bool:
        """Validate ISO8601 timestamps with timezone.
        
        Args:
            start_iso: Start time ISO string
            end_iso: End time ISO string
            
        Returns:
            True if valid, False otherwise
        """
        try:
            start_dt = datetime.fromisoformat(start_iso)
            end_dt = datetime.fromisoformat(end_iso)
            
            # Must have timezone
            if start_dt.tzinfo is None or end_dt.tzinfo is None:
                logger.warning("❌ ISO timestamps missing timezone")
                return False
            
            # End must be after start
            if end_dt <= start_dt:
                logger.warning("❌ End time must be after start time")
                return False
            
            return True
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid ISO timestamps: {e}")
            return False
    
    async def create_event_from_intent(
        self,
        intent_result: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Create calendar event from intent router result.
        
        Args:
            intent_result: Result from intent router with calendar data
            user_id: User identifier
            
        Returns:
            Response dict
        """
        # Map Telegram user ID to internal user_id
        internal_user_id = await self._get_or_create_user(user_id)
        
        # Reload credentials for this specific user
        self._load_credentials(user_id=internal_user_id)
        
        # Extract datetime from intent result
        start_time, end_time = self._extract_datetime_from_parsed_result(intent_result)
        
        # Extract event details
        title = intent_result.get('title') or intent_result.get('parameters', {}).get('title', 'Event')
        attendees = intent_result.get('attendees', [])
        location = intent_result.get('location')
        session_id = intent_result.get('session_id')
        raw_text = intent_result.get('raw_text', intent_result.get('parameters', {}).get('description', ''))
        confidence_score = intent_result.get('confidence', 1.0)
        
        # Create event object
        event = EventCreate(
            user_id=internal_user_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=raw_text,
            location=location
        )
        
        # Create event
        result = await self.create_event(event, session_id=session_id)
        
        # Store resolved event with full context
        if result.get('success'):
            await self._store_resolved_event(
                user_id=user_id,
                session_id=session_id,
                raw_text=raw_text,
                resolved_title=title,
                resolved_start_iso=start_time.isoformat(),
                resolved_end_iso=end_time.isoformat(),
                attendees=attendees,
                location=location,
                google_event_id=result.get('data', {}).get('google_event_id'),
                confidence_score=confidence_score
            )
        
        return result
    
    async def _store_resolved_event(
        self,
        user_id: str,
        session_id: Optional[str],
        raw_text: str,
        resolved_title: str,
        resolved_start_iso: str,
        resolved_end_iso: str,
        attendees: List[str],
        location: Optional[str],
        google_event_id: Optional[str],
        confidence_score: float
    ) -> bool:
        """Store resolved calendar event with full conversation context.
        
        Args:
            user_id: User identifier
            session_id: Session ID (if from multi-turn clarification)
            raw_text: Original user message
            resolved_title: Final resolved title
            resolved_start_iso: ISO start time
            resolved_end_iso: ISO end time
            attendees: List of attendees
            location: Event location
            google_event_id: Google Calendar event ID
            confidence_score: Confidence score
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build event data (only include session_id if it exists in sessions table)
            event_data = {
                "user_id": user_id,
                "raw_user_text": raw_text,
                "resolved_title": resolved_title,
                "resolved_start_iso": resolved_start_iso,
                "resolved_end_iso": resolved_end_iso,
                "attendees": attendees,
                "location": location,
                "google_event_id": google_event_id,
                "confidence_score": confidence_score
            }
            
            # Only add session_id if provided (for multi-turn clarification)
            # Skip if session doesn't exist to avoid foreign key constraint violation
            if session_id:
                # Check if session exists
                try:
                    from services.session_manager import session_manager
                    session_data = await session_manager.get_session(session_id)
                    if session_data:
                        event_data["session_id"] = session_id
                except:
                    # Session doesn't exist, skip session_id
                    logger.debug(f"Session {session_id} not found, storing event without session link")
            
            # Store in calendar_events table
            result = supabase_client.admin.table("calendar_events").insert(event_data).execute()
            
            logger.info(f"✅ Stored resolved calendar event: {resolved_title}")
            
            # Store in Qdrant for vector search
            await context_retriever.store_calendar_event(
                user_id=user_id,
                session_id=session_id or f"direct_{int(datetime.now().timestamp())}",
                raw_text=raw_text,
                resolved_title=resolved_title,
                resolved_start_iso=resolved_start_iso,
                resolved_end_iso=resolved_end_iso,
                attendees=attendees,
                confidence_score=confidence_score
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing resolved event: {e}", exc_info=True)
            return False
    
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
    
    async def create_event(
        self,
        event: EventCreate,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create calendar event in DB and Google Calendar.
        
        Args:
            event: Event data
            session_id: Optional session ID for tracking multi-turn clarifications
            
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

