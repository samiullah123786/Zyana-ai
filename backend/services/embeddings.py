"""OpenAI embedding service with automatic retry and chunking support.

Features:
- OpenAI text-embedding-3-small (fast, reliable)
- Automatic retry with exponential backoff
- Text chunking for long documents
- Token-aware processing
"""
import logging
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """OpenAI-powered embedding service with retry logic and chunking."""
    
    def __init__(self):
        """Initialize embedding service with OpenAI."""
        self.provider = "openai"  # OpenAI is now the only provider
        self.model = settings.embedding_model  # Default: text-embedding-3-small
        logger.info(f"✅ EmbeddingService initialized with OpenAI, model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def get_embedding(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using OpenAI.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each 1536 dimensions for text-embedding-3-small)
        """
        if not texts:
            return []
        
        try:
            return await self._get_openai_embeddings(texts)
        except Exception as e:
            logger.error(f"❌ Error generating OpenAI embeddings: {e}", exc_info=True)
            raise
    
    async def _get_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings from OpenAI.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        from clients.openai_client import openai_client
        
        try:
            embeddings = await openai_client.embed(texts, model=self.model)
            logger.debug(f"✅ Generated {len(embeddings)} OpenAI embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"❌ OpenAI embedding error: {e}")
            raise
    
    
    def chunk_text(
        self,
        text: str,
        max_tokens: int = 512,
        overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """Split text into chunks for embedding.
        
        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk
            overlap: Token overlap between chunks
            
        Returns:
            List of chunk dicts with {text, chunk_index, start_char, end_char}
        """
        # Simple word-based chunking (approximation of tokens)
        # For production, use tiktoken for accurate token counting
        words = text.split()
        words_per_chunk = max_tokens  # Approximate: 1 token ≈ 1 word
        overlap_words = overlap
        
        chunks = []
        start_idx = 0
        chunk_index = 0
        
        while start_idx < len(words):
            # Get chunk words
            end_idx = min(start_idx + words_per_chunk, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)
            
            # Calculate character positions (approximate)
            start_char = len(' '.join(words[:start_idx]))
            end_char = start_char + len(chunk_text)
            
            chunks.append({
                'text': chunk_text,
                'chunk_index': chunk_index,
                'start_char': start_char,
                'end_char': end_char,
                'word_count': len(chunk_words)
            })
            
            # Move to next chunk with overlap
            start_idx = end_idx - overlap_words if end_idx < len(words) else end_idx
            chunk_index += 1
        
        logger.debug(f"📄 Chunked text into {len(chunks)} chunks")
        return chunks
    
    async def embed_with_chunking(
        self,
        text: str,
        max_tokens: int = 800
    ) -> List[Dict[str, Any]]:
        """Embed text with automatic chunking if needed.
        
        Args:
            text: Text to embed
            max_tokens: Maximum tokens before chunking
            
        Returns:
            List of dicts with {chunk_text, embedding, metadata}
        """
        # Simple token estimation (1 token ≈ 0.75 words)
        estimated_tokens = len(text.split()) * 0.75
        
        if estimated_tokens <= max_tokens:
            # Small enough, embed directly
            embeddings = await self.get_embedding([text])
            return [{
                'chunk_text': text,
                'embedding': embeddings[0],
                'metadata': {
                    'chunk_index': 0,
                    'total_chunks': 1,
                    'start_char': 0,
                    'end_char': len(text)
                }
            }]
        else:
            # Too large, chunk it
            logger.info(f"📄 Text too large ({estimated_tokens:.0f} tokens), chunking...")
            chunks = self.chunk_text(text, max_tokens=512, overlap=50)
            
            # Embed all chunks
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = await self.get_embedding(chunk_texts)
            
            # Combine chunks with embeddings
            results = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                results.append({
                    'chunk_text': chunk['text'],
                    'embedding': embedding,
                    'metadata': {
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'start_char': chunk['start_char'],
                        'end_char': chunk['end_char'],
                        'word_count': chunk['word_count']
                    }
                })
            
            logger.info(f"✅ Embedded {len(results)} chunks")
            return results
    
    async def embed_single(self, text: str) -> List[float]:
        """Embed a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        embeddings = await self.get_embedding([text])
        return embeddings[0] if embeddings else []


# Global instance
embedding_service = EmbeddingService()

