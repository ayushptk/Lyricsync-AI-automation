import os
from fastapi import FastAPI
from worker import process_audio_task

app = FastAPI(title="YTSaaS API")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "FastAPI is running"}

@app.post("/process-audio/")
def process_audio(file_url: str):
    # This is a sample endpoint that triggers a Celery task
    task = process_audio_task.delay(file_url)
    return {"task_id": task.id, "status": "Processing started"}
