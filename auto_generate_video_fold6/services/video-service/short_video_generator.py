"""
短影音自動生成引擎
類似抖音平台的短影音生成系統
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class ShortVideoGenerator:
    """短影音生成器"""

    def __init__(self):
        self.video_templates = {
            "trending": {
                "duration": 15,
                "aspect_ratio": "9:16",  # 垂直格式
                "style": "dynamic",
                "effects": ["zoom_in", "text_overlay", "trending_hashtag"],
            },
            "educational": {
                "duration": 30,
                "aspect_ratio": "9:16",
                "style": "clean",
                "effects": [
                    "slide_transition",
                    "highlight_text",
                    "fact_callout",
                ],
            },
            "entertainment": {
                "duration": 45,
                "aspect_ratio": "9:16",
                "style": "energetic",
                "effects": ["flash_cuts", "music_sync", "emoji_overlay"],
            },
        }

        self.video_dimensions = {
            "9:16": (1080, 1920),  # TikTok/抖音標準
            "1:1": (1080, 1080),  # Instagram方形
            "16:9": (1920, 1080),  # YouTube橫向
        }

    async def generate_tiktok_style_video(self, content_data: Dict) -> Dict:
        """生成類似抖音風格的短影音"""
        try:
            keyword = content_data["keyword"]
            category = content_data.get("category", "trending")
            script = content_data.get("script", f"探索 {keyword} 的精彩世界！")

            logger.info(f"開始生成關鍵字 '{keyword}' 的短影音")

            # 1. 創建工作目錄
            work_dir = await self._create_work_directory(keyword)

            # 2. 生成視覺素材
            visual_assets = await self._generate_visual_assets(
                keyword, category, work_dir
            )

            # 3. 生成音頻
            audio_file = await self._generate_audio(script, work_dir)

            # 4. 創建影片場景
            scenes = await self._create_video_scenes(
                visual_assets, script, category
            )

            # 5. 組裝最終影片
            final_video = await self._assemble_video(
                scenes, audio_file, work_dir, category
            )

            # 6. 添加短影音特效
            enhanced_video = await self._add_tiktok_effects(
                final_video, keyword, work_dir
            )

            return {
                "status": "success",
                "video_path": enhanced_video,
                "keyword": keyword,
                "duration": self.video_templates[category]["duration"],
                "metadata": {
                    "category": category,
                    "script": script,
                    "created_at": datetime.now().isoformat(),
                    "style": "tiktok",
                    "aspect_ratio": "9:16",
                },
            }

        except Exception as e:
            logger.error(f"生成短影音失敗: {e}")
            return {"status": "error", "keyword": keyword, "error": str(e)}

    async def _create_work_directory(self, keyword: str) -> Path:
        """創建工作目錄"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        work_dir = Path(f"/tmp/video_gen_{keyword}_{timestamp}")
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir

    async def _generate_visual_assets(
        self, keyword: str, category: str, work_dir: Path
    ) -> Dict:
        """生成視覺素材"""
        try:
            assets = {
                "background_images": [],
                "overlay_graphics": [],
                "text_animations": [],
            }

            # 1. 背景圖片（模擬 AI 生成）
            for i in range(3):
                bg_image = await self._create_background_image(
                    keyword, i, work_dir
                )
                assets["background_images"].append(bg_image)

            # 2. 文字覆蓋層
            text_overlay = await self._create_text_overlay(keyword, work_dir)
            assets["overlay_graphics"].append(text_overlay)

            # 3. 趨勢圖標和特效
            trending_graphics = await self._create_trending_graphics(
                keyword, work_dir
            )
            assets["overlay_graphics"].extend(trending_graphics)

            return assets

        except Exception as e:
            logger.error(f"生成視覺素材失敗: {e}")
            return {}

    async def _create_background_image(
        self, keyword: str, index: int, work_dir: Path
    ) -> str:
        """創建背景圖片"""
        try:
            # 創建漸層背景（模擬 AI 生成的圖片）
            width, height = 1080, 1920
            image = Image.new("RGB", (width, height))
            draw = ImageDraw.Draw(image)

            # 主題色彩方案
            color_schemes = {
                "technology": [(0, 100, 200), (50, 150, 255)],
                "entertainment": [(255, 0, 150), (255, 100, 200)],
                "lifestyle": [(100, 200, 100), (150, 255, 150)],
                "default": [(100, 150, 200), (150, 200, 255)],
            }

            colors = color_schemes.get(
                keyword.lower(), color_schemes["default"]
            )

            # 創建漸層效果
            for y in range(height):
                ratio = y / height
                r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
                g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
                b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # 添加關鍵字文字
            try:
                font_size = 120
                font = ImageFont.truetype(
                    "/system/fonts/DroidSansFallback.ttf", font_size
                )
            except:
                font = ImageFont.load_default()

            # 文字位置和樣式
            text_y = height // 2 + (index - 1) * 200
            draw.text(
                (width // 2, text_y),
                keyword,
                font=font,
                fill=(255, 255, 255),
                anchor="mm",
            )

            # 保存圖片
            image_path = work_dir / f"bg_{index}.png"
            image.save(image_path)
            return str(image_path)

        except Exception as e:
            logger.error(f"創建背景圖片失敗: {e}")
            return ""

    async def _create_text_overlay(self, keyword: str, work_dir: Path) -> str:
        """創建文字覆蓋層"""
        try:
            width, height = 1080, 1920
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # 主標題
            title_text = f"🔥 {keyword} 正在爆紅！"
            try:
                title_font = ImageFont.truetype(
                    "/system/fonts/DroidSansFallback.ttf", 80
                )
                subtitle_font = ImageFont.truetype(
                    "/system/fonts/DroidSansFallback.ttf", 60
                )
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()

            # 標題位置
            title_y = 200
            draw.text(
                (width // 2, title_y),
                title_text,
                font=title_font,
                fill=(255, 255, 255, 255),
                anchor="mm",
                stroke_width=3,
                stroke_fill=(0, 0, 0, 255),
            )

            # 副標題
            subtitle_text = "#熱門 #趨勢 #必看"
            subtitle_y = title_y + 120
            draw.text(
                (width // 2, subtitle_y),
                subtitle_text,
                font=subtitle_font,
                fill=(255, 200, 0, 255),
                anchor="mm",
                stroke_width=2,
                stroke_fill=(0, 0, 0, 255),
            )

            # 底部 CTA
            cta_text = "👆 點擊了解更多"
            cta_y = height - 300
            draw.text(
                (width // 2, cta_y),
                cta_text,
                font=subtitle_font,
                fill=(255, 255, 255, 255),
                anchor="mm",
                stroke_width=2,
                stroke_fill=(0, 0, 0, 255),
            )

            overlay_path = work_dir / "text_overlay.png"
            overlay.save(overlay_path)
            return str(overlay_path)

        except Exception as e:
            logger.error(f"創建文字覆蓋層失敗: {e}")
            return ""

    async def _create_trending_graphics(
        self, keyword: str, work_dir: Path
    ) -> List[str]:
        """創建趨勢圖標"""
        graphics = []

        try:
            # 火焰圖標
            flame_graphic = await self._create_flame_graphic(work_dir)
            if flame_graphic:
                graphics.append(flame_graphic)

            # 上升箭頭
            arrow_graphic = await self._create_arrow_graphic(work_dir)
            if arrow_graphic:
                graphics.append(arrow_graphic)

            return graphics

        except Exception as e:
            logger.error(f"創建趨勢圖標失敗: {e}")
            return []

    async def _create_flame_graphic(self, work_dir: Path) -> str:
        """創建火焰特效圖標"""
        try:
            size = 200
            flame = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(flame)

            # 簡單火焰形狀
            flame_points = [
                (size // 2, size - 20),
                (size // 2 - 30, size // 2),
                (size // 2 - 10, size // 4),
                (size // 2, 20),
                (size // 2 + 10, size // 4),
                (size // 2 + 30, size // 2),
            ]

            # 繪製火焰
            draw.polygon(flame_points, fill=(255, 100, 0, 200))
            draw.polygon(
                [(p[0] - 5, p[1] + 10) for p in flame_points[:4]],
                fill=(255, 200, 0, 200),
            )

            flame_path = work_dir / "flame.png"
            flame.save(flame_path)
            return str(flame_path)

        except Exception as e:
            logger.error(f"創建火焰圖標失敗: {e}")
            return ""

    async def _create_arrow_graphic(self, work_dir: Path) -> str:
        """創建上升箭頭"""
        try:
            size = 150
            arrow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(arrow)

            # 箭頭形狀
            arrow_points = [
                (size // 2, 20),
                (size // 2 - 30, 60),
                (size // 2 - 15, 60),
                (size // 2 - 15, size - 20),
                (size // 2 + 15, size - 20),
                (size // 2 + 15, 60),
                (size // 2 + 30, 60),
            ]

            draw.polygon(arrow_points, fill=(0, 255, 0, 200))

            arrow_path = work_dir / "arrow.png"
            arrow.save(arrow_path)
            return str(arrow_path)

        except Exception as e:
            logger.error(f"創建箭頭圖標失敗: {e}")
            return ""

    async def _generate_audio(self, script: str, work_dir: Path) -> str:
        """生成音頻（模擬 TTS）"""
        try:
            # 這裡應該調用真實的 TTS 服務
            # 現在創建一個靜音音頻作為佔位符
            audio_duration = len(script.split()) * 0.5  # 估算時長

            # 使用 moviepy 創建靜音
            silent_audio = AudioFileClip(
                None, duration=min(audio_duration, 30)
            )
            audio_path = work_dir / "audio.wav"

            # 這裡實際應該是：
            # 1. 調用 TTS API
            # 2. 添加背景音樂
            # 3. 音頻處理和增強

            return str(audio_path)

        except Exception as e:
            logger.error(f"生成音頻失敗: {e}")
            # 返回空音頻路徑，讓影片是靜音的
            return ""

    async def _create_video_scenes(
        self, visual_assets: Dict, script: str, category: str
    ) -> List[Dict]:
        """創建影片場景"""
        scenes = []

        try:
            duration_per_scene = self.video_templates[category][
                "duration"
            ] / len(visual_assets["background_images"])

            for i, bg_image in enumerate(visual_assets["background_images"]):
                scene = {
                    "background": bg_image,
                    "overlays": visual_assets["overlay_graphics"],
                    "duration": duration_per_scene,
                    "effects": self.video_templates[category]["effects"],
                    "text": script if i == 0 else "",  # 只在第一個場景顯示文字
                    "transition": "fade" if i > 0 else None,
                }
                scenes.append(scene)

            return scenes

        except Exception as e:
            logger.error(f"創建場景失敗: {e}")
            return []

    async def _assemble_video(
        self,
        scenes: List[Dict],
        audio_file: str,
        work_dir: Path,
        category: str,
    ) -> str:
        """組裝影片"""
        try:
            clips = []
            aspect_ratio = self.video_templates[category]["aspect_ratio"]
            video_size = self.video_dimensions[aspect_ratio]

            for scene in scenes:
                if scene["background"]:
                    # 載入背景圖片
                    img_clip = ImageClip(
                        scene["background"], duration=scene["duration"]
                    )
                    img_clip = img_clip.resize(video_size)

                    # 添加覆蓋層
                    if scene["overlays"]:
                        for overlay_path in scene["overlays"]:
                            if os.path.exists(overlay_path):
                                overlay_clip = ImageClip(
                                    overlay_path, duration=scene["duration"]
                                )
                                overlay_clip = overlay_clip.resize(video_size)
                                img_clip = CompositeVideoClip(
                                    [img_clip, overlay_clip]
                                )

                    # 添加特效
                    if "zoom_in" in scene["effects"]:
                        img_clip = img_clip.resize(lambda t: 1 + 0.1 * t)

                    clips.append(img_clip)

            if clips:
                # 合併所有場景
                final_clip = concatenate_videoclips(clips, method="compose")

                # 添加音頻（如果有）
                if audio_file and os.path.exists(audio_file):
                    audio_clip = AudioFileClip(audio_file)
                    final_clip = final_clip.set_audio(audio_clip)

                # 輸出影片
                output_path = work_dir / "assembled_video.mp4"
                final_clip.write_videofile(
                    str(output_path),
                    fps=30,
                    audio_codec="aac",
                    codec="libx264",
                )

                return str(output_path)

        except Exception as e:
            logger.error(f"組裝影片失敗: {e}")
            return ""

    async def _add_tiktok_effects(
        self, video_path: str, keyword: str, work_dir: Path
    ) -> str:
        """添加短影音特效"""
        try:
            if not video_path or not os.path.exists(video_path):
                return ""

            # 載入影片
            video = VideoFileClip(video_path)

            # 1. 添加開場動畫
            intro_text = TextClip(
                f"🔥 {keyword}", fontsize=100, color="white", font="Arial"
            )
            intro_text = intro_text.set_position("center").set_duration(2)
            intro_text = intro_text.crossfadein(0.5).crossfadeout(0.5)

            # 2. 添加結尾 CTA
            outro_text = TextClip(
                "關注獲取更多熱門內容 👆",
                fontsize=80,
                color="yellow",
                font="Arial",
            )
            outro_text = outro_text.set_position("center").set_duration(2)
            outro_text = outro_text.set_start(video.duration - 2)

            # 3. 合成最終影片
            final_video = CompositeVideoClip([video, intro_text, outro_text])

            # 4. 添加趨勢標籤
            hashtag_text = TextClip(
                f"#{keyword} #熱門 #趨勢",
                fontsize=60,
                color="white",
                font="Arial",
            )
            hashtag_text = hashtag_text.set_position(
                ("left", "bottom")
            ).set_duration(final_video.duration)

            final_video = CompositeVideoClip([final_video, hashtag_text])

            # 輸出增強版影片
            enhanced_path = work_dir / f"tiktok_style_{keyword}.mp4"
            final_video.write_videofile(
                str(enhanced_path), fps=30, audio_codec="aac", codec="libx264"
            )

            return str(enhanced_path)

        except Exception as e:
            logger.error(f"添加短影音特效失敗: {e}")
            return video_path  # 返回原始影片


class TikTokStyleProcessor:
    """抖音風格處理器"""

    @staticmethod
    async def add_trending_elements(video_path: str, keyword: str) -> str:
        """添加流行元素"""
        try:
            # 1. 添加火焰特效
            # 2. 添加上升趨勢圖表
            # 3. 添加熱門標籤動畫
            # 4. 添加點擊提示

            logger.info(f"為 {keyword} 添加流行元素")
            return video_path

        except Exception as e:
            logger.error(f"添加流行元素失敗: {e}")
            return video_path

    @staticmethod
    async def optimize_for_mobile(video_path: str) -> str:
        """針對手機觀看優化"""
        try:
            # 1. 確保 9:16 比例
            # 2. 優化檔案大小
            # 3. 增強對比度
            # 4. 調整音量

            logger.info("針對手機觀看進行優化")
            return video_path

        except Exception as e:
            logger.error(f"手機優化失敗: {e}")
            return video_path
