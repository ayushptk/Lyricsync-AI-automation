from pydantic import BaseModel, EmailStr, HttpUrl, UUID4, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# --- User Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True

# --- Project & Job Schemas ---
class ProjectResponse(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    url: HttpUrl

class JobResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    job_type: str
    status: str
    progress: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    error_log: Optional[str] = None
    # File availability flags — populated by model_validator from ORM object
    has_video: bool = False
    has_audio: bool = False
    has_subtitles: bool = False

    @model_validator(mode="before")
    @classmethod
    def compute_flags(cls, values):
        # When loading from SQLAlchemy ORM object (has __dict__ with column attrs)
        if hasattr(values, "final_video_path"):
            obj = values
            # Build a plain dict for Pydantic to validate
            return {
                "id": obj.id,
                "project_id": obj.project_id,
                "job_type": obj.job_type,
                "status": obj.status,
                "progress": obj.progress,
                "started_at": obj.started_at,
                "completed_at": obj.completed_at,
                "created_at": obj.created_at,
                "error_log": obj.error_log,
                "has_video": bool(getattr(obj, "final_video_path", None)),
                "has_audio": bool(
                    getattr(obj, "piano_audio_path", None)
                    or getattr(obj, "backing_file_path", None)
                    or getattr(obj, "vocals_file_path", None)
                ),
                "has_subtitles": bool(getattr(obj, "srt_file_path", None)),
            }
        return values

    class Config:
        from_attributes = True

class PaginatedJobs(BaseModel):
    total: int
    page: int
    size: int
    items: List[JobResponse]
