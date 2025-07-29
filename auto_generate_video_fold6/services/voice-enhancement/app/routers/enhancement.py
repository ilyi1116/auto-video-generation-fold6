"""
Voice Enhancement Router
提供語音增強功能
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class EnhancementRequest(BaseModel):
    audio_url: str
    enhancement_type: str = "denoise"

@router.post("/enhance")
async def enhance_audio(request: EnhancementRequest):
    """語音增強"""
    return {"message": "Enhancement endpoint"}