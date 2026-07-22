import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, ForeignKey, 
    DateTime, Text, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True, index=True)
    reset_password_token = Column(String, nullable=True, index=True)
    reset_password_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    billing = relationship("Billing", back_populates="user", uselist=False, cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user") # SET NULL on delete handled via FK
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Billing(Base):
    __tablename__ = "billing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    stripe_customer_id = Column(String, unique=True, nullable=True)
    plan_type = Column(String, default="free")
    available_credits = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="billing")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    label = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="projects")
    uploaded_files = relationship("UploadedFile", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")
    lyrics = relationship("Lyric", back_populates="project", cascade="all, delete-orphan")
    generated_videos = relationship("GeneratedVideo", back_populates="project", cascade="all, delete-orphan")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="uploaded_files")
    audio_metadata = relationship("AudioMetadata", back_populates="uploaded_file", uselist=False, cascade="all, delete-orphan")


class AudioMetadata(Base):
    __tablename__ = "audio_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_files.id", ondelete="CASCADE"), unique=True, nullable=False)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    bitrate = Column(Integer, nullable=True)
    format = Column(String, nullable=True)

    uploaded_file = relationship("UploadedFile", back_populates="audio_metadata")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(String, nullable=False) # transcription, basic_pitch, video_generation
    status = Column(String, index=True, default="queued") # queued, processing, completed, failed
    progress = Column(Float, default=0.0)
    worker_id = Column(String, nullable=True)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Output file paths (populated by the worker pipeline)
    midi_file_path = Column(String, nullable=True)
    piano_audio_path = Column(String, nullable=True)
    vocals_file_path = Column(String, nullable=True)
    transcription_file_path = Column(String, nullable=True)
    srt_file_path = Column(String, nullable=True)
    lrc_file_path = Column(String, nullable=True)
    ass_file_path = Column(String, nullable=True)
    final_video_path = Column(String, nullable=True)

    project = relationship("Project", back_populates="jobs")
    generated_video = relationship("GeneratedVideo", back_populates="job", uselist=False)


class Lyric(Base):
    __tablename__ = "lyrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    language = Column(String, nullable=True)
    version = Column(Integer, default=1)

    project = relationship("Project", back_populates="lyrics")
    timestamps = relationship("Timestamp", back_populates="lyric", cascade="all, delete-orphan")


class Timestamp(Base):
    __tablename__ = "timestamps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lyric_id = Column(UUID(as_uuid=True), ForeignKey("lyrics.id", ondelete="CASCADE"), nullable=False)
    word = Column(String, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)

    lyric = relationship("Lyric", back_populates="timestamps")


class GeneratedVideo(Base):
    __tablename__ = "generated_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    file_path = Column(String, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="generated_videos")
    job = relationship("Job", back_populates="generated_video")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(INET, nullable=True)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
