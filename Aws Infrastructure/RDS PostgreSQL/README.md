# RDS PostgreSQL — LyricSync AI

## 1. What is RDS PostgreSQL?

Amazon RDS for PostgreSQL is the managed relational database used by LyricSync AI for production data.

Instead of running PostgreSQL inside Docker in AWS:

    ECS
    └── PostgreSQL container

LyricSync uses:

    ECS/Fargate
        ↓
    FastAPI
        ↓
    Amazon RDS PostgreSQL

RDS keeps important application data persistent even when ECS tasks are replaced.

---

## 2. Why LyricSync AI needs RDS

LyricSync is a stateful application. It needs to remember:

- Users
- User profiles
- Processing jobs
- Job status
- Transcription metadata
- Generated lyric metadata
- File/object references
- Processing history
- Application records
- Subscription/billing records if implemented

Example:

    job_id: 1007
    user_id: 42
    status: processing
    s3_key: uploads/job-1007/video.mp4

If an ECS task crashes, this information must not disappear.

That is why PostgreSQL is separated from ECS.

---

## 3. Why RDS instead of PostgreSQL in ECS?

ECS is for application compute.

RDS is for persistent database infrastructure.

Running PostgreSQL yourself would require you to manage much more of the database infrastructure, including storage, backups, recovery, maintenance, upgrades, and availability.

RDS provides managed PostgreSQL infrastructure and features such as:

- Automated backups
- DB snapshots
- Point-in-time recovery
- Encryption
- Monitoring
- Maintenance options
- Multi-AZ deployment options

Therefore:

    ECS → runs application
    RDS → stores persistent relational data

---

# 4. Local vs AWS Architecture

## Local development

Your Docker Compose environment can be:

    Docker Compose
    ├── FastAPI
    ├── Celery Worker
    ├── Redis
    └── PostgreSQL

## AWS

The production environment becomes:

    ECS/Fargate
    ├── FastAPI
    └── Celery Worker

    ElastiCache
    └── Redis

    RDS
    └── PostgreSQL

    S3
    └── Media/files

The PostgreSQL Docker container is therefore normally used for local development, while RDS is used for AWS production.

---

# 5. What RDS stores

RDS stores structured relational application data.

Possible LyricSync tables include:

## users

    id
    email
    name
    created_at

## jobs

    id
    user_id
    status
    created_at
    completed_at

## media_files

    id
    job_id
    s3_key
    file_type
    file_size

## transcriptions

    id
    job_id
    language
    model
    status

## lyrics

    id
    job_id
    language
    status
    s3_key

The exact schema depends on the database models already present in the LyricSync codebase.

---

# 6. What should NOT be stored in PostgreSQL?

Large video/audio/media files should normally be stored in S3 rather than PostgreSQL.

Example:

    S3
    └── uploads/job-1007/video.mp4

    RDS
    └── job_id = 1007
        s3_key = uploads/job-1007/video.mp4

So:

    RDS = structured metadata
    S3  = large objects/files

---

# 7. RDS + S3

A LyricSync upload can work like this:

    User
      ↓
    FastAPI
      ↓
    S3
      ↓
    video/audio stored

PostgreSQL stores:

    job_id
    user_id
    s3_key
    status
    timestamps

This keeps database storage focused on relational data.

---

# 8. RDS + Redis

PostgreSQL and Redis have different responsibilities.

## PostgreSQL

Persistent relational data:

    Users
    Jobs
    Metadata
    History
    Relationships

## Redis

Fast in-memory workloads such as:

    Caching
    Temporary state
    Queue/broker workloads
    Fast lookups
    Celery-related infrastructure

Typical application relationship:

    FastAPI
       ├──→ RDS PostgreSQL
       └──→ Redis

---

# 9. RDS + ECS

ECS runs FastAPI.

RDS stores its persistent data.

    ECS Fargate
         │
         │ database connection
         ▼
    RDS PostgreSQL

If ECS replaces a task:

    Old ECS Task
         ↓
       stopped

    New ECS Task
         ↓
    same RDS database

The application data remains available.

---

# 10. RDS + Celery Worker

A LyricSync processing workflow can be:

    User
      ↓
    FastAPI
      ↓
    Create job
      ↓
    RDS
      ↓
    Queue
      ↓
    Celery Worker
      ↓
    AI processing
      ↓
    Update RDS

Example job states:

    queued
       ↓
    processing
       ↓
    completed

Or:

    queued
       ↓
    processing
       ↓
    failed

This allows the frontend to request job status through FastAPI.

---

# 11. RDS does NOT run AI processing

RDS does not run:

- Whisper
- Video processing
- Audio separation
- Vocal extraction
- Lyric generation
- GPU inference

Those workloads belong to your compute/worker layer.

A worker can:

    Process media
       ↓
    Save result to S3
       ↓
    Update job status in RDS

