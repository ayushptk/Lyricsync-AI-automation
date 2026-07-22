import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import User, Job
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/video", tags=["video"])

@router.get("/{job_id}/download")
def download_final_video(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the final rendered MP4 karaoke video for a completed job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    if job.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this file")
        
    if job.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job is not completed yet (Current status: {job.status})")
        
    if not job.final_video_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video was not generated for this job (rendering may have been skipped)")

    if not os.path.exists(job.final_video_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found on disk")
        
    return FileResponse(path=job.final_video_path, media_type="video/mp4", filename="karaoke_final.mp4")
