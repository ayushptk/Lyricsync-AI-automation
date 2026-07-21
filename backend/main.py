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

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="YTSaaS API")

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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "FastAPI is running"}

@app.post("/process-audio/")
def process_audio(file_url: str):
    # This is a sample endpoint that triggers a Celery task
    task = process_audio_task.delay(file_url)
    return {"task_id": task.id, "status": "Processing started"}
