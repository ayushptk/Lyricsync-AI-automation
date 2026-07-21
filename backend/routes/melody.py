import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import User, Job
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api/melody", tags=["melody"])

@router.get("/{job_id}/download")
def download_midi(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the generated MIDI file for a completed job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    # Security check: Ensure the user owns the project this job belongs to
    if job.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this file")
        
    if job.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job is not completed yet (Current status: {job.status})")
        
    # In a fully implemented app, the MIDI file path would be retrieved from `UploadedFile` or `AudioMetadata` tables.
    # For now, we simulate the path based on how our worker names it
    # Assuming `file_id` is somehow tracked. This is placeholder logic:
    # midi_path = "/tmp/downloads/some_id_vocals_basic_pitch.mid"
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Database integration for file path retrieval is pending")
    
    # if not os.path.exists(midi_path):
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MIDI file not found on disk")
        
    # return FileResponse(path=midi_path, media_type="audio/midi", filename="vocals_melody.mid")

@router.get("/{job_id}/audio")
def download_piano_audio(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the rendered piano MP3 file for a completed job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    if job.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this file")
        
    if job.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job is not completed yet (Current status: {job.status})")
        
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Database integration for file path retrieval is pending")
    
    # mp3_path = "/tmp/downloads/some_id_vocals_basic_pitch_piano.mp3"
    # if not os.path.exists(mp3_path):
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found on disk")
        
    # return FileResponse(path=mp3_path, media_type="audio/mpeg", filename="piano_melody.mp3")
