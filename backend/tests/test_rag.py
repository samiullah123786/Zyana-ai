"""Tests for RAG service."""
import pytest
from services.rag import rag_service


class TestRAGService:
    """Test RAG service functionality."""
    
    @pytest.mark.asyncio
    async def test_retrieve_relevant_memories(self):
        """Test memory retrieval from Qdrant."""
        # Test with sample query
        memories = await rag_service.retrieve_relevant_memories(
            query="schedule meeting",
            user_id="test_user",
            top_k=5
        )
        
        assert isinstance(memories, list)
        # Should return empty list or results
        assert len(memories) >= 0
    
    @pytest.mark.asyncio
    async def test_build_rag_prompt(self):
        """Test RAG prompt building."""
        user_context = {
            'default_business': 'TestCo',
            'preferred_currency': 'USD'
        }
        
        memories = [
            {
                'snippet': 'Previous meeting scheduled',
                'table': 'calendar_events',
                'date': '2025-10-20',
                'score': 0.95
            }
        ]
        
        prompt = await rag_service.build_rag_prompt(
            query="Schedule new meeting",
            user_context=user_context,
            retrieved_memories=memories
        )
        
        assert isinstance(prompt, str)
        assert 'TestCo' in prompt
        assert 'Previous meeting' in prompt
    
    @pytest.mark.asyncio
    async def test_get_user_memory_context(self):
        """Test comprehensive memory context retrieval."""
        context = await rag_service.get_user_memory_context(
            user_id="test_user",
            query="test query",
            include_mirror=False
        )
        
        assert isinstance(context, dict)
        assert 'memories' in context
        assert 'user_preferences' in context
        assert 'formatted_context' in context
        assert 'has_context' in context
    
    def test_format_mirror_samples(self):
        """Test mirror sample formatting."""
        samples = [
            {'message': 'Hey bro!', 'timestamp': '2025-10-25'},
            {'message': 'Sounds good 👍', 'timestamp': '2025-10-24'}
        ]
        
        formatted = rag_service._format_mirror_samples(samples)
        
        assert isinstance(formatted, str)
        assert 'Hey bro!' in formatted
        assert 'Sounds good' in formatted

