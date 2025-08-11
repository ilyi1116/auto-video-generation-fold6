#!/usr/bin/env python3
"""
專業視頻特效和轉場系統
包含各種專業級視頻特效、轉場、濾鏡和動畫
"""

import os
import logging
import numpy as np
import math
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass
from enum import Enum
import asyncio

try:
    from moviepy.editor import VideoClip, ImageClip, ColorClip, CompositeVideoClip
    from moviepy.video.fx import resize, rotate, mirror_x, mirror_y
    import moviepy.video.fx.all as vfx
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw
    import PIL
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransitionType(Enum):
    """轉場類型枚舉"""
    FADE = "fade"
    CROSSFADE = "crossfade" 
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    ROTATE = "rotate"
    CIRCLE_WIPE = "circle_wipe"
    DIAGONAL_WIPE = "diagonal_wipe"
    PIXELATE = "pixelate"
    BLUR_TRANSITION = "blur_transition"
    GLITCH = "glitch"

class EffectType(Enum):
    """特效類型枚舉"""
    ZOOM_PAN = "zoom_pan"
    PARALLAX = "parallax"
    PARTICLE_SYSTEM = "particle_system"
    LIGHT_RAYS = "light_rays"
    CHROMATIC_ABERRATION = "chromatic_aberration"
    FILM_BURN = "film_burn"
    DATA_MOSHING = "data_moshing"
    GLITCH_EFFECT = "glitch_effect"
    COLOR_DISPLACEMENT = "color_displacement"
    VINTAGE_TV = "vintage_tv"

@dataclass
class EffectConfig:
    """特效配置"""
    effect_type: EffectType
    intensity: float = 1.0
    duration: float = 1.0
    start_time: float = 0.0
    parameters: Dict[str, Any] = None

