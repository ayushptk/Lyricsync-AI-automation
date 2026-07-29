# LyricSync (YTSaaS)

LyricSync is a full-stack, AI-powered Software-as-a-Service (SaaS) application that automatically generates professional karaoke videos from YouTube links. It leverages advanced Machine Learning models to download audio, isolate instrumental tracks, generate word-level timed lyrics, and render a final video with dynamic subtitles.

## 🚀 Features

- **Automated YouTube Ingestion**: Input a YouTube URL and the system automatically downloads the highest quality audio using `yt-dlp`.
- **AI Vocal Separation**: Uses **Demucs** to cleanly separate vocals from the instrumental backing track, creating a perfect karaoke base.
- **AI Audio Transcription**: Utilizes **Faster-Whisper** to accurately transcribe the vocals and generate word-level timestamps for karaoke lyric syncing.
- **Dynamic Video Rendering**: Generates a 1080p MP4 karaoke video using **FFmpeg**, overlaying stylized `.ass` karaoke subtitles over customizable background images.
- **Asynchronous Task Processing**: Built with **Celery** and **Redis** to reliably handle long-running machine learning and video rendering tasks in the background without blocking the UI.
- **Real-time Dashboard**: Modern frontend built with Next.js and Tailwind CSS that polls job progress and allows users to download final assets (Instrumental MP3, Vocals, SRT/LRC subtitles, and Final MP4 Video).
- **Secure Authentication**: Built-in JWT-based user authentication using Argon2 hashing.

## 🛠️ Technology Stack

### Frontend (Client)
- **Framework**: Next.js 15 (App Router) & React 19
- **Styling**: Tailwind CSS v4
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query) & Axios
- **Animations & Icons**: Framer Motion, Lucide React

### Backend (API & Workers)
- **Framework**: FastAPI (Python)
- **Task Queue**: Celery with Redis broker
- **Database**: SQLAlchemy ORM (PostgreSQL/SQLite)
- **Authentication**: Passlib (Argon2), python-jose (JWT)
- **Machine Learning & Audio Processing**:
  - `yt-dlp` (Audio Extraction)
  - `demucs` (Source Separation)
  - `faster-whisper` (Transcription)
  - `ffmpeg-python` & `imageio-ffmpeg` (Media Processing)
  - `librosa`, `soundfile`

## 📁 Project Structure

```
ytsaas/
├── frontend/               # Next.js application
│   ├── app/                # App Router pages (Dashboard, Auth, etc.)
│   ├── components/         # Reusable React components
│   └── package.json        
└── backend/                # FastAPI application & ML Workers
    ├── main.py             # FastAPI entry point
    ├── worker.py           # Celery worker and task orchestration
    ├── services/           # Core ML and processing services (Demucs, Whisper, FFmpeg)
    ├── routes/             # API endpoints (auth, video, jobs, projects)
    ├── models.py           # SQLAlchemy Database Models
    └── requirements.txt
```

## 🏁 Getting Started

### Prerequisites
- Node.js & npm (for frontend)
- Python 3.10+ (for backend)
- Redis server running (for Celery)
- FFmpeg installed and added to system PATH

### 1. Start the Backend & Worker
Navigate to the `backend/` directory, create a virtual environment, and install dependencies:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

In a separate terminal, start the Celery worker (ensure Redis is running):
```bash
celery -A worker.celery_app worker --loglevel=info -P threads
```

### 2. Start the Frontend
Navigate to the `frontend/` directory and install dependencies:
```bash
cd frontend
npm install
```

Start the Next.js development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to access the application.

## 📝 License
Proprietary / All Rights Reserved.
