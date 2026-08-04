"""
Loudness Normalizer Service
============================

Matches the perceived loudness (LUFS) of a processed instrumental track
to the original song's loudness, using FFmpeg's EBU R128 loudnorm filter
in two-pass mode.

This compensates for the energy loss that occurs when vocals are removed
by Demucs — the instrumental stem is inherently quieter because vocal
energy has been subtracted from the mix.

Design decisions:
  - Two-pass loudnorm:  Pass 1 measures; Pass 2 applies with measured values.
                        This is more accurate than single-pass loudnorm which
                        can overshoot on dynamic material.
  - Dynamic target:     We target the *original song's* integrated LUFS rather
                        than a hardcoded value, so every song is matched to itself.
  - True-peak limiter:  Enforces TP ≤ -1.0 dBTP to prevent digital clipping.
  - No pitch/tempo changes: Only gain and transparent limiting are applied.
"""

import os
import re
import json
import logging
import subprocess
import sys
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


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


class LoudnessNormalizationError(Exception):
    pass


def _measure_loudness(audio_path: str) -> Dict[str, float]:
    """
    Runs FFmpeg loudnorm filter in measurement-only mode (first pass).
    
    Returns a dict with keys:
        input_i     — integrated LUFS
        input_tp    — true peak in dBTP
        input_lra   — loudness range in LU
        input_thresh — threshold in LUFS
    """
    ffmpeg_exe = _get_ffmpeg_exe()

    cmd = [
        ffmpeg_exe,
        "-i", audio_path,
        "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json",
        "-f", "null",
        "-"
    ]

    logger.info(f"[loudness] Measuring loudness of: {os.path.basename(audio_path)}")

    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            creationflags=creationflags,
        )
    except subprocess.TimeoutExpired:
        raise LoudnessNormalizationError(f"Loudness measurement timed out for {audio_path}")

    stderr = result.stderr
    if not stderr:
        raise LoudnessNormalizationError("FFmpeg produced no output during loudness measurement")

    # FFmpeg prints the loudnorm JSON stats at the very end of stderr.
    # Find the last JSON object in the output.
    json_match = re.search(r'\{[^{}]*"input_i"[^{}]*\}', stderr, re.DOTALL)
    if not json_match:
        # Try a broader search — sometimes the keys appear in different order
        json_match = re.search(r'\{\s*\n(?:\s*"[^"]+"\s*:\s*"[^"]*",?\s*\n)+\s*\}', stderr, re.DOTALL)

    if not json_match:
        raise LoudnessNormalizationError(
            f"Could not parse loudnorm stats from FFmpeg output.\n"
            f"Last 500 chars of stderr:\n{stderr[-500:]}"
        )

    try:
        stats = json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        raise LoudnessNormalizationError(f"Failed to parse loudnorm JSON: {e}\nRaw: {json_match.group(0)}")

    parsed = {
        "input_i": float(stats.get("input_i", "-inf")),
        "input_tp": float(stats.get("input_tp", "-inf")),
        "input_lra": float(stats.get("input_lra", "0")),
        "input_thresh": float(stats.get("input_thresh", "-inf")),
        "target_offset": float(stats.get("target_offset", "0")),
    }

    logger.info(
        f"[loudness] {os.path.basename(audio_path)}: "
        f"LUFS={parsed['input_i']:.1f}, TP={parsed['input_tp']:.1f} dBTP, "
        f"LRA={parsed['input_lra']:.1f} LU"
    )
    return parsed


