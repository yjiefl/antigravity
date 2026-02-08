#!/bin/bash

# 1. Login
LOGIN_RES=$(curl -s -X POST "http://localhost:8000/api/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin&password=admin123")
TOKEN=$(echo $LOGIN_RES | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Login Success. Token length: ${#TOKEN}"

# 2. Create Task
CREATE_RES=$(curl -s -X POST "http://localhost:8000/api/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Curl Test Task", "task_type": "performance"}')

echo "Create Result: $CREATE_RES"
TASK_ID=$(echo $CREATE_RES | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Task ID: $TASK_ID"

# 3. Submit Task
echo "Submitting Task..."
SUBMIT_RES=$(curl -s -X POST "http://localhost:8000/api/tasks/$TASK_ID/submit" \
  -H "Authorization: Bearer $TOKEN")
echo "Submit Result: $SUBMIT_RES"
