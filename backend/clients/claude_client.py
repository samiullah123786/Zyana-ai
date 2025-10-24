"""Anthropic Claude API client for production-grade AI responses."""
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

# Try to import Anthropic SDK
try:
    from anthropic import AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    logger.warning("Anthropic package not installed. Install with: pip install anthropic")


class ClaudeClient:
    """Production-grade Claude AI client with proper error handling."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude client.
        
        Args:
            api_key: Anthropic API key (defaults to settings if available)
        """
        if not HAS_ANTHROPIC:
            self.enabled = False
            logger.warning("Anthropic package not available")
            return
        
        # Get API key
        self.api_key = api_key or getattr(settings, 'anthropic_api_key', None)
        if self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)
            self.enabled = True
            logger.info("✅ Claude client initialized successfully")
        else:
            self.enabled = False
            self.client = None
            logger.warning("❌ Claude API key not found")
    
    async def chat_simple(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.0,
        max_tokens: int = 1024
    ) -> str:
        """Send chat completion request to Claude.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Claude model (claude-3-5-sonnet-20241022 recommended)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If client not enabled or API error
        """
        if not self.enabled:
            raise Exception("Claude client not enabled - API key missing or package not installed")
        
        try:
            # Build messages
            messages = [{"role": "user", "content": prompt}]
            
            # Call Claude API
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else "",
                messages=messages
            )
            
            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text
            
            logger.warning("Empty response from Claude")
            return ""
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise


# Global client instance
claude_client = ClaudeClient()

