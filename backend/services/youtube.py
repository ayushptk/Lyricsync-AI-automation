import os
import re
import sys
import uuid
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any
import yt_dlp
import imageio_ffmpeg
import subprocess

# Patch subprocess.Popen to avoid Errno 22 on Windows in Uvicorn daemon threads
_original_popen = subprocess.Popen
def _patched_popen(*args, **kwargs):
    if sys.platform == 'win32':
        if kwargs.get('stdin') is None:
            kwargs['stdin'] = subprocess.DEVNULL
        if kwargs.get('stdout') is None:
            kwargs['stdout'] = subprocess.DEVNULL
        if kwargs.get('stderr') is None:
            kwargs['stderr'] = subprocess.DEVNULL
        kwargs['creationflags'] = kwargs.get('creationflags', 0) | subprocess.CREATE_NO_WINDOW
    return _original_popen(*args, **kwargs)
subprocess.Popen = _patched_popen

logger = logging.getLogger(__name__)

# Platform-safe default download directory
_DEFAULT_DOWNLOAD_DIR = str(Path(tempfile.gettempdir()) / "ytsaas_downloads")

# Basic validation for YouTube URLs
YOUTUBE_REGEX = re.compile(
    r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'
)

class YouTubeIngestionError(Exception):
    pass

def validate_youtube_url(url: str) -> bool:
    """Validates if the URL belongs to YouTube to prevent SSRF/unexpected behavior."""
    return bool(YOUTUBE_REGEX.match(url))

def download_audio(url: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Downloads the best audio stream from a YouTube video and extracts metadata.
    Sanitizes filenames by using secure UUIDs instead of video titles.
    """
    if output_dir is None:
        output_dir = _DEFAULT_DOWNLOAD_DIR

    url = url.strip()
    if not validate_youtube_url(url):
        logger.error(f"Invalid YouTube URL attempted: {url}")
        raise ValueError("Invalid YouTube URL")

    # Ensure output directory exists securely (use Path for cross-platform safety)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Generate a safe, random filename (prevent path traversal)
    file_id = str(uuid.uuid4())
    # Use standard path string conversion; .as_posix() can cause Errno 22 on Windows if interpreted as a dictionary type by yt-dlp
    output_template = str(out_path / f"{file_id}.%(ext)s")

    # Resolve ffmpeg location
    ffmpeg_loc = os.getenv('FFMPEG_LOCATION')
    if ffmpeg_loc:
        ffmpeg_loc = ffmpeg_loc.strip('"')  # Remove any surrounding quotes that cause Popen Errno 22
    if not ffmpeg_loc:
        try:
            ffmpeg_loc = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_loc = None  # Let yt-dlp find ffmpeg on PATH

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
    }

    if ffmpeg_loc:
        ydl_opts['ffmpeg_location'] = ffmpeg_loc

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Extracting metadata and downloading for {url}...")
            logger.info(f"Output directory: {out_path} (exists={out_path.exists()})")
            info = ydl.extract_info(url, download=True)
            
            # The actual path will end with .mp3 due to FFmpeg postprocessing
            expected_file_path = str(out_path / f"{file_id}.mp3")
            
            # Verify the file was actually created
            if not Path(expected_file_path).exists():
                # Sometimes yt-dlp keeps the original extension; search for the file
                candidates = list(out_path.glob(f"{file_id}.*"))
                if candidates:
                    expected_file_path = str(candidates[0])
                    logger.warning(f"Expected .mp3 not found, using: {expected_file_path}")
                else:
                    raise YouTubeIngestionError(
                        f"Download appeared to succeed but no output file found in {out_path}"
                    )
            
            metadata = {
                "title": info.get("title", "Unknown Title"),
                "duration": info.get("duration", 0),
                "uploader": info.get("uploader", "Unknown Uploader"),
                "file_path": expected_file_path,
                "file_id": file_id
            }
            logger.info(f"Successfully downloaded audio to {expected_file_path}")
            return metadata
            
    except yt_dlp.utils.DownloadError as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Download failed for {url}: {str(e)}\n{tb}")
        raise YouTubeIngestionError(f"Failed to download video: {str(e)}\n\nTraceback Details:\n{tb}")
    except YouTubeIngestionError:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.exception(f"Unexpected error during ingestion of {url}")
        raise YouTubeIngestionError(f"Unexpected error: Unable to download video: {str(e)}\n\nTraceback Details:\n{tb}")
