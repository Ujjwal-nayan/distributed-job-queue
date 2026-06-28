import streamlit as st
import pandas as pd
from database import get_connection, get_redis
from datetime import datetime

st.set_page_config(page_title="Job Queue Dashboard", layout="wide")
st.title("Distributed Job Queue Dashboard")

# Refresh button
col_refresh, col_time = st.columns([1, 5])
if col_refresh.button("🔄 Refresh"):
    st.rerun()
col_time.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

def get_stats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
    rows = cur.fetchall()
    stats = {row["status"]: row["count"] for row in rows}
    cur.execute("SELECT COUNT(*) FROM jobs")
    total = cur.fetchone()["count"]
    cur.close()
    conn.close()
    return {
        "pending": stats.get("pending", 0),
        "running": stats.get("running", 0),
        "completed": stats.get("completed", 0),
        "failed": stats.get("failed", 0),
        "total": total
    }

def get_workers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM worker_heartbeats ORDER BY last_seen DESC")
    workers = cur.fetchall()
    cur.close()
    conn.close()
    return workers

def get_recent_jobs(limit=20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT %s", (limit,))
    jobs = cur.fetchall()
    cur.close()
    conn.close()
    return jobs

def get_failed_jobs():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE status = 'failed' ORDER BY updated_at DESC")
    jobs = cur.fetchall()
    cur.close()
    conn.close()
    return jobs

def retry_job(job_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE jobs SET status = 'pending', retry_count = 0, error_message = 'Manual retry from dashboard', updated_at = now() WHERE id = %s", (job_id,))
    conn.commit()
    cur.close()
    conn.close()
    r = get_redis()
    r.xadd("jobs_stream", {"job_id": job_id})

# Fetch data
stats = get_stats()
workers = get_workers()
recent_jobs = get_recent_jobs()
failed_jobs = get_failed_jobs()

# Stats row
st.subheader("Queue Overview")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Jobs", stats["total"])
col2.metric("Pending", stats["pending"])
col3.metric("Running", stats["running"])
col4.metric("Completed", stats["completed"])
col5.metric("Failed", stats["failed"])

st.divider()

# Workers
st.subheader("Workers")
if workers:
    worker_data = []
    for w in workers:
        worker_data.append({
            "Worker ID": w["worker_id"],
            "Status": w["status"],
            "Last Heartbeat": str(w["last_seen"])
        })
    st.table(pd.DataFrame(worker_data))
else:
    st.info("No workers registered yet.")

st.divider()

# Recent jobs
st.subheader("Recent Jobs")
if recent_jobs:
    job_data = []
    for job in recent_jobs:
        job_data.append({
            "Job ID": job["id"][:8] + "...",
            "Status": job["status"],
            "Retries": f"{job['retry_count']}/{job['max_retries']}",
            "Worker": job.get("worker_id", "-"),
            "Error": job.get("error_message", "-")[:50] if job.get("error_message") else "-",
            "Created": str(job["created_at"])
        })
    st.dataframe(pd.DataFrame(job_data), use_container_width=True)
else:
    st.info("No jobs submitted yet.")

st.divider()

# Dead Letter Queue
st.subheader("Dead Letter Queue")
if failed_jobs:
    for job in failed_jobs:
        with st.expander(f"{job['id'][:8]}... — {job.get('error_message', 'No error')[:80]}"):
            st.text(f"Full Error: {job.get('error_message', 'N/A')}")
            st.text(f"Retries: {job['retry_count']}/{job['max_retries']}")
            st.text(f"Failed at: {job['updated_at']}")
            if st.button(f"Retry {job['id'][:8]}...", key=job["id"]):
                retry_job(job["id"])
                st.success(f"Re-queued!")
                st.rerun()
else:
    st.info("No failed jobs.")

st.divider()
st.caption("Distributed Job Queue — Built from Scratch")
