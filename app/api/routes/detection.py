import os
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from pydantic import ValidationError

from app.schemas.detection_schema import UploadResponse, LocationData
from app.services.inference_service import process_images_background
from app.core.logger import logger

router = APIRouter()

# Strict whitelist of supported image formats
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/avif"
}

@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_images_for_detection(
    background_tasks: BackgroundTasks,
    images: List[UploadFile] = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
):
    # 1. Pydantic Location Validation
    try:
        location = LocationData(latitude=latitude, longitude=longitude)
    except ValidationError as e:
        logger.error("❌ Invalid coordinates received.")
        raise HTTPException(
            status_code=422, detail="Invalid latitude or longitude coordinates."
        )

    # 2. Enforce Image Limits
    if not images:
        raise HTTPException(status_code=400, detail="No images provided.")

    if len(images) > 10:
        logger.warning(f"⚠️ Rejecting batch: Too many images ({len(images)}).")
        raise HTTPException(
            status_code=400, detail="Maximum 10 images allowed per batch."
        )

    job_id = str(uuid.uuid4())
    temp_dir = f"temp_uploads/{job_id}"
    os.makedirs(temp_dir, exist_ok=True)

    saved_file_paths = []

    # 3. Save Files Synchronously with Strict Validation
    for image in images:
        # Check against the explicit whitelist
        if image.content_type not in ALLOWED_MIME_TYPES:
            logger.warning(f"⚠️ Skipping unsupported file type: {image.filename} ({image.content_type})")
            continue

        file_path = os.path.join(temp_dir, image.filename)
        with open(file_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)

        saved_file_paths.append(file_path)

    # 4. Final Sanity Check
    if len(saved_file_paths) == 0:
        # Clean up the empty dir
        os.rmdir(temp_dir)
        raise HTTPException(
            status_code=400, detail="No valid image files (JPEG, PNG, WEBP) found in the payload."
        )

    # 5. Hand off to the background worker
    background_tasks.add_task(
        process_images_background,
        job_id=job_id,
        file_paths=saved_file_paths,
        lat=location.latitude,
        lng=location.longitude,
    )

    logger.info(
        f"✅ Accepted batch {job_id} with {len(saved_file_paths)} valid images."
    )

    # 6. Optimistic Response
    return UploadResponse(
        message="Images successfully queued for processing",
        job_id=job_id,
        images_received=len(saved_file_paths),
        status="processing",
    )