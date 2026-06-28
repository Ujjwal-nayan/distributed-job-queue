import time
import json
from database import get_connection, get_redis

STREAM_NAME = "jobs_stream"
CONSUMER_GROUP = "workers"
CONSUMER_NAME = "worker-1"

def setup_consumer_group(r):
    try:
        r.xgroup_create(STREAM_NAME, CONSUMER_GROUP, id="0", mkstream=True)
    except Exception:
        pass  # Group already exists

def process_job(job):
    payload = json.loads(job["payload"])
    print(f"[Worker] Processing job {job['id']} → {payload}")
    time.sleep(2)
    if payload.get("force_fail"):
        raise Exception("Simulated failure")
    print(f"[Worker] Completed job {job['id']}")

def handle_job(job_id, r):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
    job = cur.fetchone()

    if not job:
        cur.close()
        conn.close()
        return

    cur.execute("""
        UPDATE jobs SET status = 'running', updated_at = now()
        WHERE id = %s
    """, (job["id"],))
    conn.commit()

    try:
        process_job(job)
        cur.execute("""
            UPDATE jobs SET status = 'completed', updated_at = now()
            WHERE id = %s
        """, (job["id"],))
        conn.commit()

    except Exception as e:
        retry_count = job["retry_count"] + 1
        max_retries = job["max_retries"]

        if retry_count < max_retries:
            backoff = 2 ** retry_count
            print(f"[Worker] Job {job['id']} failed. Retry {retry_count}/{max_retries} in {backoff}s")
            cur.execute("""
                UPDATE jobs
                SET status = 'pending', retry_count = %s,
                    error_message = %s, updated_at = now()
                WHERE id = %s
            """, (retry_count, str(e), job["id"]))
            conn.commit()
            time.sleep(backoff)
            # Re-dispatch to Redis Stream
            r.xadd(STREAM_NAME, {"job_id": job["id"]})
        else:
            print(f"[Worker] Job {job['id']} exhausted retries. Moving to DLQ.")
            cur.execute("""
                UPDATE jobs
                SET status = 'failed', retry_count = %s,
                    error_message = %s, updated_at = now()
                WHERE id = %s
            """, (retry_count, str(e), job["id"]))
            conn.commit()

    cur.close()
    conn.close()

def run():
    r = get_redis()
    setup_consumer_group(r)
    print("[Worker] Listening on Redis Stream...")

    while True:
        messages = r.xreadgroup(
            CONSUMER_GROUP,
            CONSUMER_NAME,
            {STREAM_NAME: ">"},
            count=1,
            block=2000
        )

        if not messages:
            continue

        for stream, entries in messages:
            for message_id, data in entries:
                job_id = data["job_id"]
                print(f"[Worker] Received job_id: {job_id}")
                handle_job(job_id, r)
                r.xack(STREAM_NAME, CONSUMER_GROUP, message_id)

if __name__ == "__main__":
    run()
