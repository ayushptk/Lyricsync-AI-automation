"""
Audio Preprocessing Service
============================

Two separate preprocessing paths are provided:

1. prepare_for_separation(input_path)
   ─ Used BEFORE Demucs vocal separation.
   ─ Output: 44100 Hz, stereo (2ch), 16-bit PCM WAV.
   ─ NO loudness normalization, NO silence trimming, NO downsampling.
   ─ Reason: Demucs htdemucs / htdemucs_ft was trained on 44100 Hz stereo.
     Feeding it 16kHz mono causes the model to upsample internally, which
     introduces high-frequency artifacts (metallic/watery sound).  Mono also
     destroys the stereo phase relationships that Demucs uses to separate
     center-panned vocals from side-panned instruments.

2. prepare_for_whisper(input_path)
   ─ Used AFTER Demucs on the vocal stem only.
   ─ Output: 16000 Hz, mono (1ch), 16-bit PCM WAV.
   ─ Applies soft loudnorm so Whisper receives consistent signal level.
   ─ Reason: Faster-Whisper / OpenAI Whisper was trained on 16 kHz mono.
     Providing the correct format avoids the internal resampler and gives
     the model the signal it expects.

IMPORTANT:
  The old `preprocess_audio()` function is preserved as a compatibility shim
  so nothing else breaks immediately, but it is now deprecated — it only
  calls `prepare_for_separation()`.  Workers should call the explicit
  functions directly.
"""

import os
import logging
import subprocess
import sys
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AudioPreprocessError(Exception):
    pass


def _get_ffmpeg_exe() -> str:
    """Resolve the FFmpeg executable path."""
    ffmpeg_loc = os.getenv('FFMPEG_LOCATION')
    if ffmpeg_loc:
        ffmpeg_loc = ffmpeg_loc.strip('"')
        exe = os.path.join(ffmpeg_loc, 'ffmpeg.exe') if os.path.isdir(ffmpeg_loc) else ffmpeg_loc
        if os.path.exists(exe):
            return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _run_ffmpeg(cmd: list, step: str) -> None:
    """Run an FFmpeg command and raise AudioPreprocessError on failure."""
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=300,
            creationflags=creationflags,
        )
        if result.returncode != 0:
            err = result.stderr.decode('utf-8', errors='replace')
            raise AudioPreprocessError(f"{step} failed (rc={result.returncode}): {err[-600:]}")
    except subprocess.TimeoutExpired:
        raise AudioPreprocessError(f"{step} timed out (>300s)")
    except AudioPreprocessError:
        raise
    except Exception as e:
        raise AudioPreprocessError(f"{step} unexpected error: {e}")


# ---------------------------------------------------------------------------
# Path 1: Demucs input preparation
# ---------------------------------------------------------------------------

def prepare_for_separation(input_path: str, output_path: str = None) -> str:
    """
    Converts audio to 44100 Hz stereo WAV for Demucs input.

    This is the ONLY preprocessing Demucs should receive:
      - Format: WAV (PCM 16-bit signed little-endian)
      - Sample rate: 44100 Hz (Demucs native)
      - Channels: 2 (stereo — Demucs uses phase for separation)
      - No loudness normalization (Demucs handles its own normalization)
      - No silence trimming (would shift all timestamps)

    Args:
        input_path: Path to the source audio (MP3, M4A, WebM, WAV, etc.)
        output_path: Where to write the output WAV.  If None, writes next to input.

    Returns:
        Path to the output WAV file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        name, _ = os.path.splitext(input_path)
        output_path = f"{name}_for_demucs.wav"

    ffmpeg_exe = _get_ffmpeg_exe()

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", input_path,
        # No audio filters — pure format conversion only
        "-ar", "44100",          # 44.1 kHz — Demucs native sample rate
        "-ac", "2",              # Stereo — preserve phase information
        "-c:a", "pcm_s16le",     # 16-bit signed PCM
        output_path,
    ]

    logger.info(f"[preprocess] Preparing for Demucs: {os.path.basename(input_path)} → 44100Hz stereo WAV")
    _run_ffmpeg(cmd, "Demucs input preparation")

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise AudioPreprocessError(f"FFmpeg produced no output for Demucs preparation: {output_path}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"[preprocess] Demucs input ready: {output_path} ({size_mb:.1f} MB)")
    return output_path


# ---------------------------------------------------------------------------
# Path 2: Whisper input preparation
# ---------------------------------------------------------------------------

def prepare_for_whisper(input_path: str, output_path: str = None) -> str:
    """
    Converts a vocal stem (or any audio) to 16000 Hz mono WAV for Whisper.

    Whisper was trained on 16 kHz mono audio.  Providing this format:
      - Avoids Whisper's internal resampler (which is slower and less accurate)
      - Ensures the model receives the signal it expects
      - Applies soft EBU R128 loudnorm so quiet vocal stems are at a
        consistent level for the model

    This function is called on the VOCAL STEM output from Demucs,
    NOT on the original audio.

    Args:
        input_path: Path to the vocal stem WAV from Demucs.
        output_path: Where to write the output WAV.  If None, writes next to input.

    Returns:
        Path to the output 16kHz mono WAV file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Vocal stem not found: {input_path}")

    if output_path is None:
        name, _ = os.path.splitext(input_path)
        output_path = f"{name}_whisper.wav"

    ffmpeg_exe = _get_ffmpeg_exe()

    # Soft loudnorm: normalize to -16 LUFS (slightly louder than broadcast -23 LUFS)
    # so Whisper has a strong signal.  TP=-1 prevents clipping.
    # We use single-pass loudnorm here (not two-pass) because:
    #   1. Two-pass takes ~2x as long
    #   2. The vocal stem is already a cleaner signal than a full mix
    #   3. Whisper is tolerant of mild loudness variation
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", input_path,
        "-af", "loudnorm=I=-16:TP=-1:LRA=11",
        "-ar", "16000",          # 16 kHz — Whisper native sample rate
        "-ac", "1",              # Mono — Whisper is mono
        "-c:a", "pcm_s16le",     # 16-bit signed PCM
        output_path,
    ]

    logger.info(f"[preprocess] Preparing for Whisper: {os.path.basename(input_path)} → 16kHz mono WAV")
    _run_ffmpeg(cmd, "Whisper input preparation")

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise AudioPreprocessError(f"FFmpeg produced no output for Whisper preparation: {output_path}")

    logger.info(f"[preprocess] Whisper input ready: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Compatibility shim (deprecated — kept so nothing breaks)
# ---------------------------------------------------------------------------

def preprocess_audio(input_file_path: str) -> Dict[str, Any]:
    """
    DEPRECATED: Use prepare_for_separation() for Demucs input.

    This shim now calls prepare_for_separation() so existing code
    that calls preprocess_audio() still works, but the output is
    now correctly formatted for Demucs (44.1kHz stereo) instead of
    the old 16kHz mono which was causing separation artifacts.
    """
    logger.warning(
        "[preprocess] preprocess_audio() is deprecated. "
        "Call prepare_for_separation() directly for Demucs input."
    )

    name, _ = os.path.splitext(input_file_path)
    output_path = f"{name}_for_demucs.wav"

    prepared_path = prepare_for_separation(input_file_path, output_path)

    # Return a stats dict compatible with the old interface
    try:
        import librosa
        duration = librosa.get_duration(path=prepared_path)
    except Exception:
        duration = 0.0

    return {
        "final_file_path": prepared_path,
        "original_duration": duration,
        "trimmed_duration": duration,
        "skipped_trim": True,
    }
