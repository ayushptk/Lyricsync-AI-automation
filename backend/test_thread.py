import os
import sys
import threading
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.youtube import download_audio

def mock_worker():
    print("Worker thread started")
    url = "https://youtu.be/p9r2GxMlRD4?si=LJ9nuq_KYVJ3zb0m"
    try:
        res = download_audio(url)
        print("Worker thread success:", res)
    except Exception as e:
        print("Worker thread failed:", e)

def mock_route():
    print("Route thread started")
    thread = threading.Thread(target=mock_worker, daemon=True)
    thread.start()
    thread.join()
    print("Route thread done")

if __name__ == "__main__":
    t = threading.Thread(target=mock_route, daemon=True)
    t.start()
    t.join()
