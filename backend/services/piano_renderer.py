import os
import subprocess
import logging
import imageio_ffmpeg
from typing import Optional

logger = logging.getLogger(__name__)
ffmpeg_location = os.getenv('FFMPEG_LOCATION')
FFMPEG_EXE = os.path.join(ffmpeg_location, 'ffmpeg.exe') if ffmpeg_location else imageio_ffmpeg.get_ffmpeg_exe()


def _find_fluidsynth_exe() -> str:
    """
    Finds the FluidSynth executable. Checks, in order:
    1. FLUIDSYNTH_PATH env var (path to the folder containing fluidsynth.exe)
    2. The bundled tools/fluidsynth directory within this project
    3. System PATH (i.e. 'fluidsynth' is installed globally)
    """
    # 1. Check FLUIDSYNTH_PATH env var
    env_path = os.getenv("FLUIDSYNTH_PATH")
    if env_path:
        exe_name = "fluidsynth.exe" if os.name == "nt" else "fluidsynth"
        candidate = os.path.join(env_path, exe_name)
        if os.path.isfile(candidate):
            return candidate
        # Maybe user pointed directly to the exe
        if os.path.isfile(env_path):
            return env_path

    # 2. Check bundled tools directory (relative to this file's project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.name == "nt":
        # Search for any fluidsynth.exe inside tools/fluidsynth/
        tools_dir = os.path.join(project_root, "tools", "fluidsynth")
        if os.path.isdir(tools_dir):
            for root, dirs, files in os.walk(tools_dir):
                if "fluidsynth.exe" in files:
                    return os.path.join(root, "fluidsynth.exe")

    # 3. Fall back to system PATH
    return "fluidsynth"


def _find_soundfont() -> str:
    """
    Finds a SoundFont (.sf2) file. Checks, in order:
    1. SOUNDFONT_PATH env var (path to a specific .sf2 file)
    2. The bundled tools/soundfonts directory within this project
    3. Common Linux paths (/usr/share/sounds/sf2/)
    """
    # 1. Check SOUNDFONT_PATH env var
    env_path = os.getenv("SOUNDFONT_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. Check bundled tools/soundfonts directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    soundfonts_dir = os.path.join(project_root, "tools", "soundfonts")
    if os.path.isdir(soundfonts_dir):
        for f in os.listdir(soundfonts_dir):
            if f.lower().endswith(".sf2"):
                return os.path.join(soundfonts_dir, f)

    # 3. Common Linux paths
    linux_paths = [
        "/usr/share/sounds/sf2/FluidR3_GM.sf2",
        "/usr/share/soundfonts/FluidR3_GM.sf2",
        "/usr/share/sounds/sf2/default.sf2",
    ]
    for p in linux_paths:
        if os.path.isfile(p):
            return p

    return ""


class PianoRenderingError(Exception):
    pass

class PianoRenderer:
    def __init__(self, soundfont_path: str = None):
        """
        Initializes the FluidSynth renderer.
        Auto-detects FluidSynth executable and SoundFont file
        using environment variables and bundled tools as fallbacks.
        """
        # Find FluidSynth executable
        self.fluidsynth_exe = _find_fluidsynth_exe()

        # Verify fluidsynth is accessible
        try:
            subprocess.run([self.fluidsynth_exe, "--version"], check=True, capture_output=True, timeout=10)
            logger.info(f"FluidSynth found at: {self.fluidsynth_exe}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.error(f"FluidSynth CLI not found at '{self.fluidsynth_exe}'. "
                         f"Set FLUIDSYNTH_PATH env var or install fluidsynth. Error: {e}")
            raise PianoRenderingError(
                f"FluidSynth CLI not available. Searched: FLUIDSYNTH_PATH env var, "
                f"tools/fluidsynth/ directory, and system PATH."
            )

        # Find SoundFont
        self.soundfont_path = soundfont_path or _find_soundfont()
        if not self.soundfont_path or not os.path.exists(self.soundfont_path):
            logger.warning(f"SoundFont not found at '{self.soundfont_path}'. "
                           f"Set SOUNDFONT_PATH env var or place a .sf2 file in tools/soundfonts/.")
            raise PianoRenderingError(
                f"SoundFont (.sf2) file not found. Set SOUNDFONT_PATH env var "
                f"or place a .sf2 file in backend/tools/soundfonts/."
            )
        logger.info(f"Using SoundFont: {self.soundfont_path}")

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
            # -O s16 = 16-bit signed output
            fluidsynth_cmd = [
                self.fluidsynth_exe,
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
                FFMPEG_EXE,
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
