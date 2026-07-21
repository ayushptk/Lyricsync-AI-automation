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

from kombu import Queue

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # 1. Define explicit queues
    task_queues=(
        Queue('default', routing_key='task.#'),
        Queue('gpu_heavy', routing_key='gpu.#'),
        Queue('cpu_heavy', routing_key='cpu.#'),
        Queue('dlq', routing_key='dlq.#'), # Dead Letter Queue
    ),
    # 2. Route tasks to specific queues
    task_routes={
        'worker.ingest_youtube_audio_task': {'queue': 'gpu_heavy', 'routing_key': 'gpu.ingest'},
        'worker.process_audio_task': {'queue': 'cpu_heavy', 'routing_key': 'cpu.process'},
    }
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
    from database import SessionLocal
    from models import Job
    
    # 0. Idempotency Check
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            print(f"[{job_id}] Job not found in database. Exiting.")
            return
            
        if job.status == "completed":
            print(f"[{job_id}] Job already completed. Idempotent exit.")
            return
            
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
        
        # 6. Transcription (WhisperX)
        from services.transcriber import WhisperXTranscriber
        transcriber = WhisperXTranscriber()
        # Using the isolated vocals for much higher accuracy
        transcription_path = transcriber.transcribe(vocals_path)
        print(f"[{job_id}] Transcription complete. JSON path: {transcription_path}")
        
        metadata["transcription_file_path"] = transcription_path
        
        # 7. Generate Subtitles (SRT, LRC, ASS)
        from services.subtitle_generator import SubtitleGenerator
        sub_generator = SubtitleGenerator(transcription_path)
        srt_path = sub_generator.generate_srt()
        lrc_path = sub_generator.generate_lrc()
        ass_path = sub_generator.generate_ass()
        print(f"[{job_id}] Subtitle generation complete.")
        
        metadata["subtitles"] = {
            "srt": srt_path,
            "lrc": lrc_path,
            "ass": ass_path
        }
        
        # 8. Render Final Video (FFmpeg + ASS)
        from services.video_renderer import VideoRenderer
        video_renderer = VideoRenderer()
        # Using the rendered piano audio and the ASS karaoke lyrics
        final_video_path = video_renderer.render_karaoke_video(
            audio_path=piano_mp3_path,
            ass_path=ass_path
        )
        print(f"[{job_id}] Video rendering complete. MP4 path: {final_video_path}")
        
        metadata["final_video_path"] = final_video_path
        
        # Here you would save the metadata to `UploadedFile` and `AudioMetadata` tables
        job.status = "completed"
        db.commit()
        
        return {"status": "success", "metadata": metadata}
        
    except YouTubeIngestionError as e:
        print(f"[{job_id}] Ingestion failed: {str(e)}")
        job.status = "failed"
        db.commit()
        
        # If this is the last retry, route to DLQ
        if self.request.retries == self.max_retries:
            print(f"[{job_id}] Max retries exceeded. Sending to DLQ.")
            celery_app.send_task('worker.dlq_handler', args=[job_id, str(e)], queue='dlq')
            
        raise e
    finally:
        db.close()

@celery_app.task(bind=True)
def dlq_handler(self, job_id: str, error_msg: str):
    """
    Handles tasks that have completely failed and exhausted retries.
    Logs them for manual inspection.
    """
    print(f"[DLQ] CRITICAL: Job {job_id} permanently failed. Error: {error_msg}")
    # You could send an alert to Sentry or Slack here.
