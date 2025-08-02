import asyncio
import time
import hashlib
from typing import Dict, Any, Optional
import structlog

from .model_manager import model_manager
from ..config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class SynthesisEngine:
    """Voice synthesis engine"""

    def __init__(self):
        self.active_syntheses: Dict[str, asyncio.Task] = {}

    async def synthesize_speech(
        self,
        text: str,
        model_id: int,
        model_config: Dict[str, Any],
        synthesis_params: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Synthesize speech from text using the specified model"""

        # Validate input
        if len(text) > settings.max_text_length:
            raise ValueError(
                f"Text too long: {len(text)} > {settings.max_text_length}"
            )

        if not text.strip():
            raise ValueError("Text cannot be empty")

        # Default synthesis parameters
        if synthesis_params is None:
            synthesis_params = {}

        synthesis_params = {
            "speed": synthesis_params.get("speed", 1.0),
            "pitch": synthesis_params.get("pitch", 1.0),
            "volume": synthesis_params.get("volume", 1.0),
            "emotion": synthesis_params.get("emotion", "neutral"),
            **synthesis_params,
        }

        # Generate synthesis job ID
        job_data = f"{text}_{model_id}_{str(synthesis_params)}"
        job_id = hashlib.md5(job_data.encode()).hexdigest()

        logger.info(
            "Starting voice synthesis",
            job_id=job_id,
            model_id=model_id,
            text_length=len(text),
            user_id=user_id,
        )

        start_time = time.time()

        try:
            # Load the model
            model = await model_manager.get_model(model_id, model_config)

            # Perform synthesis
            audio_data = await asyncio.wait_for(
                model.synthesize(text, **synthesis_params),
                timeout=settings.synthesis_timeout,
            )

            processing_time = time.time() - start_time
            audio_duration = self._estimate_audio_duration(audio_data)

            logger.info(
                "Voice synthesis completed",
                job_id=job_id,
                processing_time=processing_time,
                audio_duration=audio_duration,
                audio_size=len(audio_data),
            )

            return {
                "job_id": job_id,
                "audio_data": audio_data,
                "audio_duration": audio_duration,
                "processing_time": processing_time,
                "synthesis_params": synthesis_params,
                "model_id": model_id,
                "text_length": len(text),
            }

        except asyncio.TimeoutError:
            logger.error(
                "Synthesis timeout",
                job_id=job_id,
                timeout=settings.synthesis_timeout,
            )
            raise RuntimeError(
                (
                    f"Synthesis timed out after "
                    f"{settings.synthesis_timeout} seconds"
                )
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                "Synthesis failed",
                job_id=job_id,
                error=str(e),
                processing_time=processing_time,
            )
            raise RuntimeError(f"Synthesis failed: {str(e)}")

    async def batch_synthesize(
        self,
        texts: list[str],
        model_id: int,
        model_config: Dict[str, Any],
        synthesis_params: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> list[Dict[str, Any]]:
        """Synthesize multiple texts in batch"""

        if len(texts) > 10:  # Limit batch size
            raise ValueError("Batch size too large: maximum 10 texts")

        logger.info(
            "Starting batch synthesis",
            batch_size=len(texts),
            model_id=model_id,
            user_id=user_id,
        )

        # Create synthesis tasks
        tasks = []
        for i, text in enumerate(texts):
            task = self.synthesize_speech(
                text=text,
                model_id=model_id,
                model_config=model_config,
                synthesis_params=synthesis_params,
                user_id=user_id,
            )
            tasks.append(task)

        # Execute all tasks concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            batch_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    batch_results.append(
                        {
                            "index": i,
                            "text": texts[i],
                            "error": str(result),
                            "success": False,
                        }
                    )
                else:
                    batch_results.append(
                        {
                            "index": i,
                            "text": texts[i],
                            "result": result,
                            "success": True,
                        }
                    )

            logger.info(
                "Batch synthesis completed",
                batch_size=len(texts),
                successful=sum(1 for r in batch_results if r["success"]),
                failed=sum(1 for r in batch_results if not r["success"]),
            )

            return batch_results

        except Exception as e:
            logger.error("Batch synthesis failed", error=str(e))
            raise RuntimeError(f"Batch synthesis failed: {str(e)}")

    def _estimate_audio_duration(self, audio_data: bytes) -> float:
        """Estimate audio duration from WAV data"""
        try:
            # Simple estimation based on WAV header
            # This is a simplified calculation
            if len(audio_data) > 44:  # WAV header is 44 bytes
                # Assume 16-bit mono at 22050 Hz
                data_size = len(audio_data) - 44
                bytes_per_second = 22050 * 2  # 16-bit mono
                duration = data_size / bytes_per_second
                return max(duration, 0.1)  # Minimum 0.1 seconds
            return 1.0  # Default duration
        except Exception:
            return 1.0  # Default duration on error

    async def get_synthesis_stats(self) -> Dict[str, Any]:
        """Get synthesis engine statistics"""
        return {
            "active_syntheses": len(self.active_syntheses),
            "max_text_length": settings.max_text_length,
            "synthesis_timeout": settings.synthesis_timeout,
            "max_audio_duration": settings.max_audio_duration,
        }


# Global synthesis engine instance
synthesis_engine = SynthesisEngine()
