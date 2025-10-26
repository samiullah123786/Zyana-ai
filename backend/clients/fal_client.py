"""Fal AI API client wrapper for Zyana using fal-ai/any-llm endpoint.

This client uses FAL AI's REST API following their official documentation:
https://fal.ai/models/fal-ai/any-llm/api

Key points:
1. Send arguments directly (NOT wrapped in {"input": ...})
2. Use correct model names with provider prefix (e.g., "anthropic/claude-3.5-sonnet")
3. Response has "output" field with the generated text
"""
import asyncio
import httpx
import logging
import json
from typing import List, Dict, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings

logger = logging.getLogger(__name__)


class FalAIClient:
    """Client for interacting with Fal AI API using any-llm endpoint.
    
    Follows FAL AI official documentation for any-llm model.
    Supports both synchronous and queue-based (async) requests.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Fal AI client.
        
        Args:
            api_key: Fal API key (defaults to settings)
        """
        self.api_key = api_key or settings.fal_api_key
        # FAL AI REST API endpoints
        self.sync_url = "https://fal.run/fal-ai/any-llm"  # Synchronous API
        self.queue_url = "https://queue.fal.run/fal-ai/any-llm"  # Queue API for long-running
        self.headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"✅ FalAIClient initialized with key: {self.api_key[:10]}...")
    
    @retry(
        stop=stop_after_attempt(2),  # Try 2 times only (faster failure)
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True
    )
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "anthropic/claude-3.5-sonnet",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Call FAL AI any-llm endpoint for text generation.
        
        Follows FAL AI official documentation queue pattern:
        https://fal.ai/models/fal-ai/any-llm/api
        
        1. Submit request with arguments → get request_id
        2. Poll status until COMPLETED
        3. Extract output from response
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response dict with generated text in OpenAI-compatible format
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        # Extract prompt and system_prompt from messages
        system_prompt = None
        prompt = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                prompt = msg["content"]
        
        if not prompt:
            raise ValueError("No user prompt found in messages")
        
        # Build arguments object per FAL AI documentation
        # https://fal.ai/models/fal-ai/any-llm/api#schema
        arguments = {
            "prompt": prompt,
            "model": model,
            "priority": "latency",  # Use latency priority for faster responses
            "temperature": temperature
        }
        
        if system_prompt:
            arguments["system_prompt"] = system_prompt
        
        if max_tokens:
            arguments["max_tokens"] = max_tokens
        
        logger.info(f"📤 FAL AI Request: model={model}, prompt_len={len(prompt)}, temp={temperature}")
        logger.debug(f"Full arguments: {json.dumps(arguments, indent=2)}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # STEP 1: Submit to queue
                # Send arguments directly (NOT wrapped in {"input": ...})
                submit_response = await client.post(
                    self.queue_url,
                    headers=self.headers,
                    json=arguments  # ✅ Send directly per FAL AI docs
                )
                submit_response.raise_for_status()
                submit_data = submit_response.json()
                
                logger.debug(f"Submit response: {json.dumps(submit_data, indent=2)}")
                
                # Get request_id from response
                request_id = submit_data.get("request_id")
                if not request_id:
                    logger.error(f"❌ No request_id in response: {submit_data}")
                    raise Exception("FAL AI didn't return a request_id")
                
                logger.info(f"✅ Submitted: request_id={request_id}")
                
                # STEP 2: Poll status until COMPLETED or FAILED
                status_url = f"{self.queue_url}/requests/{request_id}/status"
                max_polls = 30  # 30 polls * 2 seconds = 60 seconds max wait
                
                for poll_attempt in range(max_polls):
                    await asyncio.sleep(2)  # Wait 2 seconds between polls
                    
                    status_response = await client.get(status_url, headers=self.headers)
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    
                    status = status_data.get("status")
                    
                    # Log progress
                    if poll_attempt % 5 == 0:
                        logger.info(f"⏳ Polling status... ({poll_attempt * 2}s elapsed, status: {status})")
                    
                    if status == "COMPLETED":
                        # STEP 3: Extract output
                        logger.info(f"✅ COMPLETED after {(poll_attempt + 1) * 2}s")
                        logger.debug(f"Full response:\n{json.dumps(status_data, indent=2)}")
                        
                        # FAL AI any-llm returns output in "data" object per their schema
                        output_text = None
                        
                        # Check data.output (primary location per FAL AI docs)
                        if "data" in status_data:
                            data = status_data["data"]
                            if isinstance(data, dict):
                                output_text = data.get("output")
                        
                        # Fallback: Check top-level output
                        if not output_text and "output" in status_data:
                            output_text = status_data.get("output")
                        
                        if output_text:
                            logger.info(f"✅ Got output: {len(output_text)} characters")
                            # Return in OpenAI-compatible format
                            return {
                                "choices": [
                                    {
                                        "message": {
                                            "content": output_text
                                        }
                                    }
                                ]
                            }
                        else:
                            # No output found - this is a problem
                            metrics = status_data.get("metrics", {})
                            inference_time = metrics.get("inference_time", 0)
                            
                            logger.error(f"❌ COMPLETED but no output found!")
                            logger.error(f"Request ID: {request_id}")
                            logger.error(f"Metrics: {metrics}")
                            logger.error(f"Full response:\n{json.dumps(status_data, indent=2)}")
                            
                            if inference_time < 0.1:
                                logger.error(f"⚠️  Inference time ({inference_time:.3f}s) is suspiciously fast!")
                                logger.error(f"⚠️  Model likely didn't execute. Check model name and API key permissions.")
                            
                            # Return fallback
                            return {
                                "choices": [
                                    {
                                        "message": {
                                            "content": "I'm experiencing technical difficulties with my AI processor. Please try again!"
                                        }
                                    }
                                ]
                            }
                    
                    elif status == "FAILED":
                        error = status_data.get("error", "Unknown error")
                        logger.error(f"❌ FAL AI job FAILED: {error}")
                        logger.error(f"Full error response:\n{json.dumps(status_data, indent=2)}")
                        raise Exception(f"FAL AI request failed: {error}")
                    
                    elif status in ["IN_QUEUE", "IN_PROGRESS"]:
                        # Still processing, continue polling
                        continue
                    else:
                        logger.warning(f"⚠️  Unknown status: {status}")
                
                # Timeout after max_polls
                logger.error(f"⏰ Timeout after {max_polls * 2}s. Request ID: {request_id}")
                return {
                    "choices": [
                        {
                            "message": {
                                "content": "That's taking longer than expected, Sami. Let me try again!"
                            }
                        }
                    ]
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
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

