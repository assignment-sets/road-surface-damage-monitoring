from app.core.redis import get_redis
from app.core.logger import logger
from app.schemas.redis_schema import RedisQueuePayload

async def push_to_queue(payload: RedisQueuePayload):
    """Pushes a JSON payload to a specific Redis list based on its priority."""
    try:
        redis_client = get_redis()
        
        # Dynamically name the queue based on the status (e.g., "queue:CRITICAL")
        queue_name = f"queue:{payload.priority_status}"
        
        # Convert Pydantic object to JSON string and push to the right side of the list
        await redis_client.rpush(queue_name, payload.to_redis_json())
        
        logger.info(f"🚀 Pushed image {payload.image_id} to Redis: [{queue_name}]")
        
    except Exception as e:
        logger.error(f"❌ Failed to push payload {payload.image_id} to Redis: {e}")
        raise e