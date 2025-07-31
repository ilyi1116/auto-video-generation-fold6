import asyncio
import time
import uuid
from typing import Any, Dict, List

import google.generativeai as genai
import openai
import structlog

from ..config import settings

logger = structlog.get_logger()


class TextGenerator:
    """AI-powered text generation service for scripts, titles, and content"""

    def __init__(self):
        self.openai_client = None
        self.google_client = None
        self.initialized = False

    async def initialize(self):
        """Initialize text generation services"""
        try:
            logger.info("Initializing Text Generator")

            # Initialize OpenAI
            if settings.openai_api_key:
                self.openai_client = openai.AsyncOpenAI(
                    api_key=settings.openai_api_key
                )
                logger.info("OpenAI client initialized")

            # Initialize Google Gemini
            if settings.google_api_key:
                genai.configure(api_key=settings.google_api_key)
                self.google_client = genai.GenerativeModel("gemini-pro")
                logger.info("Google Gemini client initialized")

            self.initialized = True
            logger.info("Text Generator initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Text Generator", error=str(e))
            raise

    async def shutdown(self):
        """Shutdown text generation services"""
        if self.openai_client:
            await self.openai_client.close()
        self.initialized = False
        logger.info("Text Generator shutdown complete")

    def is_healthy(self) -> bool:
        """Check if text generation service is healthy"""
        return self.initialized and (self.openai_client or self.google_client)

    async def generate_script(
        self,
        topic: str,
        style: str = "engaging",
        duration_seconds: int = 60,
        target_audience: str = "general",
        keywords: List[str] = None,
        tone: str = "casual",
    ) -> Dict[str, Any]:
        """Generate video script based on parameters"""
        try:
            start_time = time.time()
            script_id = str(uuid.uuid4())

            logger.info(
                "Generating script",
                script_id=script_id,
                topic=topic,
                style=style,
                duration=duration_seconds,
            )

            # Build the prompt
            prompt = self._build_script_prompt(
                topic=topic,
                style=style,
                duration_seconds=duration_seconds,
                target_audience=target_audience,
                keywords=keywords or [],
                tone=tone,
            )

            # Generate using available service
            content = await self._generate_text(prompt, max_tokens=800)

            # Calculate metrics
            word_count = len(content.split())
            estimated_duration = self._estimate_reading_time(content)
            generation_time = time.time() - start_time

            result = {
                "script_id": script_id,
                "content": content,
                "word_count": word_count,
                "estimated_duration": estimated_duration,
                "style": style,
                "status": "generated",
                "generation_time_seconds": round(generation_time, 2),
                "metadata": {
                    "topic": topic,
                    "target_audience": target_audience,
                    "keywords": keywords,
                    "tone": tone,
                    "requested_duration": duration_seconds,
                },
            }

            logger.info(
                "Script generated successfully",
                script_id=script_id,
                word_count=word_count,
                duration=estimated_duration,
                generation_time=generation_time,
            )

            return result

        except Exception as e:
            logger.error("Script generation failed", topic=topic, error=str(e))
            raise

    async def generate_titles(
        self,
        script_content: str,
        style: str = "catchy",
        max_length: int = 100,
        target_keywords: List[str] = None,
    ) -> Dict[str, Any]:
        """Generate catchy titles based on script content"""
        try:
            logger.info(
                "Generating titles", style=style, max_length=max_length
            )

            # Build the prompt for title generation
            prompt = self._build_title_prompt(
                script_content=script_content,
                style=style,
                max_length=max_length,
                target_keywords=target_keywords or [],
            )

            # Generate titles
            response = await self._generate_text(prompt, max_tokens=300)

            # Parse titles from response
            titles = self._parse_titles(response)

            # Select the best title based on criteria
            recommended_title = self._select_best_title(
                titles, style, max_length
            )

            result = {
                "titles": titles,
                "recommended_title": recommended_title,
                "style": style,
                "criteria": {
                    "max_length": max_length,
                    "target_keywords": target_keywords,
                    "style": style,
                },
            }

            logger.info("Titles generated successfully", count=len(titles))
            return result

        except Exception as e:
            logger.error("Title generation failed", error=str(e))
            raise

    async def optimize_script(
        self, script_content: str, target_duration: int
    ) -> Dict[str, Any]:
        """Optimize script for specific duration and engagement"""
        try:
            logger.info("Optimizing script", target_duration=target_duration)

            current_duration = self._estimate_reading_time(script_content)

            if abs(current_duration - target_duration) <= 5:
                # Script is already close to target duration
                return {
                    "optimized_content": script_content,
                    "original_duration": current_duration,
                    "optimized_duration": current_duration,
                    "changes_made": [],
                    "optimization_score": 100,
                }

            # Build optimization prompt
            prompt = self._build_optimization_prompt(
                script_content=script_content,
                current_duration=current_duration,
                target_duration=target_duration,
            )

            # Generate optimized script
            optimized_content = await self._generate_text(
                prompt, max_tokens=800
            )
            optimized_duration = self._estimate_reading_time(optimized_content)

            # Calculate optimization metrics
            changes_made = self._analyze_changes(
                script_content, optimized_content
            )
            optimization_score = self._calculate_optimization_score(
                target_duration, optimized_duration, current_duration
            )

            result = {
                "optimized_content": optimized_content,
                "original_duration": current_duration,
                "optimized_duration": optimized_duration,
                "target_duration": target_duration,
                "changes_made": changes_made,
                "optimization_score": optimization_score,
                "improvement_percentage": round(
                    (
                        (
                            current_duration
                            - abs(optimized_duration - target_duration)
                        )
                        / current_duration
                    )
                    * 100,
                    2,
                ),
            }

            logger.info(
                "Script optimization completed",
                original_duration=current_duration,
                optimized_duration=optimized_duration,
                score=optimization_score,
            )

            return result

        except Exception as e:
            logger.error("Script optimization failed", error=str(e))
            raise

    async def _generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using available AI service"""
        if self.openai_client:
            return await self._generate_with_openai(prompt, max_tokens)
        elif self.google_client:
            return await self._generate_with_gemini(prompt, max_tokens)
        else:
            raise Exception("No AI text generation service available")

    async def _generate_with_openai(self, prompt: str, max_tokens: int) -> str:
        """Generate text using OpenAI GPT"""
        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7,
            presence_penalty=0.1,
            frequency_penalty=0.1,
        )
        return response.choices[0].message.content.strip()

    async def _generate_with_gemini(self, prompt: str, max_tokens: int) -> str:
        """Generate text using Google Gemini"""
        response = await asyncio.to_thread(
            self.google_client.generate_content,
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
            ),
        )
        return response.text.strip()

    def _build_script_prompt(
        self,
        topic: str,
        style: str,
        duration_seconds: int,
        target_audience: str,
        keywords: List[str],
        tone: str,
    ) -> str:
        """Build prompt for script generation"""
        keyword_text = ", ".join(keywords) if keywords else ""

        return f"""Create an engaging video script for social media \
            platforms like TikTok and YouTube Shorts.

