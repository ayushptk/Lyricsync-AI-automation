from pydantic import BaseModel, EmailStr, HttpUrl, UUID4
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
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    url: HttpUrl

class JobResponse(BaseModel):
    id: uuid.UUID
    project_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PaginatedJobs(BaseModel):
    total: int
    page: int
    size: int
    items: List[JobResponse]
