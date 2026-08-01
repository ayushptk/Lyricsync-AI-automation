# Amazon ECS Services

## LyricSync AI SaaS

Amazon Elastic Container Service (Amazon ECS) Service is used to run, maintain, and manage the containerized workloads of LyricSync AI on AWS.

An ECS Service keeps the required number of tasks running, replaces failed tasks, manages deployments, and can integrate ECS tasks with other AWS services such as Application Load Balancer, CloudWatch, IAM, Amazon S3, Amazon RDS PostgreSQL, and ElastiCache Redis.

---

## 1. Why ECS Service Exists

A Docker container can be started manually, but a production application needs a system that continuously manages the containers.

For example, if LyricSync AI requires one API task and that task stops unexpectedly, the application could become unavailable.

An ECS Service allows us to specify a desired number of tasks.

Example:

```text
Desired tasks = 1
```

ECS continuously attempts to maintain that desired capacity.

If the running task stops, ECS can launch a replacement task.

Therefore, an ECS Service provides continuous task management and improves application availability.

---

## 2. ECS Service vs ECS Task Definition

These are different concepts.

### ECS Task Definition

The Task Definition describes how the container should run.

It defines settings such as:

- Docker image
- CPU
- Memory
- Container port
- Environment variables
- Secrets
- IAM roles
- CloudWatch logging
- Health checks
- Storage configuration

Example:

```text
lyricsync-api-task:1
```

### ECS Service

The ECS Service describes how ECS should continuously manage the tasks.

It controls or manages:

- Desired number of tasks
- Scheduling strategy
- Deployment behavior
- Networking configuration
- Load balancer integration
- Task replacement
- Health management
- Service scaling

In simple terms:

```text
Task Definition = How should the container run?

ECS Service = How should ECS keep and manage the containers running?
```

---

## 3. ECS Service vs ECS Cluster

An ECS Cluster is the logical environment where ECS services and tasks run.

For LyricSync AI, the ECS cluster is:

```text
lyricsync-cluster
```

The cluster can contain multiple services.

For example:

```text
lyricsync-api-service
lyricsync-worker-service
```

The cluster provides the environment, while each ECS Service manages its own tasks.

---

## 4. ECS Service vs Amazon ECR

Amazon ECR stores Docker images.

ECS uses those images to launch containers.

The general process is:

```text
Application Code
      ↓
Docker Build
      ↓
Docker Image
      ↓
Amazon ECR
      ↓
ECS Task Definition
      ↓
ECS Service
      ↓
Running ECS Task
```

ECR is therefore the container image repository.

ECS Service is responsible for running and maintaining the containers.

---

# 5. LyricSync AI ECS Services

LyricSync AI has different containerized workloads.

The main services are:

1. `lyricsync-api-service`
2. `lyricsync-worker-service`

They are separated because the API and background worker have different responsibilities and resource requirements.

---

# 6. LyricSync API Service

## Service Name

```text
lyricsync-api-service
```

## Purpose

The API Service runs the LyricSync AI FastAPI backend.

The API handles requests from the frontend and communicates with the application's databases, cache, storage, and background-processing system.

Typical API responsibilities include:

- User authentication
- User registration
- Login
- API requests
- Job creation
- Job status
- File metadata
- Lyrics information
- Processing status
- S3 operations
- Database operations

---

## 7. API Service Task Definition

The API Service uses an API-specific Task Definition.

Example:

```text
lyricsync-api-task
```

The Task Definition references the API Docker image stored in Amazon ECR.

Example:

```text
lyricsync-api:v1
```

The ECS Service uses that Task Definition to launch the API container.

---

## 8. API Service Desired Tasks

For the initial LyricSync deployment, a suitable configuration is:

```text
Desired tasks = 1
```

This means ECS attempts to maintain one running API task.

Later, the service can be increased to:

```text
Desired tasks = 2
```

or more.

Multiple API tasks allow the application to handle more traffic and provide greater availability.

---

# 9. API Service Networking

The API ECS tasks should normally run in private subnets.

The API does not need a public IP when users access it through an Application Load Balancer.

The API can communicate with other AWS resources through the VPC.

These resources include:

- Amazon RDS PostgreSQL
- ElastiCache Redis
- Amazon S3
- AWS Secrets Manager
- Amazon CloudWatch

Keeping the API tasks private reduces unnecessary direct Internet exposure.

---

# 10. API Service Security

The API Service uses a dedicated security group.

Example:

```text
lyricsync-api-sg
```

The security group should allow traffic only from trusted sources.

