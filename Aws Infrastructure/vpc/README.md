# Amazon VPC Configuration

![VPC](./vpcresourcesmap.png)

## Project

**LyricSync AI SaaS**

---

# Overview

Amazon Virtual Private Cloud (VPC) is a logically isolated virtual network inside AWS where all cloud resources for the LyricSync AI application are deployed.

Instead of placing servers directly on the public internet, the VPC provides a secure networking environment where resources can communicate with each other while controlling inbound and outbound network traffic.

The VPC acts as the networking foundation for the entire AWS infrastructure.

---

# Why LyricSync AI Uses a VPC

LyricSync AI is an AI-powered SaaS application that downloads YouTube audio, performs AI vocal separation, transcribes lyrics, renders karaoke videos, and stores generated media files.

Since the application processes user data and runs multiple backend services, a secure and isolated network is required.

Amazon VPC provides:

- Network isolation
- Secure communication between AWS services
- High availability
- Traffic control
- Scalable infrastructure
- Secure database connectivity
- Protection of backend resources

Without a VPC, the application's backend services would be directly exposed to the internet, increasing security risks.


# Resources Created

## Amazon VPC

Created an isolated virtual network named **lyricsync-vpc**.

Purpose

- Host all AWS resources
- Provide secure networking
- Centralize infrastructure

---

## Public Subnets

Two public subnets were created across different Availability Zones.

Purpose

- Host internet-facing resources
- Future Application Load Balancer
- Future NAT Gateway

Characteristics

- Internet accessible
- Connected through the Internet Gateway
- High availability

---

## Private Subnets

Two private subnets were created across different Availability Zones.

Purpose

These subnets will host internal application components that should never be directly accessible from the internet.

Future services include

- FastAPI Backend
- Celery Workers
- Amazon RDS PostgreSQL
- Amazon ElastiCache Redis

Characteristics

- No direct internet access
- Higher security
- Internal communication only

---

## Internet Gateway

An Internet Gateway was attached to the VPC.

Purpose

Allows internet traffic to reach resources deployed inside public subnets.

Without the Internet Gateway:

- Users cannot access the application
- Public resources cannot communicate with the internet

---

## Route Tables

Separate route tables manage network traffic inside the VPC.

Public Route Table

Routes internet traffic through the Internet Gateway.

Private Route Tables

Used for private resources that should not be publicly accessible.

---

## Amazon S3 Gateway Endpoint

An Amazon S3 Gateway Endpoint was created.

Purpose

Allows AWS resources inside the VPC to securely communicate with Amazon S3 without sending traffic over the public internet.

Benefits

- Improved security
- Lower latency
- Reduced networking costs
- Private AWS network communication

---

# High Availability

The infrastructure is distributed across two Availability Zones.

Availability Zones

- eu-north-1a
- eu-north-1b

Benefits

- Fault tolerance
- Increased reliability
- Improved application availability

If one Availability Zone experiences an outage, services can continue operating in the second Availability Zone.

---

# Security Benefits

The VPC improves the security of LyricSync AI by:

- Isolating application resources
- Separating public and private workloads
- Preventing direct access to backend services
- Restricting network communication
- Preparing the infrastructure for Security Groups and Network ACLs

---

# Future AWS Integration

The following services will be deployed inside this VPC during later phases of the project.

| AWS Service | Purpose |
|-------------|---------|
| Amazon ECS | Host FastAPI Backend |
| Amazon ECS | Host Celery Workers |
| Amazon RDS PostgreSQL | Application Database |
| Amazon ElastiCache | Redis Queue |
| Application Load Balancer | Receive HTTPS Requests |
| CloudWatch | Monitoring |
| Secrets Manager | Secure credentials |

---

