from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum


class DamageDetail(BaseModel):
    label: str
    confidence: float


class PriorityStatus(str, Enum):
    CRITICAL = "CRITICAL"
    HOLD = "HOLD"
    IGNORED = "IGNORED"


class ProcessedImageRecord(BaseModel):
    job_id: str
    image_id: str
    latitude: float
    longitude: float
    rdi_score: float
    priority_status: PriorityStatus
    damage_details: List[DamageDetail] = []
    resolved: bool = False

    # S3 URLs
    original_image_url: Optional[str] = None
    processed_image_url: Optional[str] = None

    # Auto-generate timestamp in UTC
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Dashboard Schemas ---


class DashboardDamageSummary(BaseModel):
    type: str
    raw_code: str
    count: int
    avg_confidence: str
    max_confidence: str


class DashboardUrls(BaseModel):
    original: Optional[str]
    processed: Optional[str]


class DashboardResponse(BaseModel):
    job_id: str
    image_id: str
    coordinates: List[float]
    rdi_score: float
    priority_status: PriorityStatus
    is_resolved: bool
    urls: DashboardUrls
    damage_summary: List[DashboardDamageSummary]


class PaginatedDashboardResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[DashboardResponse]
