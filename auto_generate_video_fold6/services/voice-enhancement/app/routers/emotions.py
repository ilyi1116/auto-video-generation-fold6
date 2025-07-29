"""
Emotion Synthesis API Router
提供情感語音合成相關的 API 端點
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import structlog

from ..auth import get_current_user
from ..services.emotion_synthesizer import EmotionSynthesizer

logger = structlog.get_logger()
router = APIRouter()

# 全域情感合成器實例
emotion_synthesizer = None

@router.on_event("startup")
async def startup_event():
    """啟動時初始化情感合成器"""
    global emotion_synthesizer
    emotion_synthesizer = EmotionSynthesizer()
    await emotion_synthesizer.initialize()

# Request/Response 模型
class EmotionSynthesisRequest(BaseModel):
    text: str = Field(..., description="要合成的文字", max_length=2000)
    emotion: str = Field(default="neutral", description="目標情感")
    intensity: float = Field(default=1.0, ge=0.1, le=2.0, description="情感強度")
    language: str = Field(default="zh-TW", description="語言代碼")
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0, description="語音速度")
    voice_pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="語音音調")

class EmotionAnalysisResponse(BaseModel):
    emotion: str
    confidence: float
    all_emotions: Optional[Dict[str, float]] = None

class VoiceCharacteristicsResponse(BaseModel):
    duration: float
    sample_rate: int
    amplitude: Dict[str, float]
    pitch: Optional[Dict[str, float]] = None
    mfcc: Optional[Dict[str, List[float]]] = None
    rhythm: Optional[Dict[str, float]] = None

class SupportedEmotionsResponse(BaseModel):
    emotions: List[str]
    description: Dict[str, str]

class SupportedLanguagesResponse(BaseModel):
    languages: List[str]
    names: Dict[str, str]

@router.post("/synthesize", 
            summary="情感語音合成",
            description="根據指定的情感和參數合成語音")
async def synthesize_emotion_speech(
    request: EmotionSynthesisRequest,
    current_user: dict = Depends(get_current_user)
):
    """情感語音合成"""
    try:
        if not emotion_synthesizer:
            raise HTTPException(status_code=503, detail="情感合成器未初始化")
        
        logger.info("收到情感語音合成請求", 
                   user_id=current_user.get("id"),
                   emotion=request.emotion,
                   language=request.language)
        
        # 合成語音
        audio_data = await emotion_synthesizer.synthesize_with_emotion(
            text=request.text,
            emotion=request.emotion,
            intensity=request.intensity,
            language=request.language,
            voice_speed=request.voice_speed,
            voice_pitch=request.voice_pitch
        )
        
        # 返回音訊數據
        from fastapi.responses import Response
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=emotion_speech_{request.emotion}.wav"
            }
        )
        
    except Exception as e:
        logger.error("情感語音合成失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"語音合成失敗: {str(e)}")

@router.post("/analyze",
            response_model=EmotionAnalysisResponse,
            summary="情感分析",
            description="分析音訊中的情感")
async def analyze_audio_emotion(
    audio_file: UploadFile = File(..., description="音訊文件"),
    current_user: dict = Depends(get_current_user)
):
    """分析音訊中的情感"""
    try:
        if not emotion_synthesizer:
            raise HTTPException(status_code=503, detail="情感合成器未初始化")
        
        # 驗證文件類型
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="僅支援音訊文件")
        
        logger.info("收到情感分析請求", 
                   user_id=current_user.get("id"),
                   filename=audio_file.filename)
        
        # 讀取音訊數據
        audio_data = await audio_file.read()
        
        # 分析情感
        emotion_result = await emotion_synthesizer.analyze_emotion(audio_data)
        
        return EmotionAnalysisResponse(**emotion_result)
        
    except Exception as e:
        logger.error("情感分析失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"情感分析失敗: {str(e)}")

@router.post("/characteristics",
            response_model=VoiceCharacteristicsResponse,
            summary="語音特徵分析",
            description="分析音訊的語音特徵")
async def analyze_voice_characteristics(
    audio_file: UploadFile = File(..., description="音訊文件"),
    current_user: dict = Depends(get_current_user)
):
    """分析語音特徵"""
    try:
        if not emotion_synthesizer:
            raise HTTPException(status_code=503, detail="情感合成器未初始化")
        
        # 驗證文件類型
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="僅支援音訊文件")
        
        logger.info("收到語音特徵分析請求", 
                   user_id=current_user.get("id"),
                   filename=audio_file.filename)
        
        # 讀取音訊數據
        audio_data = await audio_file.read()
        
        # 分析語音特徵
        characteristics = await emotion_synthesizer.get_voice_characteristics(audio_data)
        
        return VoiceCharacteristicsResponse(**characteristics)
        
    except Exception as e:
        logger.error("語音特徵分析失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"語音特徵分析失敗: {str(e)}")

@router.get("/emotions",
           response_model=SupportedEmotionsResponse,
           summary="支援的情感列表",
           description="獲取系統支援的所有情感類型")
async def get_supported_emotions():
    """獲取支援的情感列表"""
    try:
        if not emotion_synthesizer:
            raise HTTPException(status_code=503, detail="情感合成器未初始化")
        
        emotions = emotion_synthesizer.get_supported_emotions()
        
        # 情感描述
        emotion_descriptions = {
            "neutral": "中性，無特殊情感色彩",
            "happy": "開心、愉悅的情感",
            "sad": "悲傷、沮喪的情感",
            "angry": "憤怒、生氣的情感",
            "fear": "恐懼、害怕的情感",
            "surprise": "驚訝、意外的情感",
            "disgust": "厭惡、不喜歡的情感",
            "excited": "興奮、激動的情感",
            "calm": "平靜、放鬆的情感",
            "confident": "自信、肯定的情感"
        }
        
        return SupportedEmotionsResponse(
            emotions=emotions,
            description=emotion_descriptions
        )
        
    except Exception as e:
        logger.error("獲取支援情感列表失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"獲取情感列表失敗: {str(e)}")

@router.get("/languages",
           response_model=SupportedLanguagesResponse,
           summary="支援的語言列表",
           description="獲取系統支援的所有語言")
async def get_supported_languages():
    """獲取支援的語言列表"""
    try:
        if not emotion_synthesizer:
            raise HTTPException(status_code=503, detail="情感合成器未初始化")
        
        languages = emotion_synthesizer.get_supported_languages()
        
        # 語言名稱
        language_names = {
            "zh-CN": "簡體中文",
            "zh-TW": "繁體中文",
            "en-US": "英語（美國）",
            "ja-JP": "日語",
            "ko-KR": "韓語"
        }
        
        return SupportedLanguagesResponse(
            languages=languages,
            names=language_names
        )
        
    except Exception as e:
        logger.error("獲取支援語言列表失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"獲取語言列表失敗: {str(e)}")

@router.post("/batch-synthesize",
            summary="批次情感語音合成",
            description="批次處理多個文字的情感語音合成")
async def batch_synthesize_emotion_speech(
    requests: List[EmotionSynthesisRequest],
    current_user: dict = Depends(get_current_user)
):
    """批次情感語音合成"""
    try:
        if not emotion_synthesizer:
            raise HTTPException(status_code=503, detail="情感合成器未初始化")
        
        if len(requests) > 10:
            raise HTTPException(status_code=400, detail="批次處理最多支援 10 個請求")
        
        logger.info("收到批次情感語音合成請求", 
                   user_id=current_user.get("id"),
                   count=len(requests))
        
        results = []
        for i, request in enumerate(requests):
            try:
                audio_data = await emotion_synthesizer.synthesize_with_emotion(
                    text=request.text,
                    emotion=request.emotion,
                    intensity=request.intensity,
                    language=request.language,
                    voice_speed=request.voice_speed,
                    voice_pitch=request.voice_pitch
                )
                
                # 將音訊數據編碼為 base64
                import base64
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                
                results.append({
                    "index": i,
                    "success": True,
                    "audio_data": audio_b64,
                    "content_type": "audio/wav"
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })
        
        return {"results": results}
        
    except Exception as e:
        logger.error("批次情感語音合成失敗", error=str(e))
        raise HTTPException(status_code=500, detail=f"批次語音合成失敗: {str(e)}")

@router.get("/presets",
           summary="情感預設配置",
           description="獲取預定義的情感配置組合")
async def get_emotion_presets():
    """獲取情感預設配置"""
    presets = {
        "storytelling": {
            "happy": {"intensity": 1.2, "voice_speed": 1.05, "voice_pitch": 1.1},
            "sad": {"intensity": 1.1, "voice_speed": 0.9, "voice_pitch": 0.9},
            "excited": {"intensity": 1.3, "voice_speed": 1.1, "voice_pitch": 1.15},
            "neutral": {"intensity": 1.0, "voice_speed": 1.0, "voice_pitch": 1.0}
        },
        "presentation": {
            "confident": {"intensity": 1.1, "voice_speed": 0.95, "voice_pitch": 0.95},
            "calm": {"intensity": 1.0, "voice_speed": 0.9, "voice_pitch": 0.95},
            "neutral": {"intensity": 1.0, "voice_speed": 1.0, "voice_pitch": 1.0}
        },
        "entertainment": {
            "happy": {"intensity": 1.4, "voice_speed": 1.1, "voice_pitch": 1.2},
            "excited": {"intensity": 1.5, "voice_speed": 1.15, "voice_pitch": 1.25},
            "surprise": {"intensity": 1.3, "voice_speed": 1.2, "voice_pitch": 1.3}
        },
        "meditation": {
            "calm": {"intensity": 0.8, "voice_speed": 0.8, "voice_pitch": 0.9},
            "neutral": {"intensity": 0.9, "voice_speed": 0.85, "voice_pitch": 0.95}
        }
    }
    
    return {
        "presets": presets,
        "description": {
            "storytelling": "適合說故事和敘述",
            "presentation": "適合簡報和演講",
            "entertainment": "適合娛樂和表演",
            "meditation": "適合冥想和放鬆"
        }
    }