"""
Faster-Whisper Transcription Service
======================================

Transcribes vocal stems for karaoke lyric generation.

Key configuration decisions for music/karaoke use:

1. VAD (silero-vad):
   - Whisper was trained on speech. Music has long silences, reverb, and
     background noise that Whisper can hallucinate over.
   - VAD pre-filters the audio so Whisper only processes actual speech segments.
   - This is the single biggest anti-hallucination measure.

2. condition_on_previous_text=False:
   - Default=True causes Whisper to "continue" from prior context.
   - In music, this means Whisper hallucinates bridge words between verses.
   - Setting to False makes each segment independent.

3. temperature=[0.0]:
   - Default: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0] — Whisper falls back to higher
     temperatures when confidence is low, introducing randomness.
   - For music, forcing temperature=0 (greedy decoding) is more deterministic
     and less likely to hallucinate creatively. We allow one fallback to 0.2.

4. beam_size=5 (GPU) / 1 (CPU):
   - beam_size=5 on CPU is very slow with minimal quality gain for music.
   - beam_size=1 (greedy) is 5x faster on CPU and acceptable for karaoke.

5. word_timestamps=True:
   - Required for per-word karaoke highlighting.
   - Whisper's word-level timestamps are generally accurate to ±100ms.

6. no_speech_threshold=0.6:
   - Segments where Whisper has >60% confidence they contain no speech
     are dropped. Prevents transcribing music-only sections as lyrics.

7. log_prob_threshold=-1.0:
   - Segments with average log probability below this are skipped.
   - Default is -1.0 which is already fairly permissive. Keep it.
"""

import os
import gc
import json
import logging
import threading
from typing import Optional
import torch
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    pass


class FasterWhisperTranscriber:
    def __init__(self):
        """
        Initializes the Faster-Whisper Transcriber.

        Model selection is automatic based on hardware:
          - GPU  -> large-v3  (fast and accurate)
          - CPU  -> base      (tolerable speed on CPU; tiny is fastest)

        Override with env var WHISPER_MODEL_SIZE.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_gpu = self.device == "cuda"

        # Pick a sensible default for the hardware
        default_model = "large-v3" if self.is_gpu else "base"
        self.model_size = os.getenv("WHISPER_MODEL_SIZE", default_model)

        # float16 needs CUDA; int8 is the fastest option on CPU
        self.compute_type = "float16" if self.is_gpu else "int8"

        # Persistent download cache so models are only downloaded once
        self._cache_dir = os.path.join(
            os.path.dirname(__file__), "..", ".whisperx_cache"
        )
        os.makedirs(self._cache_dir, exist_ok=True)

        logger.info(
            f"FasterWhisperTranscriber ready | model={self.model_size} "
            f"device={self.device} compute_type={self.compute_type}"
        )

    def _flush_memory(self):
        """Forces GC and clears CUDA cache between heavy model loads."""
        gc.collect()
        if self.is_gpu:
            torch.cuda.empty_cache()

    def _run_phase(self, func, phase_name: str, timeout_seconds: int):
        """
        Runs `func` in a daemon thread with a hard timeout.
        Raises TranscriptionError if it exceeds `timeout_seconds`.
        """
        result: list = [None]
        exc: list = [None]

        def _target():
            try:
                result[0] = func()
            except Exception as e:
                exc[0] = e

        t = threading.Thread(target=_target, daemon=True, name=f"fasterwhisper-{phase_name}")
        t.start()
        t.join(timeout=timeout_seconds)

        if t.is_alive():
            raise TranscriptionError(
                f"Faster-Whisper phase '{phase_name}' timed out after {timeout_seconds}s. "
                f"Consider setting WHISPER_MODEL_SIZE=tiny in .env for faster CPU processing."
            )
        if exc[0] is not None:
            raise exc[0]
        return result[0]

    def transcribe(self, audio_path: str, output_dir: Optional[str] = None) -> str:
        """
        Runs the Faster-Whisper transcription on a vocal stem.

        IMPORTANT: audio_path should be a 16kHz mono WAV file prepared by
        prepare_for_whisper() in audio_preprocess.py.  Do NOT pass the raw
        Demucs 44.1kHz stereo output — Whisper's internal resampler is
        slower and less accurate than a dedicated FFmpeg pass.

        Returns the path to the saved JSON transcription file.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if output_dir is None:
            output_dir = os.path.dirname(audio_path)

        name = os.path.splitext(os.path.basename(audio_path))[0]
        json_output_path = os.path.join(output_dir, f"{name}_transcription.json")

        # Per-phase timeouts — CPU needs much more time than GPU
        ph = {
            "transcription": 600 if self.is_gpu else 1800,   # 10 min GPU / 30 min CPU
        }

        logger.info(f"Faster-Whisper pipeline starting | file={audio_path}")

        try:
            logger.info(
                f"Faster-Whisper Transcription "
                f"(model={self.model_size} device={self.device})..."
            )

            def _transcribe():
                model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=self._cache_dir
                )

                # ── Transcription parameters ──────────────────────────────────
                # These are critical for music/karaoke quality. See module docstring.
                segments, info = model.transcribe(
                    audio_path,

                    # Word-level timestamps — required for karaoke highlighting
                    word_timestamps=True,

                    # VAD filter — CRITICAL for music.
                    # Silero-VAD detects actual speech frames and masks out music-only
                    # sections before they reach Whisper.  This is the #1 anti-
                    # hallucination measure for music.  Without this, Whisper reads
                    # drum fills, guitar solos, and reverb tails as lyrics.
                    vad_filter=True,
                    vad_parameters={
                        "threshold": 0.4,            # Confidence to classify as speech (lower = more sensitive)
                        "min_speech_duration_ms": 100,  # Minimum speech segment to keep
                        "max_speech_duration_s": 30,    # Split segments longer than this
                        "min_silence_duration_ms": 500, # Silence gap to trigger a new segment
                        "speech_pad_ms": 200,           # Padding around detected speech
                    },

                    # CRITICAL: Disable context conditioning between segments.
                    # Default=True causes Whisper to hallucinate bridge words when
                    # there is a gap between lyric phrases.  In music, gaps are
                    # intentional (instrumental sections).  Setting to False makes
                    # each segment independent.
                    condition_on_previous_text=False,

                    # Temperature controls decoding randomness.
                    # [0.0] = greedy decoding (deterministic, no creative hallucination)
                    # Fallback to 0.2 only if compression ratio check fails (Whisper's own heuristic).
                    # Default was [0.0, 0.2, 0.4, 0.6, 0.8, 1.0] — too many fallbacks
                    # introduce randomness in music where confidence is naturally lower.
                    temperature=[0.0, 0.2],

                    # Beam size — on CPU, beam_size=1 (greedy) is 3-5x faster
                    # than beam_size=5 with minimal quality difference for music.
                    # On GPU, use beam_size=5 for better accuracy.
                    beam_size=5 if self.is_gpu else 1,

                    # No-speech threshold: segments where Whisper is >60% confident
                    # there is no speech are dropped entirely.  This prevents
                    # transcribing instrumental bridges as lyrics.
                    no_speech_threshold=0.6,

                    # Log-probability threshold: segments with low average
                    # log-probability are skipped.  Default -1.0 is kept.
                    log_prob_threshold=-1.0,

                    # Compression ratio threshold: segments that are suspiciously
                    # repetitive (compression ratio > 2.4) are flagged as hallucinations
                    # by Whisper and re-decoded.  Keep the default.
                    compression_ratio_threshold=2.4,
                )

                # Need to consume the generator to actually process
                segments_data = []
                for segment in segments:
                    # Skip segments marked as no-speech by Whisper
                    if getattr(segment, 'no_speech_prob', 0) > 0.8:
                        logger.debug(
                            f"[whisper] Skipping high no-speech segment "
                            f"[{segment.start:.1f}s-{segment.end:.1f}s] "
                            f"no_speech_prob={segment.no_speech_prob:.2f}"
                        )
                        continue

                    words_data = []
                    if segment.words:
                        for word in segment.words:
                            # Include all words but preserve probability for downstream filtering
                            words_data.append({
                                "word": word.word,
                                "start": word.start,
                                "end": word.end,
                                "probability": word.probability
                            })

                    # Only include segments that actually have words
                    text = segment.text.strip()
                    if text:
                        segments_data.append({
                            "start": segment.start,
                            "end": segment.end,
                            "text": text,
                            "words": words_data,
                            "avg_logprob": getattr(segment, 'avg_logprob', None),
                            "no_speech_prob": getattr(segment, 'no_speech_prob', None),
                        })

                del model
                return {
                    "language": info.language,
                    "language_probability": info.language_probability,
                    "segments": segments_data
                }

            result = self._run_phase(_transcribe, "transcription", ph["transcription"])
            self._flush_memory()

            logger.info(
                f"Faster-Whisper done | language={result.get('language')} "
                f"lang_prob={result.get('language_probability', 0):.2f} "
                f"segments={len(result.get('segments', []))}"
            )

            # ---- Save result ----
            logger.info(f"Faster-Whisper — saving transcription to {json_output_path}")
            with open(json_output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.info("Faster-Whisper pipeline finished successfully.")
            return json_output_path

        except TranscriptionError:
            raise
        except Exception as e:
            logger.error(f"Faster-Whisper pipeline failed: {e}", exc_info=True)
            raise TranscriptionError(f"Transcription failed: {e}") from e
        finally:
            self._flush_memory()
