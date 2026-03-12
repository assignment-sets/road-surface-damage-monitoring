import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

# Import your custom logger
from app.core.logger import logger

load_dotenv()

MONGO_URL = os.getenv("MONGO_URI", "mongodb://admin:password123@localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "rdd_mongo")

class Database:
    client: AsyncIOMotorClient | None = None

db = Database()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    
    try:
        db.client = AsyncIOMotorClient(
            MONGO_URL,
            maxPoolSize=20,
            minPoolSize=5,
            serverSelectionTimeoutMS=5000,
        )
        
        # Force connection test
        await db.client.admin.command("ping")
        logger.info("✅ MongoDB connected successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    if db.client:
        logger.info("Closing MongoDB connection...")
        db.client.close()
        logger.info("✅ MongoDB connection closed")

def get_database() -> AsyncIOMotorDatabase:
    if not db.client:
        raise RuntimeError("MongoDB client not initialized")
    return db.client[DB_NAME]