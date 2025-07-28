import asyncio
import time
import uuid
import json
from typing import Dict, List, Optional, Any
import structlog
import httpx
from ..config import settings

logger = structlog.get_logger()


class SunoClient:
    """Suno AI music generation client for background music and audio content"""
    
    def __init__(self):
        self.api_key = settings.suno_api_key
        self.base_url = "https://api.suno.ai"
        self.http_client: Optional[httpx.AsyncClient] = None
        self.initialized = False
        
        # Music style presets for video platforms
        self.style_presets = {
            "background": {
                "genres": ["ambient", "lo-fi", "chill"],
                "moods": ["calm", "peaceful", "subtle"],
                "instruments": ["piano", "soft synthesizer", "ambient pads"]
            },
            "energetic": {
                "genres": ["electronic", "upbeat", "pop"],
                "moods": ["energetic", "uplifting", "motivating"],
                "instruments": ["electronic drums", "synthesizer", "bass"]
            },
            "cinematic": {
                "genres": ["orchestral", "epic", "dramatic"],
                "moods": ["epic", "emotional", "powerful"],
                "instruments": ["orchestra", "strings", "brass", "percussion"]
            },
            "acoustic": {
                "genres": ["acoustic", "folk", "indie"],
                "moods": ["warm", "natural", "intimate"],
                "instruments": ["acoustic guitar", "piano", "light percussion"]
            },
            "corporate": {
                "genres": ["corporate", "uplifting", "professional"],
                "moods": ["professional", "inspiring", "clean"],
                "instruments": ["piano", "strings", "light drums"]
            },
            "hip_hop": {
                "genres": ["hip-hop", "trap", "urban"],
                "moods": ["confident", "cool", "rhythmic"],
                "instruments": ["808 drums", "hi-hats", "bass", "synthesizer"]
            },
            "jazz": {
                "genres": ["jazz", "smooth", "sophisticated"],
                "moods": ["smooth", "sophisticated", "relaxed"],
                "instruments": ["piano", "saxophone", "upright bass", "drums"]
            }
        }
        
        # Platform-specific audio specifications
        self.platform_specs = {
            "tiktok": {"duration_range": (15, 60), "tempo": "medium_fast", "energy": "high"},
            "youtube": {"duration_range": (30, 300), "tempo": "variable", "energy": "medium"},
            "instagram": {"duration_range": (15, 90), "tempo": "medium", "energy": "medium_high"},
            "podcast": {"duration_range": (60, 600), "tempo": "slow", "energy": "low"}
        }
    
    async def initialize(self):
        """Initialize Suno client"""
        try:
            logger.info("Initializing Suno Client")
            
            if not self.api_key:
                logger.warning("Suno API key not provided, music generation will use fallback")
                self.initialized = True
                return
            
            # Create HTTP client with timeout
            timeout = httpx.Timeout(300.0)  # Music generation takes longer
            self.http_client = httpx.AsyncClient(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            # Test API connection
            await self._test_connection()
            
            self.initialized = True
            logger.info("Suno Client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Suno Client", error=str(e))
            # Don't raise - allow fallback music generation
            self.initialized = True
    
    async def shutdown(self):
        """Shutdown Suno client"""
        if self.http_client:
            await self.http_client.aclose()
        self.initialized = False
        logger.info("Suno Client shutdown complete")
    
    def is_healthy(self) -> bool:
        """Check if Suno client is healthy"""
        return self.initialized
    
    async def generate_music(
        self,
        prompt: str,
        style: str = "background",
        duration_seconds: int = 30,
        instrumental: bool = True,
        mood: str = "neutral",
        platform: str = "tiktok",
        custom_lyrics: Optional[str] = None,
        tempo: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate music using Suno AI"""
        try:
            start_time = time.time()
            generation_id = str(uuid.uuid4())
            
            logger.info(
                "Generating music with Suno",
                generation_id=generation_id,
                style=style,
                duration=duration_seconds,
                platform=platform
            )
            
            # Build enhanced prompt
            enhanced_prompt = self._build_music_prompt(
                prompt=prompt,
                style=style,
                mood=mood,
                duration_seconds=duration_seconds,
                instrumental=instrumental,
                platform=platform,
                tempo=tempo
            )
            
            # Generate music using Suno API
            if self.api_key and self.http_client:
                result = await self._generate_with_suno_api(
                    prompt=enhanced_prompt,
                    duration=duration_seconds,
                    instrumental=instrumental,
                    custom_lyrics=custom_lyrics,
                    generation_id=generation_id
                )
            else:
                # Fallback to procedural generation
                logger.info("Using fallback music generation")
                result = await self._generate_fallback_music(
                    style=style,
                    duration_seconds=duration_seconds,
                    mood=mood,
                    platform=platform,
                    generation_id=generation_id
                )
            
            generation_time = time.time() - start_time
            
            # Enhance result with metadata
            result.update({
                "generation_id": generation_id,
                "enhanced_prompt": enhanced_prompt,
                "original_prompt": prompt,
                "style": style,
                "mood": mood,
                "platform": platform,
                "generation_time_seconds": round(generation_time, 2),
                "status": "completed"
            })
            
            logger.info(
                "Music generation completed",
                generation_id=generation_id,
                duration=result.get("duration_seconds", 0),
                generation_time=generation_time
            )
            
            return result
            
        except Exception as e:
            logger.error("Music generation failed", prompt=prompt[:50], error=str(e))
            raise
    
    async def generate_variations(
        self,
        base_music_id: str,
        variation_count: int = 3,
        variation_strength: float = 0.5
    ) -> Dict[str, Any]:
        """Generate variations of existing music"""
        try:
            logger.info(
                "Generating music variations",
                base_music_id=base_music_id,
                count=variation_count
            )\n            \n            variations = []\n            \n            for i in range(variation_count):\n                variation_id = str(uuid.uuid4())\n                \n                # Generate variation (placeholder implementation)\n                variation = {\n                    \"variation_id\": variation_id,\n                    \"music_url\": f\"/storage/music/variation_{variation_id}.mp3\",\n                    \"variation_strength\": variation_strength,\n                    \"differences\": [\n                        \"Adjusted tempo\",\n                        \"Modified chord progression\",\n                        \"Changed instrumentation\"\n                    ]\n                }\n                \n                variations.append(variation)\n            \n            result = {\n                \"base_music_id\": base_music_id,\n                \"variations\": variations,\n                \"variation_count\": len(variations),\n                \"variation_strength\": variation_strength\n            }\n            \n            logger.info(\"Music variations generated\", count=len(variations))\n            return result\n            \n        except Exception as e:\n            logger.error(\"Music variation generation failed\", error=str(e))\n            raise
    
    async def extend_music(\n        self,\n        music_id: str,\n        additional_duration: int,\n        maintain_style: bool = True\n    ) -> Dict[str, Any]:\n        \"\"\"Extend existing music to longer duration\"\"\"\n        try:\n            logger.info(\n                \"Extending music\",\n                music_id=music_id,\n                additional_duration=additional_duration\n            )\n            \n            # This would integrate with Suno's music extension API\n            # For now, return placeholder result\n            \n            extended_id = str(uuid.uuid4())\n            \n            result = {\n                \"extended_id\": extended_id,\n                \"original_music_id\": music_id,\n                \"extended_url\": f\"/storage/music/extended_{extended_id}.mp3\",\n                \"original_duration\": 30,  # Placeholder\n                \"extended_duration\": 30 + additional_duration,\n                \"extension_method\": \"seamless_continuation\" if maintain_style else \"variation_based\",\n                \"status\": \"completed\"\n            }\n            \n            logger.info(\"Music extension completed\", extended_id=extended_id)\n            return result\n            \n        except Exception as e:\n            logger.error(\"Music extension failed\", error=str(e))\n            raise
    
    async def _generate_with_suno_api(\n        self,\n        prompt: str,\n        duration: int,\n        instrumental: bool,\n        custom_lyrics: Optional[str],\n        generation_id: str\n    ) -> Dict[str, Any]:\n        \"\"\"Generate music using actual Suno API\"\"\"\n        try:\n            # Prepare generation request\n            request_data = {\n                \"prompt\": prompt,\n                \"make_instrumental\": instrumental,\n                \"wait_audio\": True\n            }\n            \n            if custom_lyrics and not instrumental:\n                request_data[\"lyrics\"] = custom_lyrics\n            \n            # Submit generation request\n            response = await self.http_client.post(\n                f\"{self.base_url}/api/generate\",\n                json=request_data\n            )\n            response.raise_for_status()\n            \n            generation_data = response.json()\n            \n            # Wait for generation to complete\n            job_id = generation_data.get(\"id\")\n            music_url = await self._wait_for_generation(job_id)\n            \n            # Download and save music\n            music_data = await self._download_music(music_url)\n            local_url = await self._save_music(music_data, generation_id)\n            \n            return {\n                \"music_id\": generation_id,\n                \"music_url\": local_url,\n                \"suno_job_id\": job_id,\n                \"duration_seconds\": duration,\n                \"service\": \"suno_api\"\n            }\n            \n        except Exception as e:\n            logger.error(\"Suno API generation failed\", error=str(e))\n            # Fallback to procedural generation\n            return await self._generate_fallback_music(\n                style=\"background\",\n                duration_seconds=duration,\n                mood=\"neutral\",\n                platform=\"tiktok\",\n                generation_id=generation_id\n            )
    
    async def _generate_fallback_music(\n        self,\n        style: str,\n        duration_seconds: int,\n        mood: str,\n        platform: str,\n        generation_id: str\n    ) -> Dict[str, Any]:\n        \"\"\"Generate music using procedural/algorithmic methods as fallback\"\"\"\n        logger.info(\"Generating fallback music\", style=style, duration=duration_seconds)\n        \n        # Simulate music generation (in production, use actual synthesis)\n        await asyncio.sleep(2)  # Simulate processing time\n        \n        # Generate procedural music based on style\n        music_data = await self._create_procedural_music(\n            style=style,\n            duration_seconds=duration_seconds,\n            mood=mood\n        )\n        \n        # Save music file\n        music_url = await self._save_music(music_data, generation_id)\n        \n        return {\n            \"music_id\": generation_id,\n            \"music_url\": music_url,\n            \"duration_seconds\": duration_seconds,\n            \"service\": \"procedural_fallback\",\n            \"file_size_kb\": len(music_data) // 1024\n        }
    
    async def _create_procedural_music(\n        self,\n        style: str,\n        duration_seconds: int,\n        mood: str\n    ) -> bytes:\n        \"\"\"Create procedural music using algorithmic composition\"\"\"\n        # This is a placeholder - in production, you'd use libraries like:\n        # - pretty_midi for MIDI generation\n        # - pydub for audio synthesis\n        # - librosa for audio processing\n        # - FluidSynth for sound synthesis\n        \n        from pydub import AudioSegment\n        from pydub.generators import Sine, WhiteNoise\n        import random\n        \n        # Get style configuration\n        style_config = self.style_presets.get(style, self.style_presets[\"background\"])\n        \n        # Generate base composition\n        duration_ms = duration_seconds * 1000\n        \n        # Create harmonic structure based on mood\n        if mood == \"upbeat\":\n            base_frequencies = [261.63, 329.63, 392.00, 523.25]  # C Major chord\n        elif mood == \"calm\":\n            base_frequencies = [220.00, 261.63, 329.63, 440.00]  # A Minor chord\n        elif mood == \"dramatic\":\n            base_frequencies = [196.00, 246.94, 293.66, 369.99]  # G Minor chord\n        else:\n            base_frequencies = [261.63, 329.63, 392.00, 493.88]  # C Major 7th\n        \n        # Generate multiple layers\n        layers = []\n        \n        # Base harmony layer\n        for freq in base_frequencies:\n            tone = Sine(freq).to_audio_segment(duration=duration_ms)\n            tone = tone - 20  # Reduce volume\n            layers.append(tone)\n        \n        # Melody layer (simple procedural melody)\n        melody_notes = []\n        for i in range(0, duration_seconds * 2):  # 2 notes per second\n            note_freq = random.choice(base_frequencies) * random.choice([1, 1.25, 1.5])\n            note_duration = random.randint(250, 1000)\n            note = Sine(note_freq).to_audio_segment(duration=note_duration)\n            note = note - 15\n            \n            # Add note at specific time\n            start_time = i * 500\n            if start_time < duration_ms:\n                melody_notes.append((note, start_time))\n        \n        # Combine layers\n        composition = AudioSegment.silent(duration=duration_ms)\n        \n        # Add harmony layers\n        for layer in layers:\n            composition = composition.overlay(layer)\n        \n        # Add melody notes\n        for note, start_time in melody_notes:\n            composition = composition.overlay(note, position=start_time)\n        \n        # Add subtle ambient noise for texture\n        if style in [\"ambient\", \"background\"]:\n            noise = WhiteNoise().to_audio_segment(duration=duration_ms) - 45\n            composition = composition.overlay(noise)\n        \n        # Apply fades\n        fade_duration = min(2000, duration_ms // 10)\n        composition = composition.fade_in(fade_duration).fade_out(fade_duration)\n        \n        # Export to bytes\n        import io\n        output_buffer = io.BytesIO()\n        composition.export(output_buffer, format=\"mp3\", bitrate=\"128k\")\n        return output_buffer.getvalue()
    
    async def _wait_for_generation(self, job_id: str, max_wait: int = 300) -> str:\n        \"\"\"Wait for Suno generation to complete and return music URL\"\"\"\n        start_time = time.time()\n        \n        while time.time() - start_time < max_wait:\n            try:\n                response = await self.http_client.get(f\"{self.base_url}/api/feed/{job_id}\")\n                response.raise_for_status()\n                \n                data = response.json()\n                \n                if data.get(\"status\") == \"completed\":\n                    return data.get(\"audio_url\")\n                elif data.get(\"status\") == \"failed\":\n                    raise Exception(f\"Suno generation failed: {data.get('error')}\")\n                \n                # Wait before checking again\n                await asyncio.sleep(5)\n                \n            except Exception as e:\n                logger.error(\"Error checking generation status\", job_id=job_id, error=str(e))\n                await asyncio.sleep(10)\n        \n        raise Exception(f\"Music generation timed out after {max_wait} seconds\")
    
    async def _download_music(self, music_url: str) -> bytes:\n        \"\"\"Download generated music from URL\"\"\"\n        response = await self.http_client.get(music_url)\n        response.raise_for_status()\n        return response.content
    
    async def _save_music(self, music_data: bytes, music_id: str) -> str:\n        \"\"\"Save music to storage and return URL\"\"\"\n        import os\n        \n        filename = f\"generated_{music_id}.mp3\"\n        storage_path = f\"{settings.temp_storage_path}/music/{filename}\"\n        \n        # Ensure directory exists\n        os.makedirs(os.path.dirname(storage_path), exist_ok=True)\n        \n        # Save to local storage\n        with open(storage_path, 'wb') as f:\n            f.write(music_data)\n        \n        # Return URL (in production, this would be your CDN URL)\n        return f\"/storage/music/{filename}\"
    
    async def _test_connection(self):\n        \"\"\"Test connection to Suno API\"\"\"\n        try:\n            response = await self.http_client.get(f\"{self.base_url}/api/health\")\n            if response.status_code != 200:\n                logger.warning(\"Suno API connection test failed, using fallback\")\n        except Exception as e:\n            logger.warning(\"Suno API not accessible\", error=str(e))
    
    def _build_music_prompt(\n        self,\n        prompt: str,\n        style: str,\n        mood: str,\n        duration_seconds: int,\n        instrumental: bool,\n        platform: str,\n        tempo: Optional[str]\n    ) -> str:\n        \"\"\"Build enhanced prompt for music generation\"\"\"\n        # Get style configuration\n        style_config = self.style_presets.get(style, self.style_presets[\"background\"])\n        platform_config = self.platform_specs.get(platform, self.platform_specs[\"tiktok\"])\n        \n        # Build enhanced prompt\n        enhanced_parts = [prompt]\n        \n        # Add style elements\n        if style_config[\"genres\"]:\n            enhanced_parts.append(f\"Genre: {', '.join(style_config['genres'])}\")\n        \n        if style_config[\"moods\"]:\n            enhanced_parts.append(f\"Mood: {', '.join(style_config['moods'])}\")\n        \n        if style_config[\"instruments\"]:\n            enhanced_parts.append(f\"Instruments: {', '.join(style_config['instruments'])}\")\n        \n        # Add platform-specific elements\n        if platform_config[\"energy\"]:\n            enhanced_parts.append(f\"Energy level: {platform_config['energy']}\")\n        \n        # Add tempo if specified\n        if tempo:\n            enhanced_parts.append(f\"Tempo: {tempo}\")\n        elif platform_config[\"tempo\"]:\n            enhanced_parts.append(f\"Tempo: {platform_config['tempo']}\")\n        \n        # Add duration\n        enhanced_parts.append(f\"Duration: {duration_seconds} seconds\")\n        \n        # Add instrumental specification\n        if instrumental:\n            enhanced_parts.append(\"Instrumental only, no vocals\")\n        \n        # Add platform optimization\n        enhanced_parts.append(f\"Optimized for {platform} platform\")\n        \n        return \", \".join(enhanced_parts)
    \n    def get_supported_styles(self) -> Dict[str, Any]:\n        \"\"\"Get list of supported music styles\"\"\"\n        return {\n            \"styles\": [\n                {\n                    \"name\": style,\n                    \"description\": f\"Style featuring {', '.join(config['genres'])} with {', '.join(config['moods'])} mood\",\n                    \"genres\": config[\"genres\"],\n                    \"moods\": config[\"moods\"],\n                    \"typical_instruments\": config[\"instruments\"]\n                }\n                for style, config in self.style_presets.items()\n            ],\n            \"platforms\": [\n                {\n                    \"name\": platform,\n                    \"duration_range\": config[\"duration_range\"],\n                    \"recommended_tempo\": config[\"tempo\"],\n                    \"energy_level\": config[\"energy\"]\n                }\n                for platform, config in self.platform_specs.items()\n            ]\n        }