---

# 12. RDS Networking

RDS should use the same VPC as your application.

Example:

    VPC
    lyricsync-vpc-vpc
    CIDR: 10.0.0.0/16

Your architecture:

    Public Subnets
        └── ALB

    Private Application Subnets
        └── ECS

    Private DB Subnets
        └── RDS

RDS should not be placed in the public ALB subnets.

---

# 13. DB Subnet Group

RDS uses a DB subnet group to identify database subnets.

Example:

    lyricsync-db-subnet-group

    eu-north-1a
      └── Private DB Subnet A

    eu-north-1b
      └── Private DB Subnet B

A DB subnet group should span at least two Availability Zones.

This provides the network foundation for RDS deployment and Multi-AZ configurations.

---

# 14. RDS Public Access

For LyricSync production:

    Public access = No

The database should remain private.

Correct:

    Internet
       ↓
    ALB
       ↓
    ECS FastAPI
       ↓
    RDS PostgreSQL

Incorrect:

    Internet
       ↓
    RDS PostgreSQL

Users should never need direct database access.

---

# 15. RDS Security Group

LyricSync uses:

    lyricsync-db-sg

Inbound rule:

    Type: PostgreSQL
    Protocol: TCP
    Port: 5432
    Source: lyricsync-api-sg

Conceptually:

    lyricsync-api-sg
           │
           │ TCP 5432
           ▼
    lyricsync-db-sg
           │
           ▼
    RDS PostgreSQL

Do NOT use:

    0.0.0.0/0 → TCP 5432

for the production database.

Using the ECS security group as the source means changing Fargate task IP addresses does not require manually changing the database rule.

---

# 16. PostgreSQL Port

PostgreSQL normally uses:

    TCP 5432

Your LyricSync connections are therefore:

    ALB → ECS
         TCP 8000

    ECS → RDS
         TCP 5432

    ECS/Worker → Redis
         TCP 6379

These are different connections.

---

# 17. RDS Endpoint

RDS provides a DNS endpoint similar to:

    lyricsync-postgres.xxxxxxxxx.eu-north-1.rds.amazonaws.com

FastAPI uses this endpoint instead of a hard-coded database IP.

Example configuration:

    DATABASE_HOST=lyricsync-postgres.xxxxxxxxx.eu-north-1.rds.amazonaws.com
    DATABASE_PORT=5432
    DATABASE_NAME=lyricsync

The actual endpoint comes from your RDS console.

---

# 18. Database URL

Depending on your Python PostgreSQL driver, the application may use a URL such as:

    postgresql+psycopg://USER:PASSWORD@RDS_ENDPOINT:5432/lyricsync

Do not commit a real password or complete production DATABASE_URL to GitHub.

---

# 19. Secrets Manager

Database credentials should be stored securely.

Recommended production design:

    AWS Secrets Manager
            ↓
        ECS Task
            ↓
       DATABASE_URL
            ↓
      RDS PostgreSQL

Do not put database passwords in:

- GitHub
- Dockerfile
- source code
- public README files
- frontend code

This is why AWS Secrets Manager is part of the LyricSync deployment roadmap.

---

# 20. Encryption

Enable RDS encryption for production.

Encryption protects supported RDS data at rest, including database storage and backups/snapshots.

Think about security in layers:

    Network security
         +
    Encryption at rest
         +
    Secure credentials
         +
    Backups

---

# 21. Backups

RDS automated backups are important because PostgreSQL contains valuable application state.

Backups can support recovery and point-in-time restoration according to the configured retention period.

For production, also consider:

- Automated backups
- Manual snapshots before major changes
- Appropriate retention
- Deletion protection

---

# 22. Single-AZ vs Multi-AZ

For a low-cost first deployment:

    Single-AZ

can be reasonable.

For stronger production availability:

    Multi-AZ

can provide a standby/failover architecture.

A Multi-AZ DB instance deployment maintains a standby in another Availability Zone for failover. Newer RDS Multi-AZ DB cluster configurations can provide a writer and two readers across three Availability Zones.

Choose based on your availability requirements and budget.

---

# 23. RDS Read Replicas

Read replicas are different from Multi-AZ standby deployments.

A read replica can help scale read workloads:

    Primary
       │
       └── replication → Read Replica

You probably do not need a read replica for the initial LyricSync deployment.

Consider it only when database read traffic actually requires it.

---

# 24. RDS and CloudWatch

RDS integrates with CloudWatch for monitoring.

You can monitor metrics such as:

- CPU utilization
- Database connections
- Storage
- Network activity
- Performance-related metrics

Monitoring helps determine whether PostgreSQL is becoming a bottleneck.

---

# 25. Database Migrations

Creating an RDS instance does NOT automatically create your application's tables.

If your project uses Alembic, the normal flow is:

    RDS created
        ↓
    Database created
        ↓
    ECS/application connects
        ↓
    Alembic migration
        ↓
    Tables created/updated

Example:

    alembic upgrade head

Run migrations according to your project's deployment process.

Do not manually recreate every application table through the RDS console when the project already has migrations.

---

# 26. Example: Creating a LyricSync Job

User submits a video.

FastAPI creates:

    job_id = 1007
    user_id = 42
    status = queued

RDS stores the job.

The worker then changes it to:

    status = processing

After successful processing:

    status = completed

If processing fails:

    status = failed

The frontend can call FastAPI to retrieve the current status.

---

# 27. Example: Complete Processing Flow

    User
      ↓
    ALB
      ↓
    FastAPI
      ↓
    Create job in RDS
      ↓
    Store/reference media in S3
      ↓
    Queue processing
      ↓
    Celery Worker
      ↓
    AI processing
      ↓
    Generated files → S3
      ↓
    Update job → RDS
      ↓
    FastAPI reads result
      ↓
    ALB
      ↓
    User

RDS is responsible for the persistent application state in this workflow.

---

# 28. What happens when an ECS task crashes?

Suppose:

    FastAPI Task 1
        ↓
       crash

ECS can replace it:

    FastAPI Task 2
        ↓
    same RDS endpoint

The database records remain because RDS is independent of the ECS task lifecycle.

This is one of the most important architectural reasons for using RDS.

---

# 29. RDS vs Other AWS Services

## RDS vs ECS

    ECS → runs containers
    RDS → stores relational data

## RDS vs ECR

    ECR → stores Docker images
    RDS → stores PostgreSQL data

## RDS vs S3

    S3 → stores files/objects
    RDS → stores structured metadata

## RDS vs Redis

    Redis → fast cache/temporary/queue-related workloads
    RDS → persistent relational data

## RDS vs ALB

    ALB → receives and routes HTTP/HTTPS traffic
    RDS → stores database data

---

# 30. Complete LyricSync AWS Data Architecture

    INTERNET
       │
       ▼
    Application Load Balancer
       │
       ▼
    ECS/Fargate FastAPI
       │
       ├──────────→ S3
       │             └── Videos/audio/results
       │
       ├──────────→ ElastiCache Redis
       │
       └──────────→ RDS PostgreSQL
                     └── Users/jobs/metadata

    ECS Worker
       ├──────────→ S3
       ├──────────→ Redis
       └──────────→ RDS

The exact worker connections depend on the Celery configuration in your project.

---

# 31. Recommended LyricSync RDS Configuration

    Engine:
    PostgreSQL

    VPC:
    lyricsync-vpc-vpc

    DB identifier:
    lyricsync-postgres

    Database:
    lyricsync

    DB subnet group:
    lyricsync-db-subnet-group

    Subnets:
    Private DB subnets

    Public access:
    No

    Port:
    5432

    Security group:
    lyricsync-db-sg

    Encryption:
    Enabled

    Backups:
    Enabled

    Multi-AZ:
    Based on budget/availability requirements

---

# 32. RDS Security Rules

1. Keep RDS private.
2. Do not allow 5432 from 0.0.0.0/0.
3. Allow access from the ECS API security group.
4. Use a dedicated DB security group.
5. Use private DB subnets.
6. Enable encryption.
7. Enable backups.
8. Protect production credentials with Secrets Manager.
9. Never commit database passwords to GitHub.
10. Use database migrations for schema changes.

---

# 33. What RDS Does NOT Do

RDS does not:

- Run FastAPI
- Run Docker
- Run ECS containers
- Run Celery
- Run Whisper
- Process videos
- Generate lyrics
- Store Docker images
- Replace ECR
- Replace S3
- Replace Redis
- Replace ALB

Its main responsibility is:

    Persistent relational PostgreSQL data

---

# 34. Final Mental Model

Remember the main AWS services this way:

    ECR
      ↓
    Stores Docker images

    ECS
      ↓
    Runs Docker containers

    ALB
      ↓
    Receives user HTTP/HTTPS traffic

    RDS
      ↓
    Stores persistent PostgreSQL data

    S3
      ↓
    Stores files/objects

    ElastiCache Redis
      ↓
    Fast cache/temporary/queue-related workloads

For LyricSync:

    User
      ↓
    ALB
      ↓
    ECS FastAPI
      ├────────→ RDS PostgreSQL
      ├────────→ Redis
      └────────→ S3

This separation is the foundation of the AWS production architecture.

---

# 35. One-Sentence Definition

**Amazon RDS PostgreSQL is the managed persistent relational database for LyricSync AI. ECS/FastAPI and workers use it to store users, jobs, processing states, metadata, and other structured application data, while S3 stores large media objects and Redis handles fast temporary/cache/queue-related workloads.**
