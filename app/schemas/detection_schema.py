from pydantic import BaseModel, Field


class LocationData(BaseModel):
    # Real-world coordinate limits
    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude must be between -90 and 90"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude must be between -180 and 180"
    )


class UploadResponse(BaseModel):
    message: str
    job_id: str
    images_received: int
    status: str
