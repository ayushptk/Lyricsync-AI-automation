import os
import re
import uuid
import logging
from typing import Dict, Any
import yt_dlp

logger = logging.getLogger(__name__)

# Basic validation for YouTube URLs
YOUTUBE_REGEX = re.compile(
    r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'
)

class YouTubeIngestionError(Exception):
    pass

def validate_youtube_url(url: str) -> bool:
    """Validates if the URL belongs to YouTube to prevent SSRF/unexpected behavior."""
    return bool(YOUTUBE_REGEX.match(url))

def download_audio(url: str, output_dir: str = "/tmp/downloads") -> Dict[str, Any]:
    """
    Downloads the best audio stream from a YouTube video and extracts metadata.
    Sanitizes filenames by using secure UUIDs instead of video titles.
    """
    if not validate_youtube_url(url):
        logger.error(f"Invalid YouTube URL attempted: {url}")
        raise ValueError("Invalid YouTube URL")

    # Ensure output directory exists securely
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate a safe, random filename (prevent path traversal)
    file_id = str(uuid.uuid4())
    output_template = os.path.join(output_dir, f"{file_id}.%(ext)s")

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
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Extracting metadata and downloading for {url}...")
            info = ydl.extract_info(url, download=True)
            
            # The actual path will end with .mp3 due to FFmpeg postprocessing
            expected_file_path = os.path.join(output_dir, f"{file_id}.mp3")
            
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
        logger.error(f"Download failed for {url}: {str(e)}")
        raise YouTubeIngestionError(f"Failed to download video: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during ingestion of {url}: {str(e)}")
        raise YouTubeIngestionError(f"Unexpected error: {str(e)}")
