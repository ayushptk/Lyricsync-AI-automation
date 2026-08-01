# Amazon ECS Task Definition

## Project

**LyricSync AI SaaS**

---

# Overview

An **Amazon ECS Task Definition** is a blueprint that tells Amazon ECS exactly how to run a Docker container.

It contains all the runtime configuration required for a container, including the Docker image, CPU, memory, networking, ports, IAM roles, environment variables, secrets, logging, and storage.

A Docker image stored in Amazon ECR cannot run by itself. Amazon ECS needs instructions describing **how** the image should be started. These instructions are stored in the Task Definition.

Every time Amazon ECS launches a new container, it follows the Task Definition.

---

# Why Amazon ECS Task Definition Exists

Building a Docker image is only the first step.

For LyricSync AI, the Docker image contains:

- FastAPI
- Celery
- Python
- FFmpeg
- yt-dlp
- Demucs
- Faster-Whisper
- PyTorch
- Application source code

Although the Docker image contains the application, Amazon ECS still needs additional information before it can run it.

For example:

- Which Docker image should be used?
- How much CPU should be allocated?
- How much memory should be allocated?
- Which port should be exposed?
- Which environment variables should be available?
- Which secrets should be injected?
- Which IAM role should the container use?
- Where should application logs be stored?

Instead of configuring these settings every time the application starts, AWS stores them inside a Task Definition.

---

# Why LyricSync AI Uses ECS Task Definitions

LyricSync AI consists of multiple containerized services.

Examples include:

- FastAPI Backend
- Celery Worker

Each service has different runtime requirements.

For example:

The FastAPI API needs:

- Port 8000
- Database connection
- Redis connection
- JWT Secret
- CloudWatch logging

The Celery Worker needs:

- Redis connection
- S3 access
- AI models
- Background processing configuration

Instead of configuring these manually whenever a container starts, Amazon ECS reads the Task Definition and launches the container using the predefined configuration.

This guarantees every deployment starts consistently.

---

# Task Definition Components

## 1. Task Family

The Task Family is the name of the Task Definition.

Example:

```
lyricsync-api-task
```

Every time the configuration changes, AWS creates a new revision under the same family.

Example:

```
lyricsync-api-task:1

lyricsync-api-task:2

lyricsync-api-task:3
```

This makes version management easy.

---

## 2. Launch Type

LyricSync AI uses:

```
AWS Fargate
```

AWS Fargate runs containers without managing servers.

AWS automatically provides:

- Compute
- Networking
- Operating system
- Infrastructure management

No EC2 instances are required.

---

## 3. Docker Image

The Task Definition specifies which Docker image Amazon ECS should run.

For LyricSync AI, the image is stored in Amazon Elastic Container Registry (Amazon ECR).

Example:

```
lyricsync-api:latest
```

Whenever a task starts, Amazon ECS downloads the latest image from Amazon ECR.

---

## 4. CPU Allocation

Every container requires processing power.

The Task Definition specifies how much CPU the container receives.

Example:

```
1 vCPU
```

This CPU is used by:

- FastAPI
- FFmpeg
- AI processing
- Background tasks

Choosing the correct CPU allocation improves application performance.

---

## 5. Memory Allocation

Containers also require RAM.

Example:

```
2 GB
```

Memory is used by:

- Python
- FastAPI
- FFmpeg
- Demucs
- Faster-Whisper
- PyTorch

If a container exceeds its allocated memory, AWS automatically stops the task.

---

## 6. Container Name

Each running container has a logical name.

Example:

```
lyricsync-api
```

This name is used throughout ECS for identification and monitoring.

---

## 7. Port Mapping

The Task Definition specifies which application port is exposed.

For LyricSync AI:

```
8000
```

FastAPI listens on port 8000.

Later, the Application Load Balancer forwards incoming user requests to this port.

---

## 8. Environment Variables

Applications require configuration values during runtime.

Instead of hardcoding values inside the application, they are provided through Environment Variables.

