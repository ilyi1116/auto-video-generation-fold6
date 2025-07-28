from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from ..auth import get_current_user
from ..services.audio_processor import AudioProcessor

router = APIRouter()
logger = structlog.get_logger()


class VoiceSynthesisRequest(BaseModel):
    text: str
    voice_style: str = "natural"  # natural, professional, energetic, calm, enthusiastic
    language: str = "en"  # en, zh, ja, ko, es, fr, de
    speed: float = 1.0  # 0.5 - 2.0
    pitch: float = 1.0  # 0.5 - 2.0
    emotion: str = "neutral"  # neutral, happy, sad, excited, serious


class VoiceSynthesisResponse(BaseModel):
    audio_id: str
    audio_url: str
    duration_seconds: float
    text: str
    voice_style: str
    language: str
    status: str


class VoiceCloneRequest(BaseModel):
    audio_file_url: str
    target_text: str
    quality: str = "high"  # low, medium, high
    preserve_emotion: bool = True


class AudioEnhancementRequest(BaseModel):
    audio_url: str
    enhancement_type: str = "noise_reduction"  # noise_reduction, normalize, enhance_speech
    intensity: float = 0.7


@router.post("/synthesize", response_model=VoiceSynthesisResponse)
async def synthesize_voice(
    request: VoiceSynthesisRequest, current_user: dict = Depends(get_current_user)
) -> VoiceSynthesisResponse:
    """Synthesize speech from text"""
    try:
        logger.info(
            "Synthesizing voice",
            user_id=current_user.get("id"),
            text_length=len(request.text),
            voice_style=request.voice_style,
            language=request.language,
        )

        audio_processor = AudioProcessor()
        result = await audio_processor.synthesize_voice(
            text=request.text,
            voice_style=request.voice_style,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch,
            emotion=request.emotion,
        )

        return VoiceSynthesisResponse(**result)

    except Exception as e:
        logger.error("Voice synthesis failed", error=str(e))
        raise HTTPException(status_code=500, detail="Voice synthesis failed")


@router.post("/clone-voice")
async def clone_voice(request: VoiceCloneRequest, current_user: dict = Depends(get_current_user)):
    """Clone voice from sample audio"""
    try:
        logger.info(
            "Cloning voice",
            user_id=current_user.get("id"),
            target_text_length=len(request.target_text),
            quality=request.quality,
        )

        audio_processor = AudioProcessor()
        result = await audio_processor.clone_voice(
            audio_file_url=request.audio_file_url,
            target_text=request.target_text,
            quality=request.quality,
            preserve_emotion=request.preserve_emotion,
        )

        return result

    except Exception as e:
        logger.error("Voice cloning failed", error=str(e))
        raise HTTPException(status_code=500, detail="Voice cloning failed")


@router.post("/enhance-audio")
async def enhance_audio(
    request: AudioEnhancementRequest, current_user: dict = Depends(get_current_user)
):
    """Enhance audio quality"""
    try:
        logger.info(
            "Enhancing audio",
            user_id=current_user.get("id"),
            enhancement_type=request.enhancement_type,
            intensity=request.intensity,
        )

        audio_processor = AudioProcessor()
        result = await audio_processor.enhance_audio(
            audio_url=request.audio_url,
            enhancement_type=request.enhancement_type,
            intensity=request.intensity,
        )

        return result

    except Exception as e:
        logger.error("Audio enhancement failed", error=str(e))
        raise HTTPException(status_code=500, detail="Audio enhancement failed")


@router.post("/upload-audio")
async def upload_audio(
    audio_file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
):
    """Upload audio file for processing"""
    try:
        logger.info(
            "Uploading audio file",
            user_id=current_user.get("id"),
            filename=audio_file.filename,
            content_type=audio_file.content_type,
        )

        audio_processor = AudioProcessor()
        result = await audio_processor.upload_audio(
            audio_file=audio_file, user_id=current_user.get("id")
        )

        return result

    except Exception as e:
        logger.error("Audio upload failed", error=str(e))
        raise HTTPException(status_code=500, detail="Audio upload failed")


@router.post("/convert-format")
async def convert_audio_format(
    audio_url: str,
    target_format: str = "mp3",  # mp3, wav, m4a, flac
    quality: str = "high",  # low, medium, high
    current_user: dict = Depends(get_current_user),
):
    """Convert audio to different format"""
    try:
        logger.info(
            "Converting audio format",
            user_id=current_user.get("id"),
            target_format=target_format,
            quality=quality,
        )

        audio_processor = AudioProcessor()
        result = await audio_processor.convert_format(
            audio_url=audio_url, target_format=target_format, quality=quality
        )

        return result

    except Exception as e:
        logger.error("Audio format conversion failed", error=str(e))
        raise HTTPException(status_code=500, detail="Audio format conversion failed")


@router.get("/supported-voices")
async def get_supported_voices():
    """Get list of supported voice styles and languages"""
    return {
        "voice_styles": [
            {"name": "natural", "description": "Natural conversational tone"},
            {"name": "professional", "description": "Business and formal tone"},
            {"name": "energetic", "description": "High-energy and enthusiastic"},
            {"name": "calm", "description": "Soothing and relaxed"},
            {"name": "enthusiastic", "description": "Excited and passionate"},
        ],
        "languages": [
            {"code": "en", "name": "English", "variants": ["US", "UK", "AU"]},
            {"code": "zh", "name": "Chinese", "variants": ["CN", "TW", "HK"]},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
            {"code": "es", "name": "Spanish", "variants": ["ES", "MX", "AR"]},
            {"code": "fr", "name": "French"},
            {"code": "de", "name": "German"},
        ],
        "emotions": [
            {"name": "neutral", "description": "Balanced and natural"},
            {"name": "happy", "description": "Joyful and upbeat"},
            {"name": "sad", "description": "Melancholic and somber"},
            {"name": "excited", "description": "Energetic and thrilled"},
            {"name": "serious", "description": "Formal and authoritative"},
        ],
    }
