"""RQ Worker for background job processing."""
import logging
from rq import Worker, Queue, Connection
from redis import Redis
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
redis_conn = Redis.from_url(settings.redis_url)

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker(["zyana-queue"], connection=redis_conn)
        logger.info("🔄 Starting RQ worker...")
        worker.work()

