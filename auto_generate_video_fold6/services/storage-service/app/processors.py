import os
import asyncio
import tempfile
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageOps
import structlog
from abc import ABC, abstractmethod

from .config import settings

logger = structlog.get_logger()


class FileProcessor(ABC):
    """Abstract base class for file processors"""
    
    @abstractmethod
    async def process(self, file_path: str, output_path: str, **kwargs) -> Dict[str, Any]:
        """Process file and return metadata"""
        pass
    
    @abstractmethod
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from file"""
        pass


class ImageProcessor(FileProcessor):
    """Image processing and optimization"""
    
    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'WEBP', 'GIF']
    
    async def process(self, file_path: str, output_path: str, **kwargs) -> Dict[str, Any]:
        """Process image: resize, optimize, generate thumbnail"""
        try:
            with Image.open(file_path) as img:
                # Extract original metadata
                original_metadata = self.get_metadata(file_path)
                
                # Auto-orient image based on EXIF data
                img = ImageOps.exif_transpose(img)
                
                # Resize if needed
                max_dimension = kwargs.get('max_dimension', settings.max_image_dimension)
                if max(img.size) > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                
                # Optimize and save
                quality = kwargs.get('quality', settings.image_quality)
                optimize = kwargs.get('optimize', True)
                
                # Convert RGBA to RGB for JPEG
                if img.mode == 'RGBA' and output_path.lower().endswith('.jpg'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                
                img.save(output_path, quality=quality, optimize=optimize)
                
                # Generate thumbnail if requested
                thumbnail_path = None
                if kwargs.get('generate_thumbnail', True):
                    thumbnail_path = await self._generate_thumbnail(
                        img, 
                        output_path,
                        kwargs.get('thumbnail_size', settings.thumbnail_size)
                    )
                
                return {
                    'width': img.size[0],
                    'height': img.size[1],
                    'format': img.format,
                    'mode': img.mode,
                    'thumbnail_path': thumbnail_path,
                    'original_metadata': original_metadata,
                    'processed': True
                }
                
        except Exception as e:
            logger.error("Image processing failed", error=str(e), file_path=file_path)
            raise
    
    async def _generate_thumbnail(self, img: Image.Image, original_path: str, size: int) -> str:
        """Generate thumbnail for image"""
        try:
            # Create thumbnail
            thumbnail = img.copy()
            thumbnail.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            # Generate thumbnail path
            base_name = os.path.splitext(original_path)[0]
            thumbnail_path = f"{base_name}_thumb.jpg"
            
            # Convert to RGB if needed for JPEG
            if thumbnail.mode == 'RGBA':
                background = Image.new('RGB', thumbnail.size, (255, 255, 255))
                background.paste(thumbnail, mask=thumbnail.split()[-1])
                thumbnail = background
            
            thumbnail.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            return thumbnail_path
            
        except Exception as e:
            logger.error("Thumbnail generation failed", error=str(e))
            return None
    
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract image metadata"""
        try:
            with Image.open(file_path) as img:
                metadata = {
                    'width': img.size[0],
                    'height': img.size[1],
                    'format': img.format,
                    'mode': img.mode,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif_data = img._getexif()
                    metadata['exif'] = {k: v for k, v in exif_data.items() if isinstance(v, (str, int, float))}
                
                return metadata
                
        except Exception as e:
            logger.error("Failed to extract image metadata", error=str(e), file_path=file_path)
            return {}


class AudioProcessor(FileProcessor):
    """Audio processing and optimization"""
    
    def __init__(self):
        self.supported_formats = ['mp3', 'wav', 'ogg', 'm4a']
    
    async def process(self, file_path: str, output_path: str, **kwargs) -> Dict[str, Any]:
        """Process audio: convert format, optimize bitrate"""
        try:
            # This would use ffmpeg for audio processing
            # For now, we'll provide a basic implementation
            
            metadata = self.get_metadata(file_path)
            
            # Basic audio processing with ffmpeg (placeholder)
            target_format = kwargs.get('format', 'mp3')
            target_bitrate = kwargs.get('bitrate', '128k')
            
            cmd = [
                'ffmpeg', '-i', file_path,
                '-acodec', 'libmp3lame' if target_format == 'mp3' else 'copy',
                '-ab', target_bitrate,
                '-y', output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                processed_metadata = self.get_metadata(output_path)
                return {
                    'duration': processed_metadata.get('duration'),
                    'bitrate': processed_metadata.get('bitrate'),
                    'sample_rate': processed_metadata.get('sample_rate'),
                    'channels': processed_metadata.get('channels'),
                    'format': target_format,
                    'original_metadata': metadata,
                    'processed': True
                }
            else:
                raise Exception(f"Audio processing failed: {stderr.decode()}")
                
        except Exception as e:
            logger.error("Audio processing failed", error=str(e), file_path=file_path)
            raise
    
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract audio metadata using ffprobe"""
        try:
            import json
            import subprocess
            
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                audio_stream = next((s for s in data['streams'] if s['codec_type'] == 'audio'), None)
                
                if audio_stream:
                    return {
                        'duration': float(data['format'].get('duration', 0)),
                        'bitrate': int(data['format'].get('bit_rate', 0)),
                        'sample_rate': int(audio_stream.get('sample_rate', 0)),
                        'channels': int(audio_stream.get('channels', 0)),
                        'codec': audio_stream.get('codec_name'),
                        'format': data['format'].get('format_name')
                    }
            
            return {}
            
        except Exception as e:
            logger.error("Failed to extract audio metadata", error=str(e), file_path=file_path)
            return {}


class VideoProcessor(FileProcessor):
    """Video processing and optimization"""
    
    def __init__(self):
        self.supported_formats = ['mp4', 'avi', 'mov', 'webm']
    
    async def process(self, file_path: str, output_path: str, **kwargs) -> Dict[str, Any]:
        """Process video: transcode, resize, optimize"""
        try:
            metadata = self.get_metadata(file_path)
            
            # Video processing parameters
            target_width = kwargs.get('width', 1920)
            target_height = kwargs.get('height', 1080)
            target_bitrate = kwargs.get('video_bitrate', '2M')
            target_fps = kwargs.get('fps', 30)
            
            cmd = [
                'ffmpeg', '-i', file_path,
                '-vcodec', 'libx264',
                '-acodec', 'aac',
                '-vb', target_bitrate,
                '-r', str(target_fps),
                '-vf', f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2',
                '-preset', 'medium',
                '-crf', '23',
                '-movflags', '+faststart',
                '-y', output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                processed_metadata = self.get_metadata(output_path)
                
                # Generate thumbnail
                thumbnail_path = await self._generate_video_thumbnail(file_path, output_path)
                
                return {
                    'duration': processed_metadata.get('duration'),
                    'width': processed_metadata.get('width'),
                    'height': processed_metadata.get('height'),
                    'fps': processed_metadata.get('fps'),
                    'bitrate': processed_metadata.get('bitrate'),
                    'codec': processed_metadata.get('codec'),
                    'thumbnail_path': thumbnail_path,
                    'original_metadata': metadata,
                    'processed': True
                }
            else:
                raise Exception(f"Video processing failed: {stderr.decode()}")
                
        except Exception as e:
            logger.error("Video processing failed", error=str(e), file_path=file_path)
            raise
    
    async def _generate_video_thumbnail(self, input_path: str, output_path: str) -> str:
        """Generate thumbnail from video"""
        try:
            base_name = os.path.splitext(output_path)[0]
            thumbnail_path = f"{base_name}_thumb.jpg"
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-ss', '00:00:01',
                '-vframes', '1',
                '-vf', 'scale=300:300:force_original_aspect_ratio=decrease',
                '-y', thumbnail_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode == 0:
                return thumbnail_path
            
            return None
            
        except Exception as e:
            logger.error("Video thumbnail generation failed", error=str(e))
            return None
    
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract video metadata using ffprobe"""
        try:
            import json
            import subprocess
            
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
                audio_stream = next((s for s in data['streams'] if s['codec_type'] == 'audio'), None)
                
                metadata = {}
                
                if video_stream:
                    metadata.update({
                        'duration': float(data['format'].get('duration', 0)),
                        'width': int(video_stream.get('width', 0)),
                        'height': int(video_stream.get('height', 0)),
                        'fps': eval(video_stream.get('r_frame_rate', '30/1')),
                        'video_codec': video_stream.get('codec_name'),
                        'video_bitrate': int(video_stream.get('bit_rate', 0))
                    })
                
                if audio_stream:
                    metadata.update({
                        'audio_codec': audio_stream.get('codec_name'),
                        'audio_bitrate': int(audio_stream.get('bit_rate', 0)),
                        'sample_rate': int(audio_stream.get('sample_rate', 0)),
                        'channels': int(audio_stream.get('channels', 0))
                    })
                
                return metadata
            
            return {}
            
        except Exception as e:
            logger.error("Failed to extract video metadata", error=str(e), file_path=file_path)
            return {}


class ProcessorManager:
    """Manager for file processors"""
    
    def __init__(self):
        self.processors = {
            'image': ImageProcessor(),
            'audio': AudioProcessor(),
            'video': VideoProcessor()
        }
    
    def get_processor(self, file_type: str) -> Optional[FileProcessor]:
        """Get processor for file type"""
        return self.processors.get(file_type)
    
    async def process_file(
        self,
        file_path: str,
        file_type: str,
        output_path: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process file using appropriate processor"""
        
        processor = self.get_processor(file_type)
        if not processor:
            raise ValueError(f"No processor available for file type: {file_type}")
        
        if not output_path:
            # Generate output path based on input
            base_name = os.path.splitext(file_path)[0]
            extension = os.path.splitext(file_path)[1]
            output_path = f"{base_name}_processed{extension}"
        
        return await processor.process(file_path, output_path, **kwargs)
    
    def get_metadata(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Get metadata for file"""
        processor = self.get_processor(file_type)
        if not processor:
            return {}
        
        return processor.get_metadata(file_path)


# Global processor manager instance
processor_manager = ProcessorManager()