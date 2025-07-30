# 語音克隆測試數據工廠
# 遵循 TDD 原則的語音數據生成

import factory
from faker import Faker
from datetime import datetime, timezone
from typing import Dict, Any, List
from enum import Enum

from .base_factory import (
    BaseFactory, 
    TDDFactoryMixin, 
    CommonFieldsMixin,
    register_factory
)

fake = Faker(['zh_TW', 'en_US'])

class VoiceGender(Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"

class VoiceLanguage(Enum):
    ZH_TW = "zh-TW"
    ZH_CN = "zh-CN"
    EN_US = "en-US"
    EN_GB = "en-GB"
    JA_JP = "ja-JP"
    KO_KR = "ko-KR"

class VoiceStatus(Enum):
    TRAINING = "training"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"

class VoiceCloneData:
    """語音克隆數據類別"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

@register_factory('voice_clone')
class VoiceCloneFactory(factory.Factory, TDDFactoryMixin, CommonFieldsMixin):
    """
    語音克隆工廠
    為 TDD 測試提供各種語音克隆數據情境
    """
    
    class Meta:
        model = VoiceCloneData
    
    # 基本欄位
    name = factory.LazyAttribute(lambda o: fake.name())
    description = factory.LazyAttribute(lambda o: fake.text(max_nb_chars=200))
    
    # 關聯欄位
    user_id = factory.LazyFunction(lambda: fake.uuid4())
    
    # 語音屬性
    gender = factory.LazyAttribute(lambda o: fake.random_element([
        VoiceGender.MALE.value,
        VoiceGender.FEMALE.value
    ]))
    
    language = factory.LazyAttribute(lambda o: fake.random_element([
        VoiceLanguage.ZH_TW.value,
        VoiceLanguage.EN_US.value
    ]))
    
    accent = factory.LazyAttribute(lambda o: fake.random_element([
        'standard', 'northern', 'southern', 'american', 'british'
    ]))
    
    # 音色特徵
    pitch_range = factory.LazyAttribute(lambda o: {
        'min': fake.random.uniform(80, 150),
        'max': fake.random.uniform(200, 300),
        'average': fake.random.uniform(120, 250)
    })
    
    tone_characteristics = factory.LazyAttribute(lambda o: fake.random_element([
        'warm', 'professional', 'friendly', 'authoritative', 'calm', 'energetic'
    ]))
    
    speaking_rate = factory.LazyFunction(lambda: fake.random.uniform(0.8, 1.3))  # 相對於標準語速
    
    # 訓練資料
    training_audio_files = factory.LazyAttribute(lambda o: [
        f"/audio/training/{o.id}/sample_{i}.wav" 
        for i in range(fake.random_int(5, 20))
    ])
    
    total_training_duration = factory.LazyFunction(lambda: fake.random_int(300, 3600))  # 秒
    training_quality_score = factory.LazyFunction(lambda: fake.random.uniform(7.0, 9.5))
    
    # 模型資訊
    model_file_path = factory.LazyAttribute(
        lambda o: f"/models/voices/{o.id}/voice_model.pt"
    )
    model_size = factory.LazyFunction(lambda: fake.random_int(50*1024*1024, 500*1024*1024))  # bytes
    model_version = factory.LazyFunction(lambda: fake.random.uniform(1.0, 3.0))
    
    # 狀態和進度
    status = factory.LazyAttribute(lambda o: fake.random_element([
        VoiceStatus.READY.value,
        VoiceStatus.TRAINING.value
    ]))
    
    training_progress = factory.LazyFunction(lambda: fake.random_int(0, 100))
    training_started_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    training_completed_at = None
    
    # 品質指標
    similarity_score = factory.LazyFunction(lambda: fake.random.uniform(0.8, 0.95))  # 與原聲相似度
    naturalness_score = factory.LazyFunction(lambda: fake.random.uniform(0.7, 0.9))  # 自然度
    clarity_score = factory.LazyFunction(lambda: fake.random.uniform(0.8, 0.95))  # 清晰度
    
    # 使用統計
    usage_count = factory.LazyFunction(lambda: fake.random_int(0, 100))
    last_used_at = None
    
    # 錯誤資訊
    error_message = None
    
    # 原始聲音來源資訊
    source_speaker_name = factory.LazyAttribute(lambda o: fake.name())
    source_description = factory.LazyAttribute(lambda o: fake.text(max_nb_chars=100))
    consent_verified = True
    
    # 標籤和分類
    tags = factory.LazyAttribute(lambda o: [
        fake.word() for _ in range(fake.random_int(2, 5))
    ])
    
    category = factory.LazyAttribute(lambda o: fake.random_element([
        'personal', 'commercial', 'character', 'narrator', 'celebrity'
    ]))
    
    # 隱私和授權
    is_public = factory.LazyFunction(lambda: fake.boolean())
    is_commercial_use_allowed = factory.LazyFunction(lambda: fake.boolean())
    license_type = factory.LazyAttribute(lambda o: fake.random_element([
        'personal', 'commercial', 'educational', 'research'
    ]))

    @classmethod
    def create_male_voice(cls, **kwargs):
        """建立男聲語音克隆"""
        return cls.create(
            gender=VoiceGender.MALE.value,
            pitch_range={
                'min': fake.random.uniform(80, 120),
                'max': fake.random.uniform(150, 200),
                'average': fake.random.uniform(100, 160)
            },
            **kwargs
        )
    
    @classmethod
    def create_female_voice(cls, **kwargs):
        """建立女聲語音克隆"""
        return cls.create(
            gender=VoiceGender.FEMALE.value,
            pitch_range={
                'min': fake.random.uniform(150, 200),
                'max': fake.random.uniform(250, 350),
                'average': fake.random.uniform(180, 280)
            },
            **kwargs
        )
    
    @classmethod
    def create_training_voice(cls, **kwargs):
        """建立正在訓練的語音克隆"""
        return cls.create(
            status=VoiceStatus.TRAINING.value,
            training_progress=fake.random_int(10, 90),
            training_completed_at=None,
            model_file_path=None,
            **kwargs
        )
    
    @classmethod
    def create_ready_voice(cls, **kwargs):
        """建立已完成訓練的語音克隆"""
        return cls.create(
            status=VoiceStatus.READY.value,
            training_progress=100,
            training_completed_at=datetime.now(timezone.utc),
            similarity_score=fake.random.uniform(0.85, 0.95),
            naturalness_score=fake.random.uniform(0.8, 0.9),
            **kwargs
        )
    
    @classmethod
    def create_failed_voice(cls, **kwargs):
        """建立訓練失敗的語音克隆"""
        return cls.create(
            status=VoiceStatus.FAILED.value,
            training_progress=fake.random_int(5, 70),
            error_message="訓練數據品質不足，無法完成模型訓練",
            model_file_path=None,
            **kwargs
        )
    
    @classmethod
    def create_high_quality_voice(cls, **kwargs):
        """建立高品質語音克隆"""
        return cls.create(
            status=VoiceStatus.READY.value,
            training_quality_score=fake.random.uniform(8.5, 9.5),
            similarity_score=fake.random.uniform(0.9, 0.95),
            naturalness_score=fake.random.uniform(0.85, 0.9),
            clarity_score=fake.random.uniform(0.9, 0.95),
            total_training_duration=fake.random_int(1800, 3600),  # 30-60分鐘
            **kwargs
        )
    
    @classmethod
    def create_for_red_phase(cls, **kwargs):
        """RED 階段：建立會導致測試失敗的語音克隆數據"""
        return cls.create(
            name="",  # 無效：空名稱
            total_training_duration=-1,  # 無效：負數時長
            similarity_score=2.0,  # 無效：超出範圍的分數
            training_audio_files=[],  # 無效：沒有訓練音檔
            **kwargs
        )
    
    @classmethod
    def create_for_green_phase(cls, **kwargs):
        """GREEN 階段：建立讓測試通過的最簡語音克隆數據"""
        return cls.create(
            name="測試語音",
            status=VoiceStatus.READY.value,
            training_progress=100,
            **kwargs
        )

@register_factory('create_voice_clone')
class CreateVoiceCloneFactory(factory.Factory, TDDFactoryMixin):
    """
    建立語音克隆請求數據工廠
    模擬 API 請求中的語音克隆建立數據
    """
    
    class Meta:
        model = dict
    
    name = factory.LazyAttribute(lambda o: fake.name())
    description = factory.LazyAttribute(lambda o: fake.text(max_nb_chars=150))
    
    # 聲音屬性
    gender = VoiceGender.FEMALE.value
    language = VoiceLanguage.ZH_TW.value
    tone_characteristics = "friendly"
    
    # 訓練設定
    training_audio_files = factory.LazyAttribute(lambda o: [
        f"audio_sample_{i}.wav" for i in range(10)
    ])
    
    # 授權設定
    consent_verified = True
    is_commercial_use_allowed = False
    license_type = "personal"
    
    @classmethod
    def create_invalid_request(cls, **kwargs):
        """建立無效的語音克隆建立請求"""
        return cls.build(
            name="",  # 無效：空名稱
            training_audio_files=[],  # 無效：沒有訓練檔案
            consent_verified=False,  # 無效：未驗證授權
            **kwargs
        )
    
    @classmethod
    def create_minimal_valid_request(cls, **kwargs):
        """建立最簡有效的語音克隆建立請求"""
        return cls.build(
            name="簡單測試語音",
            training_audio_files=["test_sample.wav"],
            consent_verified=True,
            **kwargs
        )

class VoiceBatchFactory:
    """語音克隆批次建立工廠"""
    
    @staticmethod
    def create_user_voices(user_id: str, count: int = 3) -> List[VoiceCloneData]:
        """為特定用戶建立多個語音克隆"""
        voices = []
        for i in range(count):
            voice = VoiceCloneFactory.create_ready_voice(
                user_id=user_id,
                name=f"用戶語音 {i+1}"
            )
            voices.append(voice)
        return voices
    
    @staticmethod
    def create_mixed_gender_voices() -> Dict[str, VoiceCloneData]:
        """建立不同性別的語音克隆"""
        return {
            'male': VoiceCloneFactory.create_male_voice(),
            'female': VoiceCloneFactory.create_female_voice()
        }

# TDD 輔助函數
def create_test_voices_scenario(user_id: str = None) -> Dict[str, VoiceCloneData]:
    """
    建立完整的測試語音克隆情境
    用於複雜的 TDD 測試場景
    """
    test_user_id = user_id or fake.uuid4()
    
    return {
        'training_voice': VoiceCloneFactory.create_training_voice(user_id=test_user_id),
        'ready_voice': VoiceCloneFactory.create_ready_voice(user_id=test_user_id),
        'failed_voice': VoiceCloneFactory.create_failed_voice(user_id=test_user_id),
        'male_voice': VoiceCloneFactory.create_male_voice(user_id=test_user_id),
        'female_voice': VoiceCloneFactory.create_female_voice(user_id=test_user_id),
        'high_quality_voice': VoiceCloneFactory.create_high_quality_voice(user_id=test_user_id),
        'invalid_voice': VoiceCloneFactory.create_for_red_phase(),
        'valid_voice': VoiceCloneFactory.create_for_green_phase()
    }

def create_voice_training_sequence(base_voice: VoiceCloneData) -> List[VoiceCloneData]:
    """
    建立語音訓練進度序列
    用於測試訓練過程
    """
    sequences = []
    for progress in [25, 50, 75, 100]:
        voice_snapshot = VoiceCloneFactory.create(
            id=base_voice.id,
            name=base_voice.name,
            user_id=base_voice.user_id,
            status=VoiceStatus.TRAINING.value if progress < 100 else VoiceStatus.READY.value,
            training_progress=progress
        )
        sequences.append(voice_snapshot)
    return sequences

def cleanup_test_voices(voices: Dict[str, VoiceCloneData]):
    """
    清理測試語音克隆數據
    在測試完成後呼叫
    """
    # 清理語音模型檔案和數據庫記錄
    pass