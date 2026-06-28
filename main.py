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
    r = get_redis()

    if request.idempotency_key:
        redis_key = f"idempotency:{request.idempotency_key}"
        is_new = r.setnx(redis_key, "1")
        if not is_new:
            raise HTTPException(status_code=409, detail="Duplicate request — job already submitted")
        r.expire(redis_key, 86400)

    job = Job(
        payload=json.dumps(request.payload),
        max_retries=request.max_retries
    )

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO jobs (id, status, payload, retry_count, max_retries)
           VALUES (%s, %s, %s, %s, %s)""",
        (job.id, job.status, job.payload, job.retry_count, job.max_retries)
    )
    conn.commit()
    cur.close()
    conn.close()

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