REQUIREMENTS:
- Topic: {topic}
- Style: {style}
- Target Duration: {duration_seconds} seconds (
    approximately {duration_seconds * 2.5} words)
- Target Audience: {target_audience}
- Tone: {tone}
{f'- Include Keywords: {keyword_text}' if keyword_text else ''}

SCRIPT GUIDELINES:
1. Start with a strong hook in the first 3 seconds
2. Use conversational, direct language
3. Include clear calls-to-action
4. Structure for vertical video format
5. Use engaging transitions between points
6. End with a memorable conclusion

STYLE CHARACTERISTICS:
- Engaging: Use storytelling, personal examples, emotional hooks
- Informative: Focus on facts, statistics, educational value
- Humorous: Include light humor, wordplay, relatable situations
- Professional: Use formal language, expert positioning

Please write ONLY the script content, no additional formatting or \
    explanations."""

    def _build_title_prompt(
        self,
        script_content: str,
        style: str,
        max_length: int,
        target_keywords: List[str],
    ) -> str:
        """Build prompt for title generation"""
        keyword_text = ", ".join(target_keywords) if target_keywords else ""

        return f"""Generate 8 compelling video titles based on this \
            script content:

SCRIPT CONTENT:
{script_content[:500]}...

REQUIREMENTS:
- Style: {style}
- Maximum length: {max_length} characters
{f'- Include keywords: {keyword_text}' if keyword_text else ''}

STYLE CHARACTERISTICS:
- Catchy: Use power words, numbers, emotional triggers
- Descriptive: Clear, informative, search-friendly
- Clickbait: Curiosity-driven, provocative (but honest)
- Professional: Straightforward, authoritative

Format your response as a numbered list:
1. Title one
2. Title two
... etc."""

    def _build_optimization_prompt(
        self, script_content: str, current_duration: int, target_duration: int
    ) -> str:
        """Build prompt for script optimization"""
        if current_duration > target_duration:
            action = "shorten"
            difference = current_duration - target_duration
        else:
            action = "expand"
            difference = target_duration - current_duration

        return f"""Optimize this video script to better match the \
            target duration while maintaining engagement and key messages.

