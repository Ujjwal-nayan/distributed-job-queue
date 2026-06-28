#!/bin/bash

echo "=== Chaos Engineering Test ==="
echo ""

# Step 1: Submit a job
echo "[1] Submitting job..."
RESPONSE=$(curl -s -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"task": "chaos_test"}}')

JOB_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "    Job ID: $JOB_ID"
echo ""

# Step 2: Kill Redis mid-flight
echo "[2] Killing Redis mid-job..."
docker stop redis
echo "    Redis stopped."
echo ""

# Step 3: Wait
sleep 5

# Step 4: Restart Redis
echo "[3] Restarting Redis..."
docker start redis
sleep 3
echo "    Redis restarted."
echo ""

# Step 5: Check job status
echo "[4] Checking job status..."
STATUS=$(curl -s http://localhost:8000/jobs/$JOB_ID | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
echo "    Status: $STATUS"
echo ""

# Step 6: Kill worker mid-flight
echo "[5] Submitting another job and killing worker..."
RESPONSE2=$(curl -s -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"task": "chaos_test_2"}}')

JOB_ID2=$(echo $RESPONSE2 | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "    Job ID: $JOB_ID2"

sleep 1
echo "    Killing worker process..."
pkill -f "python3 worker.py"
echo ""

# Step 7: Wait for reaper
echo "[6] Waiting for Reaper to detect stuck job (30s)..."
sleep 35

# Step 8: Restart worker
echo "[7] Restarting worker..."
source venv/bin/activate
python3 worker.py &
WORKER_PID=$!
sleep 5

# Step 9: Check job 2 status
echo "[8] Checking recovered job status..."
STATUS2=$(curl -s http://localhost:8000/jobs/$JOB_ID2 | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
echo "    Status: $STATUS2"
echo ""

echo "=== Chaos Test Complete ==="
echo "Job 1 final status: $STATUS"
echo "Job 2 final status: $STATUS2"

kill $WORKER_PID 2>/dev/null
