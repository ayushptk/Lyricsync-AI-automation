import os
import gc
import json
import logging
from typing import Dict, Any
import torch
import whisperx

logger = logging.getLogger(__name__)

class TranscriptionError(Exception):
    pass

class WhisperXTranscriber:
    def __init__(self, model_size: str = "large-v2"):
        """
        Initializes the WhisperX Transcriber.
        """
        self.model_size = model_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # compute_type float16 requires GPU, fallback to int8 for CPU
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        
        # We need HF_TOKEN for pyannote diarization
        self.hf_token = os.getenv("HF_TOKEN")
        
        logger.info(f"Initializing WhisperX ({model_size}) on {self.device} with compute type {self.compute_type}")

    def _flush_memory(self):
        """Forces garbage collection and clears CUDA cache between heavy model loads."""
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()

    def transcribe(self, audio_path: str, output_dir: str = None) -> str:
        """
        Transcribes audio, forces alignment, and performs speaker diarization.
        Returns the path to the saved JSON transcription.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        if output_dir is None:
            output_dir = os.path.dirname(audio_path)
            
        filename = os.path.basename(audio_path)
        name, _ = os.path.splitext(filename)
        json_output_path = os.path.join(output_dir, f"{name}_transcription.json")
        
        logger.info(f"Starting WhisperX pipeline for {audio_path}")
        
        try:
            # Load audio
            audio = whisperx.load_audio(audio_path)
            
            # --- Phase 1: Transcription ---
            logger.info("Phase 1: Transcription...")
            model = whisperx.load_model(self.model_size, self.device, compute_type=self.compute_type)
            # Use batch_size=16 for speed if on GPU, otherwise lower for CPU
            batch_size = 16 if self.device == "cuda" else 4
            result = model.transcribe(audio, batch_size=batch_size)
            
            # Flush Whisper model from VRAM
            del model
            self._flush_memory()
            
            # --- Phase 2: Alignment ---
            logger.info("Phase 2: Word-Level Alignment...")
            language_code = result["language"]
            align_model, align_metadata = whisperx.load_align_model(language_code=language_code, device=self.device)
            result = whisperx.align(result["segments"], align_model, align_metadata, audio, self.device, return_char_alignments=False)
            
            # Flush Alignment model from VRAM
            del align_model
            self._flush_memory()
            
            # --- Phase 3: Diarization (Optional but recommended) ---
            if self.hf_token:
                logger.info("Phase 3: Speaker Diarization...")
                diarize_model = whisperx.DiarizationPipeline(use_auth_token=self.hf_token, device=self.device)
                diarize_segments = diarize_model(audio)
                result = whisperx.assign_word_speakers(diarize_segments, result)
                
                # Flush Diarization model
                del diarize_model
                self._flush_memory()
            else:
                logger.warning("Skipping Diarization Phase: HF_TOKEN not found in environment variables.")
                
            # Save results
            logger.info(f"Saving transcription to {json_output_path}")
            with open(json_output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
                
            return json_output_path
            
        except Exception as e:
            logger.error(f"Transcription pipeline failed: {str(e)}")
            raise TranscriptionError(f"Transcription failed: {str(e)}")
        finally:
            self._flush_memory()
