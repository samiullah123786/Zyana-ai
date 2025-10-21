"""Supabase client wrapper for Zyana."""
from supabase import create_client, Client
from config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Wrapper for Supabase client with service role access."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.url = settings.supabase_url
        self.service_key = settings.supabase_service_key
        self.anon_key = settings.supabase_anon_key
        
        # Service role client (admin access)
        self.admin: Client = create_client(self.url, self.service_key)
        
        # Anonymous client (user access)
        self.client: Client = create_client(self.url, self.anon_key)
        
        logger.info(f"Supabase client initialized: {self.url}")
    
    def get_user_client(self, access_token: str) -> Client:
        """Get Supabase client with user access token.
        
        Args:
            access_token: User JWT token
            
        Returns:
            Supabase client with user context
        """
        client = create_client(self.url, self.anon_key)
        client.auth.set_session(access_token, "")
        return client


# Global Supabase client instance
supabase_client = SupabaseClient()

