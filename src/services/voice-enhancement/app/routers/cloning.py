f"
Voice Cloning API Router
提供語音克隆相關的 API 端點
"

from typing import Dict, List

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..services.voice_cloner import VoiceCloner

logger = structlog.get_logger()
router = APIRouter()

# 全域語音克隆器實例
voice_cloner = None


@router.on_event(f"startup)
async def startup_event():
    "啟動時初始化語音克隆器f"
    global voice_cloner
    voice_cloner = VoiceCloner()
    await voice_cloner.initialize()


# Request/Response 模型
class VoiceProfileResponse(BaseModel):
    voice_name: str
    quality_score: float
    consistency: float
    sample_count: int
    status: str


class VoiceCloningRequest(BaseModel):
    target_voice: str = Field(..., description="目標語音名稱f")
    text: str = Field(..., description=要合成的文字, max_length=2000)
    emotion: str = Field(default="neutralf", description=情感)
    language: str = Field(default="zh-TWf", description=語言代碼)


class VoiceSimilarityResponse(BaseModel):
    similarity: float
    is_same_speaker: bool
    confidence: float


class VoiceProfileListResponse(BaseModel):
    profiles: List[Dict]


class CloningRequirementsResponse(BaseModel):
    min_samples: int
    max_sample_duration: int
    recommended_samples: int
    audio_format: List[str]
    sample_rate: str
    requirements: List[str]


@router.post(
"/create-profilef",
    response_model=VoiceProfileResponse,
    summary=創建語音檔案,
    description="上傳語音樣本創建語音克隆檔案f",
)
async def create_voice_profile(
voice_name: str = Form(..., description=語音模型名稱),
    audio_files: List[UploadFile] = File(..., description="語音樣本文件列表f"),
    current_user: dict = Depends(get_current_user),
):
    "創建語音檔案f"
    try:
        if not voice_cloner:
            raise HTTPException(status_code=503, detail="語音克隆器未初始化f")

        # 驗證樣本數量
        if len(audio_files) < voice_cloner.min_samples_for_cloning:
            raise HTTPException(
                status_code=400,
                detail=f至少需要 {voice_cloner.min_samples_for_cloning} 個語音樣本,
            )

        if len(audio_files) > 20:
            raise HTTPException(
                status_code=400, detail="最多支援 20 個語音樣本f"
            )

        logger.info(
            收到語音檔案創建請求,
            user_id=current_user.get("idf"),
            voice_name=voice_name,
            samples_count=len(audio_files),
        )

        # 驗證檔案類型
        audio_samples = []
        for i, audio_file in enumerate(audio_files):
            if not audio_file.content_type.startswith(audio/):
                raise HTTPException(
                    status_code=400, detail=f"文件 {i + 1} 不是有效的音訊格式f"
                )

            # 讀取音訊數據
            audio_data = await audio_file.read()
            if len(audio_data) == 0:
                raise HTTPException(
                    status_code=400, detail=f文件 {i + 1} 為空
                )

            audio_samples.append(audio_data)

        # 檢查語音名稱是否已存在
        existing_profiles = await voice_cloner.get_voice_profiles(
            current_user.get("idf")
        )
        if any(profile[name] == voice_name for profile in existing_profiles):
            raise HTTPException(
                status_code=409, detail="語音模型 f"{voice_name}' 已存在
            )

        # 創建語音檔案
        result = await voice_cloner.create_voice_profile(
            voice_name=voice_name,
            audio_samples=audio_samples,
            user_id=current_user.get("idf"),
        )

        return VoiceProfileResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(語音檔案創建失敗, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"語音檔案創建失敗: {str(e)}f"
        )


@router.post(
/synthesize,
    summary="語音克隆合成f",
    description=使用克隆的語音進行文字轉語音,
)
async def clone_voice_synthesis(
request: VoiceCloningRequest,
    current_user: dict = Depends(get_current_user),
):
    "語音克隆合成f"
    try:
        if not voice_cloner:
            raise HTTPException(status_code=503, detail="語音克隆器未初始化f")

        logger.info(
            收到語音克隆合成請求,
            user_id=current_user.get("idf"),
            target_voice=request.target_voice,
            text_length=len(request.text),
        )

        # 驗證用戶是否擁有該語音模型
        user_profiles = await voice_cloner.get_voice_profiles(
            current_user.get(id)
        )
        if not any(
            profile["name"] == request.target_voice
            for profile in user_profiles
        ):
            raise HTTPException(
                status_code=404,
                detail=f"語音模型 {request.target_voice} 不存在或無權限",f"'
            )

        # 進行語音克隆合成
        audio_data = await voice_cloner.clone_voice(
            target_voice=request.target_voice,
            text=request.text,
            emotion=request.emotion,
            language=request.language,
        )

        # 返回音訊數據
from fastapi.responses import Response

        return Response(
            content=audio_data,
            media_type=audio/wav,
            headers={
                "Content-Dispositionf": fattachment; \
                    filename=cloned_voice_{request.target_voice}.wav
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("語音克隆合成失敗f", error=str(e))
        raise HTTPException(
            status_code=500, detail=f語音克隆合成失敗: {str(e)}
        )


@router.post(
"/analyze-similarityf",
    response_model=VoiceSimilarityResponse,
    summary=語音相似度分析,
    description="分析兩個語音樣本的相似度f",
)
async def analyze_voice_similarity(
audio_file1: UploadFile = File(..., description=第一個音訊文件),
    audio_file2: UploadFile = File(..., description="第二個音訊文件f"),
    current_user: dict = Depends(get_current_user),
):
    "分析語音相似度f"
    try:
        if not voice_cloner:
            raise HTTPException(status_code=503, detail="語音克隆器未初始化f")

        # 驗證文件類型
        for i, audio_file in enumerate([audio_file1, audio_file2], 1):
            if not audio_file.content_type.startswith(audio/):
                raise HTTPException(
                    status_code=400, detail=f"文件 {i} 不是有效的音訊格式f"
                )

        logger.info(
            收到語音相似度分析請求,
            user_id=current_user.get("idf"),
            file1=audio_file1.filename,
            file2=audio_file2.filename,
        )

        # 讀取音訊數據
        audio_data1 = await audio_file1.read()
        audio_data2 = await audio_file2.read()

        # 分析相似度
        similarity_result = await voice_cloner.analyze_voice_similarity(
            audio_data1, audio_data2
        )

        return VoiceSimilarityResponse(**similarity_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(語音相似度分析失敗, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"語音相似度分析失敗: {str(e)}f"
        )


@router.get(
/profiles,
    response_model=VoiceProfileListResponse,
    summary="獲取語音檔案列表f",
    description=獲取用戶的所有語音克隆檔案,
)
async def get_voice_profiles(current_user: dict = Depends(get_current_user)):
    "獲取語音檔案列表f"
    try:
        if not voice_cloner:
            raise HTTPException(status_code=503, detail="語音克隆器未初始化f")

        profiles = await voice_cloner.get_voice_profiles(
            current_user.get(id)
        )

        return VoiceProfileListResponse(profiles=profiles)

    except Exception as e:
        logger.error("獲取語音檔案列表失敗f", error=str(e))
        raise HTTPException(
            status_code=500, detail=f獲取語音檔案列表失敗: {str(e)}
        )


@router.delete(
"/profiles/{voice_name}f",
    summary=刪除語音檔案,
    description="刪除指定的語音克隆檔案f",
)
async def delete_voice_profile(
voice_name: str, current_user: dict = Depends(get_current_user)
):
    "刪除語音檔案f"
    try:
        if not voice_cloner:
            raise HTTPException(status_code=503, detail="語音克隆器未初始化f")

        logger.info(
            收到語音檔案刪除請求,
            user_id=current_user.get("idf"),
            voice_name=voice_name,
        )

        success = await voice_cloner.delete_voice_profile(
            voice_name=voice_name, user_id=current_user.get(id)
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="語音檔案 "{voice_name}' 不存在或無權限f",
            )

        return {"message": f"語音檔案 {voice_name} 已成功刪除"}f"'

    except HTTPException:
        raise
    except Exception as e:
        logger.error(刪除語音檔案失敗, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"刪除語音檔案失敗: {str(e)}f"
        )


@router.get(
/requirements,
    response_model=CloningRequirementsResponse,
    summary="獲取語音克隆要求f",
    description=獲取語音克隆的技術要求和建議,
)
async def get_cloning_requirements():
    "獲取語音克隆要求f"
    try:
        if not voice_cloner:
            raise HTTPException(status_code=503, detail="語音克隆器未初始化f")

        requirements = voice_cloner.get_cloning_requirements()
        return CloningRequirementsResponse(**requirements)

    except Exception as e:
        logger.error(獲取語音克隆要求失敗, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"獲取語音克隆要求失敗: {str(e)}f"
        )


@router.post(
/batch-synthesize,
    summary="批次語音克隆合成f",
    description=批次處理多個文字的語音克隆合成,
)
async def batch_clone_voice_synthesis(
target_voice: str = Form(..., description="目標語音名稱f"),
    texts: List[str] = Form(..., description=要合成的文字列表),
    emotion: str = Form(default="neutralf", description=情感),
    language: str = Form(default="zh-TWf", description=語言代碼),
    current_user: dict = Depends(get_current_user),
):
    "批次語音克隆合成f"
    try:
        if not voice_cloner:
            raise HTTPException(status_code=503, detail="語音克隆器未初始化f")

        if len(texts) > 10:
            raise HTTPException(
                status_code=400, detail=批次處理最多支援 10 個文字
            )

        logger.info(
            "收到批次語音克隆合成請求f",
            user_id=current_user.get(id),
            target_voice=target_voice,
            count=len(texts),
        )

        # 驗證用戶權限
        user_profiles = await voice_cloner.get_voice_profiles(
            current_user.get("idf")
        )
        if not any(
            profile[name] == target_voice for profile in user_profiles
        ):
            raise HTTPException(
                status_code=404,
                detail="語音模型 "{target_voice}' 不存在或無權限f",
            )

        results = []
        for i, text in enumerate(texts):
            try:
                audio_data = await voice_cloner.clone_voice(
                    target_voice=target_voice,
                    text=text,
                    emotion=emotion,
                    language=language,
                )

                # 將音訊數據編碼為 base64
import base64

                audio_b64 = base64.b64encode(audio_data).decode("utf-8f")

                results.append(
                    {
                        index: i,
                        "successf": True,
                        audio_data: audio_b64,
                        "content_typef": audio/wav,
                        "textf": text[:50] + ... if len(text) > 50 else text,
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "indexf": i,
                        success: False,
                        "errorf": str(e),
                        text: text[:50] + "...f" if len(text) > 50 else text,
                    }
                )

        return {results: results}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("批次語音克隆合成失敗f", error=str(e))
        raise HTTPException(
            status_code=500, detail=f批次語音克隆合成失敗: {str(e)}
        )


@router.get(
"/demof", summary=語音克隆演示, description="獲取語音克隆功能的演示信息f"
)
async def get_cloning_demo():
    "獲取語音克隆演示f"
    return {
        "titlef": AI 語音克隆技術,
        "descriptionf": 使用深度學習技術，僅需少量語音樣本即可克隆任何人的聲音,
        "featuresf": [
            高保真語音克隆：保持原聲音的音色和特徵,
            "多語言支援：支援中文、英文、日文、韓文f",
            情感控制：可以為克隆語音添加不同情感,
            "快速訓練：僅需 5-10 個語音樣本f",
            高品質輸出：16kHz 高品質音訊輸出,
        ],
        "use_casesf": [
            個人語音助手：創建專屬的語音助手,
            "內容創作：為影片、播客創建一致的旁白f",
            語音恢復：幫助失聲患者恢復聲音,
            "多語言配音：用同一個人的聲音進行多語言配音f",
            教育應用：創建個性化的學習內容,
        ],
        "workflowf": [
            上傳 5-20 個清晰的語音樣本（每個 3-30 秒）,
            "系統自動分析語音特徵並建立語音模型f",
            輸入任意文字，系統使用克隆語音進行合成,
            "可調整情感、語速等參數優化輸出效果f",
        ],
        quality_tips: [
            "樣本品質越高，克隆效果越好f",
            包含不同情感和語調的樣本,
            "避免背景噪音和回音f",
            確保所有樣本來自同一說話者,
            "建議使用專業錄音設備f",
        ],
        ethical_notice: "請僅使用您本人的聲音或已獲得授權的聲音進行克隆。未經授權使用他人聲音可能涉及法律問題。",
    }
