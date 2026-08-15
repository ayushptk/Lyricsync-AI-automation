# LyricSync (YTSaaS) — AI-Powered Karaoke Video Generator

LyricSync is a production-grade, AI-powered Software-as-a-Service (SaaS) platform that automatically generates professional, synchronized karaoke videos from standard YouTube links. 

## 🌟 Platform Showcase

<p align="center">
  <img src="Website-images/homepagee.png" alt="Homepage" width="49%">
  <img src="Website-images/Login.png" alt="Login Page" width="49%">
</p>
<p align="center">
  <img src="Website-images/Dashboarddd.png" alt="Dashboard" width="49%">
  <img src="Website-images/youtube%20proof.png" alt="YouTube Generation Process" width="49%">
</p>
<p align="center">
  <img src="Website-images/n8n%20workflow.png" alt="n8n Automation Workflow" width="49%">
  <img src="Website-images/LoadBalancer.png" alt="AWS Load Balancer Infrastructure" width="49%">
</p>

It leverages advanced Machine Learning models to acquire media, isolate instrumental backing tracks, generate word-level timed lyrics, and render dynamic 1080p video assets with stylized karaoke subtitles. The platform features a highly asynchronous, queue-based microservices architecture deployed on AWS, designed to handle heavy audio-processing workloads efficiently without blocking the user interface.


## 🌊 The Complete User Flow

LyricSync automates a deeply complex audio-visual pipeline into a single click:

1. **Media Acquisition**: The user provides a YouTube URL. The backend fetches the highest quality audio stream.
2. **Audio Preprocessing**: Audio is standardized to a 44.1kHz stereo WAV for optimal separation, and subsequently converted to a 16kHz mono WAV for optimal transcription.
3. **Vocal/Instrumental Separation**: The AI isolates the vocal track from the instrumental backing track.
4. **Speech & Lyrics Transcription**: The vocal track is analyzed to generate a highly accurate text transcription with precise word-level timestamps.
5. **Lyrics & Timing Processing**: A custom post-processing engine filters out AI hallucinations, handles low-confidence words, and prepares the lyrics for visual synchronization.
6. **Karaoke Synchronization**: Word-level timings are mapped into Advanced SubStation Alpha (.ass) format, animating the lyric highlight precisely as the word is sung.
7. **Video Rendering**: The instrumental audio, custom background imagery, and animated subtitles are burned together into a final 1080p MP4.
8. **Delivery**: Assets are uploaded to scalable cloud storage and delivered via CDN to the user's dashboard.

---

## 🛠️ Technology Stack

LyricSync relies on a modern, scalable stack separated into specialized layers.

### Frontend
- **Next.js 15 (App Router)** & **React 19**: Server-side rendering and routing.
- **TypeScript**: End-to-end type safety.
- **Tailwind CSS v4**: Utility-first responsive styling.
- **Zustand**: Lightweight client-side state management.
- **TanStack Query (React Query) & Axios**: Data fetching, caching, and polling for job status.
- **Framer Motion & Lucide React**: UI animations and modern iconography.

### Backend & API
- **FastAPI (Python)**: High-performance async API server.
- **SQLAlchemy (PostgreSQL)**: Relational database ORM for users, jobs, and project metadata.
- **REST APIs**: Stateless endpoints for job creation, progress tracking, and asset retrieval.

### Background Processing
- **Celery**: Distributed task queue handling long-running ML jobs.
- **Redis (or AWS ElastiCache/Valkey)**: In-memory message broker coordinating the FastAPI frontend and Celery workers.

### AI & Audio Pipeline
- **yt-dlp**: High-fidelity media extraction from YouTube.
- **Demucs**: State-of-the-art deep learning model for audio source separation (extracting vocals from instrumentals).
- **Faster-Whisper**: Optimized implementation of OpenAI's Whisper (via CTranslate2) for rapid, accurate speech-to-text with word-level timestamps.
- **FFmpeg / imageio-ffmpeg**: Industry-standard media processing, audio normalization, and hardware-accelerated video rendering.

### Infrastructure (AWS)
- **Amazon ECS & Fargate**: Serverless container orchestration for the backend and workers.
- **Amazon ECR**: Private container registry for Docker images.
- **Amazon VPC**: Isolated networking with public/private subnets, NAT Gateways, and strict Security Groups.
- **Application Load Balancer (ALB)**: *Planned/Configured* for routing traffic to ECS services.
- **Amazon RDS (PostgreSQL)**: *Planned/Configured* for managed, highly available relational data.
- **Amazon S3**: Object storage for generated MP4s, instrumentals, and subtitle files.
- **Amazon CloudFront**: Global CDN for lightning-fast asset delivery.
- **AWS IAM**: Strict role-based access control (least privilege).

