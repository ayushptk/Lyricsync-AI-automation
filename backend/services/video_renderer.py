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

# ── Configurable video settings via environment variables ──────────────────
# These defaults are optimized for low-spec machines (8GB RAM, CPU-only).
# Override in .env for higher quality when hardware allows it.
VIDEO_RESOLUTION = os.getenv("VIDEO_RESOLUTION", "720p").lower()    # "720p" or "1080p"
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "15"))                       # 15 for static bg, 24+ for motion
VIDEO_PRESET = os.getenv("VIDEO_PRESET", "veryfast")                # ultrafast/veryfast/fast/medium
VIDEO_AUDIO_BITRATE = os.getenv("VIDEO_AUDIO_BITRATE", "192k")     # 192k is transparent for karaoke


class VideoRenderingError(Exception):
    pass

class VideoRenderer:
    def __init__(self):
        """
        Initializes the Video Renderer.
        Probes for hardware encoders in priority order:
          1. Intel QSV (h264_qsv) — best for Intel Iris Xe / integrated graphics
          2. NVIDIA NVENC (h264_nvenc) — for discrete NVIDIA GPUs
          3. libx264 (software fallback)
        """
        self.video_codec, self.hw_accel_type = self._detect_best_encoder()
        logger.info(f"VideoRenderer initialized. Codec: {self.video_codec} (HW: {self.hw_accel_type})")

    def _test_encoder(self, codec: str) -> bool:
        """
        Verifies an encoder actually works by doing a 1-frame test encode.
        Just listing encoders is not enough — the driver may be unavailable.
        """
        try:
            result = subprocess.run(
                [FFMPEG_EXE,
                 "-f", "lavfi", "-i", "color=black:s=16x16:d=0.1",
                 "-c:v", codec, "-frames:v", "1",
                 "-f", "null", "-"],
                capture_output=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _detect_best_encoder(self) -> tuple[str, str]:
        """
        Detects the best available H.264 encoder.
        Returns (codec_name, accel_type) tuple.
        
        Priority:
          1. h264_qsv  — Intel Quick Sync Video (Intel iGPU / Iris Xe)
                         5-10x faster than libx264, near-zero CPU usage
          2. h264_nvenc — NVIDIA hardware encoder (discrete GPU)
          3. libx264   — Software fallback (always available)
        """
        # Try Intel QSV first — ideal for Intel Iris Xe integrated graphics
        if self._test_encoder("h264_qsv"):
            logger.info("✅ Intel QSV (h264_qsv) hardware encoder detected and working")
            return "h264_qsv", "qsv"
        
        # Try NVIDIA NVENC
        if self._test_encoder("h264_nvenc"):
            logger.info("✅ NVIDIA NVENC (h264_nvenc) hardware encoder detected and working")
            return "h264_nvenc", "nvenc"
        
        # Fallback to software
        logger.info("ℹ️ No hardware encoder available — using libx264 (software)")
        return "libx264", "software"

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
        drive, tail = os.path.splitdrive(tmp_ass)  # drive = 'C:', tail = '\\Users\\...'
        unix_path = tail.replace('\\', '/')         # '/Users/ASUS/.../karaoke_subs.ass'
        return f"ass='{unix_path}'"

    def _get_resolution(self, aspect_ratio: str) -> tuple[int, int]:
        """
        Returns (width, height) based on configured resolution and aspect ratio.
        
        720p is the default for low-spec machines — karaoke text is perfectly
        readable and encoding is ~4x faster than 1080p.
        """
        if VIDEO_RESOLUTION == "1080p":
            if aspect_ratio == "9:16":
                return 1080, 1920
            return 1920, 1080
        else:  # 720p (default)
            if aspect_ratio == "9:16":
                return 720, 1280
            return 1280, 720

    def render_karaoke_video(
        self,
        audio_path: str,
        ass_path: Optional[str] = None,
        background_image_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        aspect_ratio: str = "16:9"
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

        target_w, target_h = self._get_resolution(aspect_ratio)
        fps = VIDEO_FPS

        logger.info(
            f"Starting video rendering to {output_mp4_path} "
            f"(codec={self.video_codec}, {target_w}x{target_h}@{fps}fps, "
            f"preset={VIDEO_PRESET}, subtitles={'yes' if ass_path else 'no'})"
        )

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
            # Default to a generic black background
            ffmpeg_cmd.extend([
                "-f", "lavfi",
                "-i", f"color=c=black:s={target_w}x{target_h}:r={fps}"
            ])

        ffmpeg_cmd.extend(["-i", audio_path])

        # 2. Filters & Codecs
        vf_filters = []
        if background_image_path and os.path.exists(background_image_path):
            vf_filters.append(f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h}")
            
        if ass_path:
            vf_filters.append(self._build_ass_filter_arg(ass_path))
            
        if vf_filters:
            vf_arg = ",".join(vf_filters)
            logger.info(f"VF filter arg: {vf_arg}")
            ffmpeg_cmd.extend(["-vf", vf_arg])

        # 3. Video codec settings — optimized per encoder type
        ffmpeg_cmd.extend(["-c:v", self.video_codec])
        
        if self.hw_accel_type == "qsv":
            # Intel QSV settings — quality preset mapping
            # QSV uses "global_quality" instead of CRF
            ffmpeg_cmd.extend([
                "-global_quality", "28",     # Similar to CRF 28 — good for static content
                "-look_ahead", "0",          # Disable lookahead for faster encoding
            ])
        elif self.hw_accel_type == "nvenc":
            # NVIDIA NVENC settings
            ffmpeg_cmd.extend([
                "-preset", "p4",             # NVENC preset (p1=fastest, p7=slowest)
                "-cq", "28",                 # Constant quality
            ])
        else:
            # libx264 software settings
            ffmpeg_cmd.extend([
                "-preset", VIDEO_PRESET,     # veryfast — 3x faster than medium, minimal quality loss
                "-crf", "28",                # Slightly higher CRF for faster encoding (default was 23)
            ])
        
        ffmpeg_cmd.extend([
            "-r", str(fps),               # Output framerate
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", VIDEO_AUDIO_BITRATE,  # 192k — transparent for karaoke backing tracks
            "-shortest",
            output_mp4_path
        ])

        try:
            logger.info(f"Running FFmpeg video render (codec={self.video_codec})...")
            result = subprocess.run(ffmpeg_cmd, capture_output=True)
            
            # Check if output is generated and has a reasonable size
            file_exists = os.path.exists(output_mp4_path)
            file_size = os.path.getsize(output_mp4_path) if file_exists else 0
            
            if result.returncode != 0:
                # FFmpeg on Windows sometimes returns -12 (4294967284) with -shortest even when successful
                # If the file exists and is > 100KB, it's likely a successful render that failed during cleanup
                if result.returncode in (-12, 4294967284) and file_exists and file_size > 100000:
                    logger.warning(f"FFmpeg returned {result.returncode} but file was generated successfully. Ignoring error.")
                else:
                    err = result.stderr.decode('utf-8', errors='replace') if result.stderr else "unknown error"
                    logger.error(f"FFmpeg failed (rc={result.returncode}): {err[-1000:]}")
                    raise subprocess.CalledProcessError(result.returncode, ffmpeg_cmd, result.stdout, result.stderr)
                    
            if not file_exists or file_size == 0:
                raise VideoRenderingError("FFmpeg completed but output file is missing or empty")
                
            logger.info(f"Successfully rendered video: {output_mp4_path} ({file_size} bytes)")
            return output_mp4_path
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode('utf-8', errors='replace') if e.stderr else str(e)
            raise VideoRenderingError(f"Video render failed: {err[-800:]}")
