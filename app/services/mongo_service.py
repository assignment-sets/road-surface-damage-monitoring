from collections import defaultdict
from app.core.database import get_database
from app.core.logger import logger
from app.schemas.db_schema import (
    ProcessedImageRecord,
    DashboardResponse,
    DashboardDamageSummary,
    DashboardUrls,
)
from typing import Optional

from dotenv import load_dotenv
import os

load_dotenv()

MONGO_COLLECTION: str = os.getenv("MONGO_COLLECTION_NAME", "processed_jobs")

# Standard RDD2020 Class Definitions
RDD_LABELS = {
    "D00": "Longitudinal Crack",
    "D10": "Transverse Crack",
    "D20": "Alligator Crack",
    "D40": "Pothole",
}


async def save_processed_record(record: ProcessedImageRecord) -> str:
    """Validates and dumps the processed image record into MongoDB."""
    try:
        db = get_database()
        collection = db[MONGO_COLLECTION]

        record_dict = record.model_dump()
        result = await collection.insert_one(record_dict)

        logger.info(
            f"💾 Inserted record for image {record.image_id}. Mongo ID: {result.inserted_id}"
        )
        return str(result.inserted_id)

    except Exception as e:
        logger.error(f"❌ Failed to save record {record.image_id} to Mongo: {e}")
        raise e


def format_for_dashboard(mongo_doc: dict) -> DashboardResponse:
    """Transforms a raw MongoDB record into a strictly typed dashboard payload."""
    raw_details = mongo_doc.get("damage_details", [])

    summary = defaultdict(list)
    for item in raw_details:
        summary[item["label"]].append(item["confidence"])

    formatted_damages = []
    for label, confidences in summary.items():
        human_name = RDD_LABELS.get(label, "Unknown Damage")
        avg_conf = sum(confidences) / len(confidences)
        max_conf = max(confidences)

        formatted_damages.append(
            DashboardDamageSummary(
                type=human_name,
                raw_code=label,
                count=len(confidences),
                avg_confidence=f"{avg_conf * 100:.1f}%",
                max_confidence=f"{max_conf * 100:.1f}%",
            )
        )

    formatted_damages.sort(key=lambda x: x.count, reverse=True)

    return DashboardResponse(
        job_id=mongo_doc["job_id"],
        image_id=mongo_doc["image_id"],
        coordinates=[mongo_doc.get("latitude", 0.0), mongo_doc.get("longitude", 0.0)],
        rdi_score=round(mongo_doc.get("rdi_score", 0.0), 2),
        priority_status=mongo_doc["priority_status"],
        is_resolved=mongo_doc.get("resolved", False),
        urls=DashboardUrls(
            original=mongo_doc.get("original_image_url"),
            processed=mongo_doc.get("processed_image_url"),
        ),
        damage_summary=formatted_damages,
    )


async def toggle_resolved_status(image_id: str) -> bool:
    """Flips the boolean 'resolved' state of an image in Mongo."""
    try:
        db = get_database()
        collection = db[MONGO_COLLECTION]

        # Fetch only the 'resolved' field to minimize payload
        doc = await collection.find_one({"image_id": image_id}, {"resolved": 1})

        if not doc:
            raise ValueError(f"Image ID {image_id} not found in database.")

        current_status = doc.get("resolved", False)
        new_status = not current_status

        await collection.update_one(
            {"image_id": image_id}, {"$set": {"resolved": new_status}}
        )

        logger.info(f"🔄 Toggled resolve status for {image_id} -> {new_status}")
        return new_status

    except Exception as e:
        logger.error(f"❌ Failed to toggle resolve status for {image_id}: {e}")
        raise e


async def fetch_paginated_records(
    page: int = 1, limit: int = 10, resolved_status: Optional[bool] = None
) -> dict:
    """Fetches, formats, and paginates the processed records for the dashboard."""
    try:
        db = get_database()

        collection = db[MONGO_COLLECTION]

        skip = (page - 1) * limit

        # 1. Build the dynamic query dictionary
        query = {}
        if resolved_status is not None:
            query["resolved"] = resolved_status

        # 2. Apply the query to the find operation
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

        raw_docs = await cursor.to_list(length=limit)

        # 3. Apply the exact same query to the document count
        total_count = await collection.count_documents(query)

        formatted_docs = [format_for_dashboard(doc) for doc in raw_docs]

        return {
            "total": total_count,
            "page": page,
            "limit": limit,
            "data": formatted_docs,
        }

    except Exception as e:
        logger.error(f"❌ Failed to fetch paginated records: {e}")
        raise e
