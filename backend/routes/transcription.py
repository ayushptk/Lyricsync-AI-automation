import os
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import User, Job
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api/transcription", tags=["transcription"])

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
        
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Database integration for file path retrieval is pending")
    
    # json_path = "/tmp/downloads/some_id_vocals_transcription.json"
    # if not os.path.exists(json_path):
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcription file not found on disk")
        
    # with open(json_path, 'r', encoding='utf-8') as f:
    #     data = json.load(f)
        
    # return data

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
        
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Database integration for file path retrieval is pending")
    
    # file_path = f"/tmp/downloads/some_id_vocals_transcription.{format}"
    # if not os.path.exists(file_path):
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{format.upper()} file not found on disk")
        
    # media_types = {
    #     "srt": "text/plain",
    #     "lrc": "text/plain",
    #     "ass": "text/plain"
    # }
    
    # from fastapi.responses import FileResponse
    # return FileResponse(path=file_path, media_type=media_types[format], filename=f"vocals_subtitles.{format}")
