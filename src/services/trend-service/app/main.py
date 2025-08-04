import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import analysis, entrepreneur, keywords, trends

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Trend Service started")
    yield
    logger.info("Trend Service shutting down")


app = FastAPI(
    title="Trend Service",
    description="趨勢分析與關鍵字研究服務",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
)

app.include_router(trends.router, prefix="/api/v1/trends", tags=["trends"])
app.include_router(
    keywords.router, prefix="/api/v1/keywords", tags=["keywords"]
)
app.include_router(
    analysis.router, prefix="/api/v1/analysis", tags=["analysis"]
)
app.include_router(
    entrepreneur.router, prefix="/api/v1/entrepreneur", tags=["entrepreneur"]
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "trend-service"}


@app.get("/")
async def root():
    return {"message": "Trend Service", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8007)
