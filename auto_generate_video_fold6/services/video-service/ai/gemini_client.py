"""
Google Gemini Pro API Client

This client handles script generation, content creation, and narrative structuring
using Google's Gemini Pro AI model for video content generation.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ScriptScene(BaseModel):
    """Individual scene in the video script"""

    sequence: int
    duration: float  # seconds
    narration_text: str
    visual_description: str
    scene_type: str  # "intro", "main", "transition", "outro"
    keywords: List[str]


class ScriptGenerationResponse(BaseModel):
    """Complete script generation response"""

    content: str  # Full script text
    scenes: List[ScriptScene]
    narration_text: str  # Combined narration for voice generation
    total_duration: float
    theme: str
    style: str
    generation_id: str
    created_at: datetime


class GeminiClient:
    """Google Gemini Pro API Client for script generation"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AutoVideoGeneration/1.0",
            }
            timeout = aiohttp.ClientTimeout(total=120)  # 2 minutes timeout
            self.session = aiohttp.ClientSession(
                headers=headers, timeout=timeout
            )
        return self.session

    async def health_check(self) -> Dict[str, Any]:
        """Check Gemini API health status"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/models?key={self.api_key}"

            async with session.get(url) as response:
                if response.status == 200:
                    return {"status": "healthy", "service": "gemini"}
                else:
                    return {
                        "status": "unhealthy",
                        "service": "gemini",
                        "error": f"HTTP {response.status}",
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "gemini",
                "error": str(e),
            }

    async def generate_script(
        self,
        theme: str,
        duration: int = 60,
        style: str = "modern",
        target_platform: str = "youtube",
    ) -> ScriptGenerationResponse:
        """Generate a complete video script with scenes"""

        try:
            # Create detailed prompt for script generation
            prompt = self._create_script_prompt(
                theme, duration, style, target_platform
            )

            logger.info(
                f"Generating script with Gemini Pro: theme='{theme}', duration={duration}s"
            )

            # Generate script using Gemini Pro
            response_text = await self._generate_content(prompt)

            # Parse the structured response
            script_data = self._parse_script_response(response_text)

            # Create scene objects
            scenes = []
            total_narration = []

            for i, scene_data in enumerate(script_data["scenes"]):
                scene = ScriptScene(
                    sequence=i + 1,
                    duration=scene_data["duration"],
                    narration_text=scene_data["narration"],
                    visual_description=scene_data["visual"],
                    scene_type=scene_data["type"],
                    keywords=scene_data.get("keywords", []),
                )
                scenes.append(scene)
                total_narration.append(scene_data["narration"])

            return ScriptGenerationResponse(
                content=script_data["full_script"],
                scenes=scenes,
                narration_text=" ".join(total_narration),
                total_duration=sum(scene.duration for scene in scenes),
                theme=theme,
                style=style,
                generation_id=f"gemini_{datetime.utcnow().timestamp()}",
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            raise Exception(f"Failed to generate script: {str(e)}")

    def _create_script_prompt(
        self, theme: str, duration: int, style: str, platform: str
    ) -> str:
        """Create detailed prompt for script generation"""

        platform_specs = {
            "youtube": "YouTube video format with engaging hook, detailed content, and strong call-to-action",
            "tiktok": "TikTok short-form content with quick hook, trending elements, and viral potential",
            "instagram": "Instagram Reels format with visual appeal and hashtag optimization",
        }

        platform_desc = platform_specs.get(platform, platform_specs["youtube"])

        return f"""
Generate a detailed video script for a {duration}-second video about "{theme}".

Requirements:
- Target Platform: {platform} ({platform_desc})
- Visual Style: {style}
- Total Duration: {duration} seconds
- Include engaging hook in first 5 seconds
- Clear structure with smooth transitions
- Strong conclusion with call-to-action

Please provide the response in the following JSON format:
{{
    "full_script": "Complete script text here",
    "scenes": [
        {{
            "type": "intro|main|transition|outro",
            "duration": seconds_as_float,
            "narration": "What the narrator says in this scene",
            "visual": "Detailed description of what should be shown visually",
            "keywords": ["keyword1", "keyword2", "keyword3"]
        }}
    ]
}}

