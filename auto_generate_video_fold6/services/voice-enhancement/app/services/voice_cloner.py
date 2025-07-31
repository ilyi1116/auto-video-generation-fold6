"""
Voice Cloning Service
實現高品質語音克隆功能，可以模仿特定人物的聲音特徵
"""

import io
import os
import numpy as np
import torch
from typing import Dict, List, Optional, Tuple
import structlog
from resemblyzer import VoiceEncoder, preprocess_wav
from encoder import inference as encoder_inference
from encoder.params_model import model_embedding_size as speaker_embedding_size
import librosa
import soundfile as sf
from pathlib import Path
import pickle

logger = structlog.get_logger()


class VoiceCloner:
    """語音克隆器"""

    def __init__(self):
        self.voice_encoder = None
        self.speaker_embeddings = {}  # 儲存說話者嵌入
        self.cloned_voices = {}  # 儲存已克隆的語音模型
        self.min_samples_for_cloning = 5  # 最少需要的語音樣本數
        self.max_sample_duration = 30  # 最大樣本長度（秒）

    async def initialize(self):
        """初始化語音克隆器"""
        try:
            logger.info("初始化語音克隆器")

            # 載入語音編碼器
            self.voice_encoder = VoiceEncoder()

            # 檢查已存在的語音模型
            await self._load_existing_voices()

            logger.info("語音克隆器初始化完成")

        except Exception as e:
            logger.error("語音克隆器初始化失敗", error=str(e))
            raise

    async def _load_existing_voices(self):
        """載入已存在的語音模型"""
        try:
            voices_dir = Path("voices")
            if voices_dir.exists():
                for voice_file in voices_dir.glob("*.pkl"):
                    voice_name = voice_file.stem
                    with open(voice_file, "rb") as f:
                        voice_data = pickle.load(f)
                        self.cloned_voices[voice_name] = voice_data
                    logger.info(f"已載入語音模型: {voice_name}")
        except Exception as e:
            logger.warning("載入已存在語音模型失敗", error=str(e))

    async def create_voice_profile(
        self, voice_name: str, audio_samples: List[bytes], user_id: str
    ) -> Dict:
        """
        創建語音檔案

        Args:
            voice_name: 語音模型名稱
            audio_samples: 語音樣本列表
            user_id: 用戶 ID

        Returns:
            創建結果
        """
        try:
            logger.info(
                "開始創建語音檔案",
                voice_name=voice_name,
                samples_count=len(audio_samples),
            )

            # 驗證樣本數量
            if len(audio_samples) < self.min_samples_for_cloning:
                raise ValueError(
                    f"至少需要 {self.min_samples_for_cloning} 個語音樣本"
                )

            # 處理音訊樣本
            processed_samples = []
            embeddings = []

            for i, audio_data in enumerate(audio_samples):
                try:
                    # 預處理音訊
                    processed_audio = await self._preprocess_audio(audio_data)
                    processed_samples.append(processed_audio)

                    # 提取語音嵌入
                    embedding = self._extract_voice_embedding(processed_audio)
                    embeddings.append(embedding)

                    logger.info(f"處理樣本 {i+1}/{len(audio_samples)} 完成")

                except Exception as e:
                    logger.warning(f"處理樣本 {i+1} 失敗", error=str(e))
                    continue

            if len(embeddings) < self.min_samples_for_cloning:
                raise ValueError("可用的語音樣本不足")

            # 計算平均嵌入向量
            mean_embedding = np.mean(embeddings, axis=0)

            # 計算嵌入一致性
            consistency = self._calculate_embedding_consistency(embeddings)

            # 創建語音檔案
            voice_profile = {
                "name": voice_name,
                "user_id": user_id,
                "embedding": mean_embedding,
                "consistency": consistency,
                "sample_count": len(embeddings),
                "quality_score": self._calculate_quality_score(
                    embeddings, processed_samples
                ),
                "created_at": np.datetime64("now").astype(str),
            }

            # 儲存語音檔案
            await self._save_voice_profile(voice_name, voice_profile)

            self.cloned_voices[voice_name] = voice_profile

            logger.info(
                "語音檔案創建完成",
                voice_name=voice_name,
                quality_score=voice_profile["quality_score"],
            )

            return {
                "voice_name": voice_name,
                "quality_score": voice_profile["quality_score"],
                "consistency": consistency,
                "sample_count": len(embeddings),
                "status": "success",
            }

        except Exception as e:
            logger.error("語音檔案創建失敗", error=str(e))
            raise

    async def _preprocess_audio(self, audio_data: bytes) -> np.ndarray:
        """預處理音訊數據"""
        # 將 bytes 轉換為 numpy array
        audio_array, sample_rate = sf.read(io.BytesIO(audio_data))

        # 轉換為單聲道
        if len(audio_array.shape) > 1:
            audio_array = np.mean(audio_array, axis=1)

        # 重採樣到 16kHz（Resemblyzer 要求）
        if sample_rate != 16000:
            audio_array = librosa.resample(
                audio_array, orig_sr=sample_rate, target_sr=16000
            )

        # 正規化音量
        audio_array = audio_array / np.max(np.abs(audio_array))

        # 使用 Resemblyzer 預處理
        processed_audio = preprocess_wav(audio_array, source_sr=16000)

        return processed_audio

    def _extract_voice_embedding(self, audio: np.ndarray) -> np.ndarray:
        """提取語音嵌入向量"""
        if self.voice_encoder is None:
            raise RuntimeError("語音編碼器未初始化")

        # 使用 Resemblyzer 提取嵌入
        embedding = self.voice_encoder.embed_utterance(audio)
        return embedding

    def _calculate_embedding_consistency(
        self, embeddings: List[np.ndarray]
    ) -> float:
        """計算嵌入向量的一致性"""
        if len(embeddings) < 2:
            return 1.0

        # 計算所有嵌入向量間的餘弦相似度
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i])
                    * np.linalg.norm(embeddings[j])
                )
                similarities.append(sim)

        return float(np.mean(similarities))

    def _calculate_quality_score(
        self, embeddings: List[np.ndarray], audio_samples: List[np.ndarray]
    ) -> float:
        """計算語音品質分數"""
        scores = []

        # 嵌入一致性分數
        consistency = self._calculate_embedding_consistency(embeddings)
        scores.append(consistency * 0.4)

        # 音訊品質分數
        audio_quality = 0
        for audio in audio_samples:
            # 信噪比估算
            signal_power = np.mean(audio**2)
            noise_floor = np.percentile(np.abs(audio), 10) ** 2
            snr = 10 * np.log10(signal_power / (noise_floor + 1e-10))
            audio_quality += min(snr / 30, 1.0)  # 正規化到 0-1

        scores.append((audio_quality / len(audio_samples)) * 0.3)

        # 樣本數量分數
        sample_score = min(len(embeddings) / 10, 1.0)
        scores.append(sample_score * 0.3)

        return float(sum(scores))

    async def _save_voice_profile(self, voice_name: str, voice_profile: Dict):
        """儲存語音檔案"""
        voices_dir = Path("voices")
        voices_dir.mkdir(exist_ok=True)

        voice_file = voices_dir / f"{voice_name}.pkl"
        with open(voice_file, "wb") as f:
            pickle.dump(voice_profile, f)

    async def clone_voice(
        self,
        target_voice: str,
        text: str,
        emotion: str = "neutral",
        language: str = "zh-TW",
    ) -> bytes:
        """
        使用指定語音克隆合成語音

        Args:
            target_voice: 目標語音名稱
            text: 要合成的文字
            emotion: 情感
            language: 語言

        Returns:
            合成的音訊數據
        """
        try:
            logger.info(
                "開始語音克隆合成", target_voice=target_voice, text=text[:50]
            )

            # 檢查語音模型是否存在
            if target_voice not in self.cloned_voices:
                raise ValueError(f"語音模型 '{target_voice}' 不存在")

            voice_profile = self.cloned_voices[target_voice]
            target_embedding = voice_profile["embedding"]

            # 這裡需要整合實際的語音合成模型
            # 由於這是示例實現，我們使用基礎的 TTS 並嘗試調整音色
            synthesized_audio = await self._synthesize_with_voice_transfer(
                text=text,
                target_embedding=target_embedding,
                emotion=emotion,
                language=language,
            )

            logger.info("語音克隆合成完成")
            return synthesized_audio

        except Exception as e:
            logger.error("語音克隆合成失敗", error=str(e))
            raise

    async def _synthesize_with_voice_transfer(
        self,
        text: str,
        target_embedding: np.ndarray,
        emotion: str,
        language: str,
    ) -> bytes:
        """使用語音轉換進行合成"""
        # 這是一個簡化的實現
        # 實際應用中需要整合如 Real-Time Voice Cloning 或 SV2TTS 等模型

        try:
            # 1. 首先使用標準 TTS 生成基礎語音
            from .emotion_synthesizer import EmotionSynthesizer

            emotion_synth = EmotionSynthesizer()
            await emotion_synth.initialize()

            base_audio = await emotion_synth.synthesize_with_emotion(
                text=text, emotion=emotion, language=language
            )

            # 2. 應用語音轉換（簡化實現）
            # 實際應用中這裡會使用更複雜的語音轉換模型
            enhanced_audio = await self._apply_voice_conversion(
                base_audio, target_embedding
            )

            return enhanced_audio

        except Exception as e:
            logger.error("語音轉換失敗", error=str(e))
            # 回退到基礎合成
            return base_audio

    async def _apply_voice_conversion(
        self, audio_data: bytes, target_embedding: np.ndarray
    ) -> bytes:
        """應用語音轉換（簡化實現）"""
        # 這是一個基礎實現，實際應用中需要使用專業的語音轉換模型

        # 將 bytes 轉換為音訊數組
        audio_array, sample_rate = sf.read(io.BytesIO(audio_data))

        # 簡單的音色調整（實際實現會更複雜）
        # 這裡只做基礎的音調和共振峰調整

        # 基於嵌入向量調整音調
        pitch_shift = self._embedding_to_pitch_shift(target_embedding)
        if abs(pitch_shift) > 0.1:
            audio_array = librosa.effects.pitch_shift(
                audio_array, sr=sample_rate, n_steps=pitch_shift
            )

        # 調整共振峰（簡化實現）
        formant_shift = self._embedding_to_formant_shift(target_embedding)
        if abs(formant_shift) > 0.1:
            audio_array = self._adjust_formants(audio_array, formant_shift)

        # 轉換回 bytes
        with io.BytesIO() as output:
            sf.write(output, audio_array, sample_rate, format="WAV")
            return output.getvalue()

    def _embedding_to_pitch_shift(self, embedding: np.ndarray) -> float:
        """將嵌入向量轉換為音調偏移"""
        # 簡化實現：使用嵌入向量的某些維度來決定音調
        pitch_components = embedding[:10]  # 使用前10個維度
        pitch_shift = np.mean(pitch_components) * 12  # 轉換為半音
        return float(np.clip(pitch_shift, -6, 6))  # 限制在合理範圍

    def _embedding_to_formant_shift(self, embedding: np.ndarray) -> float:
        """將嵌入向量轉換為共振峰偏移"""
        # 簡化實現：使用嵌入向量的其他維度來決定共振峰
        formant_components = embedding[10:20]  # 使用10-20維度
        formant_shift = np.mean(formant_components) * 2
        return float(np.clip(formant_shift, -1, 1))

    def _adjust_formants(self, audio: np.ndarray, shift: float) -> np.ndarray:
        """調整共振峰（簡化實現）"""
        # 這是一個非常簡化的共振峰調整
        # 實際實現需要使用專業的語音處理算法

        if abs(shift) < 0.1:
            return audio

        # 使用簡單的頻譜移位來模擬共振峰變化
        stft = librosa.stft(audio)
        stft_shifted = np.roll(stft, int(shift * 10), axis=0)
        audio_shifted = librosa.istft(stft_shifted, length=len(audio))

        return audio_shifted

    async def analyze_voice_similarity(
        self, voice1_data: bytes, voice2_data: bytes
    ) -> Dict:
        """分析兩個語音的相似度"""
        try:
            # 預處理音訊
            audio1 = await self._preprocess_audio(voice1_data)
            audio2 = await self._preprocess_audio(voice2_data)

            # 提取嵌入
            embedding1 = self._extract_voice_embedding(audio1)
            embedding2 = self._extract_voice_embedding(audio2)

            # 計算相似度
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )

            return {
                "similarity": float(similarity),
                "is_same_speaker": similarity > 0.75,
                "confidence": float(abs(similarity - 0.5) * 2),
            }

        except Exception as e:
            logger.error("語音相似度分析失敗", error=str(e))
            raise

    async def get_voice_profiles(self, user_id: str) -> List[Dict]:
        """獲取用戶的語音檔案列表"""
        profiles = []
        for name, profile in self.cloned_voices.items():
            if profile.get("user_id") == user_id:
                profiles.append(
                    {
                        "name": name,
                        "quality_score": profile["quality_score"],
                        "consistency": profile["consistency"],
                        "sample_count": profile["sample_count"],
                        "created_at": profile["created_at"],
                    }
                )
        return profiles

    async def delete_voice_profile(
        self, voice_name: str, user_id: str
    ) -> bool:
        """刪除語音檔案"""
        try:
            if voice_name not in self.cloned_voices:
                return False

            profile = self.cloned_voices[voice_name]
            if profile.get("user_id") != user_id:
                return False

            # 刪除檔案
            voice_file = Path("voices") / f"{voice_name}.pkl"
            if voice_file.exists():
                voice_file.unlink()

            # 從記憶體中移除
            del self.cloned_voices[voice_name]

            logger.info("語音檔案已刪除", voice_name=voice_name)
            return True

        except Exception as e:
            logger.error("刪除語音檔案失敗", error=str(e))
            return False

    def get_cloning_requirements(self) -> Dict:
        """獲取語音克隆要求"""
        return {
            "min_samples": self.min_samples_for_cloning,
            "max_sample_duration": self.max_sample_duration,
            "recommended_samples": 10,
            "audio_format": ["wav", "mp3", "m4a"],
            "sample_rate": "16kHz",
            "requirements": [
                "清晰的語音，無背景噪音",
                "每個樣本 3-30 秒",
                "涵蓋不同情感和語調",
                "相同說話者的聲音",
                "高品質音訊（無壓縮失真）",
            ],
        }
