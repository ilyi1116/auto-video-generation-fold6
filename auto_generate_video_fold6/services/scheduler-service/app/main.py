import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .auth import verify_token
from .celery_app import celery_app
from .config import settings
from .database import Base, engine
from .routers import scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Scheduler Service started")
    yield
    logger.info("Scheduler Service shutting down")


app = FastAPI(
    title="Scheduler Service",
    description="社交媒體排程發布服務",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scheduler.router, prefix="/api/v1/schedule", tags=["schedule"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "scheduler-service"}


@app.get("/")
async def root():
    return {"message": "Scheduler Service", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8008)
