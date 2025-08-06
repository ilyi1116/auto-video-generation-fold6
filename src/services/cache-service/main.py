import os
from contextlib import asynccontextmanager

import redis.asyncio as redis
import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class CacheItem(BaseModel):
    key: str
    value: str
    ttl: int = 3600


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    logger.info("Cache service started")
    yield
    # Shutdown
    await app.state.redis.close()
    logger.info("Cache service stopped")


app = FastAPI(
    title="Cache Service",
    description="分布式快取服務",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    try:
        await app.state.redis.ping()
        return {"status": "healthy", "service": "cache-service", "version": "1.0.0"}
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/cache/{key}")
async def set_cache(key: str, item: CacheItem):
    try:
        await app.state.redis.setex(key, item.ttl, item.value)
        logger.info("Cache item set", key=key, ttl=item.ttl)
        return {"status": "success", "key": key}
    except Exception as e:
        logger.error("Failed to set cache", key=key, error=str(e))
        raise HTTPException(status_code=500, detail="Cache operation failed")


@app.get("/cache/{key}")
async def get_cache(key: str):
    try:
        value = await app.state.redis.get(key)
        if value is None:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"key": key, "value": value.decode()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get cache", key=key, error=str(e))
        raise HTTPException(status_code=500, detail="Cache operation failed")


@app.delete("/cache/{key}")
async def delete_cache(key: str):
    try:
        result = await app.state.redis.delete(key)
        if result == 0:
            raise HTTPException(status_code=404, detail="Key not found")
        logger.info("Cache item deleted", key=key)
        return {"status": "success", "key": key}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete cache", key=key, error=str(e))
        raise HTTPException(status_code=500, detail="Cache operation failed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8014)
