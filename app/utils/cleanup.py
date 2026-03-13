import shutil
import os
from app.core.logger import logger

def cleanup_temp_uploads():
    temp_path = "temp_uploads"
    if os.path.exists(temp_path):
        # Deleting the whole directory and recreating it empty
        shutil.rmtree(temp_path)
        os.makedirs(temp_path)
        logger.info("Cleaned up stale temporary upload files.")
    else:
        os.makedirs(temp_path, exist_ok=True)