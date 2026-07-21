import os
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class PianoRenderingError(Exception):
    pass

class PianoRenderer:
    def __init__(self, soundfont_path: str = "/usr/share/sounds/sf2/FluidR3_GM.sf2"):
        """
        Initializes the FluidSynth renderer.
        Requires fluidsynth and a valid SoundFont (.sf2) installed on the system.
        """
        self.soundfont_path = soundfont_path
        
        # Verify fluidsynth is installed
        try:
            subprocess.run(["fluidsynth", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("FluidSynth CLI not found. Please install fluidsynth (e.g., apt-get install fluidsynth)")
            raise PianoRenderingError("FluidSynth CLI not installed.")
            
        if not os.path.exists(self.soundfont_path):
            logger.warning(f"SoundFont not found at {self.soundfont_path}. FluidSynth might fail if it doesn't have a default.")

    def render_midi_to_mp3(self, midi_path: str, output_dir: str = None) -> str:
        """
        Converts a MIDI file to an MP3 file using FluidSynth and FFmpeg.
        Applies high-quality interpolation and 44.1kHz sample rate.
        """
        if not os.path.exists(midi_path):
            raise FileNotFoundError(f"Input MIDI file not found: {midi_path}")
            
        if output_dir is None:
            output_dir = os.path.dirname(midi_path)
            
        filename = os.path.basename(midi_path)
        name, _ = os.path.splitext(filename)
        
        # Intermediate and final files
        raw_wav_path = os.path.join(output_dir, f"{name}_raw.wav")
        final_mp3_path = os.path.join(output_dir, f"{name}_piano.mp3")
        
        logger.info(f"Starting FluidSynth rendering for {midi_path}")
        
        try:
            # 1. Render MIDI to WAV (Offline mode, fast render)
            # -F = Output file
            # -ni = No MIDI in, No Shell
            # -r 44100 = 44.1kHz sample rate
            # -O s16 = 7th order interpolation (high quality)
            fluidsynth_cmd = [
                "fluidsynth",
                "-F", raw_wav_path,
                "-ni",
                "-r", "44100",
                "-O", "s16",
                self.soundfont_path,
                midi_path
            ]
            
            subprocess.run(fluidsynth_cmd, check=True, capture_output=True)
            logger.info(f"Successfully rendered raw WAV: {raw_wav_path}")
            
            # 2. Compress WAV to MP3 using FFmpeg
            ffmpeg_cmd = [
                "ffmpeg",
                "-y", # Overwrite output
                "-i", raw_wav_path,
                "-codec:a", "libmp3lame",
                "-b:a", "192k",
                final_mp3_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            logger.info(f"Successfully compressed to MP3: {final_mp3_path}")
            
            return final_mp3_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)}")
            raise PianoRenderingError(f"Rendering failed: {e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)}")
        except Exception as e:
            logger.error(f"Unexpected rendering error: {str(e)}")
            raise PianoRenderingError(f"Rendering failed: {str(e)}")
        finally:
            # Clean up the massive raw WAV file to save disk space
            if os.path.exists(raw_wav_path):
                os.remove(raw_wav_path)
