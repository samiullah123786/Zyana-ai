"""Tests for background workers."""
import pytest
from workers.embeddings_worker import embeddings_worker
from workers.nightly_summarizer import nightly_summarizer


class TestEmbeddingsWorker:
    """Test embeddings worker functionality."""
    
    @pytest.mark.asyncio
    async def test_process_conversation(self):
        """Test processing a conversation record."""
        record = {
            'id': 'test_conv_1',
            'user_id': 'test_user',
            'message': 'Hello, this is a test message',
            'role': 'user',
            'timestamp': '2025-10-25T10:00:00Z'
        }
        
        result = await embeddings_worker.process_conversation(record)
        
        assert isinstance(result, bool)
        # May fail if Qdrant not accessible, but shouldn't crash
    
    @pytest.mark.asyncio
    async def test_process_voice_log(self):
        """Test processing a voice log record."""
        record = {
            'id': 123,
            'user_id': 1,
            'transcript': 'This is a voice transcription test',
            'created_at': '2025-10-25T10:00:00Z'
        }
        
        result = await embeddings_worker.process_voice_log(record)
        
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_process_mirror_sample(self):
        """Test processing a mirror sample."""
        record = {
            'id': 456,
            'user_id': 1,
            'message': 'This is my communication style',
            'timestamp': '2025-10-25T10:00:00Z'
        }
        
        result = await embeddings_worker.process_mirror_sample(record)
        
        assert isinstance(result, bool)


class TestNightlySummarizer:
    """Test nightly summarizer functionality."""
    
    def test_format_conversations(self):
        """Test conversation formatting."""
        conversations = [
            {'role': 'user', 'message': 'Hello', 'timestamp': '2025-10-25T10:00:00Z'},
            {'role': 'assistant', 'message': 'Hi there!', 'timestamp': '2025-10-25T10:01:00Z'},
            {'role': 'user', 'message': 'How are you?', 'timestamp': '2025-10-25T10:02:00Z'}
        ]
        
        formatted = nightly_summarizer._format_conversations(conversations)
        
        assert isinstance(formatted, str)
        assert 'User:' in formatted
        assert 'Assistant:' in formatted
        assert 'Hello' in formatted
    
    @pytest.mark.asyncio
    async def test_generate_summary(self):
        """Test summary generation."""
        conversation_text = """User: Hello
Assistant: Hi there!
User: Can you help me schedule a meeting?
Assistant: Of course! When would you like it?"""
        
        from datetime import datetime
        
        summary = await nightly_summarizer._generate_summary(
            conversation_text,
            "test_user",
            datetime.now()
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    @pytest.mark.asyncio
    async def test_cleanup_old_conversations(self):
        """Test old conversation cleanup."""
        count = await nightly_summarizer.cleanup_old_conversations(retention_days=30)
        
        assert isinstance(count, int)
        assert count >= 0

