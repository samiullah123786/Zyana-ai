"""Calendar Agent for event management and Google Calendar sync."""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from models.schemas import ParsedMessage, EventCreate
from clients.supabase_client import supabase_client
from config import settings

logger = logging.getLogger(__name__)

TOKEN_FILE = Path("config/google_token.json")
SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarAgent:
    """Agent for handling calendar events and Google Calendar sync."""
    
    def __init__(self):
        """Initialize Calendar Agent."""
        self.credentials = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Load Google OAuth credentials."""
        if TOKEN_FILE.exists():
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    str(TOKEN_FILE), SCOPES
                )
            except Exception as e:
                logger.error(f"Error loading credentials: {e}")
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to file."""
        try:
            TOKEN_FILE.parent.mkdir(exist_ok=True)
            with TOKEN_FILE.open('w') as f:
                f.write(creds.to_json())
            self.credentials = creds
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
    
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
    
    async def handle_oauth_callback(self, code: str):
        """Handle OAuth callback and save credentials.
        
        Args:
            code: Authorization code from Google
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
        self._save_credentials(flow.credentials)
    
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
        # Parse time from description or use defaults
        start_time = datetime.combine(parsed.date, datetime.min.time().replace(hour=9))
        end_time = start_time + timedelta(hours=1)
        
        event = EventCreate(
            user_id=1,  # TODO: Map from auth
            title=parsed.description or parsed.raw_text,
            start_time=start_time,
            end_time=end_time,
            description=parsed.raw_text
        )
        
        return await self.create_event(event)
    
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
                google_event_id = await self._create_google_event(event)
            except Exception as e:
                logger.error(f"Error creating Google event: {e}")
        
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
        
        message = (
            f"✅ Event created: {event.title}\n"
            f"📅 {event.start_time.strftime('%Y-%m-%d at %I:%M %p')}"
        )
        
        if google_event_id:
            message += "\n🔗 Synced to Google Calendar"
        
        return {
            "success": True,
            "message": message,
            "data": db_event
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


# Global instance
calendar_agent = CalendarAgent()

