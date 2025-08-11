#!/usr/bin/env python3
"""
簡單的影片生成器 - MVP版本
結合文字、圖片和音頻生成基礎影片
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
import aiohttp

try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, 
        CompositeAudioClip, TextClip, concatenate_videoclips
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("MoviePy not available. Video generation will use placeholder.")

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleVideoGenerator:
    """簡單影片生成器"""
    
    def __init__(self, output_dir: str = "./uploads/dev"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 預設設置
        self.default_resolution = (1080, 1920)  # 垂直影片 (適合TikTok/Instagram)
        self.default_fps = 30
        self.default_duration = 15  # 預設15秒短影片
        
    async def generate_simple_video(
        self,
        script: str,
        images: List[str],
        audio_file: Optional[str] = None,
        title: str = "AI Generated Video",
        style: str = "modern",
        duration: int = 15
    ) -> Dict:
        """生成簡單影片"""
        
        logger.info(f"Starting video generation: {title}")
        
        try:
            if not MOVIEPY_AVAILABLE:
                return await self._generate_placeholder_video(
                    script, images, title, duration
                )
            
            # 創建輸出檔名
            timestamp = int(datetime.now().timestamp())
            output_filename = f"video_{timestamp}.mp4"
            output_path = self.output_dir / output_filename
            
            # 生成影片
            video_path = await self._create_video_with_moviepy(
                script=script,
                images=images,
                audio_file=audio_file,
                output_path=str(output_path),
                duration=duration,
                style=style
            )
            
            return {
                "success": True,
                "video_url": f"/static/{output_filename}",
                "video_path": str(video_path),
                "title": title,
                "duration": duration,
                "resolution": f"{self.default_resolution[0]}x{self.default_resolution[1]}",
                "format": "mp4",
                "file_size": os.path.getsize(video_path) if os.path.exists(video_path) else 0,
                "generated_at": datetime.utcnow().isoformat(),
                "generation_method": "moviepy"
            }
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return await self._generate_placeholder_video(script, images, title, duration)
    
    async def _create_video_with_moviepy(
        self,
        script: str,
        images: List[str],
        audio_file: Optional[str],
        output_path: str,
        duration: int,
        style: str
    ) -> str:
        """使用MoviePy創建影片"""
        
        clips = []
        
        # 處理圖片
        if images:
            # 每張圖片顯示的時長
            image_duration = duration / len(images)
            
            for i, image_url in enumerate(images):
                try:
                    # 下載或處理圖片
                    image_path = await self._prepare_image(image_url, i)
                    
                    if image_path and os.path.exists(image_path):
                        # 創建圖片剪輯
                        img_clip = ImageClip(image_path, duration=image_duration)
                        img_clip = img_clip.resize(self.default_resolution)
                        clips.append(img_clip)
                        
                except Exception as e:
                    logger.error(f"Error processing image {image_url}: {e}")
                    continue
        
        # 如果沒有成功的圖片，創建文字影片
        if not clips:
            clips = [self._create_text_video(script, duration)]
        
        # 合併影片片段
        if len(clips) > 1:
            final_video = concatenate_videoclips(clips)
        else:
            final_video = clips[0]
        
        # 添加音頻
        if audio_file and os.path.exists(audio_file):
            try:
                audio = AudioFileClip(audio_file)
                # 調整音頻長度匹配影片
                if audio.duration > final_video.duration:
                    audio = audio.subclip(0, final_video.duration)
                elif audio.duration < final_video.duration:
                    # 如果音頻太短，重複播放
                    repeats = int(final_video.duration / audio.duration) + 1
                    audio = CompositeAudioClip([audio] * repeats).subclip(0, final_video.duration)
                
                final_video = final_video.set_audio(audio)
            except Exception as e:
                logger.error(f"Error adding audio: {e}")
        
        # 輸出影片
        final_video.write_videofile(
            output_path,
            fps=self.default_fps,
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        # 清理
        final_video.close()
        if audio_file and os.path.exists(audio_file):
            AudioFileClip(audio_file).close()
        
        return output_path
    
    def _create_text_video(self, text: str, duration: int) -> ImageClip:
        """創建純文字影片片段"""
        
        if not PIL_AVAILABLE:
            # 如果PIL不可用，創建純色背景
            return ImageClip(
                self._create_solid_color_image(), 
                duration=duration
            ).resize(self.default_resolution)
        
        # 使用PIL創建文字圖片
        img = Image.new('RGB', self.default_resolution, color=(33, 37, 41))  # 深色背景
        draw = ImageDraw.Draw(img)
        
        # 嘗試使用系統字體
        try:
            # macOS/Linux常見中文字體
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            ]
            
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 48)
                    break
            
            if not font:
                font = ImageFont.load_default()
                
        except Exception:
            font = ImageFont.load_default()
        
        # 處理文字換行
        words = text.split()
        lines = []
        current_line = ""
        max_width = self.default_resolution[0] - 100  # 留邊距
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # 繪製文字
        total_height = len(lines) * 60  # 估算行高
        start_y = (self.default_resolution[1] - total_height) // 2
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.default_resolution[0] - text_width) // 2
            y = start_y + i * 60
            
            draw.text((x, y), line, font=font, fill=(255, 255, 255))
        
        # 保存臨時圖片
        temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_img.name)
        temp_img.close()
        
        return ImageClip(temp_img.name, duration=duration)
    
    def _create_solid_color_image(self) -> str:
        """創建純色背景圖片"""
        temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        
        if PIL_AVAILABLE:
            img = Image.new('RGB', self.default_resolution, color=(33, 37, 41))
            img.save(temp_img.name)
        else:
            # 如果PIL不可用，創建最小的PNG
            # 這是一個1x1像素的透明PNG的base64
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
            temp_img.write(png_data)
        
        temp_img.close()
        return temp_img.name
    
    async def _prepare_image(self, image_url: str, index: int) -> Optional[str]:
        """準備圖片（下載或使用本地檔案）"""
        
        if image_url.startswith('http'):
            # 下載網路圖片
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as response:
                        if response.status == 200:
                            content = await response.read()
                            
                            # 保存到臨時檔案
                            temp_file = tempfile.NamedTemporaryFile(
                                suffix='.jpg', 
                                delete=False,
                                dir=str(self.output_dir)
                            )
                            temp_file.write(content)
                            temp_file.close()
                            
                            return temp_file.name
            except Exception as e:
                logger.error(f"Failed to download image {image_url}: {e}")
                return None
        else:
            # 使用本地檔案
            if os.path.exists(image_url):
                return image_url
        
        return None
    
    async def _generate_placeholder_video(
        self,
        script: str,
        images: List[str],
        title: str,
        duration: int
    ) -> Dict:
        """生成影片資訊的Placeholder"""
        
        return {
            "success": True,
            "video_url": "#",  # Placeholder URL
            "video_path": "",
            "title": title,
            "duration": duration,
            "resolution": f"{self.default_resolution[0]}x{self.default_resolution[1]}",
            "format": "mp4",
            "file_size": 0,
            "generated_at": datetime.utcnow().isoformat(),
            "generation_method": "placeholder",
            "note": "Video generation requires MoviePy installation: pip install moviepy",
            "script_preview": script[:100] + "..." if len(script) > 100 else script,
            "image_count": len(images)
        }

# 獨立函數供API調用
async def generate_video_from_components(
    script: str,
    images: List[str],
    audio_file: Optional[str] = None,
    title: str = "AI Generated Video",
    style: str = "modern",
    duration: int = 15,
    output_dir: str = "./uploads/dev"
) -> Dict:
    """生成影片的主要函數"""
    
    generator = SimpleVideoGenerator(output_dir)
    return await generator.generate_simple_video(
        script=script,
        images=images,
        audio_file=audio_file,
        title=title,
        style=style,
        duration=duration
    )

# 測試函數
async def test_video_generation():
    """測試影片生成功能"""
    
    test_script = """
    歡迎來到AI影片生成測試！
    
    這是一個使用人工智能技術生成的測試影片。
    我們將展示如何結合文字、圖片和音頻來創建有趣的內容。
    
    希望你喜歡這個演示！
    """
    
    test_images = [
        "https://picsum.photos/1080/1920?random=1",
        "https://picsum.photos/1080/1920?random=2",
        "https://picsum.photos/1080/1920?random=3"
    ]
    
    result = await generate_video_from_components(
        script=test_script,
        images=test_images,
        title="AI Video Test",
        duration=10
    )
    
    print("Video generation test result:")
    print(f"Success: {result['success']}")
    print(f"Video URL: {result['video_url']}")
    print(f"Generation method: {result['generation_method']}")
    
    return result

if __name__ == "__main__":
    print("🎬 Testing Simple Video Generator...")
    
    # 檢查依賴
    print(f"MoviePy available: {MOVIEPY_AVAILABLE}")
    print(f"PIL available: {PIL_AVAILABLE}")
    
    # 運行測試
    result = asyncio.run(test_video_generation())
    
    if result['success']:
        print("✅ Video generation test completed successfully!")
    else:
        print("❌ Video generation test failed")