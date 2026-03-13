from fastapi import APIRouter, HTTPException, Query
from app.services.mongo_service import fetch_paginated_records, toggle_resolved_status
from app.schemas.db_schema import PaginatedDashboardResponse
from typing import Optional

from app.core.logger import logger

router = APIRouter()


@router.get("/", response_model=PaginatedDashboardResponse, status_code=200)
async def get_dashboard_data(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page (max 50)"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status (true/false)")
):
    """Fetches paginated and formatted image records for the frontend."""
    try:
        return await fetch_paginated_records(page=page, limit=limit, resolved_status=resolved)
    except Exception as e:
        logger.error(f"❌ Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching data.")


@router.patch("/{image_id}/toggle", status_code=200)
async def toggle_image_status(image_id: str):
    """Toggles the 'resolved' status of a specific image."""
    try:
        new_status = await toggle_resolved_status(image_id)
        return {"image_id": image_id, "resolved": new_status}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"❌ Error toggling status for {image_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while toggling status."
        )