When an Application Load Balancer is configured, the API security group should allow the application port from the ALB security group rather than allowing the whole Internet.

For example:

```text
ALB Security Group
        ↓
lyricsync-api-sg
        ↓
API container port
```

Avoid unnecessarily exposing the API container directly to:

```text
0.0.0.0/0
```

---

# 11. API Service and Application Load Balancer

The API Service can later be connected to an Application Load Balancer.

The ALB receives HTTP/HTTPS requests and forwards them to healthy ECS API tasks.

The ECS Service can automatically register tasks with the target group.

When a task is replaced, ECS can update the target registration.

The typical production setup is:

```text
User
  ↓
Application Load Balancer
  ↓
ECS API Service
  ↓
FastAPI Container
```

The API container may listen on port:

```text
8000
```

The ALB target group can forward traffic to that port.

---

# 12. API Health Checks

The FastAPI application should provide a health endpoint.

Example:

```text
GET /health
```

Example response:

```json
{
  "status": "healthy"
}
```

A load balancer can use the endpoint to determine whether the API task is healthy.

If a task becomes unhealthy, the task can be removed from traffic and ECS can replace it depending on the service and health-check configuration.

---

# 13. API Service and PostgreSQL

The API Service communicates with Amazon RDS PostgreSQL.

PostgreSQL can store application information such as:

- Users
- Jobs
- Job status
- File metadata
- Processing information
- Application records

The database should normally remain private.

The API security group can be allowed to communicate with the database security group on PostgreSQL's standard port:

```text
5432
```

The database should not be publicly accessible unless there is a specific requirement.

---

# 14. API Service and Redis

The API Service can communicate with Amazon ElastiCache Redis.

Redis can be used for:

- Celery message brokering
- Job queues
- Caching
- Temporary application state

Redis normally uses:

```text
6379
```

The Redis security group should allow access only from the required application security groups.

---

# 15. API Service and Amazon S3

LyricSync AI uses Amazon S3 for persistent media storage.

The API may perform operations such as:

- Upload files
- Read object metadata
- Generate object references
- Manage uploaded media
- Retrieve generated files

The API Task Role should have only the S3 permissions that the application actually needs.

Avoid giving the API unnecessary access to every AWS resource.

---

# 16. API Service and Secrets Manager

Sensitive information should not be hardcoded inside the Docker image.

Examples of sensitive configuration include:

- Database credentials
- JWT secrets
- API keys
- Third-party credentials
- Redis credentials

These values can be stored in AWS Secrets Manager.

ECS can provide required secrets to the container through the Task Definition.

This is safer than putting secrets directly into source code or a public GitHub repository.

---

# 17. API Service and CloudWatch

The API container should send logs to Amazon CloudWatch Logs.

Examples include:

- Application startup
- API requests
- Errors
- Exceptions
- Database errors
- Authentication events
- Processing events

CloudWatch makes it possible to troubleshoot the application without directly connecting to the container.

---

# 18. LyricSync Worker Service

## Service Name

```text
lyricsync-worker-service
```

## Purpose

The Worker Service runs the Celery worker responsible for long-running background processing.

The worker can perform resource-intensive jobs such as:

- Video/audio processing
- YouTube downloads
- FFmpeg processing
- Vocal extraction
- Vocal separation
- Whisper transcription
- Lyrics processing
- Karaoke generation

---

# 19. Why the Worker Is a Separate Service

The API and worker perform different jobs.

The API handles short-lived HTTP requests.

The worker handles potentially long-running and resource-intensive processing.

Keeping them separate allows independent scaling.

For example:

```text
API:
Handles HTTP requests

Worker:
Handles AI/media processing
```

A heavy AI job should not consume all resources needed by the API.

---

# 20. Worker Task Definition

The Worker Service uses a separate Task Definition.

Example:

```text
lyricsync-worker-task
```

It references the worker Docker image stored in ECR.

Example:

```text
lyricsync-worker:v1
```

The worker image can contain the dependencies required for background processing.

These may include:

- Python
- Celery
- FFmpeg
- Whisper/WhisperX
- AI models
- Audio-processing libraries
- Video-processing libraries

---

# 21. Worker Service Desired Tasks

For initial testing:

```text
Desired tasks = 1
```

Later, the number of worker tasks can be increased.

For example:

```text
Desired tasks = 2
```

Two workers can process different jobs concurrently.

The correct number depends on:

- CPU
- Memory
- AI model requirements
- Processing time
- Queue workload
- AWS cost

---

# 22. Worker Service and Redis