Guidelines for each scene:
1. Keep narration natural and engaging
2. Visual descriptions should be specific and detailed for image generation
3. Ensure smooth flow between scenes
4. Include relevant keywords for visual generation
5. Match the {style} aesthetic throughout

Focus on making the content informative, engaging, and optimized for {platform}.
Make sure the total duration of all scenes equals {duration} seconds.
"""

    async def _generate_content(self, prompt: str) -> str:
        """Generate content using Gemini Pro API"""

        session = await self._get_session()
        url = f"{self.base_url}/models/gemini-pro:generateContent?key={self.api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
                "stopSequences": [],
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
            ],
        }

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(
                    f"Gemini API error: {response.status} - {error_text}"
                )

            result = await response.json()

            if "candidates" not in result or not result["candidates"]:
                raise Exception("No content generated by Gemini")

            content = result["candidates"][0]["content"]["parts"][0]["text"]
            return content

    def _parse_script_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the structured JSON response from Gemini"""

        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            script_data = json.loads(response_text)

            # Validate structure
            if "full_script" not in script_data or "scenes" not in script_data:
                raise ValueError("Invalid script structure")

            # Validate scenes
            for scene in script_data["scenes"]:
                required_fields = ["type", "duration", "narration", "visual"]
                for field in required_fields:
                    if field not in scene:
                        raise ValueError(f"Missing field '{field}' in scene")

            return script_data

        except json.JSONDecodeError as e:
            # Fallback: create simple structure from text
            logger.warning(
                f"Failed to parse JSON response, creating fallback structure: {e}"
            )
            return self._create_fallback_script(response_text)
        except Exception as e:
            logger.error(f"Error parsing script response: {e}")
            raise Exception(f"Failed to parse script response: {e}")

    def _create_fallback_script(self, text: str) -> Dict[str, Any]:
        """Create fallback script structure when JSON parsing fails"""

        # Split text into rough segments for scenes
        sentences = text.split(". ")
        scene_count = max(3, min(8, len(sentences) // 2))  # 3-8 scenes

        scenes = []
        sentences_per_scene = len(sentences) // scene_count

        for i in range(scene_count):
            start_idx = i * sentences_per_scene
            end_idx = (
                start_idx + sentences_per_scene
                if i < scene_count - 1
                else len(sentences)
            )

            scene_text = ". ".join(sentences[start_idx:end_idx])

            scene_type = (
                "intro"
                if i == 0
                else "outro" if i == scene_count - 1 else "main"
            )

            scenes.append(
                {
                    "type": scene_type,
                    "duration": 60.0 / scene_count,  # Distribute evenly
                    "narration": scene_text,
                    "visual": f"Visual representation of: {scene_text[:100]}...",
                    "keywords": ["generic", "content", "scene"],
                }
            )

        return {"full_script": text, "scenes": scenes}

    async def generate_caption_text(
        self, narration: str, style: str = "modern"
    ) -> List[str]:
        """Generate formatted captions for video"""

        prompt = f"""
Generate video captions for the following narration text. Format as short, readable segments suitable for video overlay.

Narration: "{narration}"
Style: {style}

Requirements:
- Split into short segments (3-7 words each)
- Use proper timing for readability
- Include emotional cues where appropriate
- Format as a JSON array of caption segments

Example format:
["Hello everyone!", "Welcome to our channel", "Today we're discussing...", "Amazing technology trends"]

Please provide only the JSON array of caption segments.
"""

        try:
            response_text = await self._generate_content(prompt)

            # Parse JSON response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            captions = json.loads(response_text)

            if isinstance(captions, list):
                return captions
            else:
                # Fallback: split narration into chunks
                words = narration.split()
                return [
                    " ".join(words[i : i + 5]) for i in range(0, len(words), 5)
                ]

        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            # Fallback: simple word chunking
            words = narration.split()
            return [
                " ".join(words[i : i + 5]) for i in range(0, len(words), 5)
            ]

    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
