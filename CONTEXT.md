# Project: Distributed AI Monorepo

## Stack
- Python + FastAPI
- Redis Streams + Consumer Groups
- PostgreSQL + Alembic
- Docker Compose

## Phase 0 - COMPLETE
- Redis and PostgreSQL running via docker-compose.yml
- jobs table created via Alembic migration
- Python venv setup with fastapi, uvicorn, psycopg2, alembic, python-dotenv

## Structure
distributed-ai-monorepo/
├── p1-job-queue/
│   ├── venv/
│   ├── migrations/
│   ├── .env
│   └── alembic.ini
├── p2-code-reviewer/
├── p3-llm-toolkit/
├── docker-compose.yml
└── CONTEXT.md

## Docker
- Start: newgrp docker && docker compose up -d
- Stop: docker compose down
- Check: docker ps

## Database
- Host: localhost:5432
- DB: jobqueue
- User: admin / admin123
- Tables: jobs, alembic_version

## Phase 1 - IN PROGRESS
- database.py → PostgreSQL connection
- models.py → Job class
- main.py → POST /jobs, GET /jobs/{id}
- worker.py → SKIP LOCKED worker loop
- Flow working: pending → running → completed
