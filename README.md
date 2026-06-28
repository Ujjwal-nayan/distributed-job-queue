# Distributed Job Queue

A production-grade distributed job queue built from scratch in Python. No Celery, no BullMQ — just Redis Streams, PostgreSQL, and raw engineering.

---

## Why This Exists

Most developers reach for Celery without understanding what happens underneath. This project builds a job queue from first principles — the same way companies like Razorpay, Swiggy, and Zepto do it internally.

---

## Architecture

```
Producer (FastAPI)
      │
      ├── Persists job to PostgreSQL
      └── Dispatches job_id to Redis Stream
                    │
              Consumer Group
                    │
             Worker (asyncio)
                    │
          ┌─────────┴──────────┐
      Success             Failure / Timeout
          │                    │
     completed          Exponential Backoff
                              │
                        Max retries hit?
                         ┌────┴────┐
                        No       Yes
                         │         │
                       Retry      DLQ
                               (failed)

Reaper (background) — detects stuck jobs and re-queues them
```

---

## Features

- **Redis Streams + Consumer Groups** — reliable job dispatch, no polling
- **PostgreSQL persistence** — every job stored with full audit trail
- **Exponential backoff** — failed jobs retry after 2s, 4s, 8s
- **Dead Letter Queue** — jobs that exhaust retries are marked failed with error message
- **Idempotency keys** — same job submitted twice? Second request rejected with 409
- **asyncio timeout** — jobs that hang are cancelled after 10s and retried
- **Worker heartbeats** — workers register liveness every 5s in PostgreSQL
- **Reaper process** — detects stuck jobs and re-queues them
- **Chaos tested** — Redis and worker killed mid-execution, zero data loss confirmed

---

## Tech Stack

- Python, FastAPI, asyncio
- Redis Streams + Consumer Groups
- PostgreSQL + Alembic migrations
- Docker + Docker Compose

---

## Getting Started

**Prerequisites:** Docker, Python 3.10+

**1. Clone the repo**
```bash
git clone https://github.com/Ujjwal-nayan/distributed-job-queue.git
cd distributed-job-queue
```

**2. Start Redis and PostgreSQL**
```bash
docker compose up -d
```

**3. Set up Python environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**4. Run database migrations**
```bash
alembic upgrade head
```

**5. Start all three processes (separate terminals)**
```bash
uvicorn main:app --reload
python3 worker.py
python3 reaper.py
```

---

## API

**Create a job**
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"task": "review_pr", "repo": "my-repo"}}'
```

**Create a job with idempotency key**
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"task": "review_pr"}, "idempotency_key": "pr-42-review"}'
```

**Check job status**
```bash
curl http://localhost:8000/jobs/{job_id}
```

**Job status values:** pending → running → completed / failed

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

## Project Structure

```
├── main.py              # FastAPI server
├── worker.py            # Async worker with timeout
├── reaper.py            # Stuck job recovery
├── database.py          # PostgreSQL and Redis connections
├── models.py            # Job model
├── chaos_test.sh        # Chaos engineering test
├── migrations/          # Alembic migration files
├── docker-compose.yml   # Redis + PostgreSQL containers
└── requirements.txt
```
