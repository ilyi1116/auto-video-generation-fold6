"""
Emotion-aware Speech Synthesis
實現具有情感表達能力的語音合成
"""

import io
import numpy as np
import torch
from typing import Dict, List, Optional, Tuple
import structlog
from TTS.api import TTS
from speechemotionrecognition import SpeechEmotionRecognition
import librosa
import soundfile as sf
from transformers import Wav2Vec2Processor, Wav2Vec2Model

logger = structlog.get_logger()


class EmotionSynthesizer:
    """情感語音合成器"""

    def __init__(self):
        self.tts_models = {}
        self.emotion_classifier = None
        self.emotion_embedder = None
        self.supported_emotions = [
            "neutral",
            "happy",
            "sad",
            "angry",
            "fear",
            "surprise",
            "disgust",
            "excited",
            "calm",
            "confident",
        ]
        self.supported_languages = [
            "zh-CN",
            "zh-TW",
            "en-US",
            "ja-JP",
            "ko-KR",
        ]

    async def initialize(self):
        """初始化模型"""
        try:
            logger.info("初始化情感語音合成器")

            # 載入 TTS 模型
            await self._load_tts_models()

            # 載入情感分類器
            await self._load_emotion_classifier()

            # 載入情感嵌入模型
            await self._load_emotion_embedder()

            logger.info("情感語音合成器初始化完成")

        except Exception as e:
            logger.error("情感語音合成器初始化失敗", error=str(e))
            raise

    async def _load_tts_models(self):
        """載入 TTS 模型"""
        models_config = {
            "zh-CN": "tts_models/zh-CN/baker/tacotron2-DDC-GST",
            "zh-TW": "tts_models/zh-CN/baker/tacotron2-DDC-GST",  # 使用中文模型
            "en-US": "tts_models/en/ljspeech/tacotron2-DDC",
            "ja-JP": "tts_models/ja/kokoro/tacotron2-DDC",
            "ko-KR": "tts_models/ko/kss/tacotron2-DDC",
        }

        for lang, model_name in models_config.items():
            try:
                self.tts_models[lang] = TTS(model_name)
                logger.info(f"已載入 {lang} TTS 模型")
            except Exception as e:
                logger.warning(f"無法載入 {lang} TTS 模型", error=str(e))

    async def _load_emotion_classifier(self):
        """載入情感分類器"""
        try:
            self.emotion_classifier = SpeechEmotionRecognition()
            logger.info("已載入情感分類器")
        except Exception as e:
            logger.warning("無法載入情感分類器", error=str(e))

    async def _load_emotion_embedder(self):
        """載入情感嵌入模型"""
        try:
            self.emotion_processor = Wav2Vec2Processor.from_pretrained(
                "facebook/wav2vec2-base-960h"
            )
            self.emotion_model = Wav2Vec2Model.from_pretrained(
                "facebook/wav2vec2-base-960h"
            )
            logger.info("已載入情感嵌入模型")
        except Exception as e:
            logger.warning("無法載入情感嵌入模型", error=str(e))

    async def synthesize_with_emotion(
        self,
        text: str,
        emotion: str = "neutral",
        intensity: float = 1.0,
        language: str = "zh-TW",
        voice_speed: float = 1.0,
        voice_pitch: float = 1.0,
    ) -> bytes:
        """
        合成具有情感的語音

        Args:
            text: 要合成的文字
            emotion: 目標情感
            intensity: 情感強度 (0.0-2.0)
            language: 語言代碼
            voice_speed: 語音速度
            voice_pitch: 語音音調

        Returns:
            合成的音訊數據 (bytes)
        """
        try:
            logger.info(
                "開始情感語音合成",
                text=text[:50],
                emotion=emotion,
                language=language,
            )

            # 驗證參數
            if emotion not in self.supported_emotions:
                emotion = "neutral"

            if language not in self.supported_languages:
                language = "zh-TW"

            # 根據情感調整文字
            enhanced_text = self._enhance_text_for_emotion(
                text, emotion, intensity
            )

            # 選擇合適的 TTS 模型
            tts_model = self.tts_models.get(language)
            if not tts_model:
                # 使用默認模型
                tts_model = next(iter(self.tts_models.values()))

            # 生成基礎語音
            with io.BytesIO() as audio_buffer:
                tts_model.tts_to_file(
                    text=enhanced_text,
                    file_path=audio_buffer,
                    emotion=(
                        emotion if hasattr(tts_model, "emotions") else None
                    ),
                )
                base_audio = audio_buffer.getvalue()

            # 應用情感後處理
            enhanced_audio = await self._apply_emotion_processing(
                base_audio, emotion, intensity, voice_speed, voice_pitch
            )

            logger.info("情感語音合成完成")
            return enhanced_audio

        except Exception as e:
            logger.error("情感語音合成失敗", error=str(e))
            raise

    def _enhance_text_for_emotion(
        self, text: str, emotion: str, intensity: float
    ) -> str:
        """根據情感增強文字"""

        # 情感標記映射
        emotion_markers = {
            "happy": ["😊", "！", "哈哈"],
            "sad": ["😢", "...", "唉"],
            "angry": ["😠", "！！", "哼"],
            "excited": ["😆", "！！！", "哇"],
            "calm": ["😌", "。", "嗯"],
            "surprised": ["😲", "？！", "哇"],
        }

        # 根據情感強度調整
        if intensity > 1.5:
            # 高強度：增加情感標記
            markers = emotion_markers.get(emotion, [])
            if markers:
                text = f"{markers[0]} {text} {markers[1]}"
        elif intensity > 1.0:
            # 中強度：輕微調整
            if emotion == "happy":
                text = text.replace("。", "！")
            elif emotion == "sad":
                text = text.replace("！", "...")

        return text

    async def _apply_emotion_processing(
        self,
        audio_data: bytes,
        emotion: str,
        intensity: float,
        speed: float,
        pitch: float,
    ) -> bytes:
        """應用情感後處理"""

        # 將 bytes 轉換為 numpy array
        audio_array, sample_rate = sf.read(io.BytesIO(audio_data))

        # 根據情感調整音訊特性
        emotion_params = self._get_emotion_parameters(emotion, intensity)

        # 調整音調
        pitch_factor = pitch * emotion_params.get("pitch_factor", 1.0)
        if pitch_factor != 1.0:
            audio_array = librosa.effects.pitch_shift(
                audio_array, sr=sample_rate, n_steps=pitch_factor * 12
            )

        # 調整語速
        speed_factor = speed * emotion_params.get("speed_factor", 1.0)
        if speed_factor != 1.0:
            audio_array = librosa.effects.time_stretch(
                audio_array, rate=speed_factor
            )

        # 調整音量
        volume_factor = emotion_params.get("volume_factor", 1.0)
        audio_array = audio_array * volume_factor

        # 添加情感相關的音訊效果
        audio_array = self._apply_emotion_effects(
            audio_array, emotion, intensity
        )

        # 轉換回 bytes
        with io.BytesIO() as output:
            sf.write(output, audio_array, sample_rate, format="WAV")
            return output.getvalue()

    def _get_emotion_parameters(self, emotion: str, intensity: float) -> Dict:
        """獲取情感參數"""

        base_params = {
            "happy": {
                "pitch_factor": 1.1,
                "speed_factor": 1.05,
                "volume_factor": 1.1,
            },
            "sad": {
                "pitch_factor": 0.9,
                "speed_factor": 0.95,
                "volume_factor": 0.8,
            },
            "angry": {
                "pitch_factor": 1.15,
                "speed_factor": 1.1,
                "volume_factor": 1.3,
            },
            "excited": {
                "pitch_factor": 1.2,
                "speed_factor": 1.15,
                "volume_factor": 1.2,
            },
            "calm": {
                "pitch_factor": 0.95,
                "speed_factor": 0.9,
                "volume_factor": 0.9,
            },
            "fear": {
                "pitch_factor": 1.25,
                "speed_factor": 1.2,
                "volume_factor": 0.7,
            },
        }

        params = base_params.get(
            emotion,
            {"pitch_factor": 1.0, "speed_factor": 1.0, "volume_factor": 1.0},
        )

        # 根據強度調整參數
        for key, value in params.items():
            if key != "volume_factor":
                # 強度影響音調和速度
                diff = abs(value - 1.0)
                params[key] = 1.0 + diff * intensity
            else:
                # 音量根據情感調整
                params[key] = value * intensity

        return params

    def _apply_emotion_effects(
        self, audio: np.ndarray, emotion: str, intensity: float
    ) -> np.ndarray:
        """應用情感音訊效果"""

        if emotion == "happy" and intensity > 1.2:
            # 開心：輕微的回聲效果
            audio = self._add_echo(audio, delay=0.1, decay=0.3)

        elif emotion == "sad" and intensity > 1.0:
            # 悲傷：降低高頻
            audio = self._apply_lowpass_filter(audio)

        elif emotion == "angry" and intensity > 1.3:
            # 憤怒：輕微失真
            audio = self._add_distortion(audio, factor=0.1)

        elif emotion == "fear" and intensity > 1.1:
            # 恐懼：顫抖效果
            audio = self._add_tremolo(audio, rate=6.0, depth=0.3)

        return audio

    def _add_echo(
        self, audio: np.ndarray, delay: float, decay: float
    ) -> np.ndarray:
        """添加回聲效果"""
        delay_samples = int(delay * 22050)  # 假設 22050 Hz
        echo = np.zeros_like(audio)
        echo[delay_samples:] = audio[:-delay_samples] * decay
        return audio + echo

    def _apply_lowpass_filter(self, audio: np.ndarray) -> np.ndarray:
        """應用低通濾波器"""
        from scipy import signal

        b, a = signal.butter(4, 0.3, "low")
        return signal.filtfilt(b, a, audio)

    def _add_distortion(self, audio: np.ndarray, factor: float) -> np.ndarray:
        """添加失真效果"""
        return np.tanh(audio * (1 + factor))

    def _add_tremolo(
        self, audio: np.ndarray, rate: float, depth: float
    ) -> np.ndarray:
        """添加顫音效果"""
        t = np.arange(len(audio)) / 22050
        tremolo = 1 + depth * np.sin(2 * np.pi * rate * t)
        return audio * tremolo

    async def analyze_emotion(self, audio_data: bytes) -> Dict:
        """分析音訊中的情感"""
        try:
            if not self.emotion_classifier:
                return {"emotion": "neutral", "confidence": 0.0}

            # 將 bytes 轉換為臨時文件
            with io.NamedTemporaryFile(suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()

                # 分析情感
                emotion_result = self.emotion_classifier.predict_emotion(
                    temp_file.name
                )

                return {
                    "emotion": emotion_result.get("emotion", "neutral"),
                    "confidence": emotion_result.get("confidence", 0.0),
                    "all_emotions": emotion_result.get("all_emotions", {}),
                }

        except Exception as e:
            logger.error("情感分析失敗", error=str(e))
            return {"emotion": "neutral", "confidence": 0.0}

    async def get_voice_characteristics(self, audio_data: bytes) -> Dict:
        """分析語音特徵"""
        try:
            audio_array, sample_rate = sf.read(io.BytesIO(audio_data))

            # 基本特徵
            features = {
                "duration": len(audio_array) / sample_rate,
                "sample_rate": sample_rate,
                "amplitude": {
                    "mean": float(np.mean(np.abs(audio_array))),
                    "max": float(np.max(np.abs(audio_array))),
                    "std": float(np.std(audio_array)),
                },
            }

            # 音調特徵
            pitches, magnitudes = librosa.piptrack(
                y=audio_array, sr=sample_rate
            )
            pitch_values = pitches[magnitudes > np.median(magnitudes)]
            if len(pitch_values) > 0:
                features["pitch"] = {
                    "mean": float(np.mean(pitch_values)),
                    "std": float(np.std(pitch_values)),
                    "range": float(
                        np.max(pitch_values) - np.min(pitch_values)
                    ),
                }

            # 頻譜特徵
            mfccs = librosa.feature.mfcc(
                y=audio_array, sr=sample_rate, n_mfcc=13
            )
            features["mfcc"] = {
                "mean": mfccs.mean(axis=1).tolist(),
                "std": mfccs.std(axis=1).tolist(),
            }

            # 節奏特徵
            tempo, beats = librosa.beat.beat_track(
                y=audio_array, sr=sample_rate
            )
            features["rhythm"] = {
                "tempo": float(tempo),
                "beat_count": len(beats),
            }

            return features

        except Exception as e:
            logger.error("語音特徵分析失敗", error=str(e))
            return {}

    def get_supported_emotions(self) -> List[str]:
        """獲取支援的情感列表"""
        return self.supported_emotions.copy()

    def get_supported_languages(self) -> List[str]:
        """獲取支援的語言列表"""
        return self.supported_languages.copy()
