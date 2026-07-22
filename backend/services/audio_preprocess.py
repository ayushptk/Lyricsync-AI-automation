import os
import logging
import ffmpeg
import librosa
import soundfile as sf
import imageio_ffmpeg
from typing import Dict, Any

logger = logging.getLogger(__name__)
ffmpeg_location = os.getenv('FFMPEG_LOCATION')
FFMPEG_EXE = os.path.join(ffmpeg_location, 'ffmpeg.exe') if ffmpeg_location else imageio_ffmpeg.get_ffmpeg_exe()

class AudioPreprocessError(Exception):
    pass

def standardize_and_normalize(input_path: str, output_path: str) -> str:
    """
    Converts audio to 16kHz Mono WAV and applies EBU R128 loudness normalization.
    """
    try:
        logger.info(f"Normalizing and standardizing {input_path}")
        # ffmpeg -i input.mp3 -af loudnorm -ar 16000 -ac 1 output.wav
        (
            ffmpeg
            .input(input_path)
            .filter('loudnorm')
            .output(output_path, ar=16000, ac=1, format='wav')
            .overwrite_output()
            .run(cmd=FFMPEG_EXE, capture_stdout=True, capture_stderr=True)
        )
        return output_path
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg Error: {e.stderr.decode('utf8')}")
        raise AudioPreprocessError(f"Failed to normalize audio: {e.stderr.decode('utf8')}")

def trim_silence(input_path: str, output_path: str, top_db: int = 30) -> Dict[str, Any]:
    """
    Loads a standardized WAV file, trims leading/trailing silence below top_db,
    and saves the result.
    Raises AudioPreprocessError if the file is too large to load in memory safely.
    """
    logger.info(f"Trimming silence from {input_path}")
    
    try:
        # Pre-check duration using librosa.get_duration to avoid OOM on huge files
        duration = librosa.get_duration(path=input_path)
        if duration > 7200: # 2 hours
            logger.warning(f"Audio file is too long ({duration}s). Skipping Librosa trim to prevent OOM.")
            # Just rename/copy the input to output
            os.rename(input_path, output_path)
            return {"original_duration": duration, "trimmed_duration": duration, "skipped_trim": True}

        # Load the audio (sr=None because it should already be 16kHz from FFmpeg)
        y, sr = librosa.load(input_path, sr=None)
        
        # Trim silence
        yt, index = librosa.effects.trim(y, top_db=top_db)
        
        # Save trimmed audio
        sf.write(output_path, yt, sr)
        
        original_duration = len(y) / sr
        trimmed_duration = len(yt) / sr
        
        logger.info(f"Trimmed audio from {original_duration:.2f}s to {trimmed_duration:.2f}s")
        
        return {
            "original_duration": original_duration,
            "trimmed_duration": trimmed_duration,
            "skipped_trim": False
        }
    except Exception as e:
        logger.error(f"Librosa trimming failed: {str(e)}")
        raise AudioPreprocessError(f"Failed to trim audio: {str(e)}")

def preprocess_audio(input_file_path: str) -> Dict[str, Any]:
    """
    Full pipeline: Normalize -> Format -> Trim
    """
    base_dir = os.path.dirname(input_file_path)
    filename = os.path.basename(input_file_path)
    name, _ = os.path.splitext(filename)
    
    normalized_path = os.path.join(base_dir, f"{name}_norm.wav")
    final_path = os.path.join(base_dir, f"{name}_final.wav")
    
    # 1. Standardize and Normalize
    standardize_and_normalize(input_file_path, normalized_path)
    
    # 2. Trim Silence
    stats = trim_silence(normalized_path, final_path)
    
    # Clean up intermediate normalized file
    if os.path.exists(normalized_path) and normalized_path != final_path:
        os.remove(normalized_path)
        
    stats["final_file_path"] = final_path
    return stats
