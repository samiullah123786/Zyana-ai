"""
Claude via FAL AI - Access Claude Sonnet 3.5 through FAL AI's any-llm endpoint
=================================================================================
Uses FAL AI's any-llm method to access Claude without needing Anthropic API key.
"""
import asyncio
import httpx
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Claude AI client through FAL AI any-llm endpoint."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude client via FAL AI.
        
        Args:
            api_key: FAL API key (defaults to settings)
        """
        # Use FAL AI API key
        self.api_key = api_key or settings.fal_api_key
        self.base_url = "https://queue.fal.run"
        self.headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            logger.info("✅ Claude client (via FAL AI) initialized")
        else:
            logger.warning("❌ FAL API key not found")
    
    async def chat_simple(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "anthropic/claude-3.5-sonnet",
        temperature: float = 0.0,
        max_tokens: int = 1024
    ) -> str:
        """Send chat completion request to Claude via FAL AI.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Claude model via FAL AI (anthropic/claude-3.5-sonnet)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If client not enabled or API error
        """
        if not self.enabled:
            raise Exception("Claude client not enabled - FAL API key missing")
        
        try:
            # Build payload for FAL AI any-llm
            payload = {
                "prompt": prompt,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "priority": "latency"
            }
            
            if system_prompt:
                payload["system_prompt"] = system_prompt
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Submit request
                response = await client.post(
                    f"{self.base_url}/fal-ai/any-llm",
                    headers=self.headers,
                    json={"input": payload}
                )
                response.raise_for_status()
                data = response.json()
                
                # Handle queue response (poll for result)
                if data.get("status") == "IN_QUEUE":
                    status_url = data.get("status_url")
                    if not status_url:
                        raise Exception("No status URL in queue response")
                    
                    # Poll for result (max 10 seconds)
                    for _ in range(5):
                        await asyncio.sleep(2)
                        status_response = await client.get(status_url, headers=self.headers)
                        status_response.raise_for_status()
                        status_data = status_response.json()
                        
                        if status_data.get("status") == "COMPLETED":
                            if "output" in status_data:
                                return status_data["output"]
                        elif status_data.get("status") == "FAILED":
                            raise Exception(f"Claude job failed: {status_data.get('error')}")
                    
                    raise Exception("Claude request timed out")
                
                # Direct response
                elif "output" in data:
                    return data["output"]
                else:
                    raise Exception("Unexpected response format")
            
        except Exception as e:
            logger.error(f"Claude (via FAL AI) error: {e}")
            raise


# Global client instance
claude_client = ClaudeClient()

