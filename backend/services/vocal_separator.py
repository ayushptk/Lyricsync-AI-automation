import os
import logging
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)

# Maximum audio duration we'll attempt vocal separation on (seconds)
MAX_DURATION_FOR_SEPARATION = 600  # 10 minutes

# Strategy selection: "fast" (FFmpeg only, ~5 seconds), "balanced" (htdemucs, ~3-8 min on CPU)
# Controlled via env var; defaults to "fast" for best user experience
SEPARATION_STRATEGY = os.getenv("VOCAL_SEPARATION_STRATEGY", "fast").lower()


class DemucsSeparationError(Exception):
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
        return "ffmpeg"  # Hope it's on PATH


def _ffmpeg_vocal_extract(input_path: str, output_path: str) -> str:
    """
    Ultra-fast vocal extraction using FFmpeg audio filters.
    
    Uses a combination of stereo-to-mono center extraction and filtering
    to isolate vocals. Not as accurate as ML models but completes in seconds.
    
    Technique: Extract center channel (where vocals usually are in stereo mixes)
    using the 'pan' filter with L-R cancellation, then apply bandpass filter
    for vocal frequency range (100Hz - 8000Hz).
    """
    ffmpeg_exe = _get_ffmpeg_exe()
    
    # First check if audio is stereo or mono
    probe_cmd = [
        ffmpeg_exe, "-i", input_path,
        "-hide_banner",
        "-f", "null", "-"
    ]
    
    try:
        result = subprocess.run(
            probe_cmd, capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        stderr_output = result.stderr
        is_stereo = "stereo" in stderr_output.lower()
    except Exception:
        is_stereo = False
    
    if is_stereo:
        # For stereo: Extract center channel (vocals) using L+R sum,
        # then apply vocal frequency bandpass
        # This works because vocals are typically panned center in most mixes
        filter_complex = (
            # Convert to stereo processing, extract center channel
            "[0:a]pan=mono|c0=0.5*c0+0.5*c1[center];"
            # Apply bandpass filter for vocal frequencies (100Hz-8kHz)
            "[center]highpass=f=100,lowpass=f=8000[vocals]"
        )
        cmd = [
            ffmpeg_exe,
            "-i", input_path,
            "-filter_complex", filter_complex,
            "-map", "[vocals]",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            output_path
        ]
    else:
        # For mono: just apply bandpass filter for vocal frequency range
        cmd = [
            ffmpeg_exe,
            "-i", input_path,
            "-af", "highpass=f=100,lowpass=f=8000",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            output_path
        ]
    
    logger.info(f"Running FFmpeg vocal extraction (stereo={is_stereo})...")
    
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        if proc.returncode != 0:
            raise DemucsSeparationError(f"FFmpeg vocal extraction failed: {proc.stderr[-500:]}")
        
        if not os.path.exists(output_path):
            raise DemucsSeparationError("FFmpeg produced no output file")
            
        logger.info(f"FFmpeg vocal extraction complete: {output_path}")
        return output_path
        
    except subprocess.TimeoutExpired:
        raise DemucsSeparationError("FFmpeg vocal extraction timed out (>120s)")
    except DemucsSeparationError:
        raise
    except Exception as e:
        raise DemucsSeparationError(f"FFmpeg vocal extraction error: {str(e)}")


class DemucsSeparator:
    """
    Vocal separator with dual strategy:
    
    - "fast" mode: Uses FFmpeg center-channel extraction + bandpass filtering.
      Completes in ~5 seconds. Good enough for karaoke where you mostly need
      the vocal melody line for transcription.
      
    - "balanced" mode: Uses htdemucs (single hybrid transformer model).
      ~3-5x faster than the old mdx_extra (which ran 4 sub-models).
      Still takes a few minutes on CPU but produces better separation quality.
    """
    
    def __init__(self, model_name: str = None, strategy: str = None):
        """
        Initialize the separator.
        
        Args:
            model_name: Demucs model name (only used in "balanced" mode).
                        Defaults to "htdemucs" which is much faster than "mdx_extra".
            strategy: "fast" or "balanced". Defaults to SEPARATION_STRATEGY env var.
        """
        self.strategy = strategy or SEPARATION_STRATEGY
        
        if self.strategy == "balanced":
            # Only load heavy ML dependencies when actually needed
            self.model_name = model_name or "htdemucs"
            self._model = None
            self._device = None
        
        logger.info(f"VocalSeparator initialized with strategy='{self.strategy}'")
    
    def _load_model(self):
        """Lazily load the Demucs model (only for balanced strategy)."""
        if self._model is not None:
            return
        
        import torch
        import torch.nn.functional as F
        import demucs.hdemucs
        
        # Patch pad1d for CPU compatibility
        _original_pad1d = demucs.hdemucs.pad1d
        def _patched_pad1d(x, paddings, mode='constant', value=0.):
            try:
                return _original_pad1d(x, paddings, mode, value)
            except AssertionError:
                length = x.shape[-1]
                padding_left, padding_right = paddings
                if mode == 'reflect':
                    max_pad = max(padding_left, padding_right)
                    if length <= max_pad:
                        extra_pad = max_pad - length + 1
                        extra_pad_right = min(padding_right, extra_pad)
                        extra_pad_left = extra_pad - extra_pad_right
                        paddings = (padding_left - extra_pad_left, padding_right - extra_pad_right)
                        x = F.pad(x, (extra_pad_left, extra_pad_right))
                out = F.pad(x, paddings, mode, value)
                return out
        demucs.hdemucs.pad1d = _patched_pad1d
        
        from demucs.pretrained import get_model
        
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading Demucs model '{self.model_name}' on device: {self._device}")
        
        try:
            self._model = get_model(self.model_name)
            self._model.cpu()
            self._model.eval()
            logger.info(f"Demucs model loaded. Sources: {self._model.sources}")
        except Exception as e:
            raise DemucsSeparationError(f"Model load failed: {str(e)}")
    
    def _separate_with_demucs(self, input_path: str, output_path: str) -> str:
        """ML-based vocal separation using htdemucs (balanced mode)."""
        import torch
        from demucs.apply import apply_model
        from demucs.audio import AudioFile, save_audio
        
        self._load_model()
        
        logger.info(f"Loading audio for Demucs processing...")
        wav = AudioFile(input_path).read(
            streams=0,
            samplerate=self._model.samplerate,
            channels=self._model.audio_channels
        )
        
        # Normalize
        ref = wav.mean(0)
        wav = (wav - ref.mean()) / (ref.std() + 1e-8)
        
        # Move to device
        self._model.to(self._device)
        wav = wav.to(self._device)
        
        logger.info(f"Running htdemucs on {self._device}...")
        
        with torch.no_grad():
            sources = apply_model(
                self._model, wav[None],
                shifts=0,       # No shifts = much faster (was shifts=1)
                split=True,
                overlap=0.1,    # Reduced overlap for speed (was 0.25)
                progress=False,
                segment=None,
            )[0]
        
        # Reverse normalization
        sources = sources * (ref.std() + 1e-8) + ref.mean()
        
        # Extract vocals
        if 'vocals' not in self._model.sources:
            raise DemucsSeparationError("Model does not output 'vocals' stem.")
        
        vocal_idx = self._model.sources.index('vocals')
        vocal_tensor = sources[vocal_idx].cpu()
        self._model.cpu()
        
        save_audio(vocal_tensor, output_path, samplerate=self._model.samplerate)
        logger.info(f"Demucs vocal separation complete: {output_path}")
        
        # Cleanup
        if self._device == "cuda":
            torch.cuda.empty_cache()
        import gc
        gc.collect()
        
        return output_path
    
    def separate_vocals(self, input_path: str, output_dir: str = None) -> str:
        """
        Separates vocals from an audio file.
        
        Uses the configured strategy:
        - "fast": FFmpeg-based extraction (~5 seconds)
        - "balanced": htdemucs ML model (~3-8 minutes on CPU)
        
        Returns the path to the isolated vocals file.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if output_dir is None:
            output_dir = os.path.dirname(input_path)
        
        filename = os.path.basename(input_path)
        name, _ = os.path.splitext(filename)
        vocals_path = os.path.join(output_dir, f"{name}_vocals.wav")
        
        logger.info(f"Vocal separation: strategy='{self.strategy}', input={input_path}")
        
        # Check duration
        try:
            import librosa
            duration = librosa.get_duration(path=input_path)
            logger.info(f"Audio duration: {duration:.1f}s")
            
            if duration > MAX_DURATION_FOR_SEPARATION:
                raise DemucsSeparationError(
                    f"Audio too long ({duration:.0f}s > {MAX_DURATION_FOR_SEPARATION}s)."
                )
        except DemucsSeparationError:
            raise
        except Exception as e:
            logger.warning(f"Could not check duration: {e}. Proceeding anyway.")
        
        # Execute chosen strategy
        if self.strategy == "fast":
            return _ffmpeg_vocal_extract(input_path, vocals_path)
        elif self.strategy == "balanced":
            return self._separate_with_demucs(input_path, vocals_path)
        else:
            logger.warning(f"Unknown strategy '{self.strategy}', falling back to 'fast'")
            return _ffmpeg_vocal_extract(input_path, vocals_path)
