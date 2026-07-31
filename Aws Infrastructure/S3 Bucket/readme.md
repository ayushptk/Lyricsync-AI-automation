# Amazon S3 Configuration

## Project

**LyricSync AI SaaS**

---

# Overview

Amazon Simple Storage Service (Amazon S3) is the primary object storage service used by LyricSync AI to store all generated media assets.

Instead of storing large files inside the database, the application stores them in Amazon S3 while PostgreSQL stores only metadata such as file paths, job status, user information, and timestamps.

S3 provides highly durable, scalable, secure, and cost-effective storage that can grow from a few files to millions of generated karaoke videos without changing the application architecture.

---

# Why Amazon S3?

LyricSync AI generates multiple files during every AI processing job.

These files include:

- Original uploaded audio
- Instrumental track
- Vocal track
- Karaoke video (MP4)
- Subtitle files (SRT/LRC)
- Thumbnail images
- Background assets

These files can range from several megabytes to hundreds of megabytes, making them unsuitable for storage inside a relational database.

Amazon S3 is specifically designed for storing large binary objects efficiently.

---

# Why Not Store Files in PostgreSQL?

PostgreSQL is optimized for structured relational data.

Large media files increase:

- Database size
- Backup time
- Restore time
- Query performance
- Storage costs

Instead, LyricSync AI separates responsibilities.

### PostgreSQL stores

- Users
- Jobs
- Authentication
- Processing status
- Metadata
- File locations

### Amazon S3 stores

- MP4 videos
- MP3 audio
- Vocal tracks
- Instrumentals
- Subtitle files
- Images

This architecture follows AWS production best practices.

---

# How Amazon S3 Works

Amazon S3 stores data as **Objects** inside **Buckets**.

```
Bucket
│
├── Object 1
├── Object 2
├── Object 3
└── ...
```

Unlike traditional file systems, S3 does not actually have folders.

Folders displayed in the AWS Console are prefixes that help organize objects logically.

Example:

```
videos/video001.mp4
videos/video002.mp4
lyrics/song.srt
```

Here,

```
videos/
lyrics/
```

are prefixes rather than physical directories.

---

# S3 Bucket Structure

The LyricSync AI bucket is organized using prefixes for different asset types.

```
lyricsync-media-bucket
│
├── uploads/
├── videos/
├── vocals/
├── instrumentals/
├── lyrics/
└── thumbnails/
```

## uploads/

Stores original uploaded files before processing begins.

Examples

- Original audio
- Uploaded background images

---

## videos/

Stores the final rendered karaoke videos.

Examples

- karaoke.mp4

---

## vocals/

Stores separated vocal tracks generated using Demucs.

---

## instrumentals/

Stores instrumental versions after vocal separation.

---

## lyrics/

Stores subtitle files generated using Faster Whisper.

Supported formats

- SRT
- LRC

---



# Integration with FastAPI

FastAPI is responsible for:

- Creating processing jobs
- Generating upload requests
- Saving S3 object locations
- Returning download URLs
- Serving API responses


# Integration with Celery Workers

Celery performs all AI processing.

After the video is rendered, Celery uploads the generated files directly to Amazon S3.


# Security Configuration

The S3 bucket follows AWS security best practices.

## Block Public Access

All Block Public Access settings are enabled.

This prevents accidental exposure of user-generated files.

---

## Object Ownership

ACLs are disabled.

Bucket Owner Enforced is enabled.

IAM controls access instead of Access Control Lists.

---

## Server-Side Encryption

Default encryption is enabled using Amazon S3 managed keys (SSE-S3).

Every uploaded object is encrypted automatically while stored.

---

## Versioning

Bucket Versioning is enabled.

Benefits include:

- Recover deleted files
- Restore previous versions
- Protect against accidental overwrites

---

## IAM Access Control

The bucket is private.

Only authorized AWS services can access it.

Later in the project, ECS Task Roles will receive permissions to:

- Upload objects
- Download objects
- Delete objects

No long-term AWS credentials are stored inside the application.

---

## Presigned URLs

Generated media is never publicly exposed.

Instead, FastAPI generates temporary presigned URLs that allow users to download their files securely.



# Storage Class

Current storage class:

- Standard

Future optimization:

- Intelligent-Tiering
- Glacier Instant Retrieval
- Glacier Flexible Retrieval

Older karaoke projects can automatically move to cheaper storage using Lifecycle Rules.

---

# High Availability

Amazon S3 automatically replicates data across multiple Availability Zones within the selected AWS Region.

Benefits include:

- High durability
- High availability
- Fault tolerance

No manual replication setup is required.

---

# Benefits for LyricSync AI

Using Amazon S3 provides several advantages:

- Unlimited object storage
- Highly durable media storage
- Secure private bucket
- Automatic encryption
- Version history
- Cost-effective scaling
- Easy integration with FastAPI
- Easy integration with ECS and Celery
- Reliable storage for generated AI assets
- Production-ready architecture


# Screenshots

![Bucket Overview](./S3%20Bucket.png)


