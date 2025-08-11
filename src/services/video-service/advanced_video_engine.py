#!/usr/bin/env python3
"""
高級視頻處理引擎 - 企業級視頻生成系統
包含智能合成、專業轉場、動態特效、音視頻同步等功能
"""

import os
import logging
import tempfile
import asyncio
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib
import concurrent.futures
import threading

try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, 
        CompositeAudioClip, TextClip, concatenate_videoclips,
        vfx, afx, ColorClip, VideoClip
    )
    from moviepy.video.fx import resize, fadein, fadeout, crossfadein, crossfadeout
    from moviepy.audio.fx import volumex, audio_fadein, audio_fadeout
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("MoviePy not available. Advanced video processing disabled.")

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    import PIL
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logging.warning("OpenCV not available. Some advanced features disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VideoConfig:
    """視頻配置參數"""
    width: int = 1080
    height: int = 1920
    fps: int = 30
    duration: int = 15
    bitrate: str = "8M"
    codec: str = "libx264"
    audio_codec: str = "aac"
    preset: str = "medium"  # ultrafast, fast, medium, slow, slower
    crf: int = 18  # 質量參數 (0-51, 越低越好)
    
@dataclass 
class TransitionConfig:
    """轉場效果配置"""
    transition_type: str = "crossfade"  # crossfade, slide, zoom, fade, dissolve
    duration: float = 1.0
    direction: str = "left"  # left, right, up, down, center
    easing: str = "linear"  # linear, ease_in, ease_out, ease_in_out
    
@dataclass
class TextAnimation:
    """文字動畫配置"""
    animation_type: str = "fade_in"  # fade_in, slide_in, scale_up, typewriter
    duration: float = 2.0
    delay: float = 0.0
    font_size: int = 48
    font_color: Tuple[int, int, int] = (255, 255, 255)
    outline_color: Optional[Tuple[int, int, int]] = (0, 0, 0)
    outline_width: int = 2
    shadow_offset: Tuple[int, int] = (2, 2)
    
@dataclass
class AudioProcessing:
    """音頻處理配置"""
    normalize: bool = True
    fade_in_duration: float = 0.5
    fade_out_duration: float = 0.5
    volume_adjustment: float = 1.0
    noise_reduction: bool = False
    compression: bool = False

class AdvancedVideoEngine:
    """高級視頻處理引擎"""
    
    def __init__(self, output_dir: str = "./uploads/dev", cache_dir: str = "./cache"):
        self.output_dir = Path(output_dir)
        self.cache_dir = Path(cache_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 默認配置
        self.config = VideoConfig()
        self.transition_config = TransitionConfig()
        
        # 性能優化
        self.max_workers = min(4, os.cpu_count() or 1)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        
        # 緩存系統
        self.cache = {}
        self._setup_logging()
        
    def _setup_logging(self):
        """設置詳細日誌"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
    async def create_professional_video(
        self,
        scenes: List[Dict],
        audio_file: Optional[str] = None,
        title: str = "Professional Video",
        style: str = "cinematic",
        config: Optional[VideoConfig] = None
    ) -> Dict:
        """創建專業級視頻"""
        
        if not MOVIEPY_AVAILABLE:
            return self._create_fallback_response("MoviePy not available")
            
        start_time = datetime.now()
        logger.info(f"Starting professional video creation: {title}")
        
        try:
            if config:
                self.config = config
                
            # 生成輸出文件名
            timestamp = int(datetime.now().timestamp())
            output_filename = f"professional_video_{timestamp}.mp4"
            output_path = self.output_dir / output_filename
            
            # 處理場景
            video_clips = []
            for i, scene in enumerate(scenes):
                logger.info(f"Processing scene {i+1}/{len(scenes)}")
                clip = await self._process_scene(scene, i)
                if clip:
                    video_clips.append(clip)
                    
            if not video_clips:
                raise ValueError("No valid video clips generated")
                
            # 應用轉場效果
            logger.info("Applying transitions between scenes")
            final_video = await self._apply_transitions(video_clips)
            
            # 音頻處理
            if audio_file and os.path.exists(audio_file):
                logger.info("Processing and syncing audio")
                final_video = await self._process_and_sync_audio(final_video, audio_file)
                
            # 添加專業級濾鏡和色彩校正
            logger.info("Applying professional color grading and filters")
            final_video = await self._apply_professional_effects(final_video, style)
            
            # 輸出高質量視頻
            logger.info("Rendering final video with optimized settings")
            await self._render_video_optimized(final_video, str(output_path))
            
            # 清理資源
            final_video.close()
            for clip in video_clips:
                if hasattr(clip, 'close'):
                    clip.close()
                    
            processing_time = (datetime.now() - start_time).total_seconds()
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            return {
                "success": True,
                "video_url": f"/static/{output_filename}",
                "video_path": str(output_path),
                "title": title,
                "duration": self.config.duration,
                "resolution": f"{self.config.width}x{self.config.height}",
                "fps": self.config.fps,
                "format": "mp4",
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "processing_time": round(processing_time, 2),
                "scenes_processed": len(scenes),
                "style": style,
                "quality": "professional",
                "codec": self.config.codec,
                "bitrate": self.config.bitrate,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Professional video creation failed: {e}", exc_info=True)
            return self._create_fallback_response(f"Error: {str(e)}")
            
    async def _process_scene(self, scene: Dict, scene_index: int) -> Optional[VideoClip]:
        """處理單個場景"""
        
        scene_type = scene.get('type', 'image')
        duration = scene.get('duration', 3.0)
        
        if scene_type == 'image':
            return await self._create_image_scene(scene, duration)
        elif scene_type == 'text':
            return await self._create_text_scene(scene, duration)
        elif scene_type == 'video':
            return await self._create_video_scene(scene, duration)
        else:
            logger.warning(f"Unknown scene type: {scene_type}")
            return None
            
    async def _create_image_scene(self, scene: Dict, duration: float) -> Optional[VideoClip]:
        """創建圖像場景"""
        
        image_source = scene.get('source', '')
        effects = scene.get('effects', [])
        
        try:
            # 獲取或下載圖像
            image_path = await self._prepare_image_advanced(image_source)
            if not image_path:
                return None
                
            # 創建基礎圖像剪輯
            clip = ImageClip(image_path, duration=duration)
            clip = clip.resize((self.config.width, self.config.height))
            
            # 應用圖像增強
            clip = await self._enhance_image_clip(clip, scene.get('enhancement', {}))
            
            # 應用動畫效果
            for effect in effects:
                clip = await self._apply_image_effect(clip, effect)
                
            return clip
            
        except Exception as e:
            logger.error(f"Error creating image scene: {e}")
            return None
            
    async def _create_text_scene(self, scene: Dict, duration: float) -> Optional[VideoClip]:
        """創建文字場景"""
        
        text_content = scene.get('content', '')
        animation = TextAnimation(**scene.get('animation', {}))
        
        try:
            # 創建高級文字剪輯
            text_clip = await self._create_animated_text(
                text_content, 
                animation, 
                duration
            )
            
            # 創建背景
            background = scene.get('background', {})
            if background.get('type') == 'color':
                bg_clip = ColorClip(
                    size=(self.config.width, self.config.height),
                    color=background.get('color', (0, 0, 0)),
                    duration=duration
                )
            elif background.get('type') == 'image':
                bg_image_path = await self._prepare_image_advanced(background.get('source', ''))
                if bg_image_path:
                    bg_clip = ImageClip(bg_image_path, duration=duration)
                    bg_clip = bg_clip.resize((self.config.width, self.config.height))
                    # 添加模糊效果作為背景
                    bg_clip = bg_clip.fl_image(lambda img: self._apply_gaussian_blur(img, 15))
                else:
                    bg_clip = ColorClip(
                        size=(self.config.width, self.config.height),
                        color=(0, 0, 0),
                        duration=duration
                    )
            else:
                bg_clip = ColorClip(
                    size=(self.config.width, self.config.height),
                    color=(0, 0, 0),
                    duration=duration
                )
            
            # 合成文字和背景
            final_clip = CompositeVideoClip([bg_clip, text_clip])
            return final_clip
            
        except Exception as e:
            logger.error(f"Error creating text scene: {e}")
            return None
            
    async def _create_animated_text(
        self, 
        text: str, 
        animation: TextAnimation, 
        duration: float
    ) -> TextClip:
        """創建動畫文字"""
        
        # 基礎文字設置
        font_path = self._get_best_font()
        
        # 創建文字剪輯
        text_clip = TextClip(
            text,
            fontsize=animation.font_size,
            color='white' if not animation.font_color else 
                  f'rgb({animation.font_color[0]},{animation.font_color[1]},{animation.font_color[2]})',
            font=font_path,
            stroke_color='black' if animation.outline_color else None,
            stroke_width=animation.outline_width if animation.outline_color else 0
        ).set_duration(duration)
        
        # 居中定位
        text_clip = text_clip.set_position('center')
        
        # 應用動畫
        if animation.animation_type == 'fade_in':
            text_clip = text_clip.set_start(animation.delay).fadein(animation.duration)
        elif animation.animation_type == 'slide_in':
            text_clip = text_clip.set_start(animation.delay)
            # 從右側滑入
            text_clip = text_clip.set_position(lambda t: ('center' if t > animation.duration 
                                                        else (self.config.width + 100 - 
                                                              (self.config.width + 100) * 
                                                              (t / animation.duration), 'center')))
        elif animation.animation_type == 'scale_up':
            text_clip = text_clip.set_start(animation.delay)
            text_clip = text_clip.resize(lambda t: min(1, t / animation.duration))
        elif animation.animation_type == 'typewriter':
            # 打字機效果需要特殊處理
            text_clip = await self._create_typewriter_effect(text, animation, duration)
            
        return text_clip
        
    async def _create_typewriter_effect(
        self, 
        text: str, 
        animation: TextAnimation, 
        duration: float
    ) -> CompositeVideoClip:
        """創建打字機效果"""
        
        clips = []
        chars_per_second = len(text) / animation.duration
        
        for i in range(len(text) + 1):
            partial_text = text[:i]
            if not partial_text:
                continue
                
            start_time = animation.delay + (i / chars_per_second)
            clip_duration = duration - start_time
            
            if clip_duration <= 0:
                continue
                
            partial_clip = TextClip(
                partial_text,
                fontsize=animation.font_size,
                color='white',
                font=self._get_best_font()
            ).set_start(start_time).set_duration(clip_duration).set_position('center')
            
            clips.append(partial_clip)
            
        return CompositeVideoClip(clips)
        
    async def _apply_transitions(self, clips: List[VideoClip]) -> VideoClip:
        """應用專業轉場效果"""
        
        if len(clips) <= 1:
            return clips[0] if clips else None
            
        transition_duration = self.transition_config.duration
        
        # 根據轉場類型處理
        if self.transition_config.transition_type == "crossfade":
            return await self._apply_crossfade_transition(clips, transition_duration)
        elif self.transition_config.transition_type == "slide":
            return await self._apply_slide_transition(clips, transition_duration)
        elif self.transition_config.transition_type == "zoom":
            return await self._apply_zoom_transition(clips, transition_duration)
        else:
            # 默認使用交叉淡入淡出
            return await self._apply_crossfade_transition(clips, transition_duration)
            
    async def _apply_crossfade_transition(
        self, 
        clips: List[VideoClip], 
        transition_duration: float
    ) -> VideoClip:
        """應用交叉淡入淡出轉場"""
        
        if len(clips) == 1:
            return clips[0]
            
        result_clips = [clips[0]]
        current_time = clips[0].duration - transition_duration
        
        for i in range(1, len(clips)):
            # 當前片段淡出
            current_clip = clips[i-1].fadeout(transition_duration)
            
            # 下一個片段淡入
            next_clip = clips[i].fadein(transition_duration).set_start(current_time)
            
            result_clips = [current_clip, next_clip]
            current_time += clips[i].duration - transition_duration
            
        return CompositeVideoClip(result_clips)
        
    async def _apply_professional_effects(self, video: VideoClip, style: str) -> VideoClip:
        """應用專業級視覺效果"""
        
        if style == "cinematic":
            # 電影級調色
            video = video.fl_image(self._cinematic_color_grade)
            # 添加輕微的暗角效果
            video = video.fl_image(self._add_vignette)
            
        elif style == "modern":
            # 現代風格 - 高對比度和飽和度
            video = video.fl_image(self._modern_color_grade)
            
        elif style == "vintage":
            # 復古風格
            video = video.fl_image(self._vintage_color_grade)
            # 添加膠片顆粒
            video = video.fl_image(self._add_film_grain)
            
        elif style == "minimal":
            # 極簡風格 - 降低飽和度
            video = video.fl_image(self._minimal_color_grade)
            
        return video
        
    def _cinematic_color_grade(self, img):
        """電影級調色"""
        if not PIL_AVAILABLE:
            return img
            
        pil_img = Image.fromarray(img)
        
        # 增加對比度
        enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = enhancer.enhance(1.2)
        
        # 輕微降低飽和度
        enhancer = ImageEnhance.Color(pil_img)
        pil_img = enhancer.enhance(0.9)
        
        # 調整亮度
        enhancer = ImageEnhance.Brightness(pil_img)
        pil_img = enhancer.enhance(0.95)
        
        return np.array(pil_img)
        
    def _add_vignette(self, img):
        """添加暗角效果"""
        if not PIL_AVAILABLE:
            return img
            
        pil_img = Image.fromarray(img)
        width, height = pil_img.size
        
        # 創建暗角遮罩
        vignette = Image.new('L', (width, height), 0)
        vignette_draw = ImageDraw.Draw(vignette)
        
        # 繪製徑向漸變
        center_x, center_y = width // 2, height // 2
        max_radius = min(width, height) // 2
        
        for radius in range(max_radius, 0, -1):
            alpha = int(255 * (radius / max_radius))
            vignette_draw.ellipse([
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius
            ], fill=alpha)
        
        # 應用暗角
        vignette = vignette.convert('RGB')
        result = Image.blend(pil_img, vignette, 0.1)
        
        return np.array(result)
        
    async def _process_and_sync_audio(self, video: VideoClip, audio_file: str) -> VideoClip:
        """處理和同步音頻"""
        
        try:
            audio = AudioFileClip(audio_file)
            
            # 音頻標準化
            audio = audio.fx(afx.normalize)
            
            # 淡入淡出
            audio = audio.fx(audio_fadein, 0.5).fx(audio_fadeout, 0.5)
            
            # 調整音頻長度匹配視頻
            if audio.duration > video.duration:
                audio = audio.subclip(0, video.duration)
            elif audio.duration < video.duration:
                # 循環音頻或添加靜音
                repeats = int(video.duration / audio.duration) + 1
                audio = CompositeAudioClip([audio] * repeats).subclip(0, video.duration)
            
            # 將音頻附加到視頻
            video = video.set_audio(audio)
            
            return video
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return video
            
    async def _render_video_optimized(self, video: VideoClip, output_path: str):
        """優化渲染視頻"""
        
        # 使用高質量設置渲染
        video.write_videofile(
            output_path,
            fps=self.config.fps,
            codec=self.config.codec,
            bitrate=self.config.bitrate,
            audio_codec=self.config.audio_codec,
            preset=self.config.preset,
            ffmpeg_params=['-crf', str(self.config.crf)],
            threads=self.max_workers,
            verbose=False,
            logger=None
        )
        
    def _get_best_font(self) -> str:
        """獲取最佳可用字體"""
        
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",  # macOS 中文
            "/System/Library/Fonts/Helvetica.ttc",  # macOS 英文
            "/System/Library/Fonts/Arial.ttf",     # Windows
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "arial",  # 系統字體名稱
            "helvetica"
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                return font_path
                
        return "Arial"  # fallback
        
    async def _prepare_image_advanced(self, image_source: str) -> Optional[str]:
        """高級圖像預處理"""
        
        if not image_source:
            return None
            
        # 生成緩存key
        cache_key = hashlib.md5(image_source.encode()).hexdigest()
        cache_path = self.cache_dir / f"img_{cache_key}.jpg"
        
        # 檢查緩存
        if cache_path.exists():
            return str(cache_path)
            
        try:
            if image_source.startswith('http'):
                # 下載網路圖片
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_source) as response:
                        if response.status == 200:
                            content = await response.read()
                            
                            # 保存到緩存
                            with open(cache_path, 'wb') as f:
                                f.write(content)
                                
                            # 優化圖像
                            await self._optimize_image(str(cache_path))
                            return str(cache_path)
            else:
                # 本地文件
                if os.path.exists(image_source):
                    # 複製到緩存並優化
                    import shutil
                    shutil.copy2(image_source, cache_path)
                    await self._optimize_image(str(cache_path))
                    return str(cache_path)
                    
        except Exception as e:
            logger.error(f"Failed to prepare image {image_source}: {e}")
            
        return None
        
    async def _optimize_image(self, image_path: str):
        """優化圖像質量"""
        
        if not PIL_AVAILABLE:
            return
            
        try:
            with Image.open(image_path) as img:
                # 轉換為RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 調整尺寸
                img = img.resize((self.config.width, self.config.height), Image.LANCZOS)
                
                # 輕微銳化
                img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=110, threshold=3))
                
                # 保存優化後的圖像
                img.save(image_path, 'JPEG', quality=95, optimize=True)
                
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            
    def _create_fallback_response(self, error_msg: str) -> Dict:
        """創建fallback響應"""
        
        return {
            "success": False,
            "error": error_msg,
            "video_url": "#",
            "video_path": "",
            "title": "Failed Video Generation",
            "duration": 0,
            "resolution": f"{self.config.width}x{self.config.height}",
            "format": "mp4",
            "file_size": 0,
            "generated_at": datetime.utcnow().isoformat(),
            "note": "Advanced video processing requires MoviePy, PIL, and optionally OpenCV"
        }
        
    def _apply_gaussian_blur(self, img, radius: int):
        """應用高斯模糊"""
        if not PIL_AVAILABLE:
            return img
            
        pil_img = Image.fromarray(img)
        blurred = pil_img.filter(ImageFilter.GaussianBlur(radius=radius))
        return np.array(blurred)
        
    def _modern_color_grade(self, img):
        """現代風格調色"""
        if not PIL_AVAILABLE:
            return img
            
        pil_img = Image.fromarray(img)
        
        # 增加對比度和飽和度
        enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = enhancer.enhance(1.3)
        
        enhancer = ImageEnhance.Color(pil_img)
        pil_img = enhancer.enhance(1.2)
        
        return np.array(pil_img)
        
    def _vintage_color_grade(self, img):
        """復古風格調色"""
        if not PIL_AVAILABLE:
            return img
            
        pil_img = Image.fromarray(img)
        
        # 降低飽和度，增加暖色調
        enhancer = ImageEnhance.Color(pil_img)
        pil_img = enhancer.enhance(0.8)
        
        # 添加復古濾鏡效果（增加黃色調）
        # 這裡可以添加更複雜的色彩映射
        
        return np.array(pil_img)
        
    def _minimal_color_grade(self, img):
        """極簡風格調色"""
        if not PIL_AVAILABLE:
            return img
            
        pil_img = Image.fromarray(img)
        
        # 大幅降低飽和度
        enhancer = ImageEnhance.Color(pil_img)
        pil_img = enhancer.enhance(0.3)
        
        # 輕微增加對比度
        enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = enhancer.enhance(1.1)
        
        return np.array(pil_img)
        
    def _add_film_grain(self, img):
        """添加膠片顆粒效果"""
        if not PIL_AVAILABLE or not np:
            return img
            
        # 生成隨機噪音
        noise = np.random.normal(0, 10, img.shape).astype(np.int16)
        
        # 添加到原圖像
        result = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        return result
        
    async def __aenter__(self):
        """異步上下文管理器入口"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)


# 便捷函數
async def create_professional_video(
    scenes: List[Dict],
    audio_file: Optional[str] = None,
    title: str = "Professional Video",
    style: str = "cinematic",
    config: Optional[VideoConfig] = None,
    output_dir: str = "./uploads/dev"
) -> Dict:
    """創建專業視頻的便捷函數"""
    
    async with AdvancedVideoEngine(output_dir) as engine:
        return await engine.create_professional_video(
            scenes=scenes,
            audio_file=audio_file,
            title=title,
            style=style,
            config=config
        )


# 測試和演示
async def test_advanced_video_engine():
    """測試高級視頻引擎"""
    
    # 定義測試場景
    test_scenes = [
        {
            "type": "text",
            "content": "歡迎來到\n高級視頻生成測試",
            "duration": 3.0,
            "animation": {
                "animation_type": "fade_in",
                "duration": 1.0,
                "font_size": 64,
                "font_color": (255, 255, 255)
            },
            "background": {
                "type": "color",
                "color": (25, 25, 75)
            }
        },
        {
            "type": "image",
            "source": "https://picsum.photos/1080/1920?random=1",
            "duration": 4.0,
            "effects": ["zoom_in", "fade"],
            "enhancement": {
                "brightness": 1.1,
                "contrast": 1.2,
                "saturation": 1.1
            }
        },
        {
            "type": "text",
            "content": "專業級\n視頻處理技術",
            "duration": 3.0,
            "animation": {
                "animation_type": "slide_in",
                "duration": 1.5,
                "font_size": 56
            },
            "background": {
                "type": "image",
                "source": "https://picsum.photos/1080/1920?random=2"
            }
        }
    ]
    
    # 高質量配置
    hq_config = VideoConfig(
        width=1080,
        height=1920,
        fps=30,
        duration=10,
        bitrate="10M",
        crf=16,  # 高質量
        preset="slow"  # 最佳壓縮
    )
    
    result = await create_professional_video(
        scenes=test_scenes,
        title="Advanced Video Engine Test",
        style="cinematic",
        config=hq_config
    )
    
    print("\n🎬 Advanced Video Engine Test Results:")
    print("=" * 50)
    for key, value in result.items():
        print(f"{key}: {value}")
    
    return result


if __name__ == "__main__":
    print("🚀 Advanced Video Engine - Professional Video Generation")
    print("=" * 60)
    
    # 檢查依賴
    print(f"MoviePy available: {MOVIEPY_AVAILABLE}")
    print(f"PIL available: {PIL_AVAILABLE}")
    print(f"OpenCV available: {OPENCV_AVAILABLE}")
    
    if MOVIEPY_AVAILABLE and PIL_AVAILABLE:
        # 運行測試
        result = asyncio.run(test_advanced_video_engine())
        
        if result.get('success'):
            print("\n✅ Advanced video generation test completed successfully!")
            print(f"📊 Processing time: {result.get('processing_time', 0)}s")
            print(f"📏 File size: {result.get('file_size_mb', 0)}MB")
        else:
            print(f"\n❌ Test failed: {result.get('error', 'Unknown error')}")
    else:
        print("\n⚠️  Missing required dependencies for advanced video processing")
        print("Install with: pip install moviepy pillow opencv-python")