import os
from pathlib import Path
from typing import Any, Dict

import librosa
import magic
import soundfile as sf
import structlog
from app.config import settings
from app.schemas import FileValidationError

logger = structlog.get_logger(__name__)


class AudioValidator:
    """Validates and analyzes audio files"""

    def __init__(self):
        self.allowed_formats = settings.allowed_audio_formats
        self.max_file_size = settings.max_file_size
        self.min_duration = settings.min_duration
        self.max_duration = settings.max_duration

    async def validate_file_upload(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """
        Comprehensive file validation
        Returns metadata dict or raises FileValidationError
        """
        try:
            # Check file exists
            if not os.path.exists(file_path):
                raise FileValidationError(error="File not found", details={"file_path": file_path})

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise FileValidationError(
                    error="File too large",
                    details={
                        "file_size": file_size,
                        "max_size": self.max_file_size,
                    },
                )

            # Check file format by extension
            file_extension = Path(original_filename).suffix.lower().lstrip(".")
            if file_extension not in self.allowed_formats:
                raise FileValidationError(
                    error="Unsupported file format",
                    details={
                        "format": file_extension,
                        "allowed_formats": self.allowed_formats,
                    },
                )

            # Validate MIME type
            mime_type = magic.from_file(file_path, mime=True)
            if not self._is_valid_mime_type(mime_type):
                raise FileValidationError(
                    error="Invalid MIME type", details={"mime_type": mime_type}
                )

            # Analyze audio content
            audio_metadata = await self._analyze_audio(file_path)

            # Validate audio properties
            self._validate_audio_properties(audio_metadata)

            # Combine all metadata
            metadata = {
                "file_size": file_size,
                "mime_type": mime_type,
                "format": file_extension,
                **audio_metadata,
                "validation_passed": True,
            }

            logger.info(
                "File validation successful",
                filename=original_filename,
                metadata=metadata,
            )

            return metadata

        except FileValidationError:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during file validation",
                filename=original_filename,
                error=str(e),
            )
            raise FileValidationError(error="Validation failed", details={"error": str(e)})

    async def _analyze_audio(self, file_path: str) -> Dict[str, Any]:
        """Analyze audio file properties using librosa"""
        try:
            # Load audio file
            y, sr = librosa.load(file_path, sr=None)

            # Calculate basic properties
            duration = len(y) / sr
            channels = 1 if y.ndim == 1 else y.shape[0]

            # Audio quality analysis
            rms_energy = float(librosa.feature.rms(y=y).mean())
            spectral_centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
            zero_crossing_rate = float(librosa.feature.zero_crossing_rate(y).mean())

            # Silence detection
            silence_threshold = 0.01
            silence_ratio = float((librosa.util.normalize(y) < silence_threshold).mean())

            return {
                "duration": duration,
                "sample_rate": sr,
                "channels": channels,
                "rms_energy": rms_energy,
                "spectral_centroid": spectral_centroid,
                "zero_crossing_rate": zero_crossing_rate,
                "silence_ratio": silence_ratio,
                "audio_analysis_success": True,
            }

        except Exception as e:
            logger.warning(
                "Audio analysis failed, using basic file info",
                file_path=file_path,
                error=str(e),
            )

            # Fallback to basic file info
            try:
                with sf.SoundFile(file_path) as f:
                    duration = len(f) / f.samplerate
                    return {
                        "duration": duration,
                        "sample_rate": f.samplerate,
                        "channels": f.channels,
                        "audio_analysis_success": False,
                        "analysis_error": str(e),
                    }
            except Exception as fallback_error:
                logger.error(
                    "Both librosa and soundfile analysis failed",
                    file_path=file_path,
                    error=str(fallback_error),
                )
                raise FileValidationError(
                    error="Unable to analyze audio file",
                    details={"error": str(fallback_error)},
                )

    def _validate_audio_properties(self, audio_metadata: Dict[str, Any]) -> None:
        """Validate audio properties against requirements"""
        duration = audio_metadata.get("duration", 0)

        if duration < self.min_duration:
            raise FileValidationError(
                error="Audio too short",
                details={
                    "duration": duration,
                    "min_duration": self.min_duration,
                },
            )

        if duration > self.max_duration:
            raise FileValidationError(
                error="Audio too long",
                details={
                    "duration": duration,
                    "max_duration": self.max_duration,
                },
            )

        # Check for excessive silence
        silence_ratio = audio_metadata.get("silence_ratio", 0)
        if silence_ratio > 0.8:  # More than 80% silence
            raise FileValidationError(
                error="Audio contains too much silence",
                details={"silence_ratio": silence_ratio},
            )

        # Check for very low energy (likely corrupt or empty)
        rms_energy = audio_metadata.get("rms_energy", 0)
        if rms_energy < 0.001:
            raise FileValidationError(
                error="Audio has very low energy, may be corrupt",
                details={"rms_energy": rms_energy},
            )

    def _is_valid_mime_type(self, mime_type: str) -> bool:
        """Check if MIME type is valid for audio files"""
        valid_mime_types = [
            "audio/wav",
            "audio/wave",
            "audio/x-wav",
            "audio/mpeg",
            "audio/mp3",
            "audio/flac",
            "audio/x-flac",
            "audio/mp4",
            "audio/m4a",
            "audio/ogg",
            "audio/vorbis",
        ]
        return mime_type in valid_mime_types

    async def get_optimal_preprocessing_params(
        self, audio_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine optimal preprocessing parameters based on audio analysis
        """
        current_sr = audio_metadata.get("sample_rate", settings.target_sample_rate)
        current_channels = audio_metadata.get("channels", settings.target_channels)

        # Determine if resampling is needed
        needs_resampling = current_sr != settings.target_sample_rate
        needs_channel_conversion = current_channels != settings.target_channels

        # Audio quality indicators
        rms_energy = audio_metadata.get("rms_energy", 0)
        silence_ratio = audio_metadata.get("silence_ratio", 0)

        # Determine preprocessing steps
        preprocessing_steps = []

        if needs_resampling:
            preprocessing_steps.append("resample")

        if needs_channel_conversion:
            preprocessing_steps.append("channel_conversion")

        if silence_ratio > 0.1:  # More than 10% silence
            preprocessing_steps.append("silence_removal")

        if rms_energy < 0.01:  # Low energy
            preprocessing_steps.append("normalize")

        return {
            "target_sample_rate": settings.target_sample_rate,
            "target_channels": settings.target_channels,
            "preprocessing_steps": preprocessing_steps,
            "needs_resampling": needs_resampling,
            "needs_channel_conversion": needs_channel_conversion,
            "estimated_processing_time": len(preprocessing_steps) * 2,  # rough estimate in seconds
        }


# Global validator instance
audio_validator = AudioValidator()
