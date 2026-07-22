import os
import logging
from typing import Optional
import tensorflow as tf

# Configure TF memory growth to prevent OOM clashes with PyTorch (Demucs)
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)

from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH

logger = logging.getLogger(__name__)

class BasicPitchExtractionError(Exception):
    pass

class MelodyExtractor:
    def __init__(self):
        """
        Initializes the Basic Pitch melody extractor.
        Model weights are loaded from the default ICASSP 2022 model.
        """
        self.model_path = str(ICASSP_2022_MODEL_PATH) + ".onnx"
        logger.info(f"Initializing Basic Pitch extractor with model: {self.model_path}")

    def extract_melody(self, input_audio_path: str, output_dir: str = None) -> str:
        """
        Converts the input audio (ideally isolated vocals) to a MIDI file.
        Returns the path to the generated .mid file.
        """
        if not os.path.exists(input_audio_path):
            raise FileNotFoundError(f"Input audio file not found: {input_audio_path}")
            
        if output_dir is None:
            output_dir = os.path.dirname(input_audio_path)
            
        filename = os.path.basename(input_audio_path)
        name, _ = os.path.splitext(filename)
        midi_output_path = os.path.join(output_dir, f"{name}_basic_pitch.mid")
        
        logger.info(f"Starting melody extraction for {input_audio_path}")
        
        try:
            # predict_and_save outputs multiple files by default (MIDI, NPZ, SONIFY).
            # We only want the MIDI file.
            predict_and_save(
                audio_path_list=[input_audio_path],
                output_directory=output_dir,
                save_midi=True,
                sonify_midi=False,
                save_model_outputs=False,
                save_notes=False,
                model_or_model_path=self.model_path,
                # Tuned thresholds for vocals
                onset_threshold=0.6,
                frame_threshold=0.3,
                minimum_note_length=50.0, # milliseconds
                minimum_frequency=80.0,   # Hz
                maximum_frequency=2000.0, # Hz
            )
            
            # predict_and_save automatically names the output based on the input name + "_basic_pitch.mid"
            logger.info(f"Successfully generated MIDI at {midi_output_path}")
            return midi_output_path
            
        except Exception as e:
            logger.error(f"Melody extraction failed: {str(e)}")
            raise BasicPitchExtractionError(f"Extraction failed: {str(e)}")
