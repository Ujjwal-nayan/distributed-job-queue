<div align="center">

# 🚀 Distributed Job Queue

*A production-grade distributed job queue built from scratch using FastAPI, Redis Streams, PostgreSQL, and asyncio.*

<p>
  <img src="https://skillicons.dev/icons?i=python,fastapi,postgres,redis,docker" />
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/FastAPI-0.138-009688?style=for-the-badge">
  <img src="https://img.shields.io/badge/Chaos-Tested-success?style=for-the-badge">
</p>

</div>

---

## ✨ Overview

Most developers use Celery without understanding what happens underneath.

This project rebuilds a production-ready distributed job queue from first principles using **Redis Streams**, **PostgreSQL**, and **asyncio**, implementing features like reliable delivery, retries, worker heartbeats, dead-letter queues, and stuck job recovery.

---

## ⚡ Highlights

- 🚫 No Celery or BullMQ
- 📬 Redis Streams + Consumer Groups
- 🗄 PostgreSQL as the source of truth
- 🔒 Atomic job claiming
- ♻️ Exponential backoff retries
- 💀 Dead Letter Queue
- ❤️ Worker heartbeat monitoring
- 🔄 Automatic stuck-job recovery
- 🧠 Idempotency keys
- 📊 Streamlit monitoring dashboard
- 🧪 Chaos tested

---

## 📊 Dashboard

Real-time monitoring of:

- Queue statistics
- Active workers
- Job status
- Retry counts
- Dead Letter Queue

<p align="center">

![Dashboard](dashboard.png)

</p>

---

## 🏗️ Architecture

The API persists every job to PostgreSQL before dispatching only the `job_id` through Redis Streams. Workers consume jobs using Consumer Groups, update execution status, while a background Reaper recovers abandoned jobs.

<p align="center">

![Architecture](architecture.png)

</p>

---

## ✨ Features

- Redis Streams + Consumer Groups
- PostgreSQL persistence
- Atomic job claiming
- Exponential backoff (2s → 4s → 8s)
- Dead Letter Queue
- Idempotency keys
- Worker heartbeats
- Worker ID tracking
- Reaper process
- `/health` endpoint
- Streamlit dashboard
- Chaos engineering tests

---

## 🛠 Tech Stack

| Category | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| API | FastAPI |
| Concurrency | asyncio |
| Queue | Redis Streams |
| Database | PostgreSQL |
| Migrations | Alembic |
| Dashboard | Streamlit |
| Containers | Docker Compose |

---

## 🚀 Quick Start

```bash
git clone https://github.com/Ujjwal-nayan/distributed-job-queue.git
cd distributed-job-queue

docker compose up -d

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

alembic upgrade head
````

Run each service in a separate terminal.

```bash
uvicorn main:app --reload
```

```bash
python worker.py
```

```bash
python reaper.py
```

```bash
streamlit run dashboard.py
```

---

## 📡 API

### Create Job

```http
POST /jobs
```

### Get Job

```http
GET /jobs/{job_id}
```

### Health Check

```http
GET /health
```

---

## 📂 Project Structure

```text
.
├── main.py
├── worker.py
├── reaper.py
├── dashboard.py
├── database.py
├── models.py
├── migrations/
├── dashboard.png
├── architecture.png
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

<div align="center">

**Built to understand distributed systems by building one from scratch.**

⭐ If you found this project useful, consider starring the repository.

</div>
