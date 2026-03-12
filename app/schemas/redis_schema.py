from enum import Enum
from pydantic import BaseModel


class PriorityStatus(str, Enum):
    CRITICAL = "CRITICAL"
    HOLD = "HOLD"
    IGNORED = "IGNORED"


class RedisQueuePayload(BaseModel):
    job_id: str
    image_id: str
    processed_image_url: str
    latitude: float
    longitude: float
    priority_status: PriorityStatus
    rdi_score: float

    # Helper method to easily dump this to a JSON string for Redis
    def to_redis_json(self) -> str:
        return self.model_dump_json()
