# LyricSync AWS CloudFront Setup

## 1. What is CloudFront?

Amazon CloudFront is AWS's Content Delivery Network (CDN).

A CDN places an edge layer between users and your application. Instead of every request going directly to your Application Load Balancer (ALB), CloudFront receives the request first and then forwards it to the configured origin.

For the current LyricSync architecture, the main origin is the existing Application Load Balancer.

```text
                    INTERNET
                       |
                       v
                +--------------+
                |  CloudFront  |
                |     CDN      |
                +--------------+
                       |
                       v
                +--------------+
                |     ALB      |
                +--------------+
                       |
                       v
                +--------------+
                | ECS Fargate  |
                | LyricSync API|
                +--------------+
                   |        |
                   v        v
                PostgreSQL  ElastiCache
                  RDS          Valkey/Redis
```

---

# 2. Why does LyricSync need CloudFront?

CloudFront is not required for the basic application to run.

Without CloudFront:

```text
User
  |
  v
ALB
  |
  v
ECS
```

The application can work this way.

CloudFront becomes useful when LyricSync is exposed to real Internet traffic.

## Main reasons

### 2.1 Lower latency

CloudFront has edge locations around the world.

A user can connect to a nearby CloudFront edge location instead of directly reaching the AWS application origin.

This can improve the delivery of cacheable/static content.

### 2.2 HTTPS / secure public entry point

CloudFront can work with AWS Certificate Manager (ACM) certificates so the public application can use HTTPS.

Typical production architecture:

```text
https://lyricsync.example.com
          |
          v
      CloudFront
          |
          v
         ALB
          |
          v
         ECS
```

### 2.3 Reduce unnecessary origin traffic

CloudFront can cache appropriate static responses.

For example:

```text
Next.js static asset
        |
        v
    CloudFront
        |
        +---- cache hit ---> User
        |
        +---- cache miss --> ALB/ECS
```

For dynamic API operations, however, caching should generally be disabled.

### 2.4 Security layer

CloudFront can be integrated with AWS WAF and other AWS security controls.

This gives LyricSync a better production edge architecture than exposing the application directly to the Internet.

### 2.5 Scalability

As traffic increases:

```text
Many users
    |
    v
CloudFront
    |
    v
ALB
    |
    v
ECS service
```

The ALB and ECS service can handle the application traffic while CloudFront handles the edge layer.

---

# 3. What CloudFront does NOT do

This is extremely important.

CloudFront does NOT replace:

- ECS
- FastAPI
- PostgreSQL
- ElastiCache/Valkey
- Celery
- FFmpeg
- Demucs
- Faster-Whisper
- yt-dlp

Your AI/video-processing pipeline still runs on ECS/worker infrastructure.

CloudFront is primarily the Internet-facing delivery layer.

---

# 4. Why not use an S3 bucket for this CloudFront origin?

During CloudFront creation AWS gives several origin choices.

One of them is:

```text
Amazon S3
```

S3 is excellent for static content:

```text
S3
 |
 +-- images
 +-- CSS
 +-- JavaScript
 +-- static HTML
 +-- static assets
```

But S3 cannot run the LyricSync FastAPI application.

Your backend performs operations such as:

```text
YouTube URL
   |
   v
FastAPI
   |
   +--> yt-dlp
   |
   +--> Demucs
   |
   +--> Faster-Whisper
   |
   +--> FFmpeg
   |
   v
Karaoke video
```

Therefore, S3 cannot replace ECS.


# 5. What is the CloudFront origin?

The origin is the place CloudFront retrieves content from.

For LyricSync:

```text
CloudFront
    |
    v
Application Load Balancer
    |
    v
ECS Fargate
    |
    v
FastAPI
```

The ALB is the CloudFront origin.

The user should NOT directly connect to ECS task IP addresses.

---

# 6. Why use ALB instead of directly exposing ECS?

ECS tasks are managed dynamically.

A task can be:

- started
- stopped
- replaced
- scaled
- assigned a different private IP

The ALB provides a stable application entry point and distributes traffic to healthy ECS tasks.

Architecture:

```text
                 ALB
                  |
          +-------+-------+
          |               |
          v               v
       ECS Task 1      ECS Task 2
          |               |
          +-------+-------+
                  |
               FastAPI
```