CURRENT SCRIPT:
{script_content}

OPTIMIZATION TASK:
- Current Duration: {current_duration} seconds
- Target Duration: {target_duration} seconds
- Action Needed: {action} by approximately {difference} seconds

OPTIMIZATION GUIDELINES:
- Maintain the core message and hook
- Preserve the most engaging elements
- {'Remove redundant points, combine ideas, use more concise \
    language' if action == 'shorten' else 'Add supporting details, \
        examples, or elaboration on key points'}
- Keep the natural flow and transitions
- Maintain call-to-action

Please provide ONLY the optimized script content."""

    def _estimate_reading_time(self, text: str) -> int:
        """Estimate reading time in seconds (assuming ~150 words per \
            minute for speech)"""
        words = len(text.split())
        # Average speaking pace for social media: 2.5 words per second
        return int(words / 2.5)

    def _parse_titles(self, response: str) -> List[str]:
        """Parse titles from AI response"""
        lines = response.strip().split("\n")
        titles = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove numbering (1., 2., etc.)
            import re

            title = re.sub(r"^\d+\.\s*", "", line)
            title = title.strip("\"'")

            if title and len(title) > 10:  # Filter out very short titles
                titles.append(title)

        return titles[:8]  # Return maximum 8 titles

    def _select_best_title(
        self, titles: List[str], style: str, max_length: int
    ) -> str:
        """Select the best title based on criteria"""
        if not titles:
            return "Untitled Video"

        # Score titles based on style criteria
        scored_titles = []

        for title in titles:
            score = 0

            # Length score (prefer titles close to but under max_length)
            if len(title) <= max_length:
                score += 10
                # Bonus for using 70-90% of max length
                usage = len(title) / max_length
                if 0.7 <= usage <= 0.9:
                    score += 5

            # Style-specific scoring
            title_lower = title.lower()

            if style == "catchy":
                # Look for numbers, power words, emotional triggers
                power_words = [
                    "secret",
                    "hack",
                    "amazing",
                    "incredible",
                    "game-changing",
                    "revolutionary",
                ]
                score += sum(3 for word in power_words if word in title_lower)
                if any(char.isdigit() for char in title):
                    score += 5

            elif style == "descriptive":
                # Prefer clear, informative titles
                if ":" in title or "|" in title:
                    score += 3
                if any(
                    word in title_lower
                    for word in ["how", "what", "why", "guide", "tips"]
                ):
                    score += 5

            elif style == "clickbait":
                # Look for curiosity gaps and emotional triggers
                curiosity_words = [
                    "you won't believe",
                    "shocking",
                    "surprising",
                    "nobody tells you",
                ]
                score += sum(
                    5 for phrase in curiosity_words if phrase in title_lower
                )

            scored_titles.append((score, title))

        # Return the highest scoring title
        scored_titles.sort(key=lambda x: x[0], reverse=True)
        return scored_titles[0][1]

    def _analyze_changes(self, original: str, optimized: str) -> List[str]:
        """Analyze changes made during optimization"""
        changes = []

        original_words = len(original.split())
        optimized_words = len(optimized.split())
        word_diff = original_words - optimized_words

        if word_diff > 0:
            changes.append(f"Reduced word count by {word_diff} words")
        elif word_diff < 0:
            changes.append(f"Increased word count by {abs(word_diff)} words")

        # Simple structural analysis
        original_sentences = (
            original.count(".") + original.count("!") + original.count("?")
        )
        optimized_sentences = (
            optimized.count(".") + optimized.count("!") + optimized.count("?")
        )

        if original_sentences != optimized_sentences:
            changes.append(
                f"Sentence count changed from {original_sentences} to \
                    {optimized_sentences}"
            )

        return changes

    def _calculate_optimization_score(
        self,
        target_duration: int,
        optimized_duration: int,
        original_duration: int,
    ) -> int:
        """Calculate optimization score (0-100)"""
        # How close are we to the target?
        target_accuracy = max(
            0, 100 - abs(target_duration - optimized_duration) * 5
        )

        # Did we improve from the original?
        original_distance = abs(target_duration - original_duration)
        optimized_distance = abs(target_duration - optimized_duration)
        improvement = max(
            0,
            (original_distance - optimized_distance) / original_distance * 50,
        )

        return min(100, int((target_accuracy + improvement) / 1.5))
