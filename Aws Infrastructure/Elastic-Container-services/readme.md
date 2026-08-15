# Amazon ECS Cluster

## Project

**LyricSync AI SaaS**

# Overview

Amazon Elastic Container Service (Amazon ECS) is a fully managed container orchestration service that runs Docker containers on AWS.

For **LyricSync AI**, the Amazon ECS Cluster is the environment where all application containers run continuously in the cloud. Instead of running the application locally using `docker compose up`, Amazon ECS automatically starts, monitors, scales, and manages the application's containers.

---

# Why Amazon ECS Cluster Exists

After building the application, Docker creates a container image.

The image is stored inside **Amazon Elastic Container Registry (ECR)**.

However, Docker images stored in Amazon ECR do not run automatically.

Amazon ECS Cluster exists to execute those Docker images.

Without Amazon ECS:

```
Developer

↓

Docker Image

↓

Amazon ECR

↓

Nothing Happens
```

With Amazon ECS:

```
Developer

↓

Docker Image

↓

Amazon ECR

↓

Amazon ECS Cluster

↓

Running Application
```

Amazon ECS transforms a stored Docker image into a running application.

---

# Why LyricSync AI Uses Amazon ECS Cluster

LyricSync AI is an AI-powered SaaS platform that performs long-running media processing tasks.

Examples include:

- Downloading YouTube audio
- Vocal separation using Demucs
- Speech transcription using Faster-Whisper
- Subtitle generation
- Karaoke video rendering
- Uploading generated files to Amazon S3

These processes require continuously running backend services.

Instead of running these services on a personal computer, Amazon ECS runs them inside AWS.

---

# Problem Without Amazon ECS

Currently the application runs locally.

```
Laptop

↓

docker compose up

↓

FastAPI

↓

Celery

↓

Redis

↓

PostgreSQL
```

Everything depends on the developer's computer.

If the laptop is turned off:

```
Laptop Off

↓

Backend Stops

↓

Website Stops

↓

Users Cannot Access
```

This is not suitable for a production SaaS application.

---

# Solution Using Amazon ECS

```
AWS Cloud

↓

Amazon ECS Cluster

↓

Containers Running 24/7

↓

Application Always Available
```

Amazon ECS keeps the backend online without depending on the developer's computer.

---

# How Amazon ECS Works in LyricSync AI

## Step 1 — Docker Image

The backend is packaged into a Docker image.

```
lyricsync-api
```

This image contains:

- Linux
- Python
- FastAPI
- FFmpeg
- Demucs
- Faster-Whisper
- yt-dlp
- Celery
- Application source code
- Required dependencies

---

## Step 2 — Upload to Amazon ECR

The Docker image is pushed to Amazon Elastic Container Registry.

```
Developer

↓

Docker Push

↓

Amazon ECR

↓

lyricsync-api
```

The image is now stored inside AWS.

---

## Step 3 — Amazon ECS Downloads the Image

Amazon ECS reads the Task Definition.

The Task Definition tells ECS:

- Which Docker image to use
- CPU allocation
- Memory allocation
- Port number
- IAM Role
- Environment Variables
- Logging configuration

Amazon ECS downloads the Docker image directly from Amazon ECR.

---

## Step 4 — Container Starts

After downloading the image,

Amazon ECS creates a running container.

```
Amazon ECS

↓

Download Image

↓

Create Container

↓

Start FastAPI

↓

Application Running
```

Users can now access the backend.

---

# Amazon ECS Cluster Architecture

```
                        Internet
                            │
                            ▼
              Application Load Balancer
                            │
                            ▼
                  Amazon ECS Cluster
             ┌──────────────────────────┐
             │                          │
             │   API Container          │
             │   FastAPI                │
             │                          │
             │──────────────────────────│
             │                          │
             │   Worker Container       │
             │   Celery                 │
             │                          │
             └──────────────────────────┘
                      │
          ┌───────────┼─────────────┐
          ▼           ▼             ▼
      Amazon S3     Amazon RDS   ElastiCache Redis
```

---

# Components Running Inside the Cluster

For LyricSync AI, the ECS Cluster will eventually run multiple services.

## API Service

Runs:

- FastAPI
- Authentication
- REST API
- Job creation
- File uploads
- Download endpoints

