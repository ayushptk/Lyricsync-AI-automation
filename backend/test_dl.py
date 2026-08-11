import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ["LYRICSYNC_ENV"] = "local"
import logging
logging.basicConfig(level=logging.DEBUG)

from services.youtube import download_audio

if __name__ == "__main__":
    url = "https://youtu.be/p9r2GxMlRD4?si=LJ9nuq_KYVJ3zb0m"
    try:
        res = download_audio(url)
        print("Success:", res)
    except Exception as e:
        print("Failed:", e)
        import traceback
        traceback.print_exc()
