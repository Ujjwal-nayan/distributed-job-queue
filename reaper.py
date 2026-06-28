import time
from database import get_connection, get_redis

STREAM_NAME = "jobs_stream"
STUCK_JOB_THRESHOLD_SECONDS = 30

def reap():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM jobs
        WHERE status = 'running'
        AND updated_at < now() - interval '%s seconds'
    """, (STUCK_JOB_THRESHOLD_SECONDS,))

    stuck_jobs = cur.fetchall()

    if not stuck_jobs:
        print("[Reaper] No stuck jobs found.")
        cur.close()
        conn.close()
        return

    r = get_redis()

    for job in stuck_jobs:
        print(f"[Reaper] Stuck job detected: {job['id']}. Re-queuing...")
        cur.execute("""
            UPDATE jobs
            SET status = 'pending', updated_at = now(),
                error_message = 'Reaper: job was stuck in running state'
            WHERE id = %s
        """, (job["id"],))
        conn.commit()
        r.xadd(STREAM_NAME, {"job_id": job["id"]})

    cur.close()
    conn.close()

if __name__ == "__main__":
    print("[Reaper] Starting...")
    while True:
        reap()
        time.sleep(10)
