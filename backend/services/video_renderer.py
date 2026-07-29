import os
import sys
import shutil
import tempfile
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
        Verifies h264_nvenc actually works by doing a 1-frame test encode.
        Just listing encoders is not enough — the GPU driver may be unavailable.
        """
        try:
            result = subprocess.run(
                [FFMPEG_EXE,
                 "-f", "lavfi", "-i", "color=black:s=16x16:d=0.1",
                 "-c:v", "h264_nvenc", "-frames:v", "1",
                 "-f", "null", "-"],
                capture_output=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _build_ass_filter_arg(self, ass_path: str) -> str:
        """
        Builds the -vf filter argument for burning ASS subtitles.
        On Windows, FFmpeg's filter graph parser cannot handle paths with colons
        (e.g. C:/...). We work around this by copying the ASS file to a temp
        directory on the same drive (no colon in relative path from temp).
        Returns the full -vf string like: ass='path/to/file.ass'
        """
        if sys.platform != 'win32':
            # On Linux/Mac, simple forward-slash path works fine
            escaped = ass_path.replace('\\', '/')
            return f"ass='{escaped}'"

        # On Windows: copy ASS to a temp file in the system TEMP dir with no subpath issues.
        # We use a fixed short filename so the path stays predictable.
        tmp_dir = tempfile.gettempdir()
        tmp_ass = os.path.join(tmp_dir, "karaoke_subs.ass")
        shutil.copy2(ass_path, tmp_ass)
        # Safest: use the 'subtitles' filter (alias for ass) with filename= option syntax.
        # Actually the simplest fix: pass the drive-relative path without the drive letter.
        # e.g. /Users/ASUS/... — works because FFmpeg on Windows accepts /drive/path too.
        drive, tail = os.path.splitdrive(tmp_ass)  # drive = 'C:', tail = '\Users\...'
        unix_path = tail.replace('\\', '/')         # '/Users/ASUS/.../karaoke_subs.ass'
        return f"ass='{unix_path}'"

    def render_karaoke_video(
        self,
        audio_path: str,
        ass_path: Optional[str] = None,
        background_image_path: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Renders an MP4 video combining audio, background, and optional ASS karaoke subtitles.
        If ass_path is None or doesn't exist, renders audio+background without subtitles.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if ass_path and not os.path.exists(ass_path):
            logger.warning(f"Subtitle file not found: {ass_path}. Rendering without subtitles.")
            ass_path = None

        if output_dir is None:
            output_dir = os.path.dirname(audio_path)

        filename = os.path.basename(audio_path)
        name, _ = os.path.splitext(filename)
        # Clean up filename if it has prefixes from earlier pipeline steps
        name = name.replace("_piano", "").replace("_vocals", "").replace("_norm", "").replace("_backing", "")
        output_mp4_path = os.path.join(output_dir, f"{name}_karaoke.mp4")

        logger.info(f"Starting video rendering to {output_mp4_path} (subtitles: {'yes' if ass_path else 'no'})")

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

        ffmpeg_cmd.extend(["-i", audio_path])

        # 2. Filters & Codecs
        if ass_path:
            vf_arg = self._build_ass_filter_arg(ass_path)
            logger.info(f"ASS filter arg: {vf_arg}")
            ffmpeg_cmd.extend(["-vf", vf_arg])

        ffmpeg_cmd.extend([
            "-c:v", self.video_codec,
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_mp4_path
        ])

        try:
            logger.info("Running FFmpeg video render...")
            result = subprocess.run(ffmpeg_cmd, capture_output=True)
            if result.returncode != 0:
                err = result.stderr.decode('utf-8', errors='replace') if result.stderr else "unknown error"
                logger.error(f"FFmpeg failed (rc={result.returncode}): {err[-1000:]}")
                raise subprocess.CalledProcessError(result.returncode, ffmpeg_cmd, result.stdout, result.stderr)
            if not os.path.exists(output_mp4_path) or os.path.getsize(output_mp4_path) == 0:
                raise VideoRenderingError("FFmpeg completed but output file is missing or empty")
            logger.info(f"Successfully rendered video: {output_mp4_path} ({os.path.getsize(output_mp4_path)} bytes)")
            return output_mp4_path
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode('utf-8', errors='replace') if e.stderr else str(e)
            raise VideoRenderingError(f"Video render failed: {err[-800:]}")
