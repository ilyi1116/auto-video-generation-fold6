import os
from contextlib import asynccontextmanager

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


class MusicGenerationRequest(BaseModel):
    prompt: str
    duration: int = 30
    style: str = "pop"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.suno_api_key = os.getenv("SUNO_API_KEY")
    logger.info("Music service started")
    yield
    # Shutdown
    logger.info("Music service stopped")


app = FastAPI(
    title="Music Service",
    description="AI音樂生成服務",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "music-service", "version": "1.0.0"}


@app.post("/generate")
async def generate_music(request: MusicGenerationRequest):
    try:
        # TODO: 實現Suno API整合
        logger.info(
            "Music generation requested",
            prompt=request.prompt,
            duration=request.duration,
            style=request.style,
        )

        # 模擬音樂生成
        return {
            "status": "success",
            "music_id": f"music_{hash(request.prompt)}",
            "prompt": request.prompt,
            "duration": request.duration,
            "style": request.style,
            "url": "https://example.com/generated-music.mp3",
        }
    except Exception as e:
        logger.error("Music generation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Music generation failed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8016)
