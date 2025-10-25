"""Unit tests for Groq Transcriber Service."""
import pytest
import httpx
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import json

from services.groq_transcriber import (
    GroqTranscriberService,
    GroqTranscriptionError,
    GROQ_TRANSCRIBE_ENDPOINT
)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("services.groq_transcriber.settings") as mock:
        mock.groq_api_key = "test_groq_api_key"
        mock.groq_transcribe_model = "whisper-large-v3-turbo"
        mock.max_chunk_seconds = 180
        yield mock


@pytest.fixture
def transcriber(mock_settings):
    """Create transcriber instance with mocked settings."""
    return GroqTranscriberService()


@pytest.fixture
def sample_audio_file(tmp_path):
    """Create a sample audio file for testing."""
    audio_file = tmp_path / "test_voice.ogg"
    audio_file.write_bytes(b"fake_audio_data")
    return str(audio_file)


class TestGroqTranscriberInit:
    """Test GroqTranscriberService initialization."""
    
    def test_init_success(self, mock_settings):
        """Test successful initialization with API key."""
        transcriber = GroqTranscriberService()
        assert transcriber.api_key == "test_groq_api_key"
        assert transcriber.model == "whisper-large-v3-turbo"
        assert transcriber.max_chunk_seconds == 180
    
    def test_init_missing_api_key(self, mock_settings):
        """Test initialization fails without API key."""
        mock_settings.groq_api_key = None
        with pytest.raises(ValueError, match="GROQ_API_KEY is required"):
            GroqTranscriberService()


class TestGroqAPICall:
    """Test Groq API interaction."""
    
    @pytest.mark.asyncio
    async def test_call_groq_api_success(self, transcriber, sample_audio_file):
        """Test successful API call."""
        mock_response = {
            "text": "This is a test transcription",
            "language": "en",
            "duration": 5.2,
            "segments": [
                {"start": 0.0, "end": 5.2, "text": "This is a test transcription"}
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=Mock(
                status_code=200,
                json=Mock(return_value=mock_response)
            ))
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            result = await transcriber._call_groq_api(sample_audio_file)
            
            assert result["text"] == "This is a test transcription"
            assert result["language"] == "en"
            assert result["duration"] == 5.2
            
            # Verify API call parameters
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args.kwargs["data"]["model"] == "whisper-large-v3-turbo"
            assert "Authorization" in call_args.kwargs["headers"]
    
    @pytest.mark.asyncio
    async def test_call_groq_api_with_language(self, transcriber, sample_audio_file):
        """Test API call with language parameter."""
        mock_response = {"text": "Test", "language": "ur"}
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=Mock(
                status_code=200,
                json=Mock(return_value=mock_response)
            ))
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            await transcriber._call_groq_api(sample_audio_file, language="ur")
            
            call_args = mock_post.call_args
            assert call_args.kwargs["data"]["language"] == "ur"
    
    @pytest.mark.asyncio
    async def test_call_groq_api_4xx_error(self, transcriber, sample_audio_file):
        """Test API returns 4xx client error (permanent, don't retry)."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock(
                status_code=400,
                text="Bad Request: Invalid audio format"
            )
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            with pytest.raises(GroqTranscriptionError, match="Groq API error 400"):
                await transcriber._call_groq_api(sample_audio_file)
    
    @pytest.mark.asyncio
    async def test_call_groq_api_5xx_error(self, transcriber, sample_audio_file):
        """Test API returns 5xx server error (transient, retry)."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock(status_code=503)
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Service Unavailable", request=Mock(), response=mock_response
            )
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            with pytest.raises(httpx.HTTPStatusError):
                await transcriber._call_groq_api(sample_audio_file)


