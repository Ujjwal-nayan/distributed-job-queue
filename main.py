from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_connection, get_redis
from models import Job
import json

app = FastAPI()

class JobRequest(BaseModel):
    payload: dict
    max_retries: int = 3

@app.post("/jobs", status_code=201)
def create_job(request: JobRequest):
    job = Job(
        payload=json.dumps(request.payload),
        max_retries=request.max_retries
    )

    # Persist job to PostgreSQL
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

    # Dispatch job_id to Redis Stream
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
