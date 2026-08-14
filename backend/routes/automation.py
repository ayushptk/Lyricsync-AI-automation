import os
import threading
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from typing import Optional

import urllib.request
import json

from database import get_db
from models import User, Project, Job, UploadedFile, Lyric
from auth.automation_deps import get_automation_user
from auth.dependencies import get_current_user
from services.youtube import validate_youtube_url
from routes.ingest import _run_ingest_in_thread

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/automation", tags=["automation"])

class AutomationJobCreate(BaseModel):
    youtube_url: Optional[str] = None
    url: Optional[str] = None
    youtubeUrl: Optional[str] = None
    
    class Config:
        extra = "allow"

class AutomationJobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    song_title: Optional[str] = None
    duration: Optional[float] = None
    lyrics: Optional[str] = None
    error_message: Optional[str] = None

@router.post("/youtube")
def trigger_youtube_automation(
    request: AutomationJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a job under the logged-in user, start the processing pipeline,
    and optionally trigger the n8n webhook for supplemental workflows (e.g. YouTube upload).
    Returns job_id so the frontend can immediately track progress.
    """
    raw_url = request.youtube_url or request.youtubeUrl or request.url
    
    if not raw_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "MISSING_URL", "message": "Could not find URL in payload."}
        )
        
    url_str = str(raw_url)
    
    if not validate_youtube_url(url_str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_URL", "message": f"Invalid YouTube URL provided: {url_str}"}
        )

    # 1. Create Project under the LOGGED-IN user so the frontend can see it
    project = Project(
        user_id=current_user.id,
        title="Automated Generation",
        status="processing"
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # 2. Create Job
    job = Job(
        project_id=project.id,
        job_type="transcription",
        status="queued",
        aspect_ratio="16:9"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # 3. Launch the processing pipeline in a background thread
    thread = threading.Thread(
        target=_run_ingest_in_thread,
        args=(url_str, str(job.id)),
        daemon=True,
        name=f"auto-ingest-{job.id}"
    )
    thread.start()

    job.worker_id = f"thread-{thread.name}"
    db.commit()

    # 4. Optionally trigger n8n webhook for supplemental work (e.g. YouTube upload after completion)
    n8n_webhook_url = os.environ.get("N8N_WEBHOOK_URL")
    if n8n_webhook_url:
        def _fire_n8n():
            try:
                req = urllib.request.Request(
                    n8n_webhook_url,
                    data=json.dumps({"youtube_url": url_str, "job_id": str(job.id)}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5.0) as response:
                    if response.status not in (200, 201, 202):
                        logger.warning(f"n8n returned status code {response.status}")
            except Exception as e:
                logger.warning(f"Failed to trigger n8n webhook (non-critical): {e}")

        threading.Thread(target=_fire_n8n, daemon=True, name="n8n-notify").start()
        
    return {
        "success": True,
        "status": "queued",
        "message": "YouTube automation started",
        "job_id": str(job.id)
    }


@router.post("/jobs")
def create_automation_job(
    request: AutomationJobCreate,
    db: Session = Depends(get_db),
    automation_user: User = Depends(get_automation_user)
):
    """
    Submit a YouTube URL for background video generation.
    Called by n8n workflow via the HTTP Request node.
    """
    raw_url = request.youtube_url or request.youtubeUrl or request.url
    
    if not raw_url:
        logger.error(f"No URL found in n8n payload: {request.model_dump()}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "MISSING_URL", "message": "Could not find URL in payload."}
        )
        
    # Strip leading '=' which n8n adds when an expression field is treated as a string literal
    url_str = str(raw_url).lstrip("=").strip()
    
    if not validate_youtube_url(url_str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_URL", "message": f"Invalid YouTube URL provided: {url_str}"}
        )

    # 1. Create Project
    project = Project(
        user_id=automation_user.id,
        title="Automated Generation",
        status="processing"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # 2. Create Job
    job = Job(
        project_id=project.id,
        job_type="transcription",
        status="queued",
        aspect_ratio="16:9"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # 3. Launch background generation pipeline reusing existing thread logic
    thread = threading.Thread(
        target=_run_ingest_in_thread,
        args=(url_str, str(job.id)),
        daemon=True,
        name=f"auto-ingest-{job.id}"
    )
    thread.start()
    
    job.worker_id = f"thread-{thread.name}"
    db.commit()

    return {
        "job_id": str(job.id),
        "status": "queued"
    }


@router.get("/jobs/{job_id}", response_model=AutomationJobStatusResponse)
def get_automation_job_status(
    job_id: str,
    req: Request,
    db: Session = Depends(get_db),
    automation_user: User = Depends(get_automation_user)
):
    """
    Poll the status of an automation job. When completed, returns video URL and metadata.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    if job.project.user_id != automation_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this job")
        
    response = AutomationJobStatusResponse(
        job_id=str(job.id),
        status=job.status,
        progress=job.progress,
    )
    
    if job.status == "failed":
        response.error_message = job.error_log or "Processing failed"
        
    if job.status == "completed":
        # Build absolute video URL for n8n to download
        base_url = str(req.base_url).rstrip("/")
        response.video_url = f"{base_url}/api/automation/jobs/{job.id}/video"
        
        if hasattr(job, 'thumbnail_path') and job.thumbnail_path:
            response.thumbnail_url = f"{base_url}/api/automation/jobs/{job.id}/thumbnail"
        
        # Try to extract useful metadata for the AI agent
        response.song_title = job.project.title
        
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.project_id == job.project_id).first()
        if uploaded_file and uploaded_file.duration_seconds:
            response.duration = uploaded_file.duration_seconds
            
        lyric = db.query(Lyric).filter(Lyric.project_id == job.project_id).order_by(Lyric.version.desc()).first()
        if lyric:
            response.lyrics = lyric.text

    return response


@router.get("/jobs/{job_id}/video")
def get_automation_video(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Download the generated MP4 video file.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    if job.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is not completed yet")
        
    if not job.final_video_path or not os.path.exists(job.final_video_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail={"error_code": "VIDEO_UNAVAILABLE", "message": "Video file not found on disk"}
        )
    # Create a safe filename from the project title
    import re
    safe_title = re.sub(r'[\\/*?:"<>|]', "", job.project.title) if job.project and job.project.title else f"karaoke_{job_id}"
    
    return FileResponse(path=job.final_video_path, media_type="video/mp4", filename=f"{safe_title}.mp4")


@router.get("/jobs/{job_id}/thumbnail")
def get_automation_thumbnail(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Download the generated thumbnail image.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    if job.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is not completed yet")
        
    if not hasattr(job, 'thumbnail_path') or not job.thumbnail_path or not os.path.exists(job.thumbnail_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail={"error_code": "THUMBNAIL_UNAVAILABLE", "message": "Thumbnail file not found on disk"}
        )
    import re
    safe_title = re.sub(r'[\\/*?:"<>|]', "", job.project.title) if job.project and job.project.title else f"thumbnail_{job_id}"
    
    return FileResponse(path=job.thumbnail_path, media_type="image/jpeg", filename=f"{safe_title}.jpg")
