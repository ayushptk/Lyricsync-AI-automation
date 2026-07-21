import os
import time
from celery import Celery

# Configure Celery to use Redis as the broker and result backend
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(bind=True)
def process_audio_task(self, file_url: str):
    """
    Sample Celery task that represents processing an audio file.
    In a real scenario, this would use WhisperX and Basic Pitch.
    """
    print(f"Starting audio processing for {file_url}...")
    
    # Simulate processing time
    time.sleep(5)
    
    # Normally you would do something like:
    # import whisperx
    # from basic_pitch.inference import predict_and_save
    
    print(f"Completed audio processing for {file_url}.")
    return {"status": "success", "file_url": file_url}

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def ingest_youtube_audio_task(self, youtube_url: str, job_id: str):
    """
    Downloads audio from YouTube using yt-dlp with retries on failure.
    Updates the database with job progress.
    """
    from services.youtube import download_audio, YouTubeIngestionError
    # In a real app, you would fetch the Job from DB here using job_id and update status to 'processing'
    print(f"[{job_id}] Starting ingestion for URL: {youtube_url}")
    
    try:
        # 1. Download raw audio
        metadata = download_audio(youtube_url)
        print(f"[{job_id}] Download complete. Metadata: {metadata}")
        
        # 2. Preprocess audio (Normalize, 16kHz, Trim)
        from services.audio_preprocess import preprocess_audio
        preprocess_stats = preprocess_audio(metadata["file_path"])
        print(f"[{job_id}] Preprocess complete. Stats: {preprocess_stats}")
        
        # Update metadata with final file path
        metadata["preprocessed_file_path"] = preprocess_stats["final_file_path"]
        metadata["trim_stats"] = preprocess_stats
        
        # 3. Separate Vocals (Demucs)
        from services.vocal_separator import DemucsSeparator
        separator = DemucsSeparator()
        vocals_path = separator.separate_vocals(metadata["preprocessed_file_path"])
        print(f"[{job_id}] Vocal separation complete. Vocals path: {vocals_path}")
        
        metadata["vocals_file_path"] = vocals_path
        
        # 4. Extract Melody (Basic Pitch)
        from services.basic_pitch_extractor import MelodyExtractor
        melody_extractor = MelodyExtractor()
        midi_path = melody_extractor.extract_melody(vocals_path)
        print(f"[{job_id}] Melody extraction complete. MIDI path: {midi_path}")
        
        metadata["midi_file_path"] = midi_path
        
        # 5. Render MIDI to Audio (FluidSynth)
        from services.piano_renderer import PianoRenderer
        renderer = PianoRenderer()
        piano_mp3_path = renderer.render_midi_to_mp3(midi_path)
        print(f"[{job_id}] Piano rendering complete. Audio path: {piano_mp3_path}")
        
        metadata["piano_audio_path"] = piano_mp3_path
        
        # Here you would save the metadata to `UploadedFile` and `AudioMetadata` tables
        # And update `Job` status to 'completed'
        return {"status": "success", "metadata": metadata}
    except YouTubeIngestionError as e:
        print(f"[{job_id}] Ingestion failed: {str(e)}")
        # Here you would update `Job` status to 'failed' and save the error log
        raise e
