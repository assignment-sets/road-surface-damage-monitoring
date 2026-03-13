import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logger import logger
from app.core.database import connect_to_mongo, close_mongo_connection

from app.api.routes.detection import router as detection_router
from app.api.routes.dashboard import router as dashboard_router 


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info("🚀 Booting up the RDI Backend...")
    try:
        await connect_to_mongo()
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise e

    yield  # server running and accepting requests

    # --- SHUTDOWN ---
    logger.info("🛑 Shutting down the RDI Backend...")
    await close_mongo_connection()


# Initialize the FastAPI application
app = FastAPI(
    title="Road Damage Index (RDI) API",
    description="Backend for processing bulk road images through YOLOv8",
    version="1.0.0",
    lifespan=lifespan,
)

# cors config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the routes
app.include_router(detection_router, prefix="/api/v1/detection", tags=["Detection"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])


# health-check endpoint
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "RDI Backend is running"}


# Run the server on port 8000
if __name__ == "__main__":
    logger.info("Starting Uvicorn server on port 8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)