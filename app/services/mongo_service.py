from app.core.database import get_database
from app.core.logger import logger
from app.schemas.db_schema import ProcessedImageRecord

async def save_processed_record(record: ProcessedImageRecord) -> str:
    """Validates and dumps the processed image record into MongoDB."""
    try:
        db = get_database()
        collection = db["processed_jobs"]
        
        # Pydantic v2 method to convert object to a dictionary
        record_dict = record.model_dump()
        
        # Insert into Mongo
        result = await collection.insert_one(record_dict)
        
        logger.info(f"💾 Inserted record for image {record.image_id} into Mongo. ID: {result.inserted_id}")
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"❌ Failed to save record {record.image_id} to Mongo: {e}")
        raise e