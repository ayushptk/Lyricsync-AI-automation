"""
YouTube audio downloader service for LyricSync.

Key design decisions:
- Secrets Manager is always the primary source for cookies; local fallback is
  only used in non-container development environments (when LYRICSYNC_ENV=local).
- The global module-level cookie path is cached to avoid redundant Secrets Manager
  calls within a single Celery worker process. Each new process re-fetches.
- Cookie contents are never logged.
- remote_components is passed as a list (not dict) so yt-dlp can fetch its EJS
  JavaScript challenge solver from GitHub via Deno.
- tv_embedded is the primary player_client because it does not require PO Tokens
  and is consistently available from datacenter IPs (AWS Fargate).
"""

import os
import re
import uuid
import logging
import tempfile
import threading
from typing import Dict, Any, Optional

import yt_dlp
import imageio_ffmpeg
import boto3
import botocore.exceptions

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------

YOUTUBE_REGEX = re.compile(
    r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'
)


class YouTubeIngestionError(Exception):
    pass


def validate_youtube_url(url: str) -> bool:
    """Validates that the URL is a YouTube URL to prevent SSRF."""
    return bool(YOUTUBE_REGEX.match(url))


# ---------------------------------------------------------------------------
# Cookie management
# ---------------------------------------------------------------------------

_COOKIE_CACHE_LOCK = threading.Lock()
_cached_cookie_path: Optional[str] = None


def _get_region() -> str:
    """
    Returns the AWS region for Secrets Manager.
    ECS sets AWS_DEFAULT_REGION; fallback to AWS_REGION; hardcode eu-north-1.
    """
    return (
        os.getenv("AWS_DEFAULT_REGION")
        or os.getenv("AWS_REGION")
        or "eu-north-1"
    )


def _fetch_cookies_from_secrets_manager() -> Optional[str]:
    """
    Fetches the YouTube cookie file content from AWS Secrets Manager and writes
    it to a secure temporary file. Returns the path to the temporary file, or
    None if fetching fails.

    Cookie content is never logged.
    """
    secret_id = os.getenv("YOUTUBE_COOKIE_SECRET_ID", "lyricsync/youtube-cookies")
    region = _get_region()

    logger.info(
        "Fetching YouTube cookies from Secrets Manager: secret=%s region=%s",
        secret_id, region
    )

    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_id)
        secret = response.get("SecretString")

        if not secret:
            logger.error(
                "Secrets Manager returned an empty SecretString for %s. "
                "Ensure the secret is stored as a plaintext Netscape cookie file.",
                secret_id,
            )
            return None

        # Validate it looks like a Netscape cookie file
        if not secret.lstrip().startswith("# Netscape HTTP Cookie File") and \
           not secret.lstrip().startswith("# HTTP Cookie File"):
            logger.warning(
                "Cookie secret does not start with expected Netscape header. "
                "Proceeding anyway, but verify the secret format in Secrets Manager."
            )

        fd, cookie_path = tempfile.mkstemp(
            prefix="lyricsync_yt_cookies_",
            suffix=".txt",
            dir="/tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(secret)
            os.chmod(cookie_path, 0o600)
        except Exception:
            os.unlink(cookie_path)
            raise

        logger.info(
            "YouTube cookie file written to %s (%d bytes, %d lines).",
            cookie_path,
            len(secret.encode("utf-8")),
            len(secret.splitlines()),
        )
        return cookie_path

    except botocore.exceptions.NoCredentialsError:
        logger.error(
            "AWS credentials not found. "
            "Verify that the ECS Task Role has secretsmanager:GetSecretValue permission "
            "on arn:aws:secretsmanager:%s:*:secret:%s*",
            region, secret_id,
        )
    except botocore.exceptions.ClientError as e:
        code = e.response.get("Error", {}).get("Code", "Unknown")
        msg = e.response.get("Error", {}).get("Message", str(e))
        logger.error(
            "Secrets Manager ClientError fetching %s: [%s] %s",
            secret_id, code, msg,
        )
    except Exception as e:
        logger.error(
            "Unexpected error fetching YouTube cookies from Secrets Manager: %s: %s",
            type(e).__name__, e,
        )

    return None


def _get_local_cookie_path() -> Optional[str]:
    """
    Returns path to a local cookies.txt file for development use only.
    Only considered when LYRICSYNC_ENV=local (never in production/ECS).
    """
    if os.getenv("LYRICSYNC_ENV", "production") != "local":
        return None

    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies.txt"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "youtube-cookies.txt"),
    ]
    for path in candidates:
        if os.path.exists(path):
            logger.info("Development mode: using local cookie file at %s", path)
            return path
    return None