CloudFront therefore talks to the ALB, not individual ECS tasks.

---

# 7. Current LyricSync AWS architecture

The intended production architecture is:

```text
                           INTERNET
                              |
                              v
                       +-------------+
                       | CloudFront  |
                       +-------------+
                              |
                              v
                       +-------------+
                       |     ALB     |
                       +-------------+
                              |
                       Target Group
                              |
                              v
                    +------------------+
                    |   ECS Fargate    |
                    | LyricSync API    |
                    +------------------+
                       |            |
                       |            |
                       v            v
                PostgreSQL       Valkey/Redis
                   RDS            ElastiCache
                       |
                       v
                  Application data
```

Other services:

```text
ECR
 |
 +--> stores Docker images
 |
 v
ECS
```

```text
CloudWatch
 |
 +--> ECS logs
 +--> application monitoring
```

```text
Secrets Manager
 |
 +--> database credentials
 +--> application secrets
 +--> API keys
```

---

# 8. CloudFront distribution name

Recommended name:

```text
lyricsync-cloudfront
```

This name is primarily a resource tag/name.

It does NOT automatically become your website domain.

CloudFront will initially provide an AWS CloudFront domain similar to:

```text
xxxxxxxxxxxx.cloudfront.net
```

Later you can connect a custom domain through:

```text
Route 53
   |
   v
ACM certificate
   |
   v
CloudFront
```

Example:

```text
lyricsync.example.com
        |
        v
   CloudFront
```

You do not need to purchase a domain just to create/test the CloudFront distribution.

---

# 9. Distribution type

When AWS asks:

```text
Distribution type
```

Choose:

```text
Single website or app
```

## Why?

The current LyricSync deployment is being treated as one application.

The multi-tenant option is designed for architectures where multiple customer domains/tenants need to share a specialized CloudFront configuration.

That is not necessary for the current deployment.

---

# 10. Origin configuration

For the current LyricSync application:

```text
Origin type:
Elastic Load Balancer
```

Select the existing Application Load Balancer created for LyricSync.

Do NOT select:

```text
S3
```

unless you are specifically creating a separate CloudFront distribution for a static S3-hosted frontend/assets.

Do NOT select API Gateway because LyricSync's FastAPI application is running behind ECS/ALB, not API Gateway.

---

# 11. Origin protocol

If the ALB has HTTPS configured:

```text
HTTPS only
```

is preferred.

Production flow:

```text
User
 |
 | HTTPS
 v
CloudFront
 |
 | HTTPS
 v
ALB
 |
 v
ECS
```

This keeps the connection encrypted from CloudFront to the ALB.

If the ALB currently only supports HTTP, do not blindly select HTTPS. First configure an HTTPS listener and ACM certificate on the ALB.

---

# 12. Very important: CloudFront caching

LyricSync has dynamic API operations.

Examples:

```text
POST /generate
POST /upload
GET /status/{job_id}
GET /download/{job_id}
```

These should not be treated like simple public static files.

For dynamic API behavior, the recommended approach is generally:

```text
Caching:
Disabled
```

for the API behavior.

Otherwise CloudFront could potentially cache a response that should have been generated dynamically.

---

# 13. HTTP methods

Because LyricSync has API operations such as POST requests, CloudFront must support more than GET/HEAD for the API behavior.

For API traffic, configure the allowed methods to support the methods your application actually uses, commonly:

```text
GET
HEAD
OPTIONS
PUT
POST
PATCH
DELETE
```

If your application only needs a subset, using only the required methods is preferable.

The exact CloudFront screen should be checked before selecting the final option.

---

# 14. API caching example

For an API path such as:

```text
/api/*
```

a good starting design is:

```text
Path:
 /api/*

Origin:
 LyricSync ALB

Caching:
 Disabled

Methods:
 Required API methods

Forward:
 Required headers/query strings/cookies
```

This prevents CloudFront from treating API responses like static assets.

---

# 15. Static asset caching

Static assets can benefit from CloudFront caching.

Examples:

```text
/_next/static/*
/images/*
/assets/*
```

These assets are generally much safer to cache than dynamic API responses.

Ideal architecture:

```text
                    CloudFront
                    /        \
                   /          \
                  v            v
          Static assets       API
               |               |
               v               v
             cache            ALB
                               |
                               v
                              ECS
```

