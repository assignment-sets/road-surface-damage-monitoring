import os
import shutil
import asyncio
import uuid
from ultralytics import YOLO

from app.services.s3_service import upload_image_to_s3
from app.services.mongo_service import save_processed_record

from app.schemas.db_schema import ProcessedImageRecord, DamageDetail, PriorityStatus
from app.core.logger import logger

logger.info("🧠 Loading YOLOv8 Model...")
model = YOLO("app/models/best.pt")

RDI_ALERT_THRESHOLD = 1.50
AREA_WEIGHT = 2.0


def calculate_rdi(boxes, area_weight: float = 2.0) -> float:
    """Calculates the Road Damage Index based on bounding box confidences and areas."""
    if len(boxes) == 0:
        return 0.0

    confidences = [float(conf.item()) for conf in boxes.conf]
    areas = [(float(box[2].item()) * float(box[3].item())) for box in boxes.xywhn]

    sum_conf = sum(confidences)
    max_conf = max(confidences)
    sum_area = sum(areas)

    return sum_conf + max_conf + (area_weight * sum_area)


async def process_images_background(
    job_id: str, file_paths: list[str], lat: float, lng: float
):
    logger.info(f"⚙️ [JOB {job_id}] Starting inference for {len(file_paths)} images.")

    input_folder = os.path.dirname(file_paths[0])
    project_dir = os.path.abspath("temp_uploads")

    try:
        results = await asyncio.to_thread(
            model.predict,
            source=input_folder,
            conf=0.15,
            save=True,
            project=project_dir,
            name=f"predict_{job_id}",
        )

        for result in results:
            original_filename = os.path.basename(result.path)
            boxes = result.boxes
            box_count = len(boxes)

            if box_count == 0:
                logger.info(
                    f"⚪ IGNORED: {original_filename} | Clean road. Skipping DB/S3."
                )
                continue

            rdi_score = calculate_rdi(boxes, AREA_WEIGHT)

            if rdi_score >= RDI_ALERT_THRESHOLD:
                priority_status = PriorityStatus.CRITICAL
            elif rdi_score >= 0.5:
                priority_status = PriorityStatus.HOLD
            else:
                logger.info(
                    f"⚪ IGNORED: {original_filename} | RDI {rdi_score:.2f} too low. Skipping."
                )
                continue

            logger.info(
                f"🔴 ALERT: {original_filename} | RDI: {rdi_score:.2f} | Status: {priority_status.value}"
            )

            damage_list = [
                DamageDetail(
                    label=model.names[int(boxes.cls[i])],
                    confidence=float(boxes.conf[i].item()),
                )
                for i in range(box_count)
            ]

            original_file_path = os.path.join(input_folder, original_filename)
            image_uuid = str(uuid.uuid4())

            upload_tasks = [
                upload_image_to_s3(original_file_path, prefix=f"raw/{job_id}")
            ]

            filename_without_ext = os.path.splitext(original_filename)[0]
            processed_file_path = os.path.join(result.save_dir, original_filename)
            fallback_processed_path = os.path.join(
                result.save_dir, f"{filename_without_ext}.jpg"
            )

            if os.path.exists(processed_file_path):
                upload_tasks.append(
                    upload_image_to_s3(
                        processed_file_path, prefix=f"processed/{job_id}"
                    )
                )
                original_url, processed_url = await asyncio.gather(*upload_tasks)
            elif os.path.exists(fallback_processed_path):
                upload_tasks.append(
                    upload_image_to_s3(
                        fallback_processed_path, prefix=f"processed/{job_id}"
                    )
                )
                original_url, processed_url = await asyncio.gather(*upload_tasks)
            else:
                (original_url,) = await asyncio.gather(*upload_tasks)
                processed_url = None

            # create db record
            mongo_record = ProcessedImageRecord(
                job_id=job_id,
                image_id=image_uuid,
                latitude=lat,
                longitude=lng,
                rdi_score=rdi_score,
                priority_status=priority_status,
                damage_details=damage_list,
                original_image_url=original_url,
                processed_image_url=processed_url,
            )
            await save_processed_record(mongo_record)

    except Exception as e:
        logger.error(f"❌ [JOB {job_id}] Pipeline failed: {e}")

    finally:
        if os.path.exists(input_folder):
            shutil.rmtree(input_folder)

        yolo_output_dir = os.path.join(project_dir, f"predict_{job_id}")
        if os.path.exists(yolo_output_dir):
            shutil.rmtree(yolo_output_dir)

        logger.info(f"✅ [JOB {job_id}] Background processing complete.")
