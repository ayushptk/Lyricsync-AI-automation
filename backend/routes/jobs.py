from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import User, Job
from auth.dependencies import get_current_user
from schemas import PaginatedJobs, JobResponse

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

@router.get("", response_model=PaginatedJobs)
def get_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a paginated list of jobs for the current user.
    """
    # Fetch total count
    total = db.query(Job).join(Job.project).filter(Job.project.has(user_id=current_user.id)).count()
    
    # Fetch paginated items
    jobs = (
        db.query(Job)
        .join(Job.project)
        .filter(Job.project.has(user_id=current_user.id))
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return PaginatedJobs(
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        items=jobs
    )

@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve details for a specific job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    if job.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this job")
        
    return job
