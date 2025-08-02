import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import analytics, entrepreneur_publishing, platforms

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Social Service started")
    yield
    logger.info("Social Service shutting down")


app = FastAPI(
    title="Social Service",
    description="社交媒體平台整合服務",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

app.include_router(
    platforms.router, prefix="/api/v1/platforms", tags=["platforms"]
)
app.include_router(
    analytics.router, prefix="/api/v1/analytics", tags=["analytics"]
)
app.include_router(
    entrepreneur_publishing.router,
    prefix="/api/v1/entrepreneur",
    tags=["entrepreneur-publishing"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "social-service"}


@app.get("/")
async def root():
    return {"message": "Social Service", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8006)
