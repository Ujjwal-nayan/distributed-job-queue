import asyncio
import json
import os
import logging
from database import get_connection, get_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

STREAM_NAME = "jobs_stream"
CONSUMER_GROUP = "workers"
CONSUMER_NAME = os.getenv("WORKER_NAME", "worker-1")
JOB_TIMEOUT_SECONDS = 10
HEARTBEAT_INTERVAL = 5

def setup_consumer_group(r):
    try:
        r.xgroup_create(STREAM_NAME, CONSUMER_GROUP, id="0", mkstream=True)
    except Exception:
        pass

async def send_heartbeat():
    while True:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO worker_heartbeats (worker_id, last_seen, status)
                VALUES (%s, now(), 'alive')
                ON CONFLICT (worker_id)
                DO UPDATE SET last_seen = now(), status = 'alive'
            """, (CONSUMER_NAME,))
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"[Heartbeat] {CONSUMER_NAME} alive")
        except Exception as e:
            logger.error(f"[Heartbeat] Failed: {e}")
        await asyncio.sleep(HEARTBEAT_INTERVAL)

async def process_job(job):
    payload = json.loads(job["payload"])
    logger.info(f"[Worker] Processing job {job['id']} → {payload}")
    await asyncio.sleep(2)
    if payload.get("force_fail"):
        raise Exception("Simulated failure")
    if payload.get("force_timeout"):
        await asyncio.sleep(999)
    logger.info(f"[Worker] Completed job {job['id']}")

async def handle_job(job_id, r):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        job = cur.fetchone()

        if not job:
            logger.warning(f"[Worker] Job {job_id} not found in DB. Skipping.")
            return

        # Atomic claim — prevents race condition with other workers
        cur.execute("""
            UPDATE jobs SET status = 'running', updated_at = now(), worker_id = %s
            WHERE id = %s AND status = 'pending'
        """, (CONSUMER_NAME, job["id"]))
        conn.commit()

        if cur.rowcount == 0:
            logger.warning(f"[Worker] Job {job['id']} already claimed. Skipping.")
            return

        try:
            async with asyncio.timeout(JOB_TIMEOUT_SECONDS):
                await process_job(job)

            cur.execute("""
                UPDATE jobs SET status = 'completed', updated_at = now()
                WHERE id = %s
            """, (job["id"],))
            conn.commit()

        except TimeoutError:
            logger.warning(f"[Worker] Job {job['id']} timed out after {JOB_TIMEOUT_SECONDS}s")
            retry_count = job["retry_count"] + 1
            max_retries = job["max_retries"]

            if retry_count < max_retries:
                cur.execute("""
                    UPDATE jobs
                    SET status = 'pending', retry_count = %s,
                        error_message = 'Job timed out', updated_at = now()
                    WHERE id = %s
                """, (retry_count, job["id"]))
                conn.commit()
                r.xadd(STREAM_NAME, {"job_id": job["id"]})
            else:
                cur.execute("""
                    UPDATE jobs
                    SET status = 'failed', retry_count = %s,
                        error_message = 'Job timed out — max retries exhausted', updated_at = now()
                    WHERE id = %s
                """, (retry_count, job["id"]))
                conn.commit()

        except Exception as e:
            retry_count = job["retry_count"] + 1
            max_retries = job["max_retries"]
            error_message = str(e)[:1000]

            if retry_count < max_retries:
                backoff = 2 ** retry_count
                logger.warning(f"[Worker] Job {job['id']} failed. Retry {retry_count}/{max_retries} in {backoff}s")
                cur.execute("""
                    UPDATE jobs
                    SET status = 'pending', retry_count = %s,
                        error_message = %s, updated_at = now()
                    WHERE id = %s
                """, (retry_count, error_message, job["id"]))
                conn.commit()
                await asyncio.sleep(backoff)
                r.xadd(STREAM_NAME, {"job_id": job["id"]})
            else:
                logger.error(f"[Worker] Job {job['id']} exhausted retries. Moving to DLQ.")
                cur.execute("""
                    UPDATE jobs
                    SET status = 'failed', retry_count = %s,
                        error_message = %s, updated_at = now()
                    WHERE id = %s
                """, (retry_count, error_message, job["id"]))
                conn.commit()

    finally:
        cur.close()
        conn.close()

async def run():
    r = get_redis()
    setup_consumer_group(r)
    logger.info("[Worker] Listening on Redis Stream...")

    asyncio.create_task(send_heartbeat())

    while True:
        messages = r.xreadgroup(
            CONSUMER_GROUP,
            CONSUMER_NAME,
            {STREAM_NAME: ">"},
            count=1,
            block=2000
        )

        if not messages:
            await asyncio.sleep(0.1)
            continue

        for stream, entries in messages:
            for message_id, data in entries:
                job_id = data["job_id"]
                logger.info(f"[Worker] Received job_id: {job_id}")
                await handle_job(job_id, r)
                # ACK even if skipped — message should not be redelivered
                r.xack(STREAM_NAME, CONSUMER_GROUP, message_id)

if __name__ == "__main__":
    asyncio.run(run())
