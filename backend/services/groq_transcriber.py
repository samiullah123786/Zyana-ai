"""Groq Whisper Transcription Service - Cloud-based speech-to-text.

This module provides high-quality audio transcription using Groq's Whisper API.
Supports chunking for large files and automatic retries for reliability.
"""
import logging
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
import mimetypes

from config import settings
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)

# Groq API configuration
GROQ_API_BASE = "https://api.groq.com/openai/v1"
GROQ_TRANSCRIBE_ENDPOINT = f"{GROQ_API_BASE}/audio/transcriptions"
MAX_FILE_SIZE_MB = 25  # Groq's limit per request
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class GroqTranscriptionError(Exception):
    """Custom exception for Groq transcription failures."""
    pass


class GroqTranscriberService:
    """Service for transcribing audio using Groq Whisper API."""
    
    def __init__(self):
        """Initialize Groq transcriber with API key from config."""
        self.api_key = settings.groq_api_key
        self.model = settings.groq_transcribe_model
        self.max_chunk_seconds = settings.max_chunk_seconds
        
        if not self.api_key:
            logger.error("GROQ_API_KEY not configured!")
            raise ValueError("GROQ_API_KEY is required for transcription")
        
        logger.info(f"✅ Groq Transcriber initialized with model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        reraise=True
    )
    async def _call_groq_api(
        self,
        file_path: str,
        language: Optional[str] = None,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Call Groq transcription API with retry logic.
        
        Args:
            file_path: Path to audio file
            language: Optional language code (e.g., 'en', 'ur')
            temperature: Sampling temperature (0.0 = deterministic)
            
        Returns:
            Dict with transcription result
            
        Raises:
            GroqTranscriptionError: On permanent API failures
            httpx.HTTPStatusError: On transient 5xx errors (for retry)
        """
        try:
            # Prepare file for upload
            file_obj = open(file_path, "rb")
            file_name = Path(file_path).name
            
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "audio/ogg"  # Default for Telegram voice
            
            # Prepare form data
            form_data = {
                "model": self.model,
                "response_format": "verbose_json",  # Get detailed response
                "temperature": temperature,
            }
            
            if language:
                form_data["language"] = language
            
            # Prepare files
            files = {
                "file": (file_name, file_obj, mime_type)
            }
            
            logger.info(f"📤 Calling Groq API: {file_name} ({mime_type})")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    GROQ_TRANSCRIBE_ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    data=form_data,
                    files=files
                )
            
            # Close file after request
            file_obj.close()
            
            # Handle HTTP errors
            if response.status_code >= 500:
                # Transient server error - retry
                logger.warning(f"⚠️ Groq API 5xx error: {response.status_code}")
                response.raise_for_status()
            elif response.status_code >= 400:
                # Permanent client error - don't retry
                error_detail = response.text
                logger.error(f"❌ Groq API 4xx error: {response.status_code} - {error_detail}")
                raise GroqTranscriptionError(
                    f"Groq API error {response.status_code}: {error_detail}"
                )
            
            # Parse successful response
            result = response.json()
            
            logger.info(f"✅ Groq transcription successful: {len(result.get('text', ''))} chars")
            
            return result
            
        except httpx.HTTPStatusError as e:
            # Re-raise for retry mechanism
            logger.warning(f"HTTP error (will retry): {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Groq API call failed: {e}", exc_info=True)
            raise GroqTranscriptionError(f"Groq API call failed: {str(e)}")
    
    async def transcribe_with_groq(
        self,
        file_path: str,
        language: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio file using Groq Whisper API.
        
        Args:
            file_path: Path to audio file (WAV, FLAC, MP3, OGG, etc.)
            language: Optional language code (e.g., 'en', 'ur', 'auto')
            model: Optional model override (default from config)
            
        Returns:
            Dict with keys:
                - text: Full transcription text
                - language: Detected/specified language
                - duration: Audio duration in seconds
                - confidence: Confidence score (if available)
                - model_used: Which model was used
                
        Raises:
            GroqTranscriptionError: On transcription failure
        """
        try:
            # Use provided model or default
            original_model = self.model
            if model:
                self.model = model
            
            # Check file size
            file_size = Path(file_path).stat().st_size
            logger.info(f"🎙️ Transcribing: {Path(file_path).name} ({file_size / 1024:.1f} KB)")
            
            if file_size > MAX_FILE_SIZE_BYTES:
                logger.warning(f"⚠️ File too large ({file_size / 1024 / 1024:.1f} MB), chunking not yet implemented")
                # TODO: Implement chunking logic
                raise GroqTranscriptionError(
                    f"File too large ({file_size / 1024 / 1024:.1f} MB). Max: {MAX_FILE_SIZE_MB} MB"
                )
            
            # Call Groq API
            result = await self._call_groq_api(file_path, language=language)
            
            # Parse response
            transcription = {
                "text": result.get("text", "").strip(),
                "language": result.get("language", "unknown"),
                "duration": result.get("duration", 0.0),
                "confidence": None,  # Groq doesn't return confidence in verbose_json
                "model_used": self.model,
                "segments": result.get("segments", []),  # Detailed segments with timestamps
            }
            
            # Restore original model
            self.model = original_model
            
            return transcription
            
        except GroqTranscriptionError:
            raise
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}", exc_info=True)
            raise GroqTranscriptionError(f"Transcription failed: {str(e)}")
    
    async def transcribe_telegram_voice(
        self,
        file_path: str,
        language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Transcribe Telegram voice message (convenience method).
        
        Args:
            file_path: Path to downloaded Telegram voice file (.ogg)
            language: Optional language hint
            
        Returns:
            Transcription dict or None on failure
        """
        try:
            return await self.transcribe_with_groq(file_path, language=language)
        except GroqTranscriptionError as e:
            logger.error(f"❌ Telegram voice transcription failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            return None
    
    async def transcribe_chunks(
        self,
        chunk_paths: List[str],
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe multiple audio chunks and concatenate results.
        
        Args:
            chunk_paths: List of paths to audio chunks (in order)
            language: Optional language code
            
        Returns:
            Combined transcription dict
        """
        all_segments = []
        all_texts = []
        total_duration = 0.0
        detected_language = language
        
        logger.info(f"📚 Transcribing {len(chunk_paths)} chunks...")
        
        for i, chunk_path in enumerate(chunk_paths):
            try:
                result = await self.transcribe_with_groq(chunk_path, language=language)
                
                # Accumulate results
                all_texts.append(result["text"])
                all_segments.extend(result.get("segments", []))
                total_duration += result.get("duration", 0.0)
                
                if not detected_language:
                    detected_language = result.get("language")
                
                logger.info(f"✅ Chunk {i+1}/{len(chunk_paths)} done")
                
            except GroqTranscriptionError as e:
                logger.error(f"❌ Chunk {i+1} failed: {e}")
                all_texts.append(f"[Chunk {i+1} transcription failed]")
        
        # Combine results
        combined_text = " ".join(all_texts).strip()
        
        return {
            "text": combined_text,
            "language": detected_language or "unknown",
            "duration": total_duration,
            "confidence": None,
            "model_used": self.model,
            "segments": all_segments,
            "chunks_count": len(chunk_paths)
        }


# Global instance
groq_transcriber = GroqTranscriberService()

