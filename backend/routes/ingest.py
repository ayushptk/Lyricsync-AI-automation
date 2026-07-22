import threading
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import User, Project, Job
from auth.dependencies import get_current_user
from worker import ingest_youtube_audio_task
from services.youtube import validate_youtube_url
from schemas import JobCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])

from typing import Optional

class YouTubeIngestRequest(BaseModel):
    url: HttpUrl
    project_title: Optional[str] = "Untitled Project"


def _run_ingest_in_thread(youtube_url: str, job_id: str):
    """
    Wrapper that runs the ingest task in a separate daemon thread.
    This prevents the heavy pipeline from blocking FastAPI's ASGI event loop.
    If the thread crashes, the worker's error handling ensures the job is marked as failed.
    """
    try:
        logger.info(f"[Thread] Starting ingest for job {job_id}")
        ingest_youtube_audio_task(youtube_url, job_id)
        logger.info(f"[Thread] Ingest completed for job {job_id}")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"[Thread] Ingest thread crashed for job {job_id}: {str(e)}\n{tb}")
        # The worker function already handles DB updates on error,
        # but if it somehow didn't catch the error, try to update the job status here
        try:
            from database import SessionLocal
            from models import Job as JobModel
            db = SessionLocal()
            try:
                job = db.query(JobModel).filter(JobModel.id == job_id).first()
                if job and job.status not in ("completed", "failed"):
                    job.status = "failed"
                    job.error_log = (job.error_log or "") + f"\n\n⚠ ERROR: Thread crash: {str(e)}\n\nTraceback Details:\n{tb}"
                    db.commit()
            finally:
                db.close()
        except Exception as db_err:
            logger.critical(f"[Thread] Could not update job status after crash: {db_err}")


@router.post("/youtube")
def ingest_youtube(
    request: YouTubeIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts a YouTube URL, validates it, creates a project/job, 
    and queues it for background audio download and metadata extraction.
    
    The heavy processing pipeline runs in a separate daemon thread to avoid
    blocking FastAPI's ASGI event loop.
    """
    url_str = str(request.url)
    
    # 1. Synchronous validation
    if not validate_youtube_url(url_str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL provided."
        )
        
    # 2. Create Project
    project = Project(
        user_id=current_user.id,
        title=request.project_title,
        status="processing"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # 3. Create Job
    job = Job(
        project_id=project.id,
        job_type="transcription", # Initial phase is downloading/transcription prep
        status="queued"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # 4. Launch the heavy pipeline in a separate daemon thread
    # Using a daemon thread (not BackgroundTasks) so:
    #  - It doesn't block FastAPI's event loop
    #  - It can run truly in parallel
    #  - If the server restarts, daemon threads are cleaned up
    thread = threading.Thread(
        target=_run_ingest_in_thread,
        args=(url_str, str(job.id)),
        daemon=True,
        name=f"ingest-{job.id}"
    )
    thread.start()
    
    logger.info(f"Launched ingest thread for job {job.id} (thread: {thread.name})")
    
    # Update job with thread info
    job.worker_id = f"thread-{thread.name}"
    db.commit()
    
    return {
        "message": "Ingestion started",
        "project_id": str(project.id),
        "job_id": str(job.id),
        "task_id": f"thread-{thread.name}"
    }
