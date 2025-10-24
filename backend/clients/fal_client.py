"""Fal AI API client wrapper for Zyana using fal-ai/any-llm endpoint."""
import asyncio
import httpx
import logging
from typing import List, Dict, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings

logger = logging.getLogger(__name__)


class FalAIClient:
    """Client for interacting with Fal AI API using any-llm endpoint."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Fal AI client.
        
        Args:
            api_key: Fal API key (defaults to settings)
        """
        self.api_key = api_key or settings.fal_api_key
        # FAL AI base URL for REST API
        self.base_url = "https://queue.fal.run"
        self.headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-5-chat",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Call Fal AI any-llm endpoint for text generation.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (openai/gpt-5-chat, google/gemini-2.5-flash, etc.)
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response dict with generated text
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        # Build prompt from messages
        system_prompt = None
        prompt = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                prompt = msg["content"]
        
        # Build FAL AI any-llm payload
        payload = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "priority": "latency"  # For faster responses
        }
        
        if system_prompt:
            payload["system_prompt"] = system_prompt
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Submit request to FAL AI any-llm
                response = await client.post(
                    f"{self.base_url}/fal-ai/any-llm",
                    headers=self.headers,
                    json={"input": payload}
                )
                response.raise_for_status()
                data = response.json()
                
                logger.debug(f"Fal AI response: {data}")
                
                # Handle queue response
                if data.get("status") == "IN_QUEUE":
                    # Get the status URL and poll for result
                    status_url = data.get("status_url")
                    if not status_url:
                        raise Exception("No status URL in queue response")
                    
                    # Poll for result (max 30 seconds)
                    for attempt in range(15):  # 15 attempts, 2 seconds each
                        await asyncio.sleep(2)
                        
                        status_response = await client.get(status_url, headers=self.headers)
                        status_response.raise_for_status()
                        status_data = status_response.json()
                        
                        logger.debug(f"Poll attempt {attempt + 1}: {status_data.get('status')}")
                        
                        if status_data.get("status") == "COMPLETED":
                            if "output" in status_data:
                                return {
                                    "choices": [
                                        {
                                            "message": {
                                                "content": status_data["output"]
                                            }
                                        }
                                    ]
                                }
                        elif status_data.get("status") == "FAILED":
                            raise Exception(f"FAL AI job failed: {status_data.get('error')}")
                    
                    # Timeout after 30 seconds
                    raise Exception("FAL AI job timed out after 30 seconds")
                
                # Direct response (immediate result)
                elif "output" in data:
                    return {
                        "choices": [
                            {
                                "message": {
                                    "content": data["output"]
                                }
                            }
                        ]
                    }
                else:
                    logger.error(f"Unexpected FAL AI response format: {data}")
                    raise Exception("Invalid response format from FAL AI")
                
        except httpx.HTTPError as e:
            logger.error(f"Fal AI API error: {e}")
            raise
    
    async def chat_simple(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "openai/gpt-5-chat",
        temperature: float = 0.0
    ) -> str:
        """Simplified chat method that returns just the text response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model identifier (openai/gpt-5-chat recommended)
            temperature: Sampling temperature
            
        Returns:
            Generated text response
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.chat(messages, model=model, temperature=temperature)
            
            # Extract text from response
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
                elif "text" in choice:
                    return choice["text"]
            
            logger.warning(f"Unexpected response structure: {response}")
            return ""
            
        except Exception as e:
            logger.error(f"Error in chat_simple: {e}")
            raise
    
    async def embed(
        self,
        texts: List[str],
        model: str = "text-embedding-ada-002"
    ) -> List[List[float]]:
        """Generate embeddings for text using Fal AI.
        
        NOTE: FAL AI embeddings are not available via REST API.
        This method returns empty embeddings to avoid breaking the system.
        For production, use OpenAI embeddings directly.
        
        Args:
            texts: List of text strings to embed
            model: Embedding model identifier
            
        Returns:
            List of empty embedding vectors (placeholder)
        """
        logger.warning("FAL AI embeddings not available via REST API. Returning empty embeddings.")
        # Return empty 1536-dimensional vectors (OpenAI embedding size)
        return [[0.0] * 1536 for _ in texts]
    
    async def embed_single(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """Generate embedding for a single text.
        
        NOTE: Placeholder method. Returns empty embedding.
        
        Args:
            text: Text to embed
            model: Embedding model identifier
            
        Returns:
            Empty embedding vector (placeholder)
        """
        embeddings = await self.embed([text], model=model)
        return embeddings[0] if embeddings else [0.0] * 1536


# Global client instance
fal_client = FalAIClient()

