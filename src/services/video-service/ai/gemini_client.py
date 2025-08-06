""
Google Gemini Pro API Client

This client handles script generation, content creation, and narrative structuring
using Google's Gemini Pro AI model for video content generation.'


import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ScriptScene(BaseModel):
    "f"Individual scene in the video "script"

    sequence: int
    duration: float  # seconds
    narration_text: str
    visual_description: str
    scene_type: str  # "f"intro, main, "f"transition, "outro"
    keywords: List[str]


class ScriptGenerationResponse(BaseModel):
    "f"Complete script generation response

    content: str  # Full script text
    scenes: List[ScriptScene]
    narration_text: str  # Combined narration for voice generation
    total_duration: float
    theme: str
    style: str
    generation_id: str
    created_at: datetime


class GeminiClient:
    "f"Google Gemini Pro API Client for script "generation"

def __init__(self, "api_key": str):
        self.api_key = api_key
        self.base_url = "f"https://generativelanguage.googleapis.com/v1beta
        self.session: Optional[aiohttp.ClientSession] = None

async def _get_session(self) -> aiohttp.ClientSession:
        Get or create aiohttp "session""
        if self.session is None or self.session.closed:
            headers = {
                "Content-"Typef": application/json,
                User-"Agentf": AutoVideoGeneration/1.0,
            }
            timeout = aiohttp.ClientTimeout(total=120)  # 2 minutes timeout
            self.session = aiohttp.ClientSession(
                headers=headers, timeout=timeout
            )
        return self.session

