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
                        logger.debug(f"Full status data: {status_data}")
                        
                        # STEP 3: Extract output from COMPLETED status response
                        # FAL AI returns output in nested structure: response.output.choices[0].message.content
                        output = None
                        
                        # FAL AI structure: response.output.choices[0].message.content
                        if "response" in status_data:
                            response = status_data["response"]
                            if isinstance(response, dict) and "output" in response:
                                output_obj = response["output"]
                                if isinstance(output_obj, dict) and "choices" in output_obj:
                                    choices = output_obj["choices"]
                                    if isinstance(choices, list) and len(choices) > 0:
                                        choice = choices[0]
                                        if isinstance(choice, dict) and "message" in choice:
                                            message = choice["message"]
                                            if isinstance(message, dict) and "content" in message:
                                                output = message["content"]
                                                logger.info(f"✅ Extracted output from response.output.choices[0].message.content")
                        
                        # Fallback 1: Direct data.output structure
                        if not output and "data" in status_data and isinstance(status_data["data"], dict):
                            output = status_data["data"].get("output")
                            if output:
                                logger.info(f"✅ Extracted output from data.output")
                        
                        # Fallback 2: Top-level output
                        if not output and "output" in status_data:
                            output = status_data.get("output")
                            if output:
                                logger.info(f"✅ Extracted output from top-level output")
                        
                        # Fallback 3: Result field
                        if not output and "result" in status_data:
                            result = status_data.get("result")
                            if isinstance(result, dict):
                                output = result.get("output")
                            elif isinstance(result, str):
                                output = result
                            if output:
                                logger.info(f"✅ Extracted output from result")
                        
                        # Special case: Try response_url with POST (some FAL endpoints require this)
                        if not output and "response_url" in status_data:
                            logger.info(f"📥 Trying response_url with POST: {status_data['response_url']}/result")
                            try:
                                # Try POST to /result endpoint
                                result_response = await client.post(
                                    f"{status_data['response_url']}/result",
                                    headers=self.headers,
                                    json={}  # Empty body for result fetch
                                )
                                result_response.raise_for_status()
                                result_data = result_response.json()
                                
                                logger.debug(f"Result from POST: {result_data}")
                                
                                # Extract output
                                if "data" in result_data and isinstance(result_data["data"], dict):
                                    output = result_data["data"].get("output")
                                elif "output" in result_data:
                                    output = result_data.get("output")
                                    
                            except httpx.HTTPStatusError as e:
                                if e.response.status_code == 422:
                                    logger.warning(f"422 on result fetch - output might be in logs field")
                                else:
                                    logger.warning(f"HTTP {e.response.status_code} fetching result: {e.response.text[:200]}")
                            except Exception as e:
                                logger.warning(f"Error fetching from response_url: {e}")
                        
                        # Last resort: Check if output is in logs field (some models put it there)
                        if not output and "logs" in status_data and status_data["logs"]:
                            logger.info("Checking logs field for output...")
                            logs = status_data["logs"]
                            if isinstance(logs, list) and len(logs) > 0:
                                # Get last log entry which might be the output
                                last_log = logs[-1]
                                if isinstance(last_log, dict) and "message" in last_log:
                                    output = last_log["message"]
                        
                        if output:
                            logger.info(f"✅ Got output: {len(output)} chars")
                            print(f"✅ FAL AI SUCCESS: Got {len(output)} chars of output")  # Emergency print
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
                            # No output found anywhere - this might be a FAL API issue
                            # CRITICAL: Force logging with print() for visibility
                            print("=" * 100)
                            print("🔥 CRITICAL ERROR: FAL AI COMPLETED BUT NO OUTPUT FOUND!")
                            print("=" * 100)
                            logger.error(f"❌ COMPLETED but NO OUTPUT found!")
                            print(f"Status keys: {list(status_data.keys())}")
                            logger.error(f"Status keys: {list(status_data.keys())}")
                            print(f"Request ID: {request_id}")
                            logger.error(f"Request ID: {request_id}")
                            print(f"Metrics: {status_data.get('metrics')}")
                            logger.error(f"Metrics: {status_data.get('metrics')}")
                            
                            # DUMP FULL JSON for debugging
                            print("\n🔍 FULL STATUS DATA JSON:")
                            print("=" * 100)
                            import json
                            try:
                                print(json.dumps(status_data, indent=2))
                            except:
                                print(str(status_data))
                            print("=" * 100)
                            logger.error(f"Full status_data: {status_data}")
                            
                            # Check if this is a model name issue
                            if status_data.get('metrics', {}).get('inference_time', 0) < 0.1:
                                print("⚠️  WARNING: Inference time < 0.1s suggests model might not be running correctly!")
                                print(f"⚠️  Current model: {self.model if hasattr(self, 'model') else 'unknown'}")
                                logger.error("Suspiciously fast inference time - possible model configuration issue")
                            
                            print("=" * 100)
                            
                            # Return a more descriptive fallback
                            return {
                                "choices": [
                                    {
                                        "message": {
                                            "content": "Hey Sami! 👋 I'm having a technical issue with my AI brain right now. The job completed but returned no text. This might be a temporary FAL AI service issue. Could you try again in a moment?"
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

