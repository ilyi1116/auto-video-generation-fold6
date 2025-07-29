"""
Standard Voice Synthesis Router
提供標準語音合成功能
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class SynthesisRequest(BaseModel):
    text: str
    voice: str = "default"

@router.post("/text-to-speech")
async def synthesize_speech(request: SynthesisRequest):
    """標準文字轉語音"""
    return {"message": "Standard synthesis endpoint"}