The worker receives background jobs through Celery and Redis.

A typical process is:

```text
User Request
     ↓
FastAPI
     ↓
Create Job
     ↓
Celery / Redis Queue
     ↓
Celery Worker
     ↓
Process Job
```

The worker waits for jobs.

When a job becomes available, the worker receives it and performs the required processing.

---

# 23. Worker Processing

A typical LyricSync processing workflow can be:

```text
Receive Job
     ↓
Download Source
     ↓
Extract Audio
     ↓
Process Audio
     ↓
Separate Vocals
     ↓
Transcribe Audio
     ↓
Process Lyrics
     ↓
Generate Output
     ↓
Upload Result to S3
     ↓
Update Job Status
```

The exact processing pipeline depends on the implementation of LyricSync.

---

# 24. Worker and Amazon S3

The worker can use S3 for media processing.

It may:

- Download source files
- Upload processed audio
- Upload vocals
- Upload instrumentals
- Upload thumbnails
- Upload generated videos
- Store other generated files

The Worker Task Role should have only the permissions required for these operations.

---

# 25. Worker and PostgreSQL

The worker can communicate with PostgreSQL to update job information.

For example:

```text
queued
   ↓
processing
   ↓
completed
```

If processing fails:

```text
failed
```

The frontend can then request the job status through the API.

---

# 26. Worker and CloudWatch

Worker logs should also be sent to CloudWatch.

Useful logs include:

- Worker startup
- Job received
- Download started
- Audio processing
- Transcription started
- AI processing
- Upload started
- Job completed
- Job failed
- Exception details

This is particularly important for long-running AI workloads.

---

# 27. Worker and Application Load Balancer

The Worker Service normally does not need an Application Load Balancer.

The worker is not normally receiving public HTTP requests.

Instead, it waits for background jobs through Celery/Redis.

The API Service is the service that normally receives user HTTP requests.

Therefore, the ALB is normally associated with the API Service rather than the worker service.

---

# 28. ECS Scheduling Strategy

For LyricSync AI on Fargate, use:

```text
Scheduling strategy:
Replica
```

Replica scheduling allows ECS to maintain a desired number of task copies.

Example:

```text
Desired tasks = 2
```

ECS attempts to keep two tasks running.

The Daemon scheduling strategy is generally not used for a normal Fargate web application service.

---

# 29. Deployment Strategy

For the initial deployment, use:

```text
Deployment controller:
ECS

Deployment strategy:
Rolling update
```

When a new Task Definition revision is deployed, ECS gradually replaces the previous tasks with the new version according to the deployment configuration.

Example:

```text
lyricsync-api-task:1
        ↓
lyricsync-api-task:2
```

This allows application updates without manually stopping every task first.

---

# 30. Task Definition Revisions

Task Definitions have revisions.

Example:

```text
lyricsync-api-task:1
lyricsync-api-task:2
lyricsync-api-task:3
```

Each revision can contain different:

- Docker image
- Environment variables
- CPU
- Memory
- Ports
- Secrets
- Logging settings

When deploying a new application version, a new revision can be created and selected by the ECS Service.

Previous revisions remain available for deployment if needed.

---

# 31. What Happens When a Docker Image Is Updated?

Suppose the API code is changed.

A new Docker image is built:

```text
lyricsync-api:v2
```

The image is pushed to Amazon ECR.

Then a new Task Definition revision is created:

```text
lyricsync-api-task:2
```

The ECS Service is updated to use the new revision.

ECS performs the deployment according to the configured deployment strategy.

This creates a repeatable deployment process.

---

# 32. What Happens When a Task Crashes?

Suppose:

```text
Desired tasks = 1
Running tasks = 1
```

The running task crashes.

ECS detects that the service no longer has its desired number of tasks.

The service can launch a replacement task.

The goal becomes:

```text
Desired tasks = 1
Running tasks = 1
```

This automatic task replacement is one of the main reasons to use an ECS Service instead of manually running individual ECS tasks.

---

# 33. ECS Service Auto Scaling

ECS Services can be integrated with Application Auto Scaling.

For example:

```text
Minimum tasks = 1
Maximum tasks = 4
```

The service can scale based on metrics such as:

- CPU utilization
- Memory utilization
- Application Load Balancer request count per target

For the worker, scaling can also be designed around processing workload or queue depth when appropriate monitoring and scaling policies are implemented.

---

# 34. API Scaling

Suppose the API service is configured with:

```text
Minimum tasks = 1
Maximum tasks = 4
```

Normal traffic may require:

```text
1 API task
```

Higher traffic may cause:

```text
2 API tasks
```

Very high traffic could require:

```text
4 API tasks
```

The Application Load Balancer can distribute requests among healthy API tasks.

---

# 35. Worker Scaling

Suppose users submit many AI processing jobs.

The initial configuration could be:

```text
1 worker
```

As workload increases, additional workers can be launched:

```text
1 worker
   ↓
2 workers
   ↓
3 workers
```

Multiple workers can process different jobs concurrently.

Worker scaling must consider the high CPU and memory requirements of AI models.

---

# 36. ECS Service and AWS Fargate

LyricSync AI uses ECS with AWS Fargate to avoid managing EC2 servers directly.

With EC2-based ECS, you would normally manage:

- EC2 instances
- Operating systems
- Instance capacity
- Patching
- Instance scaling

With Fargate, AWS manages the underlying compute infrastructure.

You manage the application-level configuration, including:

- ECS Services
- Task Definitions
- Containers
- CPU
- Memory
- Networking
- IAM
- Application configuration

---

# 37. Security Best Practices

LyricSync ECS Services should follow the Principle of Least Privilege.

Recommended practices:

- Run application tasks in private subnets.
- Avoid unnecessary public IP addresses.
- Use dedicated security groups.
- Restrict inbound traffic.
- Use IAM Task Roles.
- Use IAM Task Execution Roles.
- Store secrets in AWS Secrets Manager.
- Do not hardcode credentials.
- Send application logs to CloudWatch.
- Keep RDS private.
- Keep Redis private.
- Restrict S3 permissions.
- Use HTTPS through the Application Load Balancer.
- Do not expose worker containers publicly.

---

# 38. ECS Task Role vs Task Execution Role

These roles have different purposes.

## Task Execution Role

The ECS Task Execution Role is used by ECS/Fargate to perform actions needed to start the task.

For example:

- Pulling private images from ECR
- Sending logs to CloudWatch
- Retrieving certain task startup resources

Example:

```text
lyricsync-task-execution-role
```

## Task Role

The Task Role gives the application inside the container permission to call AWS services.

For example:

```text
FastAPI container
      ↓
AWS API
      ↓
S3
```

or:

```text
Worker container
      ↓
AWS API
      ↓
S3
```

These permissions should follow least privilege.

---

# 39. API Service Recommended Configuration

For the initial LyricSync deployment:

```text
Service name:
lyricsync-api-service

Task definition:
lyricsync-api-task

Scheduling:
Replica

Desired tasks:
1

Launch type:
Fargate

Network:
LyricSync VPC

Subnets:
Private subnets

Public IP:
Disabled

Security group:
lyricsync-api-sg

Container port:
8000

Load balancer:
Application Load Balancer later

Deployment:
Rolling update

Logging:
CloudWatch
```

---

# 40. Worker Service Recommended Configuration

For the initial worker deployment:

```text
Service name:
lyricsync-worker-service

Task definition:
lyricsync-worker-task

Scheduling:
Replica

Desired tasks:
1

Launch type:
Fargate

Network:
LyricSync VPC

Subnets:
Private subnets

Public IP:
Disabled

Security group:
Worker-specific security group

Load balancer:
Not required

Deployment:
Rolling update

Logging:
CloudWatch
```

The worker CPU and memory should be sized according to the actual AI workload.

---

# 41. Typical LyricSync Job Lifecycle

When a user submits a processing job:

1. The frontend sends a request to the FastAPI API.
2. The Application Load Balancer forwards the request to a healthy API task.
3. FastAPI validates the request.
4. The API creates a job record in PostgreSQL.
5. The API sends the background job to Celery/Redis.
6. A worker receives the job.
7. The worker performs the required media and AI processing.
8. The worker uploads generated files to S3.
9. The worker updates the job status in PostgreSQL.
10. The frontend requests the job status through the API.
11. The user receives the completed result.

---

# 42. ECS Service Deployment Lifecycle

When an ECS Service is created:

1. ECS reads the selected Task Definition.
2. ECS determines the desired task count.
3. Fargate launches the required tasks.
4. The task starts the configured container.
5. Fargate pulls the container image from ECR.
6. The container starts.
7. Environment variables and secrets are provided.
8. Logs are sent to CloudWatch.
9. Health checks are performed where configured.
10. The ECS Service continues monitoring the desired task count.

---

# 43. Why LyricSync Uses Multiple ECS Services

Separating services provides independent control.

### API Service

Optimized for:

- HTTP traffic
- Fast response times
- Authentication
- Database requests
- Job creation
- API availability

### Worker Service

Optimized for:

- CPU-intensive processing
- Memory-intensive AI models
- Long-running jobs
- FFmpeg
- Transcription
- Vocal separation
- Background processing

This prevents heavy AI processing from consuming resources needed by the API.

---

# 44. Cost Considerations

The ECS Service itself is not the same as a traditional server.

With Fargate, the main compute cost comes from the resources allocated to running tasks.

For example:

```text
Desired tasks = 1
```

means one task is intended to remain running.

If you increase:

```text
Desired tasks = 3
```

three tasks may run and compute costs increase accordingly.

Other AWS resources can also generate costs, including:

- Application Load Balancer
- NAT Gateway
- RDS PostgreSQL
- ElastiCache Redis
- CloudWatch
- S3
- Data transfer

For a learning environment, keep the number of running tasks and other paid resources as low as practical when they are not needed.

---

# 45. GitHub Documentation

Recommended documentation structure:

```text
docs/
└── aws/
    └── ecs-service/
        └── README.md
```

Useful screenshots for documenting the implementation include:

- ECS cluster
- ECS service
- Running tasks
- Service configuration
- Deployment configuration
- Task Definition
- Service events
- CloudWatch logs

Before committing screenshots to a public GitHub repository, check that they do not expose:

- AWS access keys
- Secret keys
- Database passwords
- JWT secrets
- API keys
- OAuth secrets
- Secrets Manager values
- Private credentials
- Sensitive application data

AWS resource identifiers are not normally secret credentials, but they can still be redacted if you prefer not to publish them.

---

# 46. Practical LyricSync ECS Service Setup

For the first deployment, create the API Service using:

```text
Cluster:
lyricsync-cluster

Service:
lyricsync-api-service

Task Definition:
lyricsync-api-task

Scheduling:
Replica

Desired tasks:
1

Launch type:
Fargate

VPC:
lyricsync-vpc

Subnets:
Private subnets

Security Group:
lyricsync-api-sg

Public IP:
Disabled

Deployment:
Rolling update

Load Balancer:
Add Application Load Balancer when available
```

Then create the worker service separately:

```text
Cluster:
lyricsync-cluster

Service:
lyricsync-worker-service

Task Definition:
lyricsync-worker-task

Scheduling:
Replica

Desired tasks:
1

Launch type:
Fargate

VPC:
lyricsync-vpc

Subnets:
Private subnets

Public IP:
Disabled

Deployment:
Rolling update

Load Balancer:
None
```

---

# 47. What I Implemented in LyricSync AI

The ECS Service layer provides continuous management of the application's containerized workloads.

The implementation uses:

- Amazon ECS
- AWS Fargate
- Amazon ECR
- ECS Task Definitions
- ECS Services
- IAM Roles
- VPC
- Private Subnets
- Security Groups
- CloudWatch Logs
- Amazon S3
- Amazon RDS PostgreSQL
- ElastiCache Redis

The API and worker workloads are separated into different ECS Services so that they can be deployed, monitored, scaled, and secured independently.

---

# 48. Key Takeaways

### Amazon ECR

Stores the Docker images.

### ECS Cluster

Provides the logical environment for the services and tasks.

### ECS Task Definition

Defines how a container should run.

### ECS Service

Keeps the required number of tasks running and manages deployments and task replacement.

### Fargate

Provides serverless compute for the ECS tasks.

### Application Load Balancer

Provides HTTP/HTTPS traffic distribution to the API service.

### CloudWatch

Collects logs and monitoring information.

### IAM

Controls what ECS and the applications inside the containers are allowed to access.

### S3

Stores LyricSync media and generated files.

### RDS PostgreSQL

Stores structured application data.

### ElastiCache Redis

Supports caching and Celery/background job processing.

---

# 49. Final Summary

ECS Services are the layer that turns LyricSync AI's container definitions into continuously managed application workloads.

The main services are:

```text
lyricsync-api-service
lyricsync-worker-service
```

The API Service runs the FastAPI backend and handles user-facing API requests.

The Worker Service runs Celery workers and handles long-running AI and media-processing jobs.

Both services use ECS Task Definitions to determine how their containers run.

ECS Services maintain the desired number of tasks, replace failed tasks, support rolling deployments, and can scale according to workload.

This gives LyricSync AI a production-oriented container deployment model on AWS Fargate while keeping the API, worker, database, cache, storage, networking, IAM, and monitoring responsibilities separated.
