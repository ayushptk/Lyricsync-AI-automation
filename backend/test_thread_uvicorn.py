import os
import sys
import threading
import subprocess

# Simulate Uvicorn's detached streams in a daemon thread
sys.stdin = None
sys.stdout = None
sys.stderr = None

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.youtube import download_audio

def mock_worker():
    url = "https://youtu.be/p9r2GxMlRD4?si=LJ9nuq_KYVJ3zb0m"
    try:
        res = download_audio(url)
        # Cannot print normally since stdout is None
        with open("test_result.log", "w") as f:
            f.write(f"Success: {res}\n")
    except Exception as e:
        import traceback
        with open("test_result.log", "w") as f:
            f.write(f"Failed: {e}\n{traceback.format_exc()}\n")

def mock_route():
    thread = threading.Thread(target=mock_worker, daemon=True)
    thread.start()
    thread.join()

if __name__ == "__main__":
    t = threading.Thread(target=mock_route, daemon=True)
    t.start()
    t.join()
