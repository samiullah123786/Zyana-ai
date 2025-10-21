"""Fal AI API client wrapper for Zyana."""
import httpx
import logging
from typing import List, Dict, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings

logger = logging.getLogger(__name__)


class FalAIClient:
    """Client for interacting with Fal AI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Fal AI client.
        
        Args:
            api_key: Fal API key (defaults to settings)
        """
        self.api_key = api_key or settings.fal_api_key
        self.base_url = "https://fal.run"
        self.headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        temperature: float = 0.0,
        functions: Optional[List[Dict]] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Call Fal Chat API for text generation.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (gpt-4, gpt-3.5-turbo, etc.)
            temperature: Sampling temperature (0.0 - 2.0)
            functions: Optional function definitions for function calling
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response dict with generated text and metadata
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        payload = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
        }
        
        if functions:
            payload["functions"] = functions
            payload["function_call"] = "auto"
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                logger.debug(f"Fal Chat API response: {data}")
                return data
                
        except httpx.HTTPError as e:
            logger.error(f"Fal Chat API error: {e}")
            raise
    
    async def chat_simple(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4",
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
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.chat(messages, model=model, temperature=temperature)
        
        # Extract text from response
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            if "message" in choice:
                return choice["message"]["content"]
            elif "text" in choice:
                return choice["text"]
        
        return ""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed(
        self,
        texts: List[str],
        model: str = "text-embedding-ada-002"
    ) -> List[List[float]]:
        """Generate embeddings for text using Fal AI.
        
        Args:
            texts: List of text strings to embed
            model: Embedding model identifier
            
        Returns:
            List of embedding vectors
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        payload = {
            "input": texts,
            "model": model
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract embeddings from response
                if "data" in data:
                    embeddings = [item["embedding"] for item in data["data"]]
                    logger.debug(f"Generated {len(embeddings)} embeddings")
                    return embeddings
                
                return []
                
        except httpx.HTTPError as e:
            logger.error(f"Fal Embeddings API error: {e}")
            raise
    
    async def embed_single(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            model: Embedding model identifier
            
        Returns:
            Embedding vector
        """
        embeddings = await self.embed([text], model=model)
        return embeddings[0] if embeddings else []


# Global client instance
fal_client = FalAIClient()

