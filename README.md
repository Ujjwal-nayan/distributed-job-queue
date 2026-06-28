<div align="center">

# Distributed Job Queue

*A production-grade distributed job queue built from scratch — no Celery, no BullMQ.*

**FastAPI · Redis Streams · PostgreSQL · asyncio**

<p>
  <img src="https://skillicons.dev/icons?i=python,fastapi,postgres,redis,docker" />
</p>

<p>
  <img src="https://img.shields.io/badge/asyncio-Native-blueviolet?style=for-the-badge">
  <img src="https://img.shields.io/badge/Redis-Streams-red?style=for-the-badge">
  <img src="https://img.shields.io/badge/Chaos_Tested-zero_data_loss-success?style=for-the-badge">
</p>

</div>

---

## Dashboard

Real-time monitoring of queue activity, worker health, retries, and the Dead Letter Queue.

<p align="center">
  <img src="dashboard.png" width="1000"/>
</p>

---

## Architecture

Jobs are persisted in PostgreSQL before being dispatched via Redis Streams. Workers process jobs using Consumer Groups. A Reaper detects crashed workers via heartbeats and automatically recovers orphaned jobs.

<p align="center">
  <img src="architecture.png" width="1000"/>
</p>

---

## Features

|                                        |                                               |
| -------------------------------------- | --------------------------------------------- |
| **Redis Streams + Consumer Groups**    | Reliable job dispatch without polling         |
| **PostgreSQL Persistence**             | Source of truth with complete job history     |
| **Atomic Job Claiming**                | Prevents duplicate execution across workers   |
| **Exponential Backoff**                | Automatic retries after 2s, 4s, and 8s        |
| **Dead Letter Queue**                  | Failed jobs retained after max retries        |
| **Idempotency Keys**                   | Duplicate requests safely rejected (409)      |
| **Worker Heartbeats**                  | Detects crashed workers every 5s              |
| **Reaper Process**                     | Re-queues abandoned jobs automatically        |
| **Streamlit Dashboard**                | Live monitoring and DLQ management            |
| **Chaos Tested**                       | Redis and worker failures with zero data loss |

---

## Tech Stack

| Category             | Technology                      |
| -------------------- | ------------------------------- |
| **Language**         | Python 3.10+                    |
| **API**              | FastAPI                         |
| **Concurrency**      | asyncio                         |
| **Queue**            | Redis Streams + Consumer Groups |
| **Database**         | PostgreSQL                      |
| **Migrations**       | Alembic                         |
| **Dashboard**        | Streamlit                       |
| **Containerization** | Docker & Docker Compose         |

---

## Quick Start

### Prerequisites

Docker, Python 3.10+

### 1. Clone the repository

```bash
git clone https://github.com/Ujjwal-nayan/distributed-job-queue.git
cd distributed-job-queue
```

### 2. Start Redis & PostgreSQL

```bash
docker compose up -d
```

### 3. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
alembic upgrade head
```

### 5. Run the services

Open four terminals (with the virtual environment activated in each).

```bash
# API server
uvicorn main:app --reload

# Worker
python worker.py

# Reaper
python reaper.py

# Dashboard
streamlit run dashboard.py
```

**Optional env vars:**
- `WORKER_NAME` — unique name per worker instance (default: `worker-1`)
- `STUCK_JOB_THRESHOLD` — seconds before reaper considers a job stuck (default: `30`)

---

## API

### Health Check

```bash
curl http://localhost:8000/health
```

### Create a Job

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"task": "review_pr", "repo": "my-repo"}}'
```

### Create a Job with Idempotency Key

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"task": "review_pr"}, "idempotency_key": "pr-42-review"}'
```

### Check Job Status

```bash
curl http://localhost:8000/jobs/{job_id}
```

**Job lifecycle:**

```
pending → running → completed
                 → failed
```

---

## Chaos Engineering

Simulates Redis failure and worker crash mid-execution to prove zero data loss:

```bash
./chaos_test.sh
```

Expected output:
```
Job 1 final status: completed
Job 2 final status: completed
```

---

## Design Decisions

- **Postgres is the source of truth** — jobs persisted to PostgreSQL before Redis dispatch. Redis goes down, no data lost.
- **Atomic claiming** — `UPDATE ... WHERE status = 'pending'` with `rowcount` check prevents race conditions.
- **Reaper checks heartbeats** — only re-queues jobs whose workers have stale heartbeats. Active long-running jobs left alone.
- **ACK even on skip** — Redis messages acknowledged even for skipped jobs, preventing infinite redelivery.
- **Idempotency at two layers** — Redis `SET NX` for fast detection, PostgreSQL `UNIQUE` constraint as final guard.

---

## Project Structure

```
├── main.py              # FastAPI server
├── worker.py            # Async worker
├── reaper.py            # Stuck job recovery
├── dashboard.py         # Streamlit monitoring dashboard
├── database.py          # PostgreSQL & Redis connections
├── models.py            # Job model
├── chaos_test.sh        # Chaos engineering test
├── migrations/          # Alembic migrations
├── docker-compose.yml   # Redis + PostgreSQL
├── requirements.txt
├── dashboard.png
├── architecture.png
└── README.md
```

---

<div align="center">

⭐ If you found this project useful, consider starring the repository.

</div>
