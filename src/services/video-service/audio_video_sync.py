#!/usr/bin/env python3
"""
智能音視頻同步系統
提供精確的音視頻同步、節拍檢測、動態對齊等功能
"""

import os
import logging
import numpy as np
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import asyncio
from pathlib import Path

try:
    from moviepy.editor import (
        VideoClip, AudioClip, AudioFileClip, CompositeAudioClip,
        concatenate_audioclips
    )
    from moviepy.audio.fx import volumex, audio_fadein, audio_fadeout, afx
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logging.warning("librosa not available. Advanced audio analysis disabled.")

try:
    from scipy import signal
    from scipy.ndimage import gaussian_filter1d
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("scipy not available. Some audio processing features disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AudioAnalysis:
    """音頻分析結果"""
    duration: float
    tempo: Optional[float]
    beats: Optional[List[float]]
    onset_frames: Optional[List[int]]
    onset_times: Optional[List[float]]
    spectral_centroid: Optional[np.ndarray]
    rms_energy: Optional[np.ndarray]
    zero_crossing_rate: Optional[np.ndarray]
    chroma: Optional[np.ndarray]
    sample_rate: int

@dataclass
class SyncPoint:
    """同步點"""
    video_time: float
    audio_time: float
    importance: float  # 0-1, 重要程度
    sync_type: str  # 'beat', 'onset', 'manual', 'automatic'

@dataclass
class SyncConfig:
    """同步配置"""
    sync_method: str = "automatic"  # automatic, manual, beat_sync, onset_sync
    tolerance: float = 0.1  # 同步容忍度（秒）
    fade_duration: float = 0.5
    normalize_audio: bool = True
    remove_silence: bool = False
    tempo_adjustment: Optional[float] = None  # 速度調整比例

class AudioVideoSyncEngine:
    """智能音視頻同步引擎"""
    
    def __init__(self, cache_dir: str = "./cache/audio"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.audio_cache = {}
        
    async def analyze_audio(self, audio_path: str) -> AudioAnalysis:
        """分析音頻特徵"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        cache_key = f"{audio_path}_{os.path.getmtime(audio_path)}"
        if cache_key in self.audio_cache:
            return self.audio_cache[cache_key]
            
        logger.info(f"Analyzing audio: {audio_path}")
        
        try:
            if LIBROSA_AVAILABLE:
                # 使用librosa進行高級音頻分析
                y, sr = librosa.load(audio_path)
                duration = len(y) / sr
                
                # 節拍檢測
                tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
                beat_times = librosa.times_like(beats)
                
                # 音符開始點檢測
                onset_frames = librosa.onset.onset_detect(
                    y=y, sr=sr, units='frames'
                )
                onset_times = librosa.frames_to_time(onset_frames, sr=sr)
                
                # 頻譜質心
                spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
                
                # RMS能量
                rms_energy = librosa.feature.rms(y=y)[0]
                
                # 過零率
                zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
                
                # 色度特徵
                chroma = librosa.feature.chroma_stft(y=y, sr=sr)
                
                analysis = AudioAnalysis(
                    duration=duration,
                    tempo=float(tempo),
                    beats=beat_times.tolist(),
                    onset_frames=onset_frames.tolist(),
                    onset_times=onset_times.tolist(),
                    spectral_centroid=spectral_centroid,
                    rms_energy=rms_energy,
                    zero_crossing_rate=zero_crossing_rate,
                    chroma=chroma,
                    sample_rate=sr
                )
                
            else:
                # 基礎分析（使用MoviePy）
                audio = AudioFileClip(audio_path)
                duration = audio.duration
                sample_rate = audio.fps
                
                analysis = AudioAnalysis(
                    duration=duration,
                    tempo=None,
                    beats=None,
                    onset_frames=None,
                    onset_times=None,
                    spectral_centroid=None,
                    rms_energy=None,
                    zero_crossing_rate=None,
                    chroma=None,
                    sample_rate=sample_rate
                )
                
                audio.close()
                
            self.audio_cache[cache_key] = analysis
            logger.info(f"Audio analysis complete: duration={analysis.duration:.2f}s, "
                       f"tempo={analysis.tempo}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            raise
            
    async def detect_sync_points(
        self, 
        video_duration: float,
        audio_analysis: AudioAnalysis,
        sync_config: SyncConfig
    ) -> List[SyncPoint]:
        """檢測同步點"""
        
        sync_points = []
        
        if sync_config.sync_method == "beat_sync" and audio_analysis.beats:
            # 基於節拍的同步
            beats = audio_analysis.beats
            video_beats = np.linspace(0, video_duration, len(beats))
            
            for i, (video_time, audio_time) in enumerate(zip(video_beats, beats)):
                importance = 1.0 if i % 4 == 0 else 0.5  # 強拍更重要
                sync_points.append(SyncPoint(
                    video_time=video_time,
                    audio_time=audio_time,
                    importance=importance,
                    sync_type="beat"
                ))
                
        elif sync_config.sync_method == "onset_sync" and audio_analysis.onset_times:
            # 基於音符開始的同步
            onsets = audio_analysis.onset_times
            video_onsets = np.linspace(0, video_duration, len(onsets))
            
            for video_time, audio_time in zip(video_onsets, onsets):
                sync_points.append(SyncPoint(
                    video_time=video_time,
                    audio_time=audio_time,
                    importance=0.8,
                    sync_type="onset"
                ))
                
        elif sync_config.sync_method == "automatic":
            # 自動檢測同步點
            sync_points = await self._detect_automatic_sync_points(
                video_duration, audio_analysis
            )
            
        else:
            # 基礎線性同步
            num_points = max(5, int(min(video_duration, audio_analysis.duration)))
            for i in range(num_points):
                progress = i / (num_points - 1) if num_points > 1 else 0
                sync_points.append(SyncPoint(
                    video_time=progress * video_duration,
                    audio_time=progress * audio_analysis.duration,
                    importance=1.0,
                    sync_type="automatic"
                ))
                
        logger.info(f"Detected {len(sync_points)} sync points using {sync_config.sync_method}")
        return sync_points
        
    async def _detect_automatic_sync_points(
        self, 
        video_duration: float,
        audio_analysis: AudioAnalysis
    ) -> List[SyncPoint]:
        """自動檢測同步點"""
        
        sync_points = []
        
        # 結合多種特徵檢測重要時刻
        if (audio_analysis.rms_energy is not None and 
            audio_analysis.spectral_centroid is not None):
            
            # 能量峰值檢測
            energy = audio_analysis.rms_energy
            if SCIPY_AVAILABLE:
                # 平滑能量曲線
                energy_smooth = gaussian_filter1d(energy, sigma=2)
                # 檢測峰值
                peaks, _ = signal.find_peaks(energy_smooth, height=np.mean(energy_smooth))
                
                # 轉換為時間
                time_per_frame = audio_analysis.duration / len(energy)
                peak_times = peaks * time_per_frame
                
                # 映射到視頻時間線
                for peak_time in peak_times:
                    if peak_time <= audio_analysis.duration:
                        video_time = (peak_time / audio_analysis.duration) * video_duration
                        sync_points.append(SyncPoint(
                            video_time=video_time,
                            audio_time=peak_time,
                            importance=0.7,
                            sync_type="automatic"
                        ))
        
        # 如果沒有特殊同步點，創建均勻分佈的同步點
        if len(sync_points) < 3:
            num_points = 5
            for i in range(num_points):
                progress = i / (num_points - 1) if num_points > 1 else 0
                sync_points.append(SyncPoint(
                    video_time=progress * video_duration,
                    audio_time=progress * audio_analysis.duration,
                    importance=0.5,
                    sync_type="automatic"
                ))
                
        return sync_points
        
    async def sync_audio_to_video(
        self,
        video: VideoClip,
        audio_path: str,
        sync_config: SyncConfig
    ) -> VideoClip:
        """將音頻同步到視頻"""
        
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available for audio-video sync")
            return video
            
        logger.info("Starting audio-video synchronization")
        
        try:
            # 分析音頻
            audio_analysis = await self.analyze_audio(audio_path)
            
            # 檢測同步點
            sync_points = await self.detect_sync_points(
                video.duration, audio_analysis, sync_config
            )
            
            # 處理音頻
            audio = AudioFileClip(audio_path)
            
            # 標準化音頻
            if sync_config.normalize_audio:
                audio = audio.fx(afx.normalize)
                
            # 移除靜音（如果需要）
            if sync_config.remove_silence:
                audio = await self._remove_silence(audio)
                
            # 調整音頻時長和節奏
            synced_audio = await self._apply_sync_adjustments(
                audio, video.duration, sync_points, sync_config
            )
            
            # 添加淡入淡出
            if sync_config.fade_duration > 0:
                synced_audio = synced_audio.fx(
                    audio_fadein, sync_config.fade_duration
                ).fx(
                    audio_fadeout, sync_config.fade_duration
                )
            
            # 將同步後的音頻附加到視頻
            result_video = video.set_audio(synced_audio)
            
            logger.info("Audio-video synchronization completed")
            return result_video
            
        except Exception as e:
            logger.error(f"Audio-video sync failed: {e}")
            # 回退：簡單音頻附加
            try:
                audio = AudioFileClip(audio_path)
                if audio.duration > video.duration:
                    audio = audio.subclip(0, video.duration)
                elif audio.duration < video.duration:
                    # 循環或延長音頻
                    repeats = int(video.duration / audio.duration) + 1
                    audio = CompositeAudioClip([audio] * repeats).subclip(0, video.duration)
                
                return video.set_audio(audio)
            except Exception as fallback_error:
                logger.error(f"Fallback audio sync failed: {fallback_error}")
                return video
                
    async def _apply_sync_adjustments(
        self,
        audio: AudioClip,
        target_duration: float,
        sync_points: List[SyncPoint],
        config: SyncConfig
    ) -> AudioClip:
        """應用同步調整"""
        
        if config.tempo_adjustment and config.tempo_adjustment != 1.0:
            # 調整音頻速度
            try:
                # 使用time stretching調整速度而不改變音調
                audio = audio.fx(afx.speedx, config.tempo_adjustment)
            except Exception as e:
                logger.warning(f"Tempo adjustment failed: {e}")
        
        # 調整音頻長度匹配視頻
        if abs(audio.duration - target_duration) > config.tolerance:
            if audio.duration > target_duration:
                # 裁剪音頻
                audio = audio.subclip(0, target_duration)
            else:
                # 延長音頻
                if target_duration / audio.duration <= 2:
                    # 如果不需要太多重複，直接循環
                    repeats = int(target_duration / audio.duration) + 1
                    extended_audio = CompositeAudioClip([audio] * repeats)
                    audio = extended_audio.subclip(0, target_duration)
                else:
                    # 如果差異太大，添加靜音
                    silence_duration = target_duration - audio.duration
                    from moviepy.audio.AudioClip import AudioArrayClip
                    silence = AudioArrayClip(
                        np.zeros((int(silence_duration * audio.fps), 2)), 
                        fps=audio.fps
                    )
                    audio = concatenate_audioclips([audio, silence])
        
        return audio
        
    async def _remove_silence(self, audio: AudioClip) -> AudioClip:
        """移除音頻中的靜音片段"""
        
        try:
            if LIBROSA_AVAILABLE:
                # 使用librosa檢測靜音
                audio_array = audio.to_soundarray()
                if len(audio_array.shape) > 1:
                    # 立體聲轉單聲道
                    audio_array = np.mean(audio_array, axis=1)
                
                # 檢測非靜音片段
                non_silent_intervals = librosa.effects.split(
                    audio_array, top_db=20, frame_length=2048, hop_length=512
                )
                
                if len(non_silent_intervals) > 0:
                    # 重新組合非靜音片段
                    clips = []
                    sample_rate = audio.fps
                    
                    for start_frame, end_frame in non_silent_intervals:
                        start_time = start_frame / sample_rate
                        end_time = end_frame / sample_rate
                        
                        if end_time - start_time > 0.1:  # 至少0.1秒
                            clip_segment = audio.subclip(start_time, end_time)
                            clips.append(clip_segment)
                    
                    if clips:
                        return concatenate_audioclips(clips)
                        
        except Exception as e:
            logger.warning(f"Silence removal failed: {e}")
            
        return audio
        
    def create_rhythm_matched_video(
        self,
        video: VideoClip,
        audio_analysis: AudioAnalysis,
        beat_sync: bool = True
    ) -> VideoClip:
        """創建節奏匹配的視頻"""
        
        if not (beat_sync and audio_analysis.beats):
            return video
            
        try:
            beats = audio_analysis.beats
            video_duration = video.duration
            
            # 根據節拍調整視頻速度
            if len(beats) > 1:
                avg_beat_interval = np.mean(np.diff(beats))
                target_beat_interval = video_duration / len(beats)
                speed_ratio = avg_beat_interval / target_beat_interval
                
                if 0.5 <= speed_ratio <= 2.0:  # 合理的速度範圍
                    video = video.fx(vfx.speedx, speed_ratio)
                    
            return video
            
        except Exception as e:
            logger.warning(f"Rhythm matching failed: {e}")
            return video
            
    async def create_audio_visualization(
        self,
        audio_analysis: AudioAnalysis,
        width: int = 1080,
        height: int = 200
    ) -> Optional[VideoClip]:
        """創建音頻可視化"""
        
        if not (MOVIEPY_AVAILABLE and audio_analysis.rms_energy is not None):
            return None
            
        try:
            from moviepy.editor import ColorClip, CompositeVideoClip
            
            # 創建基礎背景
            background = ColorClip(
                size=(width, height), 
                color=(0, 0, 0), 
                duration=audio_analysis.duration
            )
            
            # 創建能量波形可視化
            energy = audio_analysis.rms_energy
            time_per_frame = audio_analysis.duration / len(energy)
            
            def make_frame(t):
                frame_index = int(t / time_per_frame)
                if frame_index >= len(energy):
                    frame_index = len(energy) - 1
                    
                current_energy = energy[frame_index]
                bar_height = int(current_energy * height * 10)  # 放大能量值
                bar_height = min(bar_height, height)
                
                # 創建簡單的能量條
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                
                # 繪製能量條（中心對稱）
                if bar_height > 0:
                    center_y = height // 2
                    start_y = max(0, center_y - bar_height // 2)
                    end_y = min(height, center_y + bar_height // 2)
                    
                    # 綠色能量條
                    frame[start_y:end_y, :, 1] = 255
                    
                return frame
                
            visualization = VideoClip(make_frame, duration=audio_analysis.duration)
            
            return CompositeVideoClip([background, visualization])
            
        except Exception as e:
            logger.error(f"Audio visualization creation failed: {e}")
            return None


# 便捷函數
async def sync_audio_to_video(
    video: VideoClip,
    audio_path: str,
    sync_method: str = "automatic",
    normalize: bool = True,
    fade_duration: float = 0.5
) -> VideoClip:
    """同步音頻到視頻的便捷函數"""
    
    sync_engine = AudioVideoSyncEngine()
    config = SyncConfig(
        sync_method=sync_method,
        normalize_audio=normalize,
        fade_duration=fade_duration
    )
    
    return await sync_engine.sync_audio_to_video(video, audio_path, config)

async def test_audio_video_sync():
    """測試音視頻同步系統"""
    
    print("🎵 Testing Audio-Video Sync Engine...")
    
    sync_engine = AudioVideoSyncEngine()
    
    # 測試基礎功能
    print(f"Dependencies available:")
    print(f"  MoviePy: {MOVIEPY_AVAILABLE}")
    print(f"  librosa: {LIBROSA_AVAILABLE}")
    print(f"  scipy: {SCIPY_AVAILABLE}")
    
    # 如果有測試音頻文件，可以進行實際測試
    test_audio = "test_audio.mp3"  # 假設的測試文件
    
    if os.path.exists(test_audio):
        try:
            analysis = await sync_engine.analyze_audio(test_audio)
            print(f"✅ Audio analysis successful:")
            print(f"   Duration: {analysis.duration:.2f}s")
            print(f"   Tempo: {analysis.tempo}")
            print(f"   Beats: {len(analysis.beats) if analysis.beats else 0}")
        except Exception as e:
            print(f"❌ Audio analysis failed: {e}")
    else:
        print("ℹ️  No test audio file found, skipping actual analysis")
    
    print("✅ Audio-Video Sync Engine initialized successfully!")
    return sync_engine

if __name__ == "__main__":
    print("🎬 Audio-Video Sync Engine - Intelligent Audio-Video Synchronization")
    print("=" * 75)
    
    # 檢查依賴
    print("Checking dependencies...")
    print(f"MoviePy available: {MOVIEPY_AVAILABLE}")
    print(f"librosa available: {LIBROSA_AVAILABLE}")
    print(f"scipy available: {SCIPY_AVAILABLE}")
    
    # 運行測試
    result = asyncio.run(test_audio_video_sync())
    print(f"Sync engine ready: {result is not None}")