---

## Worker Service

Runs:

- Celery Worker
- YouTube Downloader
- AI Processing
- Subtitle Generation
- Video Rendering

Worker containers process long-running background tasks.

---

# Why Separate API and Worker?

The API should respond quickly.

Example:

User submits a YouTube URL.

```
User

↓

POST /generate

↓

FastAPI

↓

Returns

Job Created
```

The API should not spend several minutes processing AI tasks.

Instead,

FastAPI sends the job to Redis.

Celery Worker processes the task in the background.

```
FastAPI

↓

Redis Queue

↓

Celery Worker

↓

AI Processing

↓

Amazon S3
```

This keeps the application responsive.

---

# Cluster Hierarchy

Many beginners think the Cluster directly runs containers.

Actually, the hierarchy is:

```
Amazon ECS Cluster

↓

Service

↓

Task

↓

Container
```

Explanation:

Cluster

- Groups related services together.

Service

- Keeps the required number of tasks running.

Task

- A running instance of a Task Definition.

Container

- The actual Docker container.

---

# Example for LyricSync AI

```
lyricsync-cluster

│

├── lyricsync-api-service

│      │

│      └── API Task

│              │

│              └── FastAPI Container

│

└── lyricsync-worker-service

       │

       └── Worker Task

               │

               └── Celery Container
```

One Cluster can run multiple services.

---

# Self-Healing

Suppose the API crashes.

Without ECS:

```
Container Crash

↓

Application Offline
```

With ECS:

```
Container Crash

↓

Amazon ECS Detects Failure

↓

Starts New Container

↓

Application Online Again
```

Amazon ECS automatically replaces failed containers.

---

# Auto Scaling

Suppose:

10 users visit the application.

```
One API Container
```

Now imagine:

10,000 users visit.

Amazon ECS can automatically create additional containers.

```
API Container 1

API Container 2

API Container 3

API Container 4
```

The Application Load Balancer distributes traffic across all running containers.

This improves scalability and availability.

---

# Integration with Other AWS Services

Amazon ECS integrates with multiple AWS services.

### Amazon ECR

Stores Docker images.

Amazon ECS pulls images directly from ECR.

---

### Application Load Balancer

Distributes user requests across running containers.

---

### Amazon S3

Stores generated karaoke videos, subtitles, and audio files.

Containers upload generated assets to S3.

---

### Amazon RDS PostgreSQL

Stores:

- User accounts
- Jobs
- Processing status
- Metadata

---

### Amazon ElastiCache Redis

Used as the Celery message broker.

Queues AI processing tasks.

---

### CloudWatch

Collects:

- Container logs
- CPU utilization
- Memory usage
- Performance metrics

---

### IAM

Allows Amazon ECS to securely:

- Pull Docker images from ECR
- Upload files to Amazon S3
- Send logs to CloudWatch
- Access Secrets Manager

---

# Benefits for LyricSync AI

- Runs containers in AWS
- Highly available architecture
- Automatic recovery from failures
- Supports horizontal scaling
- Integrates with Amazon ECR
- Secure IAM integration
- Supports CloudWatch monitoring
- Eliminates server management with AWS Fargate
- Enables production-ready deployments

---

# Amazon ECS Workflow

```
Developer

↓

GitHub

↓

Docker Build

↓

Docker Image

↓

Amazon ECR

↓

Amazon ECS Cluster

↓

Task Definition

↓

Service

↓

Running Containers

↓

Application Load Balancer

↓

Users
```

---



# Screenshots

```
screenshots/
├── 01-ecs-dashboard.png
├── 02-create-cluster.png
├── 03-cluster-configuration.png
├── 04-container-insights-enabled.png
├── 05-cluster-created.png
├── 06-cluster-overview.png
```

---

# Conclusion

Amazon ECS Cluster is the runtime environment for **LyricSync AI**. It is responsible for running, monitoring, and managing the application's Docker containers in AWS. Docker images stored in Amazon ECR are pulled into the cluster, where they become running containers for the FastAPI backend and Celery workers. By integrating with AWS Fargate, IAM, CloudWatch, Amazon S3, Amazon RDS, and ElastiCache Redis, the ECS Cluster provides a scalable, highly available, and production-ready platform for deploying the LyricSync AI SaaS application.