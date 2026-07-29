import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import User, Job
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/melody", tags=["melody"])

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
        
    if not job.midi_file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MIDI file was not generated for this job (melody extraction may have been skipped)")

    if not os.path.exists(job.midi_file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MIDI file not found on disk")
        
    return FileResponse(path=job.midi_file_path, media_type="audio/midi", filename="vocals_melody.mid")

@router.get("/{job_id}/audio")
def download_audio(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the instrumental/backing audio or piano audio for a completed job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    if job.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this file")
        
    if job.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job is not completed yet (Current status: {job.status})")
        
    audio_path = job.piano_audio_path
    
    if not audio_path:
        audio_path = job.backing_file_path

    if not audio_path:
        audio_path = job.vocals_file_path

    if not audio_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio was not generated for this job")

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Audio file not found on disk: {os.path.basename(audio_path)}")
        
    filename = "piano_melody.wav" if job.piano_audio_path and audio_path == job.piano_audio_path else "instrumental.wav"
    return FileResponse(path=audio_path, media_type="audio/wav", filename=filename)
