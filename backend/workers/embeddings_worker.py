"""Background worker for automatic embedding generation.

Listens for new records in:
- conversations
- voice_logs
- user_message_samples

And automatically generates embeddings and stores in Qdrant.
"""
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

from clients.qdrant_client import qdrant_client
from clients.supabase_client import supabase_client
from services.embeddings import embedding_service
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingsWorker:
    """Worker for auto-generating embeddings from new records."""
    
    def __init__(self):
        """Initialize embeddings worker."""
        self.collections = {
            'conversations': 'conversations',
            'voice_logs': 'zyana_memory',
            'user_message_samples': 'mirror_samples'
        }
        logger.info("✅ EmbeddingsWorker initialized")
    
    async def process_conversation(self, record: Dict[str, Any]) -> bool:
        """Process a conversation record and create embedding.
        
        Args:
            record: Conversation record from database
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conversation_id = record.get('id')
            user_id = record.get('user_id')
            message = record.get('message')
            role = record.get('role', 'user')
            timestamp = record.get('timestamp', datetime.now().isoformat())
            
            if not message:
                logger.warning(f"⚠️  No message in conversation {conversation_id}, skipping")
                return False
            
            # Generate embedding
            embedding = await embedding_service.embed_single(message)
            
            if not embedding:
                logger.error(f"❌ Failed to generate embedding for conversation {conversation_id}")
                return False
            
            # Store in Qdrant
            point_id = f"conv_{conversation_id}"
            
            await qdrant_client.add_memory(
                content=message,
                embedding=embedding,
                metadata={
                    'user_id': user_id,
                    'table': 'conversations',
                    'row_id': conversation_id,
                    'role': role,
                    'date': timestamp,
                    'snippet': message[:200]
                },
                point_id=point_id
            )
            
            logger.info(f"✅ Embedded conversation {conversation_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing conversation: {e}", exc_info=True)
            return False
    
    async def process_voice_log(self, record: Dict[str, Any]) -> bool:
        """Process a voice log record and create embedding.
        
        Args:
            record: Voice log record from database
            
        Returns:
            True if successful, False otherwise
        """
        try:
            log_id = record.get('id')
            user_id = record.get('user_id')
            transcript = record.get('transcript')
            timestamp = record.get('created_at', datetime.now().isoformat())
            
            if not transcript:
                logger.warning(f"⚠️  No transcript in voice log {log_id}, skipping")
                return False
            
            # Generate embedding
            embedding = await embedding_service.embed_single(transcript)
            
            if not embedding:
                logger.error(f"❌ Failed to generate embedding for voice log {log_id}")
                return False
            
            # Store in Qdrant
            point_id = f"voice_{log_id}"
            
            await qdrant_client.add_memory(
                content=transcript,
                embedding=embedding,
                metadata={
                    'user_id': str(user_id),
                    'table': 'voice_logs',
                    'row_id': log_id,
                    'date': timestamp,
                    'snippet': transcript[:200]
                },
                point_id=point_id
            )
            
            logger.info(f"✅ Embedded voice log {log_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing voice log: {e}", exc_info=True)
            return False
    
    async def process_mirror_sample(self, record: Dict[str, Any]) -> bool:
        """Process a mirror sample and create embedding.
        
        Args:
            record: Mirror sample record from database
            
        Returns:
            True if successful, False otherwise
        """
        try:
            sample_id = record.get('id')
            user_id = record.get('user_id')
            message = record.get('message')
            timestamp = record.get('timestamp', datetime.now().isoformat())
            
            if not message:
                logger.warning(f"⚠️  No message in mirror sample {sample_id}, skipping")
                return False
            
            # Generate embedding
            embedding = await embedding_service.embed_single(message)
            
            if not embedding:
                logger.error(f"❌ Failed to generate embedding for mirror sample {sample_id}")
                return False
            
            # Store in Qdrant mirror_samples collection
            point_id = f"mirror_{sample_id}"
            
            # Note: This requires mirror_samples collection in Qdrant
            # For now, store in main memory collection with mirror tag
            await qdrant_client.add_memory(
                content=message,
                embedding=embedding,
                metadata={
                    'user_id': str(user_id),
                    'table': 'mirror_samples',
                    'row_id': sample_id,
                    'date': timestamp,
                    'snippet': message[:200],
                    'type': 'mirror_sample'
                },
                point_id=point_id
            )
            
            logger.info(f"✅ Embedded mirror sample {sample_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing mirror sample: {e}", exc_info=True)
            return False
    
    async def process_pending_embeddings(self, limit: int = 100) -> Dict[str, int]:
        """Process all pending embeddings from recent records.
        
        Args:
            limit: Maximum records to process per table
            
        Returns:
            Dict with counts of processed records per table
        """
        results = {
            'conversations': 0,
            'voice_logs': 0,
            'mirror_samples': 0,
            'errors': 0
        }
        
        try:
            # Process recent conversations
            logger.info("📝 Processing recent conversations...")
            conv_result = supabase_client.admin.table("conversations").select(
                "*"
            ).order("timestamp", desc=True).limit(limit).execute()
            
            if conv_result.data:
                for record in conv_result.data:
                    success = await self.process_conversation(record)
                    if success:
                        results['conversations'] += 1
                    else:
                        results['errors'] += 1
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)
            
            # Process recent voice logs
            logger.info("🎤 Processing recent voice logs...")
            voice_result = supabase_client.admin.table("voice_logs").select(
                "*"
            ).order("created_at", desc=True).limit(limit).execute()
            
            if voice_result.data:
                for record in voice_result.data:
                    success = await self.process_voice_log(record)
                    if success:
                        results['voice_logs'] += 1
                    else:
                        results['errors'] += 1
                    
                    await asyncio.sleep(0.1)
            
            # Process recent mirror samples
            logger.info("✨ Processing recent mirror samples...")
            mirror_result = supabase_client.admin.table("user_message_samples").select(
                "*"
            ).order("timestamp", desc=True).limit(limit).execute()
            
            if mirror_result.data:
                for record in mirror_result.data:
                    success = await self.process_mirror_sample(record)
                    if success:
                        results['mirror_samples'] += 1
                    else:
                        results['errors'] += 1
                    
                    await asyncio.sleep(0.1)
            
            logger.info(
                f"✅ Embeddings worker completed: "
                f"{results['conversations']} conversations, "
                f"{results['voice_logs']} voice logs, "
                f"{results['mirror_samples']} mirror samples, "
                f"{results['errors']} errors"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in embeddings worker: {e}", exc_info=True)
            results['errors'] += 1
            return results


# Global instance
embeddings_worker = EmbeddingsWorker()


async def run_embeddings_worker():
    """Run the embeddings worker job."""
    logger.info("🚀 Starting embeddings worker...")
    results = await embeddings_worker.process_pending_embeddings(limit=50)
    logger.info(f"✅ Embeddings worker finished: {results}")
    return results

