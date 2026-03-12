import os
import uuid
from botocore.exceptions import ClientError
from app.core.s3 import session, S3_BUCKET_NAME
from app.core.logger import logger


async def upload_image_to_s3(local_file_path: str, prefix: str = "raw") -> str:
    """
    Uploads a file to S3 and returns the public URL.
    Prefix to help organize folders in S3 (e.g., "raw/image1.jpg" vs "processed/image1.jpg")
    """
    if not os.path.exists(local_file_path):
        logger.error(f"❌ File not found for S3 upload: {local_file_path}")
        raise FileNotFoundError(f"File {local_file_path} does not exist.")

    # Generate a unique filename to prevent overwriting in S3
    file_extension = os.path.splitext(local_file_path)[1]
    unique_filename = f"{prefix}/{uuid.uuid4().hex}{file_extension}"

    try:
        # Open an async client using session
        async with session.client("s3") as s3_client:
            # open the file in binary read mode ('rb')
            with open(local_file_path, "rb") as file_data:
                await s3_client.upload_fileobj(
                    file_data,
                    S3_BUCKET_NAME,
                    unique_filename,
                    ExtraArgs={"ContentType": "image/jpeg"},
                )

            # Constructing the public URL (Assuming bucket is public-read)
            region = session.region_name
            public_url = (
                f"https://{S3_BUCKET_NAME}.s3.{region}.amazonaws.com/{unique_filename}"
            )

            logger.info(f"☁️ Successfully uploaded to S3: {public_url}")
            return public_url

    except ClientError as e:
        logger.error(f"❌ AWS S3 Upload failed: {e}")
        raise e