def get_youtube_cookies_file() -> Optional[str]:
    """
    Returns a path to a valid YouTube Netscape cookie file.

    Priority:
      1. Cached path from a previous call in this process (avoids repeated SM calls).
      2. AWS Secrets Manager (always preferred in production/ECS).
      3. Local file (only when LYRICSYNC_ENV=local, for development).

    Returns None if no cookie source is available. Callers should treat this
    as a configuration error in production and fail loudly.
    """
    global _cached_cookie_path

    with _COOKIE_CACHE_LOCK:
        # Return cached path if the file still exists
        if _cached_cookie_path and os.path.exists(_cached_cookie_path):
            logger.debug("Using cached cookie file: %s", _cached_cookie_path)
            return _cached_cookie_path

        # Invalidate stale cache entry
        if _cached_cookie_path:
            logger.warning(
                "Cached cookie file %s no longer exists. Re-fetching.",
                _cached_cookie_path,
            )
            _cached_cookie_path = None

        # Try Secrets Manager first (production path)
        path = _fetch_cookies_from_secrets_manager()

        # Fall back to local file only in explicit development mode
        if not path:
            path = _get_local_cookie_path()

        if path:
            _cached_cookie_path = path
        else:
            logger.error(
                "No YouTube cookie source is available. "
                "Downloads requiring authentication will fail. "
                "Ensure the ECS Task Role can read secret '%s' in region '%s'.",
                os.getenv("YOUTUBE_COOKIE_SECRET_ID", "lyricsync/youtube-cookies"),
                _get_region(),
            )

        return path


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_audio(
    url: str,
    output_dir: str = "/tmp/downloads",
) -> Dict[str, Any]:
    """
    Downloads the best audio stream from a YouTube video, extracts it as MP3,
    and returns a metadata dict with title, duration, uploader, file_path,
    and file_id.

    Player client strategy (datacenter-IP safe):
      - tv_embedded: primary — no PO Token required, works from AWS IPs for
        public content, equivalent to YouTube's own embedded player.
      - web: secondary — may need PO Token; yt-dlp+Deno+EJS will handle it
        automatically if remote_components is configured correctly.
      - mweb: tertiary — mobile web fallback.

    Raises:
      ValueError: if the URL fails validation.
      YouTubeIngestionError: if download or extraction fails.
    """
    if not validate_youtube_url(url):
        logger.error("Invalid YouTube URL rejected: %s", url)
        raise ValueError("Invalid YouTube URL")

    os.makedirs(output_dir, exist_ok=True)

    file_id = str(uuid.uuid4())
    output_template = os.path.join(output_dir, f"{file_id}.%(ext)s")

    # Determine FFmpeg location
    ffmpeg_exe = os.getenv("FFMPEG_LOCATION") or imageio_ffmpeg.get_ffmpeg_exe()

    ydl_opts: Dict[str, Any] = {
        # Audio quality
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "ffmpeg_location": ffmpeg_exe,

        # Player client selection — tv_embedded first (no PO Token needed from
        # datacenter IPs), then web/mweb with automatic PO Token via EJS/Deno.
        # Adding android and ios as they are more resilient to 403 Forbidden blocks.
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "tv_embedded", "web", "mweb"],
            },
        },

        # Allow yt-dlp to fetch its EJS JavaScript challenge solver from GitHub.
        # This is used by Deno to solve YouTube's PO Token challenges for the
        # web/mweb clients. Must be a list, NOT a dict.
        "remote_components": ["ejs:github"],

        # Retry on transient network errors
        "retries": 3,
        "fragment_retries": 3,

        # Do NOT use quiet=True or no_warnings=True in production.
        # yt-dlp output goes to stderr which is captured by CloudWatch Logs.
        # Verbose logging is critical for diagnosing YouTube bot-detection issues.
        "verbose": True,

        # Socket timeout to avoid hanging forever
        "socket_timeout": 60,
    }

    cookie_file = get_youtube_cookies_file()
    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file
        logger.info("Using cookie file for download: %s", cookie_file)
    else:
        # In production, missing cookies is an error worth flagging clearly.
        # tv_embedded can sometimes work without cookies for public content,
        # but log a prominent warning so the operator knows.
        logger.warning(
            "No cookie file available. Attempting download without authentication. "
            "This may fail for some videos depending on YouTube's bot detection."
        )

    logger.info("Starting yt-dlp download: url=%s file_id=%s", url, file_id)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        expected_file_path = os.path.join(output_dir, f"{file_id}.mp3")

        if not os.path.exists(expected_file_path):
            # The postprocessor may have chosen a different extension in edge cases.
            # Scan for the actual file.
            candidates = [
                p for p in os.listdir(output_dir)
                if p.startswith(file_id)
            ]
            if candidates:
                actual = os.path.join(output_dir, candidates[0])
                logger.warning(
                    "Expected %s but found %s — using actual path.",
                    expected_file_path, actual,
                )
                expected_file_path = actual
            else:
                raise YouTubeIngestionError(
                    f"Download succeeded but no output file found for file_id={file_id}"
                )

        metadata: Dict[str, Any] = {
            "title": info.get("title", "Unknown Title"),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", "Unknown Uploader"),
            "file_path": expected_file_path,
            "file_id": file_id,
        }

        logger.info(
            "Download complete: title=%r duration=%ss path=%s",
            metadata["title"],
            metadata["duration"],
            expected_file_path,
        )
        return metadata

    except yt_dlp.utils.DownloadError as e:
        error_str = str(e)
        logger.error(
            "yt-dlp DownloadError for %s: %s",
            url, error_str,
        )

        # Surface actionable messages for known failure modes
        if "Sign in to confirm" in error_str or "LOGIN_REQUIRED" in error_str:
            raise YouTubeIngestionError(
                f"YouTube authentication required. "
                f"The ECS IP may be flagged as a bot. "
                f"Check cookie freshness and try player_client=tv_embedded. "
                f"Original error: {error_str}"
            ) from e
        if "429" in error_str or "Too Many Requests" in error_str:
            raise YouTubeIngestionError(
                f"YouTube rate limit hit (HTTP 429). "
                f"Reduce request frequency. Original error: {error_str}"
            ) from e

        raise YouTubeIngestionError(
            f"Failed to download video: {error_str}"
        ) from e

    except Exception as e:
        logger.error(
            "Unexpected error during download of %s: %s: %s",
            url, type(e).__name__, e,
        )
        raise YouTubeIngestionError(f"Unexpected error: {e}") from e