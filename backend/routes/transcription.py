import os
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import User, Job
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/transcription", tags=["transcription"])

@router.get("/{job_id}")
def get_transcription(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the generated WhisperX JSON transcription for a completed job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    if job.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this file")
        
    if job.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job is not completed yet (Current status: {job.status})")
        
    if not job.transcription_file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcription was not generated for this job")

    if not os.path.exists(job.transcription_file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcription file not found on disk")
        
    with open(job.transcription_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    return data

@router.get("/{job_id}/subtitles")
def download_subtitles(
    job_id: uuid.UUID,
    format: str = "srt",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the generated subtitle file (SRT, LRC, or ASS) for a completed job.
    """
    if format not in ["srt", "lrc", "ass"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid format. Supported formats: srt, lrc, ass")
        
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    if job.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this file")
        
    if job.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job is not completed yet (Current status: {job.status})")
        
    # Map format to the corresponding Job column
    format_path_map = {
        "srt": job.srt_file_path,
        "lrc": job.lrc_file_path,
        "ass": job.ass_file_path,
    }
    
    file_path = format_path_map.get(format)
    
    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{format.upper()} file was not generated for this job")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{format.upper()} file not found on disk")
        
    return FileResponse(path=file_path, media_type="text/plain", filename=f"vocals_subtitles.{format}")
