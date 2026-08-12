# Application Load Balancer (ALB) — LyricSync AI SaaS

![Load Balancer](./LoadBalancer.png)

## 1. Overview

An Application Load Balancer (ALB) is the public HTTP/HTTPS entry point for the LyricSync AI backend.

LyricSync AI uses Amazon ECS with AWS Fargate to run its FastAPI API container. The ALB receives requests from users and forwards them to healthy ECS API tasks running inside private subnets.

```text
User
  ↓
Internet
  ↓
Internet-facing Application Load Balancer
  ↓
ALB Listener
  ↓
Target Group
  ↓
Healthy ECS Fargate API Task
  ↓
FastAPI Container :8000
```

The ALB does not run the application. ECS/Fargate runs the containers. The ALB manages incoming application traffic and sends it to the appropriate healthy targets.

---

# 2. Why an ALB Exists in LyricSync AI

Without a load balancer, users would need to communicate directly with an individual backend task.

That creates several problems:

- Fargate task IP addresses can change.
- A task can stop or be replaced.
- Multiple API tasks need a single public endpoint.
- Unhealthy tasks should not receive normal traffic.
- HTTPS termination should be handled centrally.
- Traffic distribution should not be implemented manually by the application.

The ALB solves these problems.

It provides:

- A stable public endpoint
- HTTP/HTTPS traffic handling
- Traffic distribution
- Health checks
- Integration with ECS services
- Multi-Availability-Zone availability
- HTTPS termination with ACM
- Automatic use of healthy targets

---

# 3. LyricSync AI ALB Configuration

Current project configuration:

```text
Load Balancer:
lyricsync-alb

Type:
Application Load Balancer

Scheme:
Internet-facing

VPC:
lyricsync-vpc

Public Subnet A:
lyricsync-vpc-subnet-public1-eu-north-1a

Public Subnet B:
lyricsync-vpc-subnet-public2-eu-north-1b

Security Group:
lyricsync-alb-sg

Listener:
HTTP :80

Target Group:
lyricsync-api-tg

Target Type:
IP addresses

Backend Protocol:
HTTP

Backend Port:
8000
```

---

# 4. Application Load Balancer

## What is it?

An Application Load Balancer is an AWS managed load-balancing service designed for HTTP and HTTPS application traffic.

For LyricSync AI, the ALB receives requests such as:

```text
GET /health
POST /api/transcribe
POST /api/lyrics
GET /api/jobs/123
```

and forwards them to the ECS API service.

## Why LyricSync uses it

The FastAPI application should not be directly exposed to the Internet.

Instead:

```text
Internet
   ↓
ALB
   ↓
Private ECS API
```

This creates a controlled public entry point.

---

# 5. Internet-Facing ALB

The ALB is configured as:

```text
Internet-facing
```

This means the ALB receives traffic from users on the public Internet.

The ALB is placed in public subnets:

```text
eu-north-1a
    ↓
Public Subnet A
    ↓
ALB node

eu-north-1b
    ↓
Public Subnet B
    ↓
ALB node
```

The ECS API tasks remain in private subnets.

---

# 6. Why the ALB Uses Two Public Subnets

The project uses two Availability Zones:

```text
eu-north-1a
eu-north-1b
```

The ALB is attached to a public subnet in each Availability Zone.

This provides higher availability and lets AWS operate ALB nodes across multiple zones.

The design is:

```text
Public Subnet A → ALB
Public Subnet B → ALB

Private Subnet A → ECS
Private Subnet B → ECS
```

---

# 7. Internet Gateway and Route Tables

The public subnets containing the internet-facing ALB have routes toward the Internet Gateway.

Conceptually:

```text
Internet
   ↓
Internet Gateway
   ↓
Public Subnet
   ↓
ALB
```

A public subnet route table normally contains:

```text
Destination: 0.0.0.0/0
Target: Internet Gateway
```

The route table provides the network path. The ALB handles application-level HTTP/HTTPS traffic distribution.

---

# 8. ALB Security Group

The ALB uses a dedicated security group:

```text
lyricsync-alb-sg
```

For initial HTTP testing:

```text
Inbound:
HTTP
Port: 80
Source: 0.0.0.0/0
```

Later, production HTTPS should use:

```text
Inbound:
HTTPS
Port: 443
Source: 0.0.0.0/0
```

The backend application port should not be opened directly to the Internet.

---

# 9. ECS API Security Group

The ECS API tasks use:

```text
lyricsync-api-sg
```

The important inbound rule is:

```text
Source:
lyricsync-alb-sg

Protocol:
TCP

Port:
8000
```

This creates:

```text
Internet
   ↓
ALB
   ↓
lyricsync-alb-sg
   ↓
ECS API
   ↓
Port 8000
```

Do not unnecessarily configure:

```text
0.0.0.0/0 → TCP 8000
```

for the private ECS API.

---

# 10. Listener

A listener tells the ALB what protocol and port to accept.

Current listener:

```text
HTTP :80
```

Therefore:

```text
User
 ↓
ALB :80
```

The listener forwards requests to the configured target group.

Later the project can use:

```text
HTTPS :443
```

with an ACM certificate.

---

# 11. Listener vs Target Group

These are different components.

### Listener

Receives incoming traffic:

```text
ALB
 ↓
HTTP :80
```

### Target Group

Defines backend targets:

```text
Target Group
 ↓
ECS Fargate Tasks
```

Together:

```text
User
 ↓
ALB :80
 ↓
Listener
 ↓
Target Group
 ↓
ECS Task :8000
```

---

# 12. Target Group

LyricSync uses:

```text
lyricsync-api-tg
```

A target group defines the backend destinations to which the ALB sends traffic.

Configuration:

```text
Name:
lyricsync-api-tg

Target type:
IP addresses

Protocol:
HTTP

Port:
8000

VPC:
lyricsync-vpc
```

---

# 13. Why Target Type = IP Addresses

LyricSync uses Amazon ECS Fargate.

Fargate tasks receive private IP addresses through their task network interfaces.

Therefore the target group uses:

```text
Target type:
IP addresses
```

Conceptually:

```text
ALB
 ↓
lyricsync-api-tg
 ↓
10.0.x.x:8000
```

The ECS service manages registration of running task IP addresses.

Do not manually maintain Fargate task IPs. When ECS replaces a task, its IP can change and ECS can register the new task with the target group.

---

# 14. Why Not Target Type = Instance?

Instance targets are used for architectures where the load balancer sends traffic to EC2 instances.

LyricSync uses Fargate instead of managing EC2 container instances.

Therefore:

```text
ECS Fargate
    ↓
IP target type
```

is appropriate for this project.

---

# 15. Backend Port 8000

The FastAPI application runs on:

```text
8000
```

The target group therefore sends traffic to:

```text
ECS Task Private IP:8000
```

The traffic path is:

```text
Client
 ↓
ALB :80
 ↓
Target Group
 ↓
ECS Task :8000
 ↓
FastAPI
```

The ALB listener port and backend port can be different.

Example:

```text
ALB:
80

Backend:
8000
```

---

# 16. Container Port

The ECS task definition contains:

```text
lyricsync-api
```

with container port:

```text
8000
```

The ECS service connects this container to the ALB target group.

Relationship:

```text
ALB
 ↓
Target Group
 ↓
lyricsync-api
 ↓
Port 8000
```

---

# 17. FastAPI Binding

The FastAPI/Uvicorn application should listen on the container network interface:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The important part is:

```text
--host 0.0.0.0
```

Binding only to:

```text
127.0.0.1
```

can prevent the ALB from reaching the application through the task network interface.

---

# 18. Health Checks

The ALB continuously checks registered targets.

LyricSync should provide a simple endpoint:

```text
GET /health
```

Example response:

```json
{
  "status": "healthy"
}
```

Recommended target group health check:

```text
Protocol:
HTTP

Path:
/health

Port:
Traffic port

Success code:
200
```

The ALB periodically requests the health endpoint on the ECS task.

---

# 19. Why Health Checks Matter

Suppose:

```text
Task 1 → Healthy
Task 2 → Healthy
```

If Task 2 stops responding:

```text
Task 1 → Healthy
Task 2 → Unhealthy
```

The ALB can stop routing normal traffic to the unhealthy target.

This prevents users from repeatedly reaching a failed task.

---

# 20. ECS Service Integration

The ECS service maintains the desired number of tasks.

For example:

```text
Desired tasks:
2
```

ECS can maintain:

```text
API Task 1
API Task 2
```

The ALB target group contains the reachable task IPs.

Relationship:

```text
ECS Service
    ↓
Fargate Tasks
    ↓
Task Private IPs
    ↓
Target Group
    ↓
ALB
```

ECS handles target registration and deregistration when the service is configured with the load balancer.

---

# 21. What Happens When a User Sends a Request?

For example:

```text
POST /api/transcribe
```

Flow:

```text
1. User sends request.

2. ALB receives request.

3. Listener accepts HTTP/HTTPS traffic.

4. ALB checks the target group.

5. ALB selects a healthy ECS API target.

6. Request is forwarded to FastAPI :8000.

7. FastAPI processes the request.

8. FastAPI can communicate with internal services such as
   PostgreSQL, Redis, S3, and background workers.

9. FastAPI returns a response.

10. ALB sends the response back to the user.
```

---

# 22. ALB and Redis

The ALB does not send traffic directly to Redis.

Redis is an internal backend service.

Correct relationship:

```text
User
 ↓
ALB
 ↓
FastAPI
 ↓
Redis
```

Redis should remain private.

---

# 23. ALB and PostgreSQL

The ALB does not connect directly to PostgreSQL.

Correct relationship:

```text
User
 ↓
ALB
 ↓
FastAPI
 ↓
RDS PostgreSQL
```

The database remains private.

The API security group can communicate with the database security group on PostgreSQL's port, normally:

```text
5432
```

---

# 24. ALB and S3

The ALB does not act as an S3 gateway.

The FastAPI application can communicate with S3 through AWS APIs and IAM permissions.

Conceptually:

```text
User
 ↓
ALB
 ↓
FastAPI
 ↓
S3
```

---

# 25. ALB and ECR

The ALB does not pull Docker images from ECR.

ECR stores the container images.

ECS/Fargate pulls the image from ECR when starting a task.

```text
ECR
 ↓
ECS/Fargate
 ↓
Running API Container
 ↓
Target Group
 ↓
ALB
```

---

# 26. ALB and CloudWatch

CloudWatch can be used for monitoring and logging around the application.

For example:

```text
ECS
 ↓
Container logs
 ↓
CloudWatch Logs
```

CloudWatch helps investigate:

- Application errors
- Container startup failures
- Resource utilization
- Target health problems
- Request/traffic metrics

---

# 27. ALB and ACM

Later, LyricSync should use HTTPS with AWS Certificate Manager (ACM).

Production flow:

```text
User
 ↓
HTTPS :443
 ↓
ALB
 ↓
ACM Certificate
 ↓
Target Group
 ↓
ECS FastAPI
```

The TLS connection can terminate at the ALB. The backend can continue using HTTP inside the private VPC if that matches the project's security requirements.

---

# 28. ALB and Route 53

Later, Route 53 can provide the custom domain.

For example:

```text
api.example.com
       ↓
Route 53
       ↓
ALB
       ↓
ECS API
```

Users do not need to use the AWS-generated ALB DNS name.

---

# 29. ALB and CloudFront

CloudFront can later be introduced for appropriate frontend/static-content or API delivery requirements.

A possible production flow is:

```text
Users
  ↓
CloudFront
  ↓
ALB
  ↓
ECS API
```

CloudFront is not required just to make the ALB work.

---

# 30. What the ALB Does NOT Do

The ALB does not:

- Run Docker containers
- Store Docker images
- Store PostgreSQL data
- Run Redis
- Process AI jobs
- Store application files
- Replace ECS
- Replace security groups
- Replace route tables
- Replace the ECS task definition
- Replace ECR

Its primary responsibility is application traffic management.

---

# 31. ALB vs ECS Service

### ALB

```text
Receives traffic
       ↓
Checks targets
       ↓
Routes traffic
```

### ECS Service

```text
Maintains desired task count
       ↓
Starts/stops/replaces tasks
       ↓
Connects tasks to the load balancer
```

Together:

```text
ALB
 ↓
Target Group
 ↓
ECS Service
 ↓
Fargate API Tasks
```

---

# 32. ALB vs Target Group

### ALB

Actual load balancer:

```text
lyricsync-alb
```

### Listener

Waits for requests:

```text
HTTP :80
```

### Target Group

Defines backend targets:

```text
lyricsync-api-tg
```

### ECS Tasks

Actual application targets:

```text
FastAPI :8000
```

Therefore:

```text
ALB
 ↓
Listener
 ↓
Target Group
 ↓
Fargate Task
```

---

# 33. Failure Scenario

Suppose:

```text
API Task 1 → Healthy
API Task 2 → Healthy
```

Task 1 crashes.

ECS can detect the task failure and replace it according to the service configuration.

The target group/ALB should avoid sending normal traffic to an unhealthy target.

After the replacement becomes healthy:

```text
New Task
   ↓
Registered
   ↓
Health check passes
   ↓
Receives traffic
```

---

# 34. Scaling Scenario

Suppose traffic increases.

Initially:

```text
1 API Task
```

Auto Scaling can later increase the service to:

```text
3 API Tasks
```

The target group can contain:

```text
Task 1
Task 2
Task 3
```

The ALB can distribute requests among healthy targets.

The public endpoint remains the same.

---

# 35. Recommended Security Design

```text
Internet
   ↓
ALB :80/:443
   ↓
lyricsync-alb-sg
   ↓
ECS API :8000
   ↓
lyricsync-api-sg
   ↓
Internal services
```

Database and Redis should remain private.

Example:

```text
lyricsync-api-sg
       ↓
lyricsync-db-sg :5432

lyricsync-api-sg
       ↓
lyricsync-redis-sg :6379
```

Only required communication paths should be allowed.

---

# 36. Practical AWS Configuration

## ALB

```text
Name:
lyricsync-alb

Type:
Application Load Balancer

Scheme:
Internet-facing

VPC:
lyricsync-vpc

Subnets:
Public Subnet A
Public Subnet B

Security Group:
lyricsync-alb-sg
```

## Listener

```text
Protocol:
HTTP

Port:
80
```

Later:

```text
HTTPS
443
```

## Target Group

```text
Name:
lyricsync-api-tg

Target type:
IP addresses

Protocol:
HTTP

Port:
8000

VPC:
lyricsync-vpc
```

## Health Check

```text
Protocol:
HTTP

Path:
/health

Port:
Traffic port

Success code:
200
```

## ECS Integration

```text
ECS Service:
lyricsync-api-service

Container:
lyricsync-api

Container Port:
8000

Target Group:
lyricsync-api-tg
```

---

# 37. Final LyricSync Traffic Flow

```text
                    INTERNET
                       │
                       ▼
                Internet Gateway
                       │
                       ▼
              ┌─────────────────┐
              │   lyricsync     │
              │      ALB        │
              └────────┬────────┘
                       │
                  Listener
                   HTTP :80
                       │
                       ▼
              lyricsync-api-tg
               Target Group
                       │
              ┌────────┴────────┐
              ▼                 ▼
        Fargate Task 1     Fargate Task 2
        Private IP         Private IP
             │                  │
             ▼                  ▼
       FastAPI :8000      FastAPI :8000
```

The ALB does not decide "public subnet or private subnet" for every request.

Instead:

- The ALB is deployed across your selected public subnets.
- ECS tasks run in private subnets.
- The listener receives the request.
- The target group contains ECS task targets.
- Health checks determine which targets are healthy.
- The ALB forwards requests to healthy targets.
- Security groups control which connections are allowed.

---

# 38. Why ALB Is Important for LyricSync AI

The ALB is the bridge between the public Internet and the private application layer.

It allows LyricSync to move from:

```text
Local Docker
```

to:

```text
Internet
   ↓
AWS ALB
   ↓
ECS/Fargate
   ↓
FastAPI
```

while keeping the backend tasks private.

This is important because LyricSync AI processes application workloads such as video/audio uploads, transcription, lyric generation, and background processing.

The ALB provides the stable HTTP/HTTPS entry point while ECS manages the application containers.

---

# 39. Current AWS Progress

At this stage, the project has:

```text
01. IAM
02. VPC
03. Subnets
04. Internet Gateway
05. NAT Gateway
06. Route Tables
07. Security Groups
08. S3
09. ECR
10. ECS Cluster
11. ECS Task Definition
12. ECS Service
13. Application Load Balancer
```

Next planned services:

```text
14. RDS PostgreSQL
15. ElastiCache Redis
16. CloudFront
17. Route 53
18. ACM SSL
19. CloudWatch
20. Secrets Manager
21. Auto Scaling
22. GitHub Actions CI/CD
```

---

# 40. GitHub Security Notes

It is fine to document your ALB configuration in GitHub.

Avoid committing:

```text
AWS access keys
AWS secret access keys
Database passwords
Redis passwords
JWT secrets
API keys
Secrets Manager values
.env files containing secrets
Private credentials
Session tokens
```

Names such as:

```text
lyricsync-alb
lyricsync-api-tg
lyricsync-vpc
```

are resource identifiers, not credentials.

---

# 41. Final Definition

> **Application Load Balancer (ALB) is the public HTTP/HTTPS entry point of LyricSync AI. It receives user requests, uses listeners and target groups to process application traffic, performs health checks, and forwards requests to healthy ECS Fargate API tasks through an IP-based target group.**

Core flow:

```text
ALB
 ↓
Listener :80 / :443
 ↓
lyricsync-api-tg
 ↓
Healthy ECS Fargate API
 ↓
FastAPI :8000
```