Examples:

```
ENV=production

AWS_REGION=ap-southeast-2

LOG_LEVEL=INFO

S3_BUCKET=lyricsync-media
```

Environment Variables make the application configurable without modifying the source code.

---

## 9. Secrets

Sensitive information should never be stored inside:

- Source code
- Docker images
- GitHub repositories
- Environment Variables

Instead, Amazon ECS integrates with AWS Secrets Manager.

Examples of secrets include:

- Database password
- JWT Secret
- API Keys
- OAuth credentials

When the container starts, ECS securely retrieves these secrets and injects them into the application.

This improves security and prevents credential exposure.

---

## 10. Task Role

Applications often need permission to access AWS services.

Instead of storing AWS Access Keys inside the application, Amazon ECS attaches an IAM Task Role.

The Task Role allows the application to securely access AWS services.

Examples include:

- Upload karaoke videos to Amazon S3
- Download files from Amazon S3
- Read Secrets Manager
- Send messages to Amazon SQS

The application temporarily receives these permissions while the container is running.

---

## 11. Task Execution Role

The Task Execution Role is different from the Task Role.

It is used by Amazon ECS itself.

It allows ECS to:

- Pull Docker images from Amazon ECR
- Send container logs to Amazon CloudWatch
- Retrieve secrets during container startup

The application does not directly use this role.

It exists so Amazon ECS can prepare the container before the application starts.

---

## 12. Logging

Amazon ECS integrates with Amazon CloudWatch Logs.

All application logs are automatically sent to CloudWatch.

Examples include:

- API requests
- Authentication events
- AI processing progress
- Errors
- Warnings
- Debug information

CloudWatch provides centralized logging and troubleshooting.

---

## 13. Health Checks

The Task Definition can define a health check command.

Amazon ECS periodically checks whether the application is still responding.

If the application fails the health check:

- ECS marks the task as unhealthy.
- ECS automatically stops the failed task.
- ECS launches a replacement task.

This increases application availability.

---

## 14. Ephemeral Storage

Containers require temporary storage while running.

LyricSync AI temporarily stores:

- Downloaded audio
- Instrumental tracks
- AI-generated files
- Temporary video files

This temporary storage exists only while the task is running.

Once the task stops, the temporary storage is removed.

Permanent files are uploaded to Amazon S3.

---

# How LyricSync AI Uses Task Definitions

For the API service:

- Uses the FastAPI Docker image
- Opens port 8000
- Connects to PostgreSQL
- Connects to Redis
- Sends logs to CloudWatch
- Uploads generated files to Amazon S3
- Reads secrets from AWS Secrets Manager

For the Worker service:

- Uses the Celery Worker Docker image
- Connects to Redis
- Processes AI tasks
- Downloads YouTube audio
- Runs Demucs
- Runs Faster-Whisper
- Renders karaoke videos
- Uploads output files to Amazon S3

Although both services run in the same ECS Cluster, each has its own Task Definition because they require different configurations.

---

# Benefits of Amazon ECS Task Definition

- Standardizes container configuration
- Eliminates manual deployment configuration
- Enables repeatable deployments
- Supports automatic versioning
- Integrates with Amazon ECR
- Supports AWS Fargate
- Securely injects secrets
- Supports IAM Roles
- Enables CloudWatch logging
- Provides health checks
- Supports container scaling
- Simplifies production deployments

---



# Conclusion

Amazon ECS Task Definition is the deployment blueprint for LyricSync AI. It defines exactly how each container should run, including the Docker image, compute resources, networking, IAM permissions, environment variables, secrets, logging, and health checks. By storing this configuration in AWS, every deployment is consistent, secure, and repeatable. It enables Amazon ECS to launch FastAPI and Celery containers reliably while integrating seamlessly with Amazon ECR, AWS Fargate, Amazon S3, Amazon RDS, ElastiCache Redis, CloudWatch, and Secrets Manager.