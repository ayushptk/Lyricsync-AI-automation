import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from worker import process_audio_task
from database import Base, engine, SessionLocal
from models import Job
from auth.routes import router as auth_router
from routes.ingest import router as ingest_router
from routes.melody import router as melody_router
from routes.transcription import router as transcription_router
from routes.video import router as video_router
from routes.jobs import router as jobs_router
from routes.projects import router as projects_router

from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)


def _recover_stale_jobs():
    """
    On server startup, find any jobs stuck in 'processing' or 'queued' status.
    These are orphaned by a previous server crash/reload and will never complete.
    Mark them as 'failed' so the user sees a clear status instead of being stuck forever.
    """
    db = SessionLocal()
    try:
        stale_jobs = db.query(Job).filter(Job.status.in_(["processing"])).all()
        if stale_jobs:
            logger.warning(f"Found {len(stale_jobs)} stale job(s) from previous server run. Marking as failed.")
            for job in stale_jobs:
                job.status = "failed"
                old_log = job.error_log or ""
                job.error_log = old_log + "\n⚠ Server restarted while this job was processing. Please retry."
                logger.info(f"  → Marked job {job.id} as failed (was stuck in 'processing')")
            db.commit()
        else:
            logger.info("No stale jobs found on startup.")
    except Exception as e:
        logger.error(f"Failed to recover stale jobs: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app):
    # Startup: recover orphaned jobs
    _recover_stale_jobs()
    yield
    # Shutdown: nothing special needed


app = FastAPI(
    title="LyricSync API",
    description="Internal API for LyricSync AI Video Generation SaaS.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation Error", "errors": exc.errors()},
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Database Error occurred."},
    )

# CORS configuration
# Rate limiting
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Update in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ingest_router)
app.include_router(melody_router)
app.include_router(transcription_router)
app.include_router(video_router)
app.include_router(jobs_router)
app.include_router(projects_router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "FastAPI is running"}

@app.post("/process-audio/")
def process_audio(file_url: str):
    # This is a sample endpoint that triggers a Celery task
    task = process_audio_task.delay(file_url)
    return {"task_id": task.id, "status": "Processing started"}
