import os

# Suppress TensorFlow/oneDNN/abseil warnings BEFORE any TF imports
# These must be set before TF is loaded (even transitively via basic_pitch)
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")        # Suppress TF C++ INFO/WARNING
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")       # Suppress oneDNN warnings
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")           # Suppress gRPC noise
os.environ.setdefault("ABSL_MIN_LOG_LEVEL", "2")           # Suppress abseil INFO logs

import time
import logging
import threading
import traceback
from dotenv import load_dotenv
from celery import Celery

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Configure Celery to use Redis as the broker and result backend
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

celery_app = Celery(
    "worker",
    broker=REDIS_URL
)

from kombu import Queue

celery_app.conf.update(
    task_ignore_result=True,
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

# --- Timeout Configuration (seconds) ---
STEP_TIMEOUTS = {
    "download": 300,          # 5 minutes for YouTube download
    "preprocess": 300,        # 5 minutes for FFmpeg normalization + trim
    "vocal_separation": 600,  # Increased to 10 minutes (better quality demucs settings take longer on CPU)
    "melody_extraction": 600, # 10 minutes for Basic Pitch
    "piano_rendering": 300,   # 5 minutes for FluidSynth + FFmpeg
    "transcription": 2700,     # 45 minutes total for WhisperX on CPU (base model)
    "subtitle_generation": 60,# 1 minute for subtitle file generation
    "video_rendering": 600,   # 10 minutes for FFmpeg video render
}


class StepTimeoutError(Exception):
    """Raised when a pipeline step exceeds its timeout."""
    pass


def _start_progress_heartbeat(db, job, start_progress, end_progress, interval_seconds=30, total_expected_seconds=300):
    """
    Starts a background thread that gradually increments job progress from
    start_progress toward end_progress while a long-running step executes.
    Returns a threading.Event that should be set to stop the heartbeat.
    """
    stop_event = threading.Event()
    job_id = job.id
    
    def _heartbeat():
        from database import SessionLocal
        from models import Job as JobModel
        elapsed = 0
        while not stop_event.is_set():
            stop_event.wait(timeout=interval_seconds)
            if stop_event.is_set():
                break
            elapsed += interval_seconds
            # Calculate progress: ease toward end_progress but never reach it
            # Use a curve that slows down as it approaches the target
            fraction = min(elapsed / total_expected_seconds, 0.95)
            current = start_progress + (end_progress - start_progress) * fraction
            current = min(current, end_progress - 1)  # Never exceed end_progress-1
            
            local_db = SessionLocal()
            try:
                local_job = local_db.query(JobModel).filter(JobModel.id == job_id).first()
                if local_job and local_job.status == "processing":
                    local_job.progress = round(current, 1)
                    local_db.commit()
            except Exception as e:
                logger.warning(f"[{job_id}] Heartbeat DB update failed: {e}")
            finally:
                local_db.close()
    
    heartbeat_thread = threading.Thread(target=_heartbeat, daemon=True, name=f"heartbeat-{job_id}")
    heartbeat_thread.start()
    return stop_event


def run_with_timeout(func, args=(), kwargs=None, timeout_seconds=300, step_name="step"):
    """
    Runs a function in a separate thread with a timeout.
    Returns the result or raises StepTimeoutError if it takes too long.
    """
    if kwargs is None:
        kwargs = {}
    
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if thread.is_alive():
        # Thread is still running — it exceeded the timeout
        logger.error(f"[TIMEOUT] Step '{step_name}' exceeded {timeout_seconds}s timeout. "
                     f"The thread is still running in background but we are moving on.")
        raise StepTimeoutError(
            f"Step '{step_name}' timed out after {timeout_seconds} seconds. "
            f"This usually means the operation is too heavy for this machine's resources."
        )
    
    if exception[0] is not None:
        raise exception[0]
    
    return result[0]


def _safe_update_job(db, job, status=None, progress=None, log_msg=None, error_msg=None):
    """
    Safely updates job status in DB with rollback protection.
    Ensures the job status always gets persisted even if prior operations failed.
    """
    try:
        if status:
            job.status = status
        if progress is not None:
            job.progress = progress
        if log_msg:
            if not job.error_log:
                job.error_log = log_msg
            else:
                job.error_log += "\n" + log_msg
        if error_msg:
            formatted_err = error_msg if error_msg.startswith("⚠ ERROR:") else f"⚠ ERROR: {error_msg}"
            if not job.error_log:
                job.error_log = formatted_err
            else:
                job.error_log += "\n\n" + formatted_err
        db.commit()
        logger.info(f"[{job.id}] Status={job.status} Progress={job.progress}% | {log_msg or error_msg or ''}")
    except Exception as commit_err:
        logger.error(f"[{job.id}] DB commit failed: {commit_err}. Attempting rollback...")
        try:
            db.rollback()
            # Retry the update after rollback
            if status:
                job.status = status
            if progress is not None:
                job.progress = progress
            if log_msg or error_msg:
                formatted_err = error_msg if (error_msg and error_msg.startswith("⚠ ERROR:")) else (f"⚠ ERROR: {error_msg}" if error_msg else "")
                job.error_log = (log_msg or "") + ("\n\n" + formatted_err if formatted_err else "")
            db.commit()
        except Exception as rollback_err:
            logger.critical(f"[{job.id}] CRITICAL: Could not update job status even after rollback: {rollback_err}")


@celery_app.task(bind=True)
def process_audio_task(self, file_url: str):
    """
    Sample Celery task that represents processing an audio file.
    In a real scenario, this would use WhisperX and Basic Pitch.
    """
    pass


def ingest_youtube_audio_task(youtube_url: str, job_id: str):
    """
    Pipeline orchestrator that downloads audio, preprocesses it, runs Demucs, Basic Pitch,
    WhisperX, subtitle creation, and FFmpeg video rendering.
    Updates the Job database record with fine-grained status and progress at each step.
    """
    from database import SessionLocal
    from models import Job as JobModel
    
    start_time = time.time()
    
    db = SessionLocal()
    job = None
    try:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if not job:
            logger.error(f"[{job_id}] Job record not found in DB.")
            return
            
        _safe_update_job(db, job, status="processing", progress=5,
                         log_msg=f"Starting ingestion for URL: {youtube_url}")
        
        # =====================================================================
        # STEP 1: Download raw audio from YouTube
        # =====================================================================
        metadata = {}
        try:
            from services.youtube import download_audio, YouTubeIngestionError
            
            logger.info(f"[{job_id}] Step 1/8: Downloading audio...")
            download_result = run_with_timeout(
                download_audio, args=(youtube_url,),
                timeout_seconds=STEP_TIMEOUTS["download"],
                step_name="YouTube Download"
            )
            metadata.update(download_result)
            _safe_update_job(db, job, progress=15,
                             log_msg=f"Download complete. Title: {metadata.get('title', 'Unknown')}")
        except StepTimeoutError as e:
            _safe_update_job(db, job, status="failed", progress=15,
                             error_msg=f"Download timed out: {str(e)}")
            return
        except Exception as e:
            tb = traceback.format_exc()
            err_text = f"Download failed: {str(e)}"
            if tb and "Traceback Details:" not in str(e):
                err_text += f"\n\nTraceback Details:\n{tb}"
            _safe_update_job(db, job, status="failed", progress=15,
                             error_msg=err_text)
            return  # Can't continue without the audio file
        
        # =====================================================================
        # STEP 2: Preprocess audio (Normalize, 16kHz, Trim)
        # =====================================================================
        try:
            from services.audio_preprocess import preprocess_audio
            
            logger.info(f"[{job_id}] Step 2/8: Preprocessing audio...")
            preprocess_stats = run_with_timeout(
                preprocess_audio, args=(metadata["file_path"],),
                timeout_seconds=STEP_TIMEOUTS["preprocess"],
                step_name="Audio Preprocess"
            )
            metadata["preprocessed_file_path"] = preprocess_stats["final_file_path"]
            metadata["trim_stats"] = preprocess_stats
            _safe_update_job(db, job, progress=25,
                             log_msg=f"Preprocess complete. Duration: {preprocess_stats.get('trimmed_duration', '?')}s")
        except StepTimeoutError as e:
            _safe_update_job(db, job, status="failed", progress=25,
                             error_msg=f"Preprocess timed out: {str(e)}")
            return
        except Exception as e:
            tb = traceback.format_exc()
            err_text = f"Preprocess failed: {str(e)}"
            if tb and "Traceback Details:" not in str(e):
                err_text += f"\n\nTraceback Details:\n{tb}"
            _safe_update_job(db, job, status="failed", progress=25,
                             error_msg=err_text)
            return  # Can't continue without preprocessed audio audio
        
        # =====================================================================
        # STEP 3: Separate Tracks (Demucs) — GRACEFUL FALLBACK
        # =====================================================================
        vocals_path = metadata["preprocessed_file_path"]  # Fallback: use preprocessed audio
        backing_path = metadata["preprocessed_file_path"]
        piano_path = None
        heartbeat_stop = None
        try:
            from services.vocal_separator import DemucsSeparator, DemucsSeparationError
            
            logger.info(f"[{job_id}] Step 3/8: Separating tracks...")
            _safe_update_job(db, job, progress=30,
                             log_msg="Starting track separation...")
            
            # Start progress heartbeat: gradually move from 30% → 49%
            # With fast mode this completes in seconds, but keep heartbeat for balanced mode fallback
            heartbeat_stop = _start_progress_heartbeat(
                db, job,
                start_progress=30,
                end_progress=50,
                interval_seconds=10,
                total_expected_seconds=300  # Expected ~5 min on CPU
            )
            
            def _run_track_separation(input_path):
                separator = DemucsSeparator()  # Uses VOCAL_SEPARATION_STRATEGY env var
                return separator.separate_tracks(input_path)
            
            vocals_path, backing_path, piano_path = run_with_timeout(
                _run_track_separation, args=(metadata["preprocessed_file_path"],),
                timeout_seconds=STEP_TIMEOUTS["vocal_separation"],
                step_name="Track Separation"
            )
            metadata["vocals_file_path"] = vocals_path
            metadata["backing_file_path"] = backing_path
            if piano_path:
                metadata["piano_audio_path"] = piano_path
                job.piano_audio_path = piano_path
            job.vocals_file_path = vocals_path
            job.backing_file_path = backing_path
            _safe_update_job(db, job, progress=50,
                             log_msg="Track separation complete.")
            
        except (StepTimeoutError, Exception) as e:
            error_type = "timed out" if isinstance(e, StepTimeoutError) else "failed"
            logger.error(f"[{job_id}] Track separation {error_type}: {str(e)}. Failing job as vocals cannot be removed.")
            _safe_update_job(db, job, status="failed", progress=50,
                             error_msg=f"Track separation {error_type} ({type(e).__name__}): {str(e)[:200]}. Cannot produce karaoke track.")
            return
        finally:
            # Always stop the heartbeat thread
            if heartbeat_stop is not None:
                heartbeat_stop.set()
        
        # We no longer extract piano melody; backing_path is the instrumental track.
        # (Skipping Steps 4 and 5)
        
        # =====================================================================
        # STEP 6: Transcription (Faster-Whisper) — OPTIONAL
        # =====================================================================
        ass_path = None
        heartbeat_stop_tx = None
        try:
            from services.transcriber import FasterWhisperTranscriber
            
            logger.info(f"[{job_id}] Step 6/8: Transcribing with Faster-Whisper...")
            
            # Start progress heartbeat: gradually move from 70% → 79%
            # Faster-Whisper on CPU can take 5-15 minutes, so we keep the UI alive
            heartbeat_stop_tx = _start_progress_heartbeat(
                db, job,
                start_progress=70,
                end_progress=80,
                interval_seconds=20,
                total_expected_seconds=1200  # Expected ~20 min on CPU
            )
            
            def _run_transcription(audio_path):
                transcriber = FasterWhisperTranscriber()
                return transcriber.transcribe(audio_path)
            
            transcription_path = run_with_timeout(
                _run_transcription, args=(vocals_path,),
                timeout_seconds=STEP_TIMEOUTS["transcription"],
                step_name="Transcription (Faster-Whisper)"
            )
            metadata["transcription_file_path"] = transcription_path
            job.transcription_file_path = transcription_path
            _safe_update_job(db, job, progress=80,
                             log_msg="Transcription complete.")
            
            # -----------------------------------------------------------------
            # STEP 7: Generate Subtitles (SRT, LRC, ASS) — DEPENDS ON STEP 6
            # -----------------------------------------------------------------
            try:
                from services.subtitle_generator import SubtitleGenerator
                
                logger.info(f"[{job_id}] Step 7/8: Generating subtitles...")
                sub_generator = SubtitleGenerator(transcription_path)
                srt_path = sub_generator.generate_srt()
                lrc_path = sub_generator.generate_lrc()
                ass_path = sub_generator.generate_ass()
                metadata["subtitles"] = {
                    "srt": srt_path,
                    "lrc": lrc_path,
                    "ass": ass_path
                }
                job.srt_file_path = srt_path
                job.lrc_file_path = lrc_path
                job.ass_file_path = ass_path
                _safe_update_job(db, job, progress=85,
                                 log_msg="Subtitle generation complete.")
            except Exception as e:
                logger.warning(f"[{job_id}] Subtitle generation failed: {str(e)}")
                _safe_update_job(db, job, progress=85,
                                 log_msg=f"Subtitle generation failed ({type(e).__name__}).")
                metadata["subtitles"] = None
                ass_path = None
                
        except Exception as e:
            logger.warning(f"[{job_id}] Skipping transcription/subtitles: {str(e)}")
            _safe_update_job(db, job, progress=85,
                             log_msg=f"Transcription skipped ({type(e).__name__}: {str(e)[:100]})")
            metadata["transcription_file_path"] = None
            metadata["subtitles"] = None
        finally:
            # Always stop the transcription heartbeat
            if heartbeat_stop_tx is not None:
                heartbeat_stop_tx.set()
        
        # =====================================================================
        # STEP 8: Render Final Video (FFmpeg) — always runs, ASS subtitles optional
        # =====================================================================
        try:
            from services.video_renderer import VideoRenderer
            
            logger.info(f"[{job_id}] Step 8/8: Rendering final karaoke video...")
            audio_for_video = backing_path
            
            def _run_video_render(audio_path, subtitle_path):
                renderer = VideoRenderer()
                return renderer.render_karaoke_video(audio_path=audio_path, ass_path=subtitle_path)
            
            final_video_path = run_with_timeout(
                _run_video_render, args=(audio_for_video, ass_path),
                timeout_seconds=STEP_TIMEOUTS["video_rendering"],
                step_name="Video Rendering"
            )
            metadata["final_video_path"] = final_video_path
            job.final_video_path = final_video_path
            _safe_update_job(db, job, progress=100,
                             log_msg="Video rendering complete.")
        except Exception as e:
            logger.warning(f"[{job_id}] Video rendering failed: {str(e)}")
            _safe_update_job(db, job, progress=100,
                             log_msg=f"Video rendering failed ({type(e).__name__}: {str(e)[:200]}).")
            metadata["final_video_path"] = None
        
        # =====================================================================
        # DONE — Mark job as completed
        # =====================================================================
        elapsed = time.time() - start_time
        _safe_update_job(db, job, status="completed", progress=100,
                         log_msg=f"Pipeline finished in {elapsed:.1f}s.")
        
        logger.info(f"[{job_id}] ✅ Pipeline completed successfully in {elapsed:.1f}s")
        return {"status": "success", "metadata": metadata}
        
    except Exception as e:
        # Catch-all: if anything unexpected crashes, mark the job as failed
        error_details = traceback.format_exc()
        logger.error(f"[{job_id}] ❌ FATAL pipeline error: {error_details}")
        if job:
            _safe_update_job(db, job, status="failed",
                             error_msg=f"Fatal pipeline error: {str(e)}\n{error_details}")
    finally:
        try:
            db.close()
        except Exception:
            pass


@celery_app.task(bind=True)
def dlq_handler(self, job_id: str, error_msg: str):
    """
    Handles tasks that have completely failed and exhausted retries.
    Logs them for manual inspection.
    """
    print(f"[DLQ] CRITICAL: Job {job_id} permanently failed. Error: {error_msg}")
    # You could send an alert to Sentry or Slack here.
