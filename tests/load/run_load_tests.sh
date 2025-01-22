#!/bin/bash

# Configuration
TARGET_HOST="http://localhost:3000/api"
NUM_USERS=10
SPAWN_RATE=1
DURATION="1m"
CSV_FILE="load_test_metrics_$(date +%Y%m%d_%H%M%S).csv"

# Print test configuration
echo "Load Test Configuration:"
echo "----------------------"
echo "Target Host: $TARGET_HOST"
echo "Number of Users: $NUM_USERS"
echo "Spawn Rate: $SPAWN_RATE users/sec"
echo "Test Duration: $DURATION"
echo "CSV Report: $CSV_FILE"
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
    --csv="$CSV_FILE" \
    --locustfile="tests/load/locustfile.py"

# Process and display metrics summary
if [ -f "${CSV_FILE}_stats.csv" ]; then
    echo ""
    echo "Detailed Performance Metrics:"
    echo "----------------------------"
    echo "Transaction Summary (in milliseconds):"
    # Using awk to process the CSV and calculate metrics
    awk -F',' 'NR>1 {
        printf "%-30s | Avg: %6.2f ms | Min: %6.2f ms | Max: %6.2f ms | 90%%: %6.2f ms | RPS: %6.2f | Failures: %d%%\n", 
        $2,                    # Name
        $5,                    # Average Response Time
        $6,                    # Min Response Time
        $7,                    # Max Response Time
        $9,                    # 90th percentile
        $12,                   # Requests per Second
        ($4/$3)*100           # Failure Percentage
    }' "${CSV_FILE}_stats.csv" | sort -t'|' -k2n
    
    echo ""
    echo "Response Time Distribution:"
    echo "-------------------------"
    if [ -f "${CSV_FILE}_distribution.csv" ]; then
        awk -F',' 'NR>1 {
            printf "%-30s | 50%%: %6.2f ms | 75%%: %6.2f ms | 95%%: %6.2f ms | 99%%: %6.2f ms\n",
            $2,                # Name
            $4,                # 50th percentile
            $5,                # 75th percentile
            $6,                # 95th percentile
            $7                 # 99th percentile
        }' "${CSV_FILE}_distribution.csv" | sort -t'|' -k2n
    fi
    
    # Calculate overall statistics
    echo ""
    echo "Overall Performance:"
    echo "------------------"
    awk -F',' 'NR>1 {
        total_requests += $3
        total_failures += $4
        total_response_time += ($5 * $3)
        if(max_rps < $12) max_rps = $12
    } END {
        printf "Total Requests: %d\n", total_requests
        printf "Total Failures: %d (%.2f%%)\n", total_failures, (total_failures/total_requests)*100
        printf "Average Response Time: %.2f ms\n", total_response_time/total_requests
        printf "Peak RPS: %.2f\n", max_rps
    }' "${CSV_FILE}_stats.csv"
    
    # Cleanup CSV files
    echo ""
    echo "CSV reports saved as: ${CSV_FILE}_*.csv"
else
    echo "No metrics file generated. The test might have failed."
    exit 1
fi

# Check for errors in the Locust output
if [ $? -eq 0 ]; then
    echo "Load test completed successfully"
else
    echo "Load test completed with errors"
fi
