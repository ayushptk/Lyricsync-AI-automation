import os
import logging
import torch
import torchaudio
from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile, save_audio

logger = logging.getLogger(__name__)

class DemucsSeparationError(Exception):
    pass

class DemucsSeparator:
    def __init__(self, model_name: str = "htdemucs"):
        """
        Initializes the Demucs model.
        Model weights are downloaded and cached automatically via torch.hub.
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initializing Demucs model '{model_name}' on device: {self.device}")
        
        try:
            self.model = get_model(self.model_name)
            self.model.cpu()
            self.model.eval()
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
            # Load audio using Demucs AudioFile utility
            wav = AudioFile(input_path).read(streams=0, samplerate=self.model.samplerate, channels=self.model.audio_channels)
            
            # Normalize
            ref = wav.mean(0)
            wav = (wav - ref.mean()) / ref.std()
            
            # Move model and data to device
            self.model.to(self.device)
            wav = wav.to(self.device)
            
            # Apply model (Memory Optimized: shifts=1, split=True)
            logger.info(f"Applying Demucs model... (VRAM Allocated: {torch.cuda.memory_allocated() / 1e6:.2f}MB)" if self.device == "cuda" else "Applying Demucs model...")
            with torch.no_grad():
                sources = apply_model(
                    self.model, wav,
                    shifts=1,
                    split=True,
                    overlap=0.25,
                    progress=False
                )
            
            # Reverse normalization
            sources = sources * ref.std() + ref.mean()
            
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
            
            return vocals_path
            
        except Exception as e:
            logger.error(f"Vocal separation failed: {str(e)}")
            raise DemucsSeparationError(f"Separation failed: {str(e)}")
        finally:
            # Attempt to clear CUDA cache if used
            if self.device == "cuda":
                torch.cuda.empty_cache()
