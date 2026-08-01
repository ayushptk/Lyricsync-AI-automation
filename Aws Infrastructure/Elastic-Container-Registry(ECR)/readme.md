# Amazon Elastic Container Registry (ECR)

## Project

**LyricSync AI SaaS**

---

# Overview

Amazon Elastic Container Registry (ECR) is a fully managed AWS service that securely stores Docker container images.

For **LyricSync AI**, Amazon ECR acts as the central repository for Docker images that are deployed to Amazon ECS. Instead of deploying source code directly, the application is first packaged into a Docker image and uploaded to ECR. Amazon ECS later pulls this image to launch the application.

---

# Why Amazon ECR Exists

Docker images created on a local computer are only available on that machine.

For example:

```bash
docker build -t lyricsync-api .
```

creates a Docker image named:

```
lyricsync-api:latest
```

However, this image only exists on the developer's computer.

AWS services such as Amazon ECS cannot access Docker images stored locally.

Amazon ECR solves this problem by providing a secure cloud-based container registry where Docker images can be stored and accessed by AWS services.

---

# Why LyricSync AI Uses Amazon ECR

LyricSync AI consists of multiple components that require a consistent runtime environment.

The backend includes:

- FastAPI
- Python
- FFmpeg
- yt-dlp
- Demucs
- Faster-Whisper
- Celery
- Redis client
- PostgreSQL client
- All Python dependencies

These dependencies are packaged into a Docker image.

Instead of reinstalling these dependencies every deployment, the Docker image is uploaded once to Amazon ECR and reused whenever the application is deployed.

# How Amazon ECR Works in LyricSync AI

## Step 1 — Develop the Application

The backend application is developed locally.

```

backend/
├── FastAPI
├── Celery
├── FFmpeg
├── Faster-Whisper
├── Demucs
└── Dockerfile

```

---

## Step 2 — Build Docker Image

The application is packaged into a Docker image.

```bash
docker build -t lyricsync-api .
```

Docker creates a portable image containing:

- Linux
- Python
- FastAPI
- FFmpeg
- Machine Learning libraries
- Project source code
- Application startup command

---

## Step 3 — Push Image to Amazon ECR

The Docker image is uploaded to Amazon ECR.

```

Developer
│
▼
Docker Push
│
▼
Amazon ECR Repository

```

The image is now securely stored inside AWS.

---

## Step 4 — Amazon ECS Pulls the Image

When an ECS Task starts, ECS requests the Docker image from Amazon ECR.

```

Amazon ECS
│
▼
Pull Image
│
▼
Amazon ECR

```

The image is downloaded automatically.

---

## Step 5 — Run the Container

After downloading the image, Amazon ECS creates a running Docker container.

```

Amazon ECR
│
▼
Docker Image
│
▼
Amazon ECS
│
▼
Running FastAPI Container

```

The application is now available to users.

---

# Why Not Deploy Source Code Directly?

Deploying only the source code would require every server to manually install:

- Python
- FFmpeg
- PyTorch
- Faster-Whisper
- Demucs
- yt-dlp
- All project dependencies

This would be slow, inconsistent, and error-prone.

Docker packages everything into one image.

Amazon ECR stores that image for deployment.

---

# Docker Image Lifecycle

```

Source Code
│
▼
Dockerfile
│
▼
docker build
│
▼
Docker Image
│
▼
Amazon ECR
│
▼
Amazon ECS
│
▼
Running Container

```

---

# Image Versioning

Amazon ECR supports multiple versions of the same application.

Example:

```

lyricsync-api:v1
lyricsync-api:v2
lyricsync-api:v3
lyricsync-api:latest

```

Benefits:

- Easy rollback
- Safe deployments
- Version tracking
- Multiple application releases

If version **v3** contains a bug, Amazon ECS can immediately deploy **v2** without rebuilding the application.

---

# Security Features

Amazon ECR provides several built-in security features.

### Private Repository

Only authorized AWS accounts can access the repository.

---

### IAM Integration

Access is controlled using IAM Users, IAM Roles, and IAM Policies.

Only approved users and AWS services can push or pull Docker images.

---

### Encryption

Docker images are encrypted at rest using AWS-managed encryption keys.

---

### Image Scanning

Image scanning detects known software vulnerabilities inside Docker images.

This helps identify outdated packages before deployment.

---

# Benefits for LyricSync AI

- Central storage for Docker images
- Secure integration with Amazon ECS
- Version-controlled application deployments
- Reliable and consistent runtime environment
- Eliminates manual server configuration
- Supports rollback to previous versions
- Built-in vulnerability scanning
- IAM-based access control

