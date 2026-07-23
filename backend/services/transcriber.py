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
        Runs the Faster-Whisper transcription.
        Returns the path to the saved JSON transcription file in WhisperX format.
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
                
                # word_timestamps=True is necessary for karaoke
                segments, info = model.transcribe(audio_path, word_timestamps=True)
                
                # Need to consume the generator to actually process
                segments_data = []
                for segment in segments:
                    words_data = []
                    if segment.words:
                        for word in segment.words:
                            words_data.append({
                                "word": word.word,
                                "start": word.start,
                                "end": word.end,
                                "probability": word.probability
                            })
                    
                    segments_data.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                        "words": words_data
                    })
                
                del model
                return {
                    "language": info.language,
                    "segments": segments_data
                }

            result = self._run_phase(_transcribe, "transcription", ph["transcription"])
            self._flush_memory()
            
            logger.info(f"Faster-Whisper done | detected language={result.get('language')}")

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
