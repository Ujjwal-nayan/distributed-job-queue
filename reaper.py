import asyncio
import logging
import os
from database import get_connection, get_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

STREAM_NAME = "jobs_stream"
STUCK_JOB_THRESHOLD_SECONDS = int(os.getenv("STUCK_JOB_THRESHOLD", "30"))

async def reap():
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Only re-queue jobs whose workers are genuinely dead
        # Join on worker_heartbeats to verify worker liveness
        cur.execute("""
            SELECT j.* FROM jobs j
            LEFT JOIN worker_heartbeats wh ON j.worker_id = wh.worker_id
            WHERE j.status = 'running'
            AND j.updated_at < now() - interval '%s seconds'
            AND (
                wh.worker_id IS NULL
                OR wh.last_seen < now() - interval '%s seconds'
            )
        """, (STUCK_JOB_THRESHOLD_SECONDS, STUCK_JOB_THRESHOLD_SECONDS))

        stuck_jobs = cur.fetchall()

        if not stuck_jobs:
            logger.debug("[Reaper] No stuck jobs found.")
            return

        r = get_redis()

        for job in stuck_jobs:
            logger.warning(f"[Reaper] Stuck job detected: {job['id']} (worker: {job.get('worker_id', 'unknown')}). Re-queuing...")
            cur.execute("""
                UPDATE jobs
                SET status = 'pending', updated_at = now(),
                    error_message = 'Reaper: job was stuck in running state'
                WHERE id = %s
            """, (job["id"],))
            conn.commit()

            # Re-dispatch to Redis with error handling
            try:
                r.xadd(STREAM_NAME, {"job_id": job["id"]})
                logger.info(f"[Reaper] Job {job['id']} re-queued successfully.")
            except Exception as e:
                logger.error(f"[Reaper] Failed to re-dispatch job {job['id']} to Redis: {e}")
                # Job remains 'pending' in DB — next reaper cycle will retry

    except Exception as e:
        logger.error(f"[Reaper] Error during reaper cycle: {e}")
    finally:
        cur.close()
        conn.close()

async def run():
    logger.info(f"[Reaper] Starting... (threshold: {STUCK_JOB_THRESHOLD_SECONDS}s)")
    while True:
        await reap()
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run())
