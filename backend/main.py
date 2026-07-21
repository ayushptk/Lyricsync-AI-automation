import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from worker import process_audio_task
from database import Base, engine
from limiter import limiter
from auth.routes import router as auth_router
from routes.ingest import router as ingest_router
from routes.melody import router as melody_router
from routes.transcription import router as transcription_router
from routes.video import router as video_router
from routes.jobs import router as jobs_router

from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LyricSync API",
    description="Internal API for LyricSync AI Video Generation SaaS.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "FastAPI is running"}

@app.post("/process-audio/")
def process_audio(file_url: str):
    # This is a sample endpoint that triggers a Celery task
    task = process_audio_task.delay(file_url)
    return {"task_id": task.id, "status": "Processing started"}