### Automation
- **n8n**: Workflow automation for orchestrating external job requests, webhooks, and pipeline monitoring.

---

## 🏗️ Complete System Architecture

LyricSync is built on an asynchronous, decoupled architecture to ensure the frontend remains highly responsive while the backend chews through heavy ML tasks.

1. **Client Request**: The user submits a YouTube URL via the Next.js frontend. The request is routed to the FastAPI backend.
2. **Job Orchestration (API & DB)**: FastAPI creates a Job record in **PostgreSQL** (status: `pending`) and immediately pushes a task message to the **Redis** broker. It returns a `job_id` to the client.
3. **Frontend Polling**: The frontend begins polling the API (via React Query) for updates on that specific `job_id`.
4. **Background Processing (Celery)**: An idle Celery worker picks up the message from Redis and begins the heavy pipeline:
   - Downloads the audio.
   - Runs **Demucs** to split the audio.
   - Runs **Faster-Whisper** on the isolated vocals.
   - Generates `.ass`, `.srt`, and `.lrc` subtitle formats.
   - Uses **FFmpeg** to render the final video.
5. **State Updates**: Throughout the process, the Celery worker directly updates the PostgreSQL database with percentage progress and log messages.
6. **Cloud Storage**: Upon completion, the worker pushes the final MP4, instrumental MP3, and subtitle files to **Amazon S3**.
7. **Asset Delivery**: The frontend receives the `completed` status and uses **Amazon CloudFront** URLs to serve the final video and download links to the user instantly.

---

## 🧠 The AI / Audio Pipeline In-Depth

The core value of LyricSync lies in its complex, multi-stage audio processing pipeline.

### 1. Media Acquisition (yt-dlp)
The pipeline begins by extracting the highest-available bitrate audio from the provided URL, bypassing video streams to save bandwidth and processing time.

### 2. Audio Preprocessing (FFmpeg)
Raw audio is heavily preprocessed before AI ingestion. It is converted to **44.1kHz stereo WAV**—the exact format the Demucs model was trained on. Bypassing standard normalizations here prevents timestamp shifting which would ruin karaoke sync.

### 3. Vocal Separation (Demucs)
This is the most computationally expensive step. Demucs uses a deep U-Net convolutional neural network to separate the track into independent stems (Vocals, Drums, Bass, Other). 
* **Why it matters**: Feeding a raw song into transcription models causes massive hallucinations (transcribing guitar solos as words). Isolating the vocals is mandatory for accurate lyrics.

### 4. Transcription & Alignment (Faster-Whisper)
The isolated vocal stem is converted to **16kHz mono** and normalized to -16 LUFS to feed into Faster-Whisper. 
We utilize heavily tuned parameters for music:
- **VAD (Voice Activity Detection)**: Masks out long instrumental bridges to prevent hallucinated lyrics.
- **Disabled Condition-on-Previous**: Prevents the model from trying to mathematically connect lyrics across long musical gaps.
- **Zero Temperature**: Forces deterministic, greedy decoding to prevent "creative" hallucinations.

### 5. Lyric Synchronization & Post-Processing
A custom Python processor catches Whisper's known edge cases in music:
- Detects and drops "repetition loops" (where the model gets stuck repeating a word).
- Flags low-confidence words.
- Applies conservative spelling corrections (`tonite` -> `tonight`) without altering slang or artistic intent.

### 6. Rendering (FFmpeg)
FFmpeg takes the original instrumental track, a custom background image loop, and the generated `.ass` subtitles, and burns them together. The `.ass` format uses the `\kf` (karaoke fill) tag to animate the color of the text smoothly from left to right precisely matching the duration of the sung word.

---

## ⚡ High-Performance / GPU Configuration

LyricSync's AI models are incredibly hardware-sensitive. 

### Current / Default Configuration
The standard deployment utilizes CPU-based processing. While cost-effective, transcription and separation are bottlenecked by CPU thread counts. 
- **Setup**: Standard x86 CPUs, 8-16GB RAM.
- **Performance**: 10-20 minutes per song.

### Optional High-Performance (GPU) Configuration
For enterprise or production use, LyricSync is fully designed to leverage NVIDIA CUDA hardware.
- **Hardware**: NVIDIA GPU (T4, A10g, or better), 8-16GB+ VRAM, fast NVMe SSD.
- **Acceleration**: 
  - Demucs natively shifts tensor operations to CUDA, reducing separation time from 5 minutes to 30 seconds.
  - Faster-Whisper (via CTranslate2 and cuBLAS) utilizes FP16 precision on the GPU, transcribing songs in under 10 seconds.
  - FFmpeg can be configured to use `h264_nvenc` for real-time hardware video encoding.

