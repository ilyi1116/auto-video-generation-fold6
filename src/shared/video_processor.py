#!/usr/bin/env python3
"""
影片處理引擎
使用FFmpeg進行影片合成、編輯和渲染
"""

import os
import asyncio
import logging
import subprocess
import tempfile
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VideoFormat(Enum):
    """支援的影片格式"""
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    WEBM = "webm"
    MKV = "mkv"


class VideoQuality(Enum):
    """影片品質設定"""
    LOW = "low"      # 480p
    MEDIUM = "medium" # 720p
    HIGH = "high"    # 1080p
    ULTRA = "ultra"  # 4K


@dataclass
class VideoAsset:
    """影片素材"""
    type: str  # "image", "video", "audio", "text"
    path: str  # 檔案路徑
    start_time: float = 0.0  # 開始時間（秒）
    duration: float = 0.0    # 持續時間（秒）
    position: Dict[str, Union[int, float]] = None  # 位置資訊 {x, y, width, height}
    effects: List[Dict[str, Any]] = None  # 特效列表
    
    def __post_init__(self):
        if self.position is None:
            self.position = {"x": 0, "y": 0, "width": 1920, "height": 1080}
        if self.effects is None:
            self.effects = []


@dataclass
class VideoProject:
    """影片專案配置"""
    title: str
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration: float = 60.0
    format: VideoFormat = VideoFormat.MP4
    quality: VideoQuality = VideoQuality.HIGH
    assets: List[VideoAsset] = None
    background_color: str = "#000000"
    background_music: Optional[str] = None
    
    def __post_init__(self):
        if self.assets is None:
            self.assets = []


