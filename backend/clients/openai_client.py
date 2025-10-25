"""OpenAI API client as fallback for Fal AI."""
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

# Try to import OpenAI with new API
try:
    from openai import AsyncOpenAI
    HAS_OPENAI_PACKAGE = True
except ImportError:
    HAS_OPENAI_PACKAGE = False
    logger.warning("OpenAI package not installed. Install with: pip install openai")


class OpenAIClient:
    """Client for OpenAI API as fallback."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to settings if available)
        """
        if not HAS_OPENAI_PACKAGE:
            self.enabled = False
            logger.warning("OpenAI package not available")
            return
        
        # Try to get OpenAI key from env, otherwise skip
        self.api_key = api_key or getattr(settings, 'openai_api_key', None)
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.enabled = True
            logger.info("OpenAI client initialized successfully")
        else:
            self.enabled = False
            self.client = None
            logger.warning("OpenAI API key not found, client disabled")
    
    async def chat_simple(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.0
    ) -> str:
        """Simplified chat method that returns just the text response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model identifier
            temperature: Sampling temperature
            
        Returns:
            Generated text response
        """
        if not self.enabled:
            raise Exception("OpenAI client not enabled - API key missing or package not installed")
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def embed(self, texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not self.enabled:
            raise Exception("OpenAI client not enabled")
        
        try:
            response = await self.client.embeddings.create(model=model, input=texts)
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise
    
    async def embed_single(self, text: str, model: str = "text-embedding-3-small") -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed([text], model=model)
        return embeddings[0] if embeddings else []


# Global client instance
openai_client = OpenAIClient()