class TestTranscribeWithGroq:
    """Test main transcription method."""
    
    @pytest.mark.asyncio
    async def test_transcribe_success(self, transcriber, sample_audio_file):
        """Test successful transcription."""
        mock_api_response = {
            "text": "Hello world from Groq",
            "language": "en",
            "duration": 3.5,
            "segments": []
        }
        
        with patch.object(transcriber, "_call_groq_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_api_response
            
            result = await transcriber.transcribe_with_groq(sample_audio_file)
            
            assert result["text"] == "Hello world from Groq"
            assert result["language"] == "en"
            assert result["duration"] == 3.5
            assert result["model_used"] == "whisper-large-v3-turbo"
            assert result["confidence"] is None  # Groq doesn't provide confidence
    
    @pytest.mark.asyncio
    async def test_transcribe_with_custom_model(self, transcriber, sample_audio_file):
        """Test transcription with custom model."""
        mock_api_response = {"text": "Test", "language": "en", "duration": 1.0}
        
        with patch.object(transcriber, "_call_groq_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_api_response
            
            result = await transcriber.transcribe_with_groq(
                sample_audio_file,
                model="whisper-large-v3"
            )
            
            # Should use custom model for this call
            assert mock_call.call_args[0][0] == sample_audio_file
            # Model should be restored after
            assert transcriber.model == "whisper-large-v3-turbo"
    
    @pytest.mark.asyncio
    async def test_transcribe_file_too_large(self, transcriber, tmp_path):
        """Test transcription fails for files > 25MB."""
        # Create a fake large file
        large_file = tmp_path / "large_audio.ogg"
        large_file.write_bytes(b"x" * (26 * 1024 * 1024))  # 26 MB
        
        with pytest.raises(GroqTranscriptionError, match="File too large"):
            await transcriber.transcribe_with_groq(str(large_file))


class TestTelegramVoiceTranscription:
    """Test Telegram-specific transcription."""
    
    @pytest.mark.asyncio
    async def test_transcribe_telegram_voice_success(self, transcriber, sample_audio_file):
        """Test successful Telegram voice transcription."""
        mock_result = {
            "text": "Telegram voice test",
            "language": "en",
            "duration": 2.0,
            "model_used": "whisper-large-v3-turbo"
        }
        
        with patch.object(transcriber, "transcribe_with_groq", new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.return_value = mock_result
            
            result = await transcriber.transcribe_telegram_voice(sample_audio_file)
            
            assert result == mock_result
            mock_transcribe.assert_called_once_with(sample_audio_file, language=None)
    
    @pytest.mark.asyncio
    async def test_transcribe_telegram_voice_failure(self, transcriber, sample_audio_file):
        """Test Telegram voice transcription handles failures gracefully."""
        with patch.object(transcriber, "transcribe_with_groq", new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.side_effect = GroqTranscriptionError("API error")
            
            result = await transcriber.transcribe_telegram_voice(sample_audio_file)
            
            assert result is None  # Returns None on failure


class TestChunkTranscription:
    """Test transcription of multiple audio chunks."""
    
    @pytest.mark.asyncio
    async def test_transcribe_chunks_success(self, transcriber, tmp_path):
        """Test successful transcription of multiple chunks."""
        # Create 3 fake chunk files
        chunks = []
        for i in range(3):
            chunk = tmp_path / f"chunk_{i}.ogg"
            chunk.write_bytes(b"chunk_data")
            chunks.append(str(chunk))
        
        # Mock transcription results for each chunk
        mock_results = [
            {"text": "First chunk", "language": "en", "duration": 3.0, "segments": []},
            {"text": "Second chunk", "language": "en", "duration": 3.0, "segments": []},
            {"text": "Third chunk", "language": "en", "duration": 3.0, "segments": []},
        ]
        
        with patch.object(transcriber, "transcribe_with_groq", new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.side_effect = mock_results
            
            result = await transcriber.transcribe_chunks(chunks)
            
            assert result["text"] == "First chunk Second chunk Third chunk"
            assert result["language"] == "en"
            assert result["duration"] == 9.0
            assert result["chunks_count"] == 3
            assert mock_transcribe.call_count == 3
    
    @pytest.mark.asyncio
    async def test_transcribe_chunks_partial_failure(self, transcriber, tmp_path):
        """Test chunk transcription continues even if one chunk fails."""
        chunks = [str(tmp_path / f"chunk_{i}.ogg") for i in range(3)]
        for chunk in chunks:
            Path(chunk).write_bytes(b"data")
        
        # Second chunk fails
        mock_results = [
            {"text": "First", "language": "en", "duration": 1.0, "segments": []},
            GroqTranscriptionError("Chunk 2 failed"),
            {"text": "Third", "language": "en", "duration": 1.0, "segments": []},
        ]
        
        with patch.object(transcriber, "transcribe_with_groq", new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.side_effect = mock_results
            
            result = await transcriber.transcribe_chunks(chunks)
            
            assert "First" in result["text"]
            assert "[Chunk 2 transcription failed]" in result["text"]
            assert "Third" in result["text"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

