"""Voice Transcriber Service using faster-whisper for speech-to-text."""
import logging
import os
from typing import Optional
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_whisper_model = None


def get_whisper_model():
    """Get or initialize Whisper model (singleton pattern).
    
    Returns:
        WhisperModel instance
    """
    global _whisper_model
    
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            
            # Use "base" model (74MB) for good balance of speed and accuracy
            # Options: tiny, base, small, medium, large
            model_size = "base"
            
            logger.info(f"Loading Whisper model: {model_size}")
            _whisper_model = WhisperModel(
                model_size,
                device="cpu",  # Use "cuda" if GPU available
                compute_type="int8"  # Quantization for faster inference
            )
            logger.info("Whisper model loaded successfully")
            
        except ImportError:
            logger.warning("faster-whisper not installed - voice transcription disabled. Install with: pip install faster-whisper")
            _whisper_model = None
            return None
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}", exc_info=True)
            _whisper_model = None
            return None
    
    return _whisper_model


class VoiceTranscriberService:
    """Service for transcribing voice messages to text."""
    
    def __init__(self):
        """Initialize voice transcriber."""
        self.model = None
    
    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> Optional[str]:
        """Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to audio file
            language: Optional language code (e.g., 'en', 'ur')
            
        Returns:
            Transcribed text or None on failure
        """
        try:
            # Get model (lazy load)
            if self.model is None:
                self.model = get_whisper_model()
            
            # Check if model loaded successfully
            if self.model is None:
                logger.warning("Whisper model not available - voice transcription disabled")
                return None
            
            logger.info(f"Transcribing audio file: {audio_file_path}")
            
            # Transcribe
            segments, info = self.model.transcribe(
                audio_file_path,
                language=language,
                beam_size=5,
                vad_filter=True  # Voice activity detection
            )
            
            # Combine segments
            text = " ".join([segment.text.strip() for segment in segments])
            
            logger.info(f"Transcription complete: {len(text)} chars, detected language: {info.language}")
            
            return text.strip() if text else None
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}", exc_info=True)
            return None
    
    async def transcribe_telegram_voice(
        self,
        file_content: bytes,
        language: Optional[str] = None
    ) -> Optional[str]:
        """Transcribe Telegram voice message.
        
        Args:
            file_content: Audio file bytes
            language: Optional language code
            
        Returns:
            Transcribed text or None on failure
        """
        temp_file = None
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp:
                temp.write(file_content)
                temp_file = temp.name
            
            # Transcribe
            text = await self.transcribe_audio(temp_file, language)
            
            return text
            
        except Exception as e:
            logger.error(f"Error transcribing Telegram voice: {e}", exc_info=True)
            return None
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up temp file: {cleanup_error}")
    
    def convert_ogg_to_wav(self, ogg_path: str) -> Optional[str]:
        """Convert OGG file to WAV format (if needed).
        
        Note: faster-whisper can handle OGG directly, but this is here
        as a utility in case conversion is needed.
        
        Args:
            ogg_path: Path to OGG file
            
        Returns:
            Path to WAV file or None on failure
        """
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_ogg(ogg_path)
            
            wav_path = ogg_path.replace(".ogg", ".wav")
            audio.export(wav_path, format="wav")
            
            return wav_path
            
        except ImportError:
            logger.warning("pydub not installed. Install with: pip install pydub")
            return None
        except Exception as e:
            logger.error(f"Error converting OGG to WAV: {e}", exc_info=True)
            return None


# Global instance
voice_transcriber = VoiceTranscriberService()

