"""OpenAI API client - Primary AI provider for Zyana.

Supports:
- GPT-4o (default, optimized for speed and intelligence)
- GPT-4 Turbo
- GPT-3.5 Turbo
- text-embedding-3-small (embeddings)

Includes retry logic, error handling, and graceful fallbacks.
"""
import logging
from typing import Optional, List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import settings

logger = logging.getLogger(__name__)

# Try to import OpenAI with new API
try:
    from openai import AsyncOpenAI, OpenAIError, RateLimitError, APIConnectionError
    HAS_OPENAI_PACKAGE = True
except ImportError:
    HAS_OPENAI_PACKAGE = False
    OpenAIError = Exception  # Fallback
    RateLimitError = Exception
    APIConnectionError = Exception
    logger.warning("OpenAI package not installed. Install with: pip install openai")


class OpenAIClient:
    """Primary AI client for Zyana using OpenAI GPT models.
    
    Replaces FAL AI as the default provider for:
    - Chat completions (intent routing, summarization, conversations)
    - Text embeddings (memory, RAG, semantic search)
    
    Features:
    - Automatic retry on rate limits and connection errors
    - Graceful error handling with user-friendly fallbacks
    - Support for GPT-4o, GPT-4, and GPT-3.5-turbo
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to settings.openai_api_key)
            
        Raises:
            Warning if package not installed or API key missing
        """
        if not HAS_OPENAI_PACKAGE:
            self.enabled = False
            logger.error("❌ OpenAI package not installed. Run: pip install openai")
            return
        
        # Get API key from parameter or settings
        self.api_key = api_key or getattr(settings, 'openai_api_key', None)
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key, timeout=60.0)
            self.enabled = True
            logger.info(f"✅ OpenAI client initialized (key: {self.api_key[:10]}...)")
        else:
            self.enabled = False
            self.client = None
            logger.error("❌ OpenAI API key not found - set OPENAI_API_KEY environment variable")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
        reraise=True
    )
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Full chat completion method with retry logic.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (defaults to settings.openai_model)
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response dict in OpenAI format with choices
            
        Raises:
            Exception: If client not enabled or API error
        """
        if not self.enabled:
            raise Exception("OpenAI client not enabled - API key missing or package not installed")
        
        # Use default model from settings if not specified
        model = model or getattr(settings, 'openai_model', 'gpt-4o')
        
        try:
            logger.info(f"📤 OpenAI Request: model={model}, messages={len(messages)}, temp={temperature}")
            
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            
            response = await self.client.chat.completions.create(**kwargs)
            
            logger.info(f"✅ OpenAI Response: {len(response.choices[0].message.content)} characters")
            
            # Return in compatible format
            return {
                "choices": [
                    {
                        "message": {
                            "content": response.choices[0].message.content
                        }
                    }
                ]
            }
            
        except RateLimitError as e:
            logger.warning(f"⚠️  OpenAI rate limit hit, retrying...")
            raise  # Retry will handle this
        except APIConnectionError as e:
            logger.warning(f"⚠️  OpenAI connection error, retrying...")
            raise  # Retry will handle this
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}", exc_info=True)
            raise
    
    async def chat_simple(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """Simplified chat method that returns just the text response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model identifier (defaults to settings.openai_model)
            temperature: Sampling temperature
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If client not enabled or API error
        """
        if not self.enabled:
            raise Exception("OpenAI client not enabled - API key missing or package not installed")
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Use full chat method which includes retry logic
            response = await self.chat(messages, model=model, temperature=temperature)
            
            return response["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"❌ OpenAI chat_simple error: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
        reraise=True
    )
    async def embed(self, texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
        """Generate embeddings for multiple texts with retry logic.
        
        Args:
            texts: List of text strings to embed
            model: Embedding model (default: text-embedding-3-small)
            
        Returns:
            List of embedding vectors (each is a list of floats)
            
        Raises:
            Exception: If client not enabled or API error
        """
        if not self.enabled:
            raise Exception("OpenAI client not enabled")
        
        try:
            logger.debug(f"📤 OpenAI Embeddings: {len(texts)} texts, model={model}")
            response = await self.client.embeddings.create(model=model, input=texts)
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings
        except RateLimitError as e:
            logger.warning(f"⚠️  OpenAI embedding rate limit, retrying...")
            raise
        except APIConnectionError as e:
            logger.warning(f"⚠️  OpenAI embedding connection error, retrying...")
            raise
        except Exception as e:
            logger.error(f"❌ OpenAI embedding error: {e}", exc_info=True)
            raise
    
    async def embed_single(self, text: str, model: str = "text-embedding-3-small") -> list[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            model: Embedding model (default: text-embedding-3-small)
            
        Returns:
            Embedding vector (list of floats)
        """
        embeddings = await self.embed([text], model=model)
        return embeddings[0] if embeddings else []


# Global client instance
openai_client = OpenAIClient()

