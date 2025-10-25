"""One-time script to recreate Qdrant collection with proper indexes.

This script will:
1. Delete the existing zyana_memory collection (if exists)
2. Recreate it with proper payload indexes for user_id and type fields

WARNING: This will delete all existing vectors in the collection!

Usage:
    python backend/scripts/recreate_qdrant_collection.py
"""
import sys
import os

# Add backend directory to path for imports
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)

# For Render deployment, use absolute path
sys.path.insert(0, '/opt/render/project/src/backend')

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to recreate Qdrant collection."""
    try:
        logger.info("=" * 60)
        logger.info("Starting Qdrant collection recreation with indexes...")
        logger.info("=" * 60)
        
        # Import here to ensure proper path is set
        from clients.qdrant_client import qdrant_client
        
        # Recreate collection with indexes
        qdrant_client.recreate_collection_with_indexes()
        
        logger.info("=" * 60)
        logger.info("✅ Collection recreation complete!")
        logger.info("=" * 60)
        logger.info("The zyana_memory collection now has proper indexes for:")
        logger.info("  - user_id (KEYWORD)")
        logger.info("  - type (KEYWORD)")
        logger.info("")
        logger.info("You can now use memory search and RAG features without errors.")
        
        return 0
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Error recreating collection: {e}", exc_info=True)
        logger.error("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

