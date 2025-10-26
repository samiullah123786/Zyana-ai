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
        stop=stop_after_attempt(3),  # Try 3 times with exponential backoff
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-5-chat",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Call Fal AI any-llm endpoint for text generation.
        
        Following official FAL AI queue pattern:
        1. Submit request → get request_id
        2. Poll status until COMPLETED
        3. Fetch result from /requests/{request_id}/result endpoint
        
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
        
        # Build FAL AI any-llm payload (per official docs schema)
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
            async with httpx.AsyncClient(timeout=90.0) as client:
                # STEP 1: Submit request to FAL AI any-llm queue
                logger.info(f"📤 Submitting FAL AI request (model: {model})")
                response = await client.post(
                    f"{self.base_url}/fal-ai/any-llm",
                    headers=self.headers,
                    json={"input": payload}
                )
                response.raise_for_status()
                submit_data = response.json()
                
                logger.debug(f"Submit response: {submit_data}")
                
                # Extract request_id (this is critical!)
                request_id = submit_data.get("request_id")
                if not request_id:
                    logger.error(f"No request_id in submit response: {submit_data}")
                    raise Exception("Failed to get request_id from FAL AI")
                
                logger.info(f"✅ Job submitted: request_id={request_id}")
                
                # STEP 2: Poll status endpoint until COMPLETED
                status_url = f"{self.base_url}/fal-ai/any-llm/requests/{request_id}/status"
                max_attempts = 40  # 40 attempts, 2 seconds each = 80 seconds
                
                for attempt in range(max_attempts):
                    await asyncio.sleep(2)
                    
                    status_response = await client.get(status_url, headers=self.headers)
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    
                    current_status = status_data.get('status')
                    
                    # Log progress every 5 attempts
                    if attempt % 5 == 0 and attempt > 0:
                        logger.info(f"⏳ FAL AI processing... ({attempt * 2}s elapsed, status: {current_status})")
                    
                    if current_status == "COMPLETED":
                        logger.info(f"✅ Job COMPLETED after {(attempt + 1) * 2} seconds")
                        
                        # STEP 3: Fetch the ACTUAL RESULT from the result endpoint
                        # THIS IS THE MISSING STEP that was causing the issue!
                        result_url = f"{self.base_url}/fal-ai/any-llm/requests/{request_id}/result"
                        logger.info(f"📥 Fetching result from: {result_url}")
                        
                        try:
                            result_response = await client.get(result_url, headers=self.headers)
                            result_response.raise_for_status()
                            result_data = result_response.json()
                            
                            logger.debug(f"Result data: {result_data}")
                            
                            # Extract output per FAL AI schema: result_data["data"]["output"]
                            output = None
                            if "data" in result_data:
                                output = result_data["data"].get("output")
                            
                            # Fallback: try top-level output
                            if not output:
                                output = result_data.get("output")
                            
                            if output:
                                logger.info(f"✅ Got output: {len(output)} chars")
                                return {
                                    "choices": [
                                        {
                                            "message": {
                                                "content": output
                                            }
                                        }
                                    ]
                                }
                            else:
                                # No output even after fetching result
                                logger.error(f"❌ No output in result data: {result_data}")
                                return {
                                    "choices": [
                                        {
                                            "message": {
                                                "content": "Hey Sami! I processed your request but need a moment to formulate my thoughts. Could you try rephrasing?"
                                            }
                                        }
                                    ]
                                }
                        except Exception as e:
                            logger.error(f"❌ Failed to fetch result: {e}", exc_info=True)
                            return {
                                "choices": [
                                    {
                                        "message": {
                                            "content": "I'm having a bit of trouble processing that right now. Mind trying again?"
                                        }
                                    }
                                ]
                            }
                    
                    elif current_status == "FAILED":
                        error_msg = status_data.get('error', 'Unknown error')
                        logger.error(f"❌ FAL AI job failed: {error_msg}")
                        raise Exception(f"FAL AI job failed: {error_msg}")
                    
                    elif current_status in ["IN_QUEUE", "IN_PROGRESS"]:
                        # Normal - keep polling
                        continue
                    else:
                        logger.warning(f"Unknown status: {current_status}")
                
                # Timeout
                logger.error(f"⏰ FAL AI timeout after {max_attempts * 2}s. request_id: {request_id}")
                return {
                    "choices": [
                        {
                            "message": {
                                "content": "That's taking longer than expected, Sami. Let me try again in a moment!"
                            }
                        }
                    ]
                }
                
        except httpx.HTTPError as e:
            logger.error(f"❌ Fal AI HTTP error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"❌ Fal AI unexpected error: {e}", exc_info=True)
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
            # Validate API key before making request
            if not self.api_key or self.api_key == "":
                logger.error("FAL_API_KEY is not configured")
                return "I'm having trouble reaching my brain right now, Sami. Please try again shortly. (API key missing)"
            
            response = await self.chat(messages, model=model, temperature=temperature)
            
            # Extract text from response
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
                elif "text" in choice:
                    return choice["text"]
            
            logger.warning(f"Unexpected response structure: {response}")
            return "I got a response but couldn't understand it. Please try again."
            
        except Exception as e:
            logger.error(f"Error in chat_simple: {e}", exc_info=True)
            # Graceful fallback instead of crashing
            return "I'm having trouble reaching my brain right now, Sami. Please try again shortly."
    
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