def normalize_instrumental(
    original_audio_path: str,
    instrumental_audio_path: str,
    output_path: Optional[str] = None,
    true_peak_limit: float = -1.0,
) -> Tuple[str, Dict]:
    """
    Match the instrumental track's perceived loudness to the original song.

    This is the main entry point.  It:
      1. Measures the original song's integrated LUFS (the loudness target).
      2. Measures the instrumental's integrated LUFS.
      3. Applies FFmpeg two-pass loudnorm with the original's LUFS as the
         target and the instrumental's measured stats as the input parameters.
      4. Verifies the output LUFS and true peak.

    Args:
        original_audio_path:      Path to the original downloaded audio (MP3/WAV).
        instrumental_audio_path:  Path to the Demucs backing track.
        output_path:              Where to write the normalized file.  Defaults to
                                  <instrumental>_loud.wav next to the input.
        true_peak_limit:          Maximum true peak in dBTP (default -1.0).

    Returns:
        (output_path, report_dict)
        report_dict contains full before/after loudness measurements.

    Raises:
        LoudnessNormalizationError on any failure.
    """
    if not os.path.exists(original_audio_path):
        raise FileNotFoundError(f"Original audio not found: {original_audio_path}")
    if not os.path.exists(instrumental_audio_path):
        raise FileNotFoundError(f"Instrumental audio not found: {instrumental_audio_path}")

    # ── Default output path ──────────────────────────────────────────────
    if output_path is None:
        base, ext = os.path.splitext(instrumental_audio_path)
        output_path = f"{base}_loud{ext}"

    # ── Pass 1: Measure both files ───────────────────────────────────────
    logger.info("[loudness] ═══ Pass 1: Measuring loudness ═══")

    original_stats = _measure_loudness(original_audio_path)
    instrumental_stats = _measure_loudness(instrumental_audio_path)

    target_lufs = original_stats["input_i"]
    instrumental_lufs = instrumental_stats["input_i"]
    lufs_diff = target_lufs - instrumental_lufs

    logger.info(
        f"[loudness] Original LUFS: {target_lufs:.1f} | "
        f"Instrumental LUFS: {instrumental_lufs:.1f} | "
        f"Difference: {lufs_diff:+.1f} dB"
    )

    # Guard: if instrumental is already louder or within 1 dB, skip
    if lufs_diff <= 1.0:
        logger.info(
            f"[loudness] Instrumental is already within 1 dB of the original "
            f"({lufs_diff:+.1f} dB). Skipping normalization."
        )
        import shutil
        shutil.copy2(instrumental_audio_path, output_path)
        report = _build_report(original_stats, instrumental_stats, instrumental_stats, lufs_diff, skipped=True)
        _log_report(report)
        return output_path, report

    # ── Pass 2: Apply loudnorm with measured values ──────────────────────
    logger.info("[loudness] ═══ Pass 2: Applying loudness normalization ═══")

    ffmpeg_exe = _get_ffmpeg_exe()

    # Two-pass loudnorm: feed the measured stats from Pass 1 so FFmpeg
    # does not need to re-measure and can apply precise correction.
    loudnorm_filter = (
        f"loudnorm=I={target_lufs:.1f}"
        f":TP={true_peak_limit:.1f}"
        f":LRA=11"
        f":measured_I={instrumental_stats['input_i']:.2f}"
        f":measured_TP={instrumental_stats['input_tp']:.2f}"
        f":measured_LRA={instrumental_stats['input_lra']:.2f}"
        f":measured_thresh={instrumental_stats['input_thresh']:.2f}"
        f":offset={instrumental_stats['target_offset']:.2f}"
        f":linear=true"
        f":print_format=json"
    )

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", instrumental_audio_path,
        "-af", loudnorm_filter,
        "-ar", "44100",         # Keep at CD quality for the final video
        "-c:a", "pcm_s16le",    # Lossless WAV output
        output_path,
    ]

    logger.info(f"[loudness] Running two-pass loudnorm → {os.path.basename(output_path)}")

    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            creationflags=creationflags,
        )
    except subprocess.TimeoutExpired:
        raise LoudnessNormalizationError("Loudness normalization timed out (>180s)")

    if result.returncode != 0:
        raise LoudnessNormalizationError(
            f"FFmpeg loudnorm failed (rc={result.returncode}):\n{result.stderr[-800:]}"
        )

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise LoudnessNormalizationError("FFmpeg produced no output or empty file during normalization")

    # ── Verify: measure the output ───────────────────────────────────────
    logger.info("[loudness] ═══ Verification: Measuring normalized output ═══")
    output_stats = _measure_loudness(output_path)

    report = _build_report(original_stats, instrumental_stats, output_stats, lufs_diff, skipped=False)
    _log_report(report)

    # Sanity check
    final_diff = abs(target_lufs - output_stats["input_i"])
    if final_diff > 3.0:
        logger.warning(
            f"[loudness] ⚠ Output LUFS differs from target by {final_diff:.1f} dB. "
            f"This is larger than expected but proceeding anyway."
        )

    logger.info(f"[loudness] ✅ Normalization complete: {output_path}")
    return output_path, report


def _build_report(
    original: Dict, instrumental: Dict, output: Dict,
    gain_applied: float, skipped: bool = False
) -> Dict:
    """Build a structured report dict for logging and debugging."""
    return {
        "original": {
            "integrated_lufs": original["input_i"],
            "true_peak_dbtp": original["input_tp"],
            "loudness_range_lu": original["input_lra"],
        },
        "instrumental_before": {
            "integrated_lufs": instrumental["input_i"],
            "true_peak_dbtp": instrumental["input_tp"],
            "loudness_range_lu": instrumental["input_lra"],
        },
        "calculated_gain_db": round(gain_applied, 2),
        "skipped": skipped,
        "instrumental_after": {
            "integrated_lufs": output["input_i"],
            "true_peak_dbtp": output["input_tp"],
            "loudness_range_lu": output["input_lra"],
        },
    }


def _log_report(report: Dict) -> None:
    """Pretty-print the loudness comparison report."""
    orig = report["original"]
    before = report["instrumental_before"]
    after = report["instrumental_after"]

    lines = [
        "",
        "╔══════════════════════════════════════════════════════╗",
        "║          LOUDNESS NORMALIZATION REPORT               ║",
        "╠══════════════════════════════════════════════════════╣",
        f"║  ORIGINAL AUDIO                                      ║",
        f"║    Integrated LUFS:  {orig['integrated_lufs']:>8.1f}                        ║",
        f"║    True Peak:        {orig['true_peak_dbtp']:>8.1f} dBTP                   ║",
        f"║    Loudness Range:   {orig['loudness_range_lu']:>8.1f} LU                     ║",
        "╠══════════════════════════════════════════════════════╣",
        f"║  INSTRUMENTAL (BEFORE)                               ║",
        f"║    Integrated LUFS:  {before['integrated_lufs']:>8.1f}                        ║",
        f"║    True Peak:        {before['true_peak_dbtp']:>8.1f} dBTP                   ║",
        f"║    Loudness Range:   {before['loudness_range_lu']:>8.1f} LU                     ║",
        "╠══════════════════════════════════════════════════════╣",
        f"║  CALCULATED GAIN:    {report['calculated_gain_db']:>+8.1f} dB                     ║",
        f"║  SKIPPED:            {'YES' if report['skipped'] else 'NO':>8s}                        ║",
        "╠══════════════════════════════════════════════════════╣",
        f"║  INSTRUMENTAL (AFTER NORMALIZATION)                  ║",
        f"║    Integrated LUFS:  {after['integrated_lufs']:>8.1f}                        ║",
        f"║    True Peak:        {after['true_peak_dbtp']:>8.1f} dBTP                   ║",
        f"║    Loudness Range:   {after['loudness_range_lu']:>8.1f} LU                     ║",
        "╚══════════════════════════════════════════════════════╝",
        "",
    ]
    logger.info("\n".join(lines))