class VideoEffectsSystem:
    """專業視頻特效系統"""
    
    def __init__(self):
        self.effects_registry = {}
        self.transitions_registry = {}
        self._register_effects()
        self._register_transitions()
        
    def _register_effects(self):
        """註冊所有特效"""
        self.effects_registry = {
            EffectType.ZOOM_PAN: self._zoom_pan_effect,
            EffectType.PARALLAX: self._parallax_effect,
            EffectType.PARTICLE_SYSTEM: self._particle_system_effect,
            EffectType.LIGHT_RAYS: self._light_rays_effect,
            EffectType.CHROMATIC_ABERRATION: self._chromatic_aberration_effect,
            EffectType.FILM_BURN: self._film_burn_effect,
            EffectType.GLITCH_EFFECT: self._glitch_effect,
            EffectType.COLOR_DISPLACEMENT: self._color_displacement_effect,
            EffectType.VINTAGE_TV: self._vintage_tv_effect,
        }
        
    def _register_transitions(self):
        """註冊所有轉場"""
        self.transitions_registry = {
            TransitionType.FADE: self._fade_transition,
            TransitionType.CROSSFADE: self._crossfade_transition,
            TransitionType.SLIDE_LEFT: self._slide_left_transition,
            TransitionType.SLIDE_RIGHT: self._slide_right_transition,
            TransitionType.SLIDE_UP: self._slide_up_transition,
            TransitionType.SLIDE_DOWN: self._slide_down_transition,
            TransitionType.ZOOM_IN: self._zoom_in_transition,
            TransitionType.ZOOM_OUT: self._zoom_out_transition,
            TransitionType.ROTATE: self._rotate_transition,
            TransitionType.CIRCLE_WIPE: self._circle_wipe_transition,
            TransitionType.DIAGONAL_WIPE: self._diagonal_wipe_transition,
            TransitionType.PIXELATE: self._pixelate_transition,
            TransitionType.BLUR_TRANSITION: self._blur_transition,
            TransitionType.GLITCH: self._glitch_transition,
        }
        
    # ========== 特效實現 ==========
    
    def _zoom_pan_effect(self, clip: VideoClip, config: EffectConfig) -> VideoClip:
        """肯·伯恩斯效果（縮放和平移）"""
        params = config.parameters or {}
        start_zoom = params.get('start_zoom', 1.0)
        end_zoom = params.get('end_zoom', 1.2)
        start_pos = params.get('start_pos', ('center', 'center'))
        end_pos = params.get('end_pos', ('center', 'center'))
        
        def zoom_pan(get_frame, t):
            frame = get_frame(t)
            progress = min(t / clip.duration, 1.0)
            
            # 計算當前縮放比例
            current_zoom = start_zoom + (end_zoom - start_zoom) * progress
            
            # 應用縮放
            if current_zoom != 1.0:
                height, width = frame.shape[:2]
                new_height = int(height * current_zoom)
                new_width = int(width * current_zoom)
                
                if PIL_AVAILABLE:
                    pil_img = Image.fromarray(frame)
                    pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # 裁切到原始尺寸
                    left = (new_width - width) // 2
                    top = (new_height - height) // 2
                    pil_img = pil_img.crop((left, top, left + width, top + height))
                    
                    frame = np.array(pil_img)
            
            return frame
            
        return clip.fl(zoom_pan)
        
    def _parallax_effect(self, clip: VideoClip, config: EffectConfig) -> VideoClip:
        """視差效果"""
        params = config.parameters or {}
        layers = params.get('layers', 3)
        max_offset = params.get('max_offset', 50)
        
        def parallax(get_frame, t):
            frame = get_frame(t)
            progress = (t / clip.duration) * 2 * math.pi
            
            # 創建多個層的視差效果
            result = frame.copy()
            
            for layer in range(1, layers + 1):
                offset_x = int(math.sin(progress + layer * 0.5) * max_offset / layer)
                offset_y = int(math.cos(progress + layer * 0.3) * max_offset / layer)
                
                # 簡單的圖層偏移模擬
                # 這裡可以實現更複雜的多層視差
                if abs(offset_x) > 0 or abs(offset_y) > 0:
                    # 創建偏移效果的簡化版本
                    alpha = 0.3 / layer
                    shifted = np.roll(np.roll(frame, offset_x, axis=1), offset_y, axis=0)
                    result = (result * (1 - alpha) + shifted * alpha).astype(np.uint8)
            
            return result
            
        return clip.fl(parallax)
        
    def _particle_system_effect(self, clip: VideoClip, config: EffectConfig) -> VideoClip:
        """粒子系統效果"""
        params = config.parameters or {}
        particle_count = params.get('particle_count', 100)
        particle_color = params.get('particle_color', (255, 255, 255))
        
        def particles(get_frame, t):
            frame = get_frame(t)
            height, width = frame.shape[:2]
            
            if PIL_AVAILABLE:
                pil_img = Image.fromarray(frame)
                draw = ImageDraw.Draw(pil_img)
                
                # 生成粒子位置
                np.random.seed(int(t * 100))  # 確保一致性
                for _ in range(particle_count):
                    x = np.random.randint(0, width)
                    y = np.random.randint(0, height)
                    size = np.random.randint(1, 4)
                    
                    # 繪製粒子
                    draw.ellipse([x-size, y-size, x+size, y+size], fill=particle_color)
                
                frame = np.array(pil_img)
            
            return frame
            
        return clip.fl(particles)
        
    def _light_rays_effect(self, clip: VideoClip, config: EffectConfig) -> VideoClip:
        """光線效果"""
        params = config.parameters or {}
        ray_count = params.get('ray_count', 8)
        intensity = params.get('intensity', 0.3)
        
        def light_rays(get_frame, t):
            frame = get_frame(t)
            height, width = frame.shape[:2]
            
            if PIL_AVAILABLE:
                # 創建光線遮罩
                mask = Image.new('L', (width, height), 0)
                draw = ImageDraw.Draw(mask)
                
                center_x, center_y = width // 2, height // 2
                angle_step = 360 / ray_count
                
                for i in range(ray_count):
                    angle = math.radians(i * angle_step + t * 30)  # 旋轉光線
                    end_x = center_x + math.cos(angle) * width
                    end_y = center_y + math.sin(angle) * height
                    
                    # 繪製光線
                    draw.line([center_x, center_y, end_x, end_y], fill=255, width=5)
                
                # 模糊光線
                mask = mask.filter(ImageFilter.GaussianBlur(radius=10))
                mask_array = np.array(mask) / 255.0
                
                # 應用光線效果
                light_effect = np.stack([mask_array] * 3, axis=2)
                frame = frame + (light_effect * intensity * 255).astype(np.uint8)
                frame = np.clip(frame, 0, 255)
            
            return frame
            
        return clip.fl(light_rays)
        
    def _chromatic_aberration_effect(self, clip: VideoClip, config: EffectConfig) -> VideoClip:
        """色差效果"""
        params = config.parameters or {}
        offset = params.get('offset', 5)
        
        def chromatic_aberration(get_frame, t):
            frame = get_frame(t)
            
            # 分離RGB通道並創建偏移
            r_channel = frame[:, :, 0]
            g_channel = frame[:, :, 1] 
            b_channel = frame[:, :, 2]
            
            # 創建偏移
            r_shifted = np.roll(r_channel, offset, axis=1)
            b_shifted = np.roll(b_channel, -offset, axis=1)
            
            # 重組
            result = frame.copy()
            result[:, :, 0] = r_shifted
            result[:, :, 2] = b_shifted
            
            return result
            
        return clip.fl(chromatic_aberration)
        
    def _film_burn_effect(self, clip: VideoClip, config: EffectConfig) -> VideoClip:
        """膠片燒燬效果"""
        params = config.parameters or {}
        intensity = params.get('intensity', 0.5)
        
        def film_burn(get_frame, t):
            frame = get_frame(t)
            height, width = frame.shape[:2]
            
            if PIL_AVAILABLE:
                # 創建燒燬遮罩
                burn_mask = Image.new('L', (width, height), 0)
                draw = ImageDraw.Draw(burn_mask)
                
                # 隨機燒燬點
                np.random.seed(int(t * 50))
                num_burns = np.random.randint(5, 15)
                
                for _ in range(num_burns):
                    x = np.random.randint(0, width)
                    y = np.random.randint(0, height)
                    size = np.random.randint(20, 100)
                    
                    # 繪製燒燬圓形
                    draw.ellipse([x-size//2, y-size//2, x+size//2, y+size//2], fill=255)
                
                # 模糊燒燬邊緣
                burn_mask = burn_mask.filter(ImageFilter.GaussianBlur(radius=15))
                mask_array = np.array(burn_mask) / 255.0
                
                # 應用燒燬效果（增加橙色調）
                burn_color = np.array([255, 100, 0])  # 橙色
                burn_effect = np.outer(mask_array.flatten(), burn_color).reshape(height, width, 3)
                
                frame = frame * (1 - mask_array[:, :, None]) + burn_effect * intensity
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            
            return frame
            
        return clip.fl(film_burn)
        
    def _glitch_effect(self, clip: VideoClip, config: EffectConfig) -> VideoClip:
        """故障效果"""
        params = config.parameters or {}
        intensity = params.get('intensity', 0.5)
        
        def glitch(get_frame, t):
            frame = get_frame(t)
            height, width = frame.shape[:2]
            
            # 隨機決定是否應用故障
            np.random.seed(int(t * 60))
            if np.random.random() > 0.7:  # 30%概率應用故障
                # 水平線條故障
                num_lines = np.random.randint(1, 5)
                for _ in range(num_lines):
                    line_y = np.random.randint(0, height)
                    line_height = np.random.randint(1, 10)
                    offset = np.random.randint(-50, 50)
                    
                    if 0 <= line_y < height and 0 <= line_y + line_height < height:
                        # 水平位移
                        line_section = frame[line_y:line_y+line_height].copy()
                        if offset > 0:
                            frame[line_y:line_y+line_height, offset:] = line_section[:, :-offset]
                        elif offset < 0:
                            frame[line_y:line_y+line_height, :offset] = line_section[:, -offset:]
                
                # 色彩通道分離
                if np.random.random() > 0.5:
                    r_offset = np.random.randint(-10, 10)
                    frame[:, :, 0] = np.roll(frame[:, :, 0], r_offset, axis=1)
            
            return frame
            
        return clip.fl(glitch)
        
    def _color_displacement_effect(self, clip: VideoClip, config: EffectConfig) -> VideoClip:
        """顏色偏移效果"""
        params = config.parameters or {}
        displacement = params.get('displacement', 10)
        
        def color_displacement(get_frame, t):
            frame = get_frame(t)
            
            # 波形偏移
            wave_offset = int(math.sin(t * 2) * displacement)
            
            # 偏移RGB通道
            result = frame.copy()
            result[:, :, 0] = np.roll(frame[:, :, 0], wave_offset, axis=1)
            result[:, :, 2] = np.roll(frame[:, :, 2], -wave_offset, axis=1)
            
            return result
            
        return clip.fl(color_displacement)
        
    def _vintage_tv_effect(self, clip: VideoClip, config: EffectConfig) -> VideoClip:
        """復古電視效果"""
        params = config.parameters or {}
        scan_lines = params.get('scan_lines', True)
        static_noise = params.get('static_noise', 0.1)
        
        def vintage_tv(get_frame, t):
            frame = get_frame(t)
            height, width = frame.shape[:2]
            
            # 添加掃描線
            if scan_lines:
                for y in range(0, height, 4):  # 每4行一條掃描線
                    if y < height:
                        frame[y] = frame[y] * 0.8  # 降低掃描線亮度
            
            # 添加靜態噪聲
            if static_noise > 0:
                noise = np.random.random((height, width, 3)) * static_noise * 255
                frame = frame + noise.astype(np.uint8)
                frame = np.clip(frame, 0, 255)
            
            # 添加輕微的彎曲效果（簡化版）
            curve_strength = 5
            for y in range(height):
                offset = int(math.sin(y / height * math.pi) * curve_strength)
                if offset != 0:
                    frame[y] = np.roll(frame[y], offset, axis=0)
            
            return frame
            
        return clip.fl(vintage_tv)
        
    # ========== 轉場實現 ==========
    
    def _fade_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """淡入淡出轉場"""
        fade_out = clip1.fadeout(duration)
        fade_in = clip2.fadein(duration).set_start(clip1.duration - duration)
        return CompositeVideoClip([fade_out, fade_in])
        
    def _crossfade_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """交叉淡化轉場"""
        # 第一個片段淡出
        clip1_faded = clip1.fadeout(duration)
        # 第二個片段淡入，在轉場期間開始
        clip2_faded = clip2.fadein(duration).set_start(clip1.duration - duration)
        
        return CompositeVideoClip([clip1_faded, clip2_faded])
        
    def _slide_left_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """向左滑動轉場"""
        w, h = clip1.size
        
        # 第二個片段從右側進入
        clip2_sliding = clip2.set_position(lambda t: (-w + w * min(t / duration, 1), 0))
        clip2_sliding = clip2_sliding.set_start(clip1.duration - duration).set_duration(duration)
        
        # 第一個片段向左退出
        clip1_sliding = clip1.set_position(lambda t: (w * min(t / duration, 1) if t >= clip1.duration - duration else 0, 0))
        
        return CompositeVideoClip([clip1_sliding, clip2_sliding])
        
    def _slide_right_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """向右滑動轉場"""
        w, h = clip1.size
        
        # 第二個片段從左側進入
        clip2_sliding = clip2.set_position(lambda t: (w - w * min(t / duration, 1), 0))
        clip2_sliding = clip2_sliding.set_start(clip1.duration - duration).set_duration(duration)
        
        # 第一個片段向右退出
        clip1_sliding = clip1.set_position(lambda t: (-w * min(t / duration, 1) if t >= clip1.duration - duration else 0, 0))
        
        return CompositeVideoClip([clip1_sliding, clip2_sliding])
        
    def _zoom_in_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """縮放進入轉場"""
        # 第一個片段縮放出去
        def zoom_out_resize(t):
            if t < clip1.duration - duration:
                return 1
            progress = (t - (clip1.duration - duration)) / duration
            return 1 - progress * 0.5
            
        clip1_zoomed = clip1.resize(zoom_out_resize)
        
        # 第二個片段從小縮放進入
        def zoom_in_resize(t):
            progress = min(t / duration, 1)
            return 0.5 + progress * 0.5
            
        clip2_zoomed = clip2.resize(zoom_in_resize).set_start(clip1.duration - duration)
        
        return CompositeVideoClip([clip1_zoomed, clip2_zoomed])
        
    def _circle_wipe_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """圓形擦除轉場"""
        w, h = clip1.size
        center_x, center_y = w // 2, h // 2
        max_radius = math.sqrt(center_x**2 + center_y**2)
        
        def make_mask(t):
            progress = min(t / duration, 1)
            current_radius = progress * max_radius
            
            mask = np.zeros((h, w))
            y, x = np.ogrid[:h, :w]
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            mask[distance <= current_radius] = 1
            
            return mask
            
        # 創建遮罩動畫
        def masked_clip2(get_frame, t):
            if t < clip1.duration - duration:
                return clip1.get_frame(t)
            
            frame1 = clip1.get_frame(t)
            frame2 = clip2.get_frame(t - (clip1.duration - duration))
            mask = make_mask(t - (clip1.duration - duration))
            
            result = frame1.copy()
            mask_3d = np.stack([mask] * 3, axis=2)
            result = frame1 * (1 - mask_3d) + frame2 * mask_3d
            
            return result.astype(np.uint8)
            
        return clip1.fl(masked_clip2)
        
    def _blur_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """模糊轉場"""
        def blur_transition_func(get_frame, t):
            if t < clip1.duration - duration:
                return clip1.get_frame(t)
            elif t > clip1.duration:
                return clip2.get_frame(t - clip1.duration)
            else:
                # 轉場階段
                progress = (t - (clip1.duration - duration)) / duration
                
                frame1 = clip1.get_frame(t)
                frame2 = clip2.get_frame(0)  # 第二個片段的開始
                
                # 應用模糊
                if PIL_AVAILABLE:
                    blur_radius = int(progress * 15)  # 最大模糊半徑15
                    
                    pil_frame1 = Image.fromarray(frame1)
                    pil_frame2 = Image.fromarray(frame2)
                    
                    if blur_radius > 0:
                        pil_frame1 = pil_frame1.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                        pil_frame2 = pil_frame2.filter(ImageFilter.GaussianBlur(radius=15-blur_radius))
                    
                    # 混合兩個框架
                    result = Image.blend(pil_frame1, pil_frame2, progress)
                    return np.array(result)
                else:
                    # 簡單混合
                    return (frame1 * (1 - progress) + frame2 * progress).astype(np.uint8)
                    
        return clip1.fl(blur_transition_func)
        
    def _glitch_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """故障轉場"""
        def glitch_transition_func(get_frame, t):
            if t < clip1.duration - duration:
                return clip1.get_frame(t)
            elif t > clip1.duration:
                return clip2.get_frame(t - clip1.duration)
            else:
                # 故障轉場階段
                progress = (t - (clip1.duration - duration)) / duration
                
                frame1 = clip1.get_frame(t)
                frame2 = clip2.get_frame(0)
                
                # 創建故障效果
                np.random.seed(int(t * 100))
                
                if np.random.random() < 0.7:  # 70%概率顯示故障
                    # 隨機選擇顯示哪個框架的部分
                    height, width = frame1.shape[:2]
                    
                    # 創建隨機遮罩
                    mask = np.random.random((height, width)) < (1 - progress)
                    mask_3d = np.stack([mask] * 3, axis=2)
                    
                    result = frame1 * mask_3d + frame2 * (1 - mask_3d)
                    
                    # 添加色彩故障
                    if np.random.random() < 0.5:
                        offset = np.random.randint(-20, 20)
                        result[:, :, 0] = np.roll(result[:, :, 0], offset, axis=1)
                    
                    return result.astype(np.uint8)
                else:
                    # 正常混合
                    return (frame1 * (1 - progress) + frame2 * progress).astype(np.uint8)
                    
        return clip1.fl(glitch_transition_func)
        
    # ========== 公共接口 ==========
    
    def apply_effect(self, clip: VideoClip, effect_config: EffectConfig) -> VideoClip:
        """應用特效到視頻片段"""
        if effect_config.effect_type not in self.effects_registry:
            logger.warning(f"Unknown effect type: {effect_config.effect_type}")
            return clip
            
        effect_func = self.effects_registry[effect_config.effect_type]
        return effect_func(clip, effect_config)
        
    def apply_transition(
        self, 
        clip1: VideoClip, 
        clip2: VideoClip, 
        transition_type: TransitionType, 
        duration: float = 1.0
    ) -> VideoClip:
        """應用轉場效果"""
        if transition_type not in self.transitions_registry:
            logger.warning(f"Unknown transition type: {transition_type}")
            return CompositeVideoClip([clip1, clip2.set_start(clip1.duration)])
            
        transition_func = self.transitions_registry[transition_type]
        return transition_func(clip1, clip2, duration)
        
    def create_effect_chain(self, clip: VideoClip, effect_configs: List[EffectConfig]) -> VideoClip:
        """創建特效鏈"""
        result = clip
        for config in effect_configs:
            result = self.apply_effect(result, config)
        return result
        
    def get_available_effects(self) -> List[str]:
        """獲取可用特效列表"""
        return [effect.value for effect in EffectType]
        
    def get_available_transitions(self) -> List[str]:
        """獲取可用轉場列表"""
        return [transition.value for transition in TransitionType]


# 工廠函數和便捷接口
def create_effects_system() -> VideoEffectsSystem:
    """創建視頻特效系統實例"""
    return VideoEffectsSystem()

async def test_effects_system():
    """測試視頻特效系統"""
    print("🎭 Testing Video Effects System...")
    
    effects_system = create_effects_system()
    
    print(f"Available effects: {effects_system.get_available_effects()}")
    print(f"Available transitions: {effects_system.get_available_transitions()}")
    
    # 模擬測試（需要實際視頻才能完全測試）
    print("✅ Effects system initialized successfully!")
    
    return effects_system

if __name__ == "__main__":
    print("🎬 Video Effects System - Professional Video Effects & Transitions")
    print("=" * 70)
    
    # 檢查依賴
    print(f"MoviePy available: {MOVIEPY_AVAILABLE}")
    print(f"PIL available: {PIL_AVAILABLE}")
    print(f"OpenCV available: {OPENCV_AVAILABLE}")
    
    # 運行測試
    result = asyncio.run(test_effects_system())
    print(f"Effects system ready: {result is not None}")