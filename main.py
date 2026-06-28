from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_connection, get_redis
from models import Job
import json

app = FastAPI()

class JobRequest(BaseModel):
    payload: dict
    max_retries: int = 3
    idempotency_key: str = None

@app.post("/jobs", status_code=201)
def create_job(request: JobRequest):
    job = Job(
        payload=json.dumps(request.payload),
        max_retries=request.max_retries,
        idempotency_key=request.idempotency_key
    )

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO jobs (id, status, payload, retry_count, max_retries, idempotency_key)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (job.id, job.status, job.payload, job.retry_count, job.max_retries, job.idempotency_key)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        if "unique" in str(e).lower() and "idempotency_key" in str(e).lower():
            raise HTTPException(status_code=409, detail="Duplicate request — job already submitted")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        pass

    cur.close()
    conn.close()

    if request.idempotency_key:
        r = get_redis()
        r.set(f"idempotency:{request.idempotency_key}", job.id, nx=True, ex=86400)

    r = get_redis()
    r.xadd("jobs_stream", {"job_id": job.id})

    return job.to_dict()

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
    job = cur.fetchone()
    cur.close()
    conn.close()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(job)


@app.get("/health")
def health():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        r = get_redis()
        r.ping()
    except Exception:
        raise HTTPException(status_code=503, detail="Redis unavailable")

    return {"status": "healthy"}
