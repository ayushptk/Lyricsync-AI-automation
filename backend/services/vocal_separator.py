import os
import logging
import torch
import torchaudio
import torch.nn.functional as F
import demucs.hdemucs

_original_pad1d = demucs.hdemucs.pad1d
def _patched_pad1d(x, paddings, mode='constant', value=0.):
    try:
        return _original_pad1d(x, paddings, mode, value)
    except AssertionError:
        # Bypass PyTorch CPU reflection padding precision bug
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

from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile, save_audio

logger = logging.getLogger(__name__)

# Maximum audio duration we'll attempt vocal separation on (seconds)
MAX_DURATION_FOR_SEPARATION = 600  # 10 minutes

class DemucsSeparationError(Exception):
    pass

class DemucsSeparator:
    def __init__(self, model_name: str = "mdx_extra"):
        """
        Initializes the Demucs model.
        Model weights are downloaded and cached automatically via torch.hub.
        """
        self.model_name = model_name
        # Force CPU on Windows to avoid CUDA issues
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initializing Demucs model '{model_name}' on device: {self.device}")
        
        try:
            self.model = get_model(self.model_name)
            self.model.cpu()
            self.model.eval()
            logger.info(f"Demucs model loaded successfully. Sources: {self.model.sources}")
        except Exception as e:
            logger.error(f"Failed to load Demucs model: {str(e)}")
            raise DemucsSeparationError(f"Model load failed: {str(e)}")

    def separate_vocals(self, input_path: str, output_dir: str = None) -> str:
        """
        Separates the vocal stem from a preprocessed audio file.
        Optimized for memory by using shifts=1.
        Returns the path to the isolated vocals.wav.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        if output_dir is None:
            output_dir = os.path.dirname(input_path)
            
        filename = os.path.basename(input_path)
        name, _ = os.path.splitext(filename)
        vocals_path = os.path.join(output_dir, f"{name}_vocals.wav")
        
        logger.info(f"Starting vocal separation for {input_path}")
        
        try:
            # --- Pre-flight checks ---
            # Check audio duration to prevent OOM on very long files
            import librosa
            duration = librosa.get_duration(path=input_path)
            logger.info(f"Audio duration: {duration:.1f}s")
            
            if duration > MAX_DURATION_FOR_SEPARATION:
                raise DemucsSeparationError(
                    f"Audio is too long ({duration:.0f}s > {MAX_DURATION_FOR_SEPARATION}s). "
                    f"Skipping vocal separation to prevent memory issues."
                )
            
            # Check available memory (rough heuristic: need ~4x the audio file size)
            file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
            logger.info(f"Input file size: {file_size_mb:.1f}MB")
            
            # Load audio using Demucs AudioFile utility
            logger.info("Loading audio into Demucs...")
            wav = AudioFile(input_path).read(
                streams=0, 
                samplerate=self.model.samplerate, 
                channels=self.model.audio_channels
            )
            
            # Normalize
            ref = wav.mean(0)
            wav = (wav - ref.mean()) / (ref.std() + 1e-8)  # Added epsilon to prevent division by zero
            
            # Move model and data to device
            self.model.to(self.device)
            wav = wav.to(self.device)
            
            # Apply model (Memory Optimized: shifts=1, split=True)
            if self.device == "cuda":
                logger.info(f"Applying Demucs model... (VRAM Allocated: {torch.cuda.memory_allocated() / 1e6:.2f}MB)")
            else:
                logger.info(f"Applying Demucs model on CPU (this will be slow for {duration:.0f}s of audio)...")
            
            with torch.no_grad():
                sources = apply_model(
                    self.model, wav[None],
                    shifts=1,
                    split=True,
                    overlap=0.25,
                    progress=True,  # Enable progress logging
                    segment=None,   # Let Demucs auto-decide segment size
                )[0]
            
            logger.info("Demucs model applied successfully.")
            
            # Reverse normalization
            sources = sources * (ref.std() + 1e-8) + ref.mean()
            
            # Verify the index of vocals
            if 'vocals' not in self.model.sources:
                raise DemucsSeparationError("Model does not output 'vocals' stem.")
            
            vocal_idx = self.model.sources.index('vocals')
            vocal_tensor = sources[vocal_idx]
            
            # Move back to CPU to save
            vocal_tensor = vocal_tensor.cpu()
            self.model.cpu() # Free VRAM
            
            logger.info(f"Saving isolated vocals to {vocals_path}")
            save_audio(vocal_tensor, vocals_path, samplerate=self.model.samplerate)
            
            logger.info(f"Vocal separation completed successfully: {vocals_path}")
            return vocals_path
            
        except DemucsSeparationError:
            raise  # Re-raise our own errors
        except Exception as e:
            logger.error(f"Vocal separation failed: {str(e)}")
            raise DemucsSeparationError(f"Separation failed: {str(e)}")
        finally:
            # Attempt to clear CUDA cache if used
            if self.device == "cuda":
                torch.cuda.empty_cache()
            # Force garbage collection to free memory
            import gc
            gc.collect()
