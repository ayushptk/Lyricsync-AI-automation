from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import User, Project, Job
from auth.dependencies import get_current_user
from worker import ingest_youtube_audio_task
from services.youtube import validate_youtube_url
from schemas import JobCreate

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])

class YouTubeIngestRequest(BaseModel):
    url: HttpUrl
    project_title: str

@router.post("/youtube")
def ingest_youtube(
    request: YouTubeIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts a YouTube URL, validates it, creates a project/job, 
    and queues it for background audio download and metadata extraction.
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
    
    # 4. Asynchronously queue the task
    task = ingest_youtube_audio_task.delay(url_str, str(job.id))
    
    # Update job with celery worker task id
    job.worker_id = task.id
    db.commit()
    
    return {
        "message": "Ingestion started",
        "project_id": str(project.id),
        "job_id": str(job.id),
        "task_id": task.id
    }