The exact path behavior depends on how the Next.js application is deployed.

---

# 16. Next.js consideration

LyricSync uses Next.js for the frontend.

If Next.js is running inside ECS behind the ALB:

```text
CloudFront
    |
    v
ALB
    |
    +--> Next.js container
    |
    +--> FastAPI container/service
```

CloudFront can sit in front of the ALB.

If the frontend is instead deployed as a static site in S3, the architecture can be:

```text
                    CloudFront
                    /        \
                   /          \
                  v            v
                 S3           ALB
                  |             |
             Frontend          ECS
                               |
                              FastAPI
```

This is a separate design decision.

Do not move the frontend to S3 just because CloudFront offers an S3 origin.

---

# 17. Security model

The important security principle for LyricSync is:

```text
Internet
   |
   v
CloudFront / ALB
   |
   v
ECS
   |
   +----> RDS PostgreSQL
   |
   +----> ElastiCache/Valkey
```

Do NOT design:

```text
Internet
   |
   v
RDS
```

RDS should remain private.

Likewise, ElastiCache/Valkey should not be publicly accessible.

---

# 18. Security Groups

The intended security group relationship is:

```text
CloudFront
    |
    v
ALB Security Group
    |
    v
ECS Security Group
    |
    +----> RDS Security Group
    |
    +----> ElastiCache Security Group
```

Conceptually:

```text
ALB SG
  |
  +--> allows traffic to ECS SG

ECS SG
  |
  +--> allows PostgreSQL to RDS SG
  |
  +--> allows Redis/Valkey to ElastiCache SG
```

Do not open database ports to:

```text
0.0.0.0/0
```

unless there is an exceptional, carefully reviewed reason.

---

# 19. CloudFront + ALB vs CloudFront + S3

## Option A — Current application

```text
CloudFront
    |
    v
ALB
    |
    v
ECS
```

Best when serving:

- FastAPI
- dynamic application
- Next.js server
- API endpoints
- authenticated requests

## Option B — Static frontend

```text
CloudFront
    |
    v
S3
```

Best when serving:

- static HTML
- CSS
- JavaScript
- images
- static Next.js export

## Option C — Combined architecture

```text
                 CloudFront
                 /        \
                /          \
               v            v
              S3           ALB
               |             |
          static files       ECS
                             |
                           FastAPI
```

This can be a more advanced production architecture.

---

# 20. What happens when a user generates a karaoke video?

CloudFront does NOT perform the AI/video generation.

The flow remains:

```text
User
 |
 | YouTube URL
 v
CloudFront
 |
 v
ALB
 |
 v
FastAPI
 |
 v
Create background job
 |
 v
Celery Worker
 |
 +--> yt-dlp
 |
 +--> Demucs
 |
 +--> Faster-Whisper
 |
 +--> FFmpeg
 |
 v
Generated karaoke video
```

CloudFront only sits at the application delivery edge.

---

# 21. Where should generated videos be stored?

For a production SaaS, generated files are better suited to object storage such as S3 rather than keeping large files permanently inside ECS containers.

Possible architecture:

```text
Celery Worker
     |
     v
Generate MP4
     |
     v
S3
     |
     v
CloudFront
     |
     v
User downloads/streams video
```

This is a future improvement if your current LyricSync implementation does not already use S3 for generated videos.

---

# 22. Cost considerations

CloudFront is usage-based.

Costs depend on things such as:

- data transferred
- requests
- cache behavior
- geographic usage
- additional CloudFront features

Creating the distribution itself is not the same as having unlimited free usage.

Also remember:

```text
CloudFront cost
+
ALB cost
+
ECS cost
+
RDS cost
+
ElastiCache/Valkey cost
+
NAT Gateway cost
+
S3 cost
+
ECR cost
+
CloudWatch cost
```

Therefore, do not enable every optional feature just because it appears in the CloudFront wizard.

For your learning/project deployment, use the simplest configuration that satisfies the architecture.

---

# 23. CloudFront deployment can take time

After creating a distribution, AWS needs to deploy the configuration globally.

The distribution may initially show a deployment status such as:

```text
Deploying
```

Wait until it becomes:

```text
Enabled
```

before assuming the final configuration is ready.



