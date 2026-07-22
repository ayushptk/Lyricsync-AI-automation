import os
import subprocess
import logging
import imageio_ffmpeg
from typing import Optional

logger = logging.getLogger(__name__)
ffmpeg_location = os.getenv('FFMPEG_LOCATION')
FFMPEG_EXE = os.path.join(ffmpeg_location, 'ffmpeg.exe') if ffmpeg_location else imageio_ffmpeg.get_ffmpeg_exe()

class VideoRenderingError(Exception):
    pass

class VideoRenderer:
    def __init__(self):
        """
        Initializes the Video Renderer.
        Probes for NVIDIA GPU to use h264_nvenc, else falls back to libx264.
        """
        self.has_gpu = self._check_gpu_encoder()
        self.video_codec = "h264_nvenc" if self.has_gpu else "libx264"
        logger.info(f"VideoRenderer initialized. GPU Acceleration: {self.has_gpu} (Codec: {self.video_codec})")

    def _check_gpu_encoder(self) -> bool:
        """
        Checks if FFmpeg has access to the h264_nvenc encoder.
        """
        try:
            result = subprocess.run(
                [FFMPEG_EXE, "-encoders"],
                capture_output=True, text=True, check=True
            )
            return "h264_nvenc" in result.stdout
        except Exception:
            return False

    def render_karaoke_video(
        self,
        audio_path: str,
        ass_path: str,
        background_image_path: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Renders an MP4 video combining audio, background, and ASS karaoke subtitles.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if not os.path.exists(ass_path):
            raise FileNotFoundError(f"Subtitle file not found: {ass_path}")

        if output_dir is None:
            output_dir = os.path.dirname(audio_path)

        filename = os.path.basename(audio_path)
        name, _ = os.path.splitext(filename)
        # Clean up filename if it has prefixes from earlier pipeline steps
        name = name.replace("_piano", "").replace("_vocals", "").replace("_norm", "")
        output_mp4_path = os.path.join(output_dir, f"{name}_karaoke.mp4")

        # Due to FFmpeg filter limitations on Windows/paths, we must escape the ASS path
        # Replace backslashes with forward slashes for FFmpeg filter graph
        escaped_ass_path = ass_path.replace('\\', '/')
        # Windows drives (C:/) need special escaping in FFmpeg filters: C\:/ 
        if ':' in escaped_ass_path:
            escaped_ass_path = escaped_ass_path.replace(':', '\\:')

        logger.info(f"Starting video rendering to {output_mp4_path}")

        ffmpeg_cmd = [
            FFMPEG_EXE,
            "-y", # Overwrite
        ]

        # 1. Inputs
        if background_image_path and os.path.exists(background_image_path):
            ffmpeg_cmd.extend([
                "-loop", "1",
                "-i", background_image_path
            ])
        else:
            # Default to a generic black background (1920x1080)
            ffmpeg_cmd.extend([
                "-f", "lavfi",
                "-i", "color=c=black:s=1920x1080:r=30"
            ])

        ffmpeg_cmd.extend([
            "-i", audio_path
        ])

        # 2. Filters & Codecs
        # Shortest ensures the looped background stops when the audio ends
        ffmpeg_cmd.extend([
            "-vf", f"ass='{escaped_ass_path}'",
            "-c:v", self.video_codec,
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_mp4_path
        ])

        try:
            logger.info("Running FFmpeg video render...")
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            logger.info(f"Successfully rendered video: {output_mp4_path}")
            return output_mp4_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg Rendering failed: {e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)}")
            raise VideoRenderingError(f"Video render failed: {e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)}")