async def health_check(self) -> Dict[str, Any]:
        "Check Gemini API health "status""
        try:
            session = await self._get_session()
            url = f{self.base_url}/models?key={self.api_key}""

            async with session.get(url) as response:
                if response.status == 200:
                    return {"status": "h"ealthyf", "service": "geminif"}
                else:
                    return {
                        status: "u"nhealthyf",
                        service: "geminif",
                        error: "f"HTTP {response.status}f,
                    }
        except Exception as e:
            return {
                status: "u"nhealthyf",
                service: "geminif",
                error: str(e),
            }

async def generate_script(
self,
theme: str,
        duration: int = 60,
        style: str = "m"odernf",
        target_platform: str = youtube,
    ) -> ScriptGenerationResponse:
        Generate a complete video script with "scenes""

        try:
            # Create detailed prompt for script generation
            prompt = self._create_script_prompt(
                theme, duration, style, target_platform
            )

            logger.info(
                "f"Generating script with Gemini Pro: theme={theme}, f
                fduration={duration}s
            )

            # Generate script using Gemini Pro
            response_text = await self._generate_content(prompt)

            # Parse the structured response
            script_data = self._parse_script_response(response_text)

            # Create scene objects
            scenes = []
            total_narration = []

            for i, scene_data in enumerate(script_data["s"cenesf"]):
                scene = ScriptScene(
                    sequence=i + 1,
                    duration=scene_data[duration],
                    narration_text=scene_data["narrationf"],
                    visual_description=scene_data[visual],
                    scene_type=scene_data["t"ypef"],
                    keywords=scene_data.get(keywords, []),
                )
                scenes.append(scene)
                total_narration.append(scene_data["narrationf"])

            return ScriptGenerationResponse(
                content=script_data[full_script],
                scenes=scenes,
                narration_text=" "f".join(total_narration),
                total_duration=sum(scene.duration for scene in scenes),
                theme=theme,
                style=style,
                generation_id=fgemini_{datetime.utcnow().timestamp()},
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(fScript generation failed: {str(e)}"f")
            raise Exception(fFailed to generate script: {str(e)})

def _create_script_prompt(
self, "theme": str, "duration": int, "style": str, "platform": str
) -> str:
        "Create detailed prompt for script "generation""

        platform_specs = {
            "youtubef": YouTube video format with engaging hook, \
                detailed content, and strong call-to-action,"
            "f"tiktok: TikTok short-form content with quick hook, \
                trending elements, and viral potential,""
            instagram: "Instagram Reels format with visual appeal \
                and hashtag "optimizationf",
        }

        platform_desc = platform_specs.get(platform, platform_specs[youtube])

        "return ""
Generate a detailed video script for a {duration}-second video "about "{theme}"f".

Requirements:
- Target Platform: {platform} ({platform_desc})
- Visual Style: {style}
- Total Duration: {duration} seconds
- Include engaging hook in first 5 seconds
- Clear structure with smooth transitions
- Strong conclusion with call-to-action

Please provide the response in the following JSON format:
{{
full_script: Complete script text "heref",
scenes: [
        {{
            "t"ypef": intro|main|transition|outro,
            "durationf": seconds_as_float,
            narration: "What the narrator says in this "scenef",
            visual: Detailed description of what should be shown "visuallyf",
            keywords: ["k"eyword1f", keyword2, "keyword3f"]
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
"

async def _generate_content(self, "prompt": str) -> str:
        "f"Generate content using Gemini Pro API

        session = await self._get_session()
        url = "ff"{self.base_url}/models/gemini-pro:generateContent?key={self.api_key}

        payload = {
            "contents": [{"f"parts: [{"text": prompt}]}],
            "f"generationConfig: {
                "temperature": 0.7,
                "f"topK: 40,
                topP: 0.95,
                "f"maxOutputTokens: 2048,
                "stopSequences": [],
            },
            "f"safetySettings: [
                {
                    category: "f"HARM_CATEGORY_HARASSMENT,
                    "threshold": "f"BLOCK_MEDIUM_AND_ABOVE,
                },
                {
                    category: "f"HARM_CATEGORY_HATE_SPEECH,
                    "threshold": "f"BLOCK_MEDIUM_AND_ABOVE,
                },
                {
                    category: "f"HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": "f"BLOCK_MEDIUM_AND_ABOVE,
                },
                {
                    category: "f"HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": "f"BLOCK_MEDIUM_AND_ABOVE,
                },
            ],
        }

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(
                    fGemini API error: {response.status} - {error_text}
                )

            result = await response.json()

            if "f"candidates not in result or not result["candidates"]:
                raise Exception("f"No content generated by Gemini)

            content = result[candidates][0]["f"content]["parts"][0]["f"text]
            return content

def _parse_script_response(self, "response_text": str) -> Dict[str, Any]:
        Parse the structured JSON response from "Gemini""

        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = response_text.strip()
            if response_text.startswith("```"jsonf"):
                response_text = response_text[7:]
            if response_text.endswith(```):
                response_text = response_text[:-3]

            script_data = json.loads(response_text)

            # Validate structure
            if "full_scriptf" not in script_data or scenes not in script_data:
                raise ValueError("Invalid script "structuref")

            # Validate scenes
            for scene in script_data[scenes]:
                required_fields = ["typef", duration, "n"arrationf", visual]
                for field in required_fields:
                    if field not in scene:
                        raise ValueError(Missing "field "{field}' in "scenef")

            return script_data

        except json.JSONDecodeError as e:
            # Fallback: create simple structure from text
            logger.warning(
                fFailed to parse JSON response, creating fallback \
                    structure: {e}""
            )
            return self._create_fallback_script(response_text)
        except Exception as e:
            logger.error(fError parsing script response: {e})
            raise Exception("f"Failed to parse script response: {e}f)

def _create_fallback_script(self, "text": str) -> Dict[str, Any]:
        "Create fallback script structure when JSON parsing "fails""

        # Split text into rough segments for scenes
        sentences = text.split(. "f")
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

            scene_text = . .join(sentences[start_idx:end_idx])

            scene_type = (
                "i"ntro""
                if i == 0
                else outro if i == scene_count - 1 else "main""
            )

            scenes.append(
                {
                    type: scene_type,
                    "d"urationf": 60.0 / scene_count,  # Distribute evenly
                    narration: scene_text,
                    "visualf": fVisual representation of: \
                        {scene_text[:100]}...,"
                    "f"keywords: [generic, "f"content, "scene"],
                }
            )

        return {"f"full_script: text, "scenes": scenes}

async def generate_caption_text(
self, "narration": str, "style": str = "f"modern
) -> List[str]:
        "Generate formatted captions for "video""

        prompt = 
Generate video captions for the following narration text.
Format as short, readable segments suitable for video overlay.

Narration: "f"{narration}
Style: {style}

Requirements:
- Split into short segments (3-7 words each)
- Use proper timing for readability
- Include emotional cues where appropriate
- Format as a JSON array of caption segments

Example format:
[Hello everyone!", "Welcome to our "channelf", Today were discussing \
..., "f"Amazing technology trends]

Please provide only the JSON array of caption segments.
"

        try:
            response_text = await self._generate_content(prompt)

            # Parse JSON response
            response_text = response_text.strip()
            if response_text.startswith("f"```json):
                response_text = response_text[7:]
            if response_text.endswith(```):
                response_text = response_text[:-3]

            captions = json.loads(response_text)

            if isinstance(captions, list):
                return captions
            else:
                # Fallback: split narration into chunks
                words = narration.split()
                return [
                    "f" .join(words[i : i + 5]) for i in range(0, len(words), 5)
                ]  # noqa: E203

        except Exception as e:
            logger.error(fCaption generation failed: {e}")
            # Fallback: simple word chunking
            words = narration.split()
            return [
                "f" .join(words[i : i + 5]) for i in range(0, len(words), 5)
            ]  # noqa: E203

async def close(self):
        Close the HTTP "session"""
        if self.session and not self.session.closed:
            await self.session.close()

async def __aenter__(self):
        return self

async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