class VideoProcessor:
    """影片處理器"""
    
    def __init__(self, output_dir: str = "./output", temp_dir: str = None):
        """
        初始化影片處理器
        
        Args:
            output_dir: 輸出目錄
            temp_dir: 暫存目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "video_processor"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.ffmpeg_path = self._find_ffmpeg()
        
    def _find_ffmpeg(self) -> str:
        """查找FFmpeg執行檔"""
        # 首先嘗試從環境變數
        ffmpeg_path = os.getenv("FFMPEG_PATH")
        if ffmpeg_path and Path(ffmpeg_path).exists():
            return ffmpeg_path
            
        # 嘗試常見路徑
        common_paths = [
            "ffmpeg",  # 系統PATH中
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg",  # macOS Homebrew ARM64
            "/usr/local/homebrew/bin/ffmpeg",  # macOS Homebrew x86
        ]
        
        for path in common_paths:
            try:
                result = subprocess.run([path, "-version"], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"Found FFmpeg at: {path}")
                    return path
            except FileNotFoundError:
                continue
        
        raise FileNotFoundError(
            "FFmpeg not found. Please install FFmpeg and ensure it's in PATH, "
            "or set FFMPEG_PATH environment variable."
        )
    
    async def check_ffmpeg(self) -> Dict[str, Any]:
        """檢查FFmpeg版本和支援的功能"""
        try:
            # 檢查版本
            version_proc = await asyncio.create_subprocess_exec(
                self.ffmpeg_path, "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await version_proc.communicate()
            
            if version_proc.returncode != 0:
                raise RuntimeError(f"FFmpeg check failed: {stderr.decode()}")
            
            version_output = stdout.decode()
            version_line = version_output.split('\n')[0]
            
            # 檢查編碼器
            codecs_proc = await asyncio.create_subprocess_exec(
                self.ffmpeg_path, "-encoders",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            codecs_stdout, _ = await codecs_proc.communicate()
            codecs_output = codecs_stdout.decode()
            
            # 檢查支援的格式
            formats_proc = await asyncio.create_subprocess_exec(
                self.ffmpeg_path, "-formats",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            formats_stdout, _ = await formats_proc.communicate()
            formats_output = formats_stdout.decode()
            
            return {
                "version": version_line,
                "available": True,
                "h264_supported": "libx264" in codecs_output,
                "h265_supported": "libx265" in codecs_output,
                "mp4_supported": "mp4" in formats_output,
                "webm_supported": "webm" in formats_output,
            }
            
        except Exception as e:
            logger.error(f"FFmpeg check failed: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def _get_quality_settings(self, quality: VideoQuality) -> Dict[str, str]:
        """獲取品質設定參數"""
        settings = {
            VideoQuality.LOW: {
                "video_bitrate": "500k",
                "audio_bitrate": "64k",
                "scale": "scale=854:480",
                "preset": "fast",
                "crf": "28"
            },
            VideoQuality.MEDIUM: {
                "video_bitrate": "1500k", 
                "audio_bitrate": "128k",
                "scale": "scale=1280:720",
                "preset": "medium",
                "crf": "23"
            },
            VideoQuality.HIGH: {
                "video_bitrate": "3000k",
                "audio_bitrate": "192k", 
                "scale": "scale=1920:1080",
                "preset": "medium",
                "crf": "20"
            },
            VideoQuality.ULTRA: {
                "video_bitrate": "8000k",
                "audio_bitrate": "320k",
                "scale": "scale=3840:2160", 
                "preset": "slow",
                "crf": "18"
            }
        }
        return settings.get(quality, settings[VideoQuality.HIGH])
    
    async def create_video_from_images(
        self,
        image_paths: List[str],
        output_filename: str,
        duration_per_image: float = 3.0,
        transition_duration: float = 0.5,
        background_music: Optional[str] = None,
        quality: VideoQuality = VideoQuality.HIGH
    ) -> str:
        """
        從圖片序列創建影片
        
        Args:
            image_paths: 圖片檔案路徑列表
            output_filename: 輸出檔案名
            duration_per_image: 每張圖片顯示時間
            transition_duration: 轉場時間
            background_music: 背景音樂檔案路徑
            quality: 影片品質
            
        Returns:
            生成的影片檔案路徑
        """
        if not image_paths:
            raise ValueError("No images provided")
        
        output_path = self.output_dir / output_filename
        quality_settings = self._get_quality_settings(quality)
        
        # 構建FFmpeg命令
        cmd = [
            self.ffmpeg_path,
            "-y",  # 覆蓋輸出檔案
        ]
        
        # 添加圖片輸入
        total_duration = len(image_paths) * duration_per_image
        
        for i, image_path in enumerate(image_paths):
            cmd.extend([
                "-loop", "1",
                "-t", str(duration_per_image + transition_duration),
                "-i", image_path
            ])
        
        # 添加背景音樂
        if background_music and Path(background_music).exists():
            cmd.extend(["-i", background_music])
        
        # 構建濾鏡
        filter_complex = []
        
        # 圖片處理濾鏡
        for i in range(len(image_paths)):
            # 縮放和淡入淡出效果
            filter_complex.append(
                f"[{i}:v]{quality_settings['scale']},fade=in:0:15,fade=out:{int((duration_per_image + transition_duration - 0.5) * 30)}:15[img{i}]"
            )
        
        # 拼接濾鏡
        if len(image_paths) > 1:
            concat_inputs = "".join([f"[img{i}]" for i in range(len(image_paths))])
            filter_complex.append(f"{concat_inputs}concat=n={len(image_paths)}:v=1:a=0[video]")
            video_stream = "[video]"
        else:
            video_stream = "[img0]"
        
        # 應用濾鏡
        if filter_complex:
            cmd.extend(["-filter_complex", ";".join(filter_complex)])
            cmd.extend(["-map", video_stream])
        
        # 添加音頻映射
        if background_music and Path(background_music).exists():
            cmd.extend([
                "-map", f"{len(image_paths)}:a",
                "-shortest",  # 以最短流為準
                "-b:a", quality_settings["audio_bitrate"]
            ])
        
        # 輸出設定
        cmd.extend([
            "-c:v", "libx264",
            "-preset", quality_settings["preset"], 
            "-crf", quality_settings["crf"],
            "-b:v", quality_settings["video_bitrate"],
            "-r", "30",  # 30fps
            "-pix_fmt", "yuv420p",
            str(output_path)
        ])
        
        logger.info(f"Creating video from {len(image_paths)} images: {output_filename}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        # 執行FFmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
            logger.error(f"FFmpeg failed: {error_msg}")
            raise RuntimeError(f"Video creation failed: {error_msg}")
        
        logger.info(f"Video created successfully: {output_path}")
        return str(output_path)
    
    async def add_subtitles(
        self,
        video_path: str,
        subtitle_text: str,
        output_filename: str,
        font_size: int = 24,
        font_color: str = "white",
        background_color: str = "black@0.7"
    ) -> str:
        """
        為影片添加字幕
        
        Args:
            video_path: 輸入影片路徑
            subtitle_text: 字幕文字
            output_filename: 輸出檔案名
            font_size: 字體大小
            font_color: 字體顏色
            background_color: 背景顏色（含透明度）
            
        Returns:
            生成的影片檔案路徑
        """
        output_path = self.output_dir / output_filename
        
        # 創建字幕濾鏡
        subtitle_filter = (
            f"drawtext=text='{subtitle_text}':fontsize={font_size}:fontcolor={font_color}:"
            f"x=(w-text_w)/2:y=h-text_h-50:box=1:boxcolor={background_color}:boxborderw=10"
        )
        
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-vf", subtitle_filter,
            "-c:a", "copy",  # 保持音頻不變
            str(output_path)
        ]
        
        logger.info(f"Adding subtitles to video: {video_path}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
            logger.error(f"Subtitle addition failed: {error_msg}")
            raise RuntimeError(f"Subtitle addition failed: {error_msg}")
        
        logger.info(f"Subtitles added successfully: {output_path}")
        return str(output_path)
    
    async def merge_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_filename: str,
        video_volume: float = 0.5,
        audio_volume: float = 1.0
    ) -> str:
        """
        合併影片和音頻
        
        Args:
            video_path: 影片檔案路徑
            audio_path: 音頻檔案路徑
            output_filename: 輸出檔案名
            video_volume: 影片原音量比例
            audio_volume: 新增音頻音量比例
            
        Returns:
            合併後的影片檔案路徑
        """
        output_path = self.output_dir / output_filename
        
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex", f"[0:a]volume={video_volume}[va];[1:a]volume={audio_volume}[aa];[va][aa]amix=inputs=2[audio]",
            "-map", "0:v",
            "-map", "[audio]",
            "-shortest",  # 以最短流為準
            "-c:v", "copy",  # 保持影片編碼不變
            str(output_path)
        ]
        
        logger.info(f"Merging audio with video: {video_path} + {audio_path}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
            logger.error(f"Audio merge failed: {error_msg}")
            raise RuntimeError(f"Audio merge failed: {error_msg}")
        
        logger.info(f"Audio merged successfully: {output_path}")
        return str(output_path)
    
    async def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """獲取影片資訊"""
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-hide_banner",
            "-f", "null", "-"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        output = stderr.decode()
        
        # 解析影片資訊（簡化版）
        info = {
            "path": video_path,
            "exists": Path(video_path).exists(),
            "duration": 0.0,
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "bitrate": "",
        }
        
        # 提取時長
        import re
        duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})", output)
        if duration_match:
            hours, minutes, seconds = duration_match.groups()
            info["duration"] = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        
        # 提取解析度和fps
        video_match = re.search(r"(\d{3,4})x(\d{3,4}).*?(\d+(?:\.\d+)?)\s*fps", output)
        if video_match:
            info["width"] = int(video_match.group(1))
            info["height"] = int(video_match.group(2))
            info["fps"] = float(video_match.group(3))
        
        return info
    
    def cleanup_temp_files(self):
        """清理暫存檔案"""
        import shutil
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")


# 高階介面函數
async def create_simple_video(
    images: List[str],
    output_path: str,
    background_music: Optional[str] = None,
    duration_per_image: float = 3.0,
    quality: VideoQuality = VideoQuality.HIGH
) -> str:
    """
    創建簡單影片的便利函數
    
    Args:
        images: 圖片檔案路徑列表
        output_path: 輸出影片路徑
        background_music: 背景音樂路徑
        duration_per_image: 每張圖片顯示時間
        quality: 影片品質
        
    Returns:
        生成的影片檔案路徑
    """
    processor = VideoProcessor()
    return await processor.create_video_from_images(
        image_paths=images,
        output_filename=Path(output_path).name,
        duration_per_image=duration_per_image,
        background_music=background_music,
        quality=quality
    )


if __name__ == "__main__":
    # 測試腳本
    async def test_video_processor():
        print("Testing Video Processor...")
        
        processor = VideoProcessor()
        
        # 檢查FFmpeg
        ffmpeg_info = await processor.check_ffmpeg()
        print(f"FFmpeg Status: {ffmpeg_info}")
        
        if ffmpeg_info.get("available"):
            print("✅ Video processor is ready!")
            print(f"   - Version: {ffmpeg_info.get('version', 'Unknown')}")
            print(f"   - H.264 Support: {'✅' if ffmpeg_info.get('h264_supported') else '❌'}")
            print(f"   - MP4 Support: {'✅' if ffmpeg_info.get('mp4_supported') else '❌'}")
        else:
            print(f"❌ FFmpeg not available: {ffmpeg_info.get('error')}")
    
    asyncio.run(test_video_processor())