#!/bin/bash

# Configuration
TARGET_HOST="http://localhost:3000/api"
NUM_USERS=10
SPAWN_RATE=1
DURATION="1m"

# Print test configuration
echo "Load Test Configuration:"
echo "----------------------"
echo "Target Host: $TARGET_HOST"
echo "Number of Users: $NUM_USERS"
echo "Spawn Rate: $SPAWN_RATE users/sec"
echo "Test Duration: $DURATION"
echo "----------------------"

# Check if API is available
echo "Checking API availability..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$TARGET_HOST/products")
if [ "$response" == "200" ]; then
    echo "API is available (HTTP 200)"
else
    echo "API is not available (HTTP $response)"
    exit 1
fi

# Start load test
echo "Starting load test..."
locust \
    --headless \
    --host="$TARGET_HOST" \
    --users="$NUM_USERS" \
    --spawn-rate="$SPAWN_RATE" \
    --run-time="$DURATION" \
    --only-summary \
    --locustfile="tests/load/locustfile.py"

# Check for errors in the Locust output
if [ $? -eq 0 ]; then
    echo "Load test completed successfully"
else
    echo "Load test completed with errors"
fi
