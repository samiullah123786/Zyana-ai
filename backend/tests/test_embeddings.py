"""Tests for embeddings service."""
import pytest
from services.embeddings import embedding_service


class TestEmbeddingService:
    """Test pluggable embedding service."""
    
    @pytest.mark.asyncio
    async def test_embed_single(self):
        """Test single text embedding."""
        text = "This is a test message"
        
        embedding = await embedding_service.embed_single(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_get_embedding_multiple(self):
        """Test batch embedding."""
        texts = [
            "First message",
            "Second message",
            "Third message"
        ]
        
        embeddings = await embedding_service.get_embedding(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(isinstance(e, list) for e in embeddings)
    
    def test_chunk_text(self):
        """Test text chunking."""
        # Create a long text
        text = " ".join(["word"] * 1000)
        
        chunks = embedding_service.chunk_text(text, max_tokens=100, overlap=10)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 1
        assert all('text' in chunk for chunk in chunks)
        assert all('chunk_index' in chunk for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_embed_with_chunking_short(self):
        """Test embedding with chunking for short text."""
        text = "Short message"
        
        results = await embedding_service.embed_with_chunking(text, max_tokens=100)
        
        assert isinstance(results, list)
        assert len(results) == 1  # Should not chunk
        assert 'embedding' in results[0]
        assert 'metadata' in results[0]
    
    @pytest.mark.asyncio
    async def test_embed_with_chunking_long(self):
        """Test embedding with chunking for long text."""
        text = " ".join(["word"] * 1000)  # Long text
        
        results = await embedding_service.embed_with_chunking(text, max_tokens=100)
        
        assert isinstance(results, list)
        assert len(results) > 1  # Should chunk
        assert all('embedding' in r for r in results)
        assert all('chunk_text' in r for r in results)

