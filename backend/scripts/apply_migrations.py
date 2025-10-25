"""Script to apply database migrations to Supabase."""
import sys
import logging
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from clients.supabase_client import supabase_client
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_migrations():
    """Apply SQL migrations to Supabase."""
    logger.info("📊 Applying database migrations to Supabase...")
    
    # Get all migration files
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        logger.error(f"No migration files found in: {migrations_dir}")
        return False
    
    logger.info(f"Found {len(migration_files)} migration(s)")
    
    try:
        # Execute SQL using Supabase RPC or direct connection
        # Note: Supabase Python client doesn't support raw SQL execution
        # We need to use the SQL Editor in Supabase dashboard or use psycopg2
        
        logger.info("⚠️  Please apply migrations manually via Supabase SQL Editor:")
        logger.info(f"   1. Go to: {settings.supabase_url}/project/_/sql")
        logger.info("   2. Copy and run each migration in order:")
        logger.info("")
        
        for i, migration_file in enumerate(migration_files, 1):
            logger.info(f"   {i}. {migration_file.name}")
        
        logger.info("")
        logger.info("Alternatively, use psql:")
        for migration_file in migration_files:
            logger.info(f"   psql $POSTGRES_CONN < backend/migrations/{migration_file.name}")
        
        logger.info("")
        logger.info("📝 Latest migration (004): Adds Google OAuth credentials storage")
        logger.info("   - Adds google_credentials column to users table")
        logger.info("   - Adds google_calendar_connected flag")
        logger.info("   - Required for persistent Google Calendar auto-sync!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error applying migrations: {e}")
        return False


def verify_tables():
    """Verify that tables were created."""
    logger.info("\n🔍 Verifying tables...")
    
    tables = [
        "businesses", "users", "transactions", "loans",
        "loan_repayments", "goals", "events", "agent_logs",
        "habit_profiles", "memory_summaries"
    ]
    
    for table in tables:
        try:
            result = supabase_client.admin.table(table).select("*").limit(1).execute()
            logger.info(f"   ✓ Table exists: {table}")
        except Exception as e:
            logger.error(f"   ✗ Table missing or error: {table} - {e}")
    
    logger.info("\n✅ Verification complete")


if __name__ == "__main__":
    if apply_migrations():
        logger.info("\n" + "="*60)
        logger.info("After applying migrations manually, run this script again")
        logger.info("to verify tables were created successfully.")
        logger.info("="*60)
        
        # Ask user if they want to verify
        response = input("\nHave you applied the migrations? (y/n): ")
        if response.lower() == 'y':
            verify_tables()