### Pushing Accuracy to 98% with High-End GPUs
The system is currently sitting at around 90% accuracy in my standard testing. However, the architecture is modular and designed to scale with compute. If you have access to a high-performance GPU, you can swap the default models for heavier, state-of-the-art alternatives to dramatically increase the output quality:

- **Vocal Separation:** Instead of the base model, swapping to **HTDemucs_ft** (fine-tuned) or **MDX-Net / UVR (Ultimate Vocal Remover)** models yields pristine vocal isolation with zero bleed.
- **Transcription & Alignment:** Upgrading to **Whisper Large-v3** ensures near-perfect lyric generation and timestamp alignment, even with complex background instrumentals.

---

## ☁️ AWS Infrastructure & Deployment Details

LyricSync is designed for cloud-native deployment on AWS, utilizing a highly decoupled, secure architecture.

### 1. Amazon VPC (Networking)
The foundation is a custom Virtual Private Cloud (VPC). It contains **Public Subnets** (for Load Balancers and NAT Gateways) and **Private Subnets** (for the ECS Tasks, RDS, and Redis). This ensures the ML workers and databases are entirely cut off from the public internet, dramatically reducing the attack surface.

### 2. Amazon ECR (Elastic Container Registry)
Docker images for both the FastAPI backend and Celery workers are built, tagged, and pushed to ECR. This provides a secure, private repository that ECS pulls from rapidly within the AWS backbone.

### 3. Amazon ECS & Fargate
We use the Elastic Container Service (ECS) with the serverless Fargate launch type. 
- **Task Definitions**: We define the CPU/Memory requirements, container images, and inject environment variables via Secrets Manager.
- **Services**: ECS Services ensure that the desired number of API and Worker containers are always running, automatically restarting them if they fail.

### 4. Amazon IAM & Security Groups
- **IAM**: Execution roles strictly limit what ECS tasks can do (e.g., they can write to specific S3 buckets, but cannot delete them).
- **Security Groups**: The database only accepts traffic from the ECS Worker/API security groups on port 5432. Redis only accepts traffic on 6379.

### 5. Amazon S3 & CloudFront
- **S3**: Used purely as a scalable data lake for the generated media assets.
- **CloudFront**: A global Content Delivery Network sits in front of the S3 bucket. It caches the heavy MP4 video files at edge locations globally. This prevents massive egress costs from S3 and ensures users experience zero buffering when previewing their videos.

---

## 🤖 n8n Automation

LyricSync utilizes **n8n** for workflow automation and external orchestration.

**Why n8n?**
While Celery handles the internal ML queue, n8n is used to trigger jobs from external sources (e.g., incoming emails, Discord messages, or scheduled batch jobs), interact with the LyricSync REST API via HTTP Request nodes, and automatically route the final CloudFront video URLs to other platforms.

![n8n Workflow](./n8nfiles/n8nworkflow.png)



## 🔒 Security

LyricSync treats security as a first-class citizen:
- **No hardcoded secrets**: AWS Credentials, Database URLs, and API keys are stored in environment variables (and AWS Secrets Manager in production).
- **Network Isolation**: RDS and Redis are placed in Private Subnets. They have no public IP addresses.
- **Least Privilege**: IAM roles restrict ECS tasks to specific S3 buckets.
- **Ignored Files**: `.env` and `__pycache__` are strictly enforced in `.gitignore`.
- **JWT Auth**: API routes are protected by Argon2-hashed JWT token authentication.

---

## 💻 Local Installation

### Prerequisites
- Node.js & npm
- Python 3.10+
- Redis Server (Running locally or via Docker)
- FFmpeg (Installed and added to system PATH)

### 1. Backend Setup
```bash
git clone https://github.com/ayushptk/ytsaas.git
cd ytsaas/backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the `backend/` directory (see `.env.example` below).

### 3. Start Backend Services
You need three terminal windows for the backend:

**Terminal 1 (Redis):**
Ensure your local Redis server is running on port 6379.

**Terminal 2 (FastAPI):**
```bash
cd backend
uvicorn main:app --reload
```

**Terminal 3 (Celery Worker):**
```bash
cd backend
celery -A worker.celery_app worker --loglevel=info -P threads
```

### 4. Frontend Setup
Open a fourth terminal:
```bash
cd frontend
npm install
npm run dev
```
Access the dashboard at `http://localhost:3000`.

---

## ⚙️ Environment Variables (`.env.example`)

```env
# Backend & Database
DATABASE_URL=postgresql://user:password@localhost:5432/ytsaas
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your_super_secret_jwt_key

# AWS Configuration (Production)
AWS_REGION=us-east-1
# Prefer IAM Roles over hardcoded keys in production
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=ytsaas-media-bucket
CLOUDFRONT_URL=https://d12345abcdef.cloudfront.net

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🐳 Docker Deployment & ECR

The best and easiest way to run LyricSync locally is using **Docker Compose**. This will automatically spin up the entire stack: PostgreSQL, Redis, FastAPI backend, Celery worker, Flower monitoring, and the Next.js frontend.

### 1. Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### 2. Environment Variables
Ensure you have a `.env` file created in the root directory (or update the existing one) with the required values. At a minimum, you'll need:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ytsaas
DATABASE_URL=postgresql://postgres:postgres@db:5432/ytsaas
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 3. Run the Stack
From the root of the project, run:
```bash
docker-compose up --build
```

### 4. Access the Services
Once all containers are running, you can access the various services at:
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend / Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Flower (Celery Worker Monitoring)**: [http://localhost:5555](http://localhost:5555)

---

### ☁️ AWS ECR Push (Production)

If you are containerizing the application for ECS deployment to AWS:

```bash
# Build the images
docker build -t ytsaas-backend ./backend
docker build -t ytsaas-frontend ./frontend

# Tag for AWS ECR (Replace with your actual AWS Account ID)
docker tag ytsaas-backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/ytsaas-backend:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/ytsaas-backend:latest
```

---

## 🛠️ Troubleshooting

- **FFmpeg Errors (`VideoRenderingError`)**: Ensure FFmpeg is added to your system PATH. If using Windows, ensure you have the required fonts installed (e.g., "Permanent Marker") for `.ass` subtitle rendering, otherwise FFmpeg will fall back to Arial.
- **Whisper Memory Issues / OOM**: If the Celery worker crashes silently during transcription, your machine ran out of RAM. Ensure you have at least 8GB of free memory, or switch to the `tiny` or `base` Faster-Whisper model in `transcriber.py`.
- **yt-dlp Bot Detection**: YouTube frequently updates its bot protections. Keep `yt-dlp` updated (`pip install -U yt-dlp`) or provide a `cookies.txt` file in the environment to bypass age-restrictions and blocks.
- **Celery Tasks Pending**: If jobs stay at 0% progress, ensure your Redis server is running and the `REDIS_URL` exactly matches in both FastAPI and Celery worker configurations.

---

## ✅ Production Readiness Checklist

- [x] Background Queue Processing (Celery)
- [x] S3 Media Storage
- [x] CloudFront CDN Delivery
- [x] Strict `.gitignore` implementations
- [x] JWT Authentication
- [ ] HTTPS / ACM Certificates
- [ ] Application Load Balancer Health Checks
- [ ] Secrets Manager Integration
- [ ] CI/CD Pipeline (GitHub Actions)

---

## 📸 AWS & Automation Deployment Evidence

Below is the actual architectural deployment and configuration evidence for LyricSync.

### VPC & Networking
![VPC Resource Map](./Aws%20Infrastructure/vpc/Vpcresoucesmap.png)
![VPC Architecture](./Aws%20Infrastructure/vpc/vpc%20arch.png)

### IAM & Security
![IAM Roles](./Aws%20Infrastructure/Iam/IAM.png)
![Security Groups](./Aws%20Infrastructure/Security-Groups/image.png)

### Elastic Container Registry (ECR)
![ECR Repositories](./Aws%20Infrastructure/Elastic-Container-Registry%28ECR%29/Imagerepository.png)
![Docker Images](./Aws%20Infrastructure/Elastic-Container-Registry%28ECR%29/docker%20images.png)

### Elastic Container Service (ECS)
![ECS Cluster](./Aws%20Infrastructure/Elastic-Container-services/Cluster.png)
![ECS Service](./Aws%20Infrastructure/ECS%20Service/image.png)
![ECS Task Definition](./Aws%20Infrastructure/ECS%20task%20Definations/Task%20Definations.png)

### Application Load Balancer
![Application Load Balancer](./Aws%20Infrastructure/Application%20Load%20Balancer/LoadBalancer.png)

### Database (RDS PostgreSQL)
![RDS PostgreSQL](./Aws%20Infrastructure/RDS%20PostgreSQL/image.png)

### Storage & CDN
![S3 Bucket](./Aws%20Infrastructure/S3%20Bucket/S3%20Bucket.png)
![CloudFront](./Aws%20Infrastructure/CloudFront/cloudfront.png)

### Automation
![n8n Workflow](./n8nfiles/n8nworkflow.png)

