import os
import redis.asyncio as redis
from dotenv import load_dotenv
from app.core.logger import logger

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class RedisConnection:
    client: redis.Redis | None = None

redis_db = RedisConnection()

async def connect_to_redis():
    logger.info("Connecting to Redis...")
    
    try:
        # decode_responses=True automatically converts byte strings to Python strings
        redis_db.client = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Force a connection test
        await redis_db.client.ping()
        logger.info("✅ Redis connected successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        raise e

async def close_redis_connection():
    if redis_db.client:
        logger.info("Closing Redis connection...")
        await redis_db.client.aclose()
        logger.info("✅ Redis connection closed")

def get_redis() -> redis.Redis:
    if not redis_db.client:
        raise RuntimeError("Redis client not initialized")
    return redis_db.client