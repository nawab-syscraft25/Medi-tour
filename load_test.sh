#!/bin/bash
# Simple Load Test Script using curl
# Tests your Medi-Tour API with various endpoints

BASE_URL="http://165.22.223.163:8000"

echo "🚀 Starting Load Tests for Medi-Tour API"
echo "Base URL: $BASE_URL"
echo "=========================="

# Function to run multiple curl requests in parallel
run_load_test() {
    local endpoint=$1
    local concurrent=$2
    local total=$3
    local name=$4
    
    echo ""
    echo "🔄 Testing: $name"
    echo "Endpoint: $endpoint"
    echo "Concurrent requests: $concurrent"
    echo "Total requests: $total"
    echo "------------------------"
    
    # Create a temporary file for results
    temp_file=$(mktemp)
    
    # Function to make a single request
    make_request() {
        local url="$BASE_URL$endpoint"
        local start=$(date +%s%N)
        local response=$(curl -s -o /dev/null -w "%{http_code},%{time_total}" "$url")
        local end=$(date +%s%N)
        echo "$response" >> "$temp_file"
    }
    
    # Export function for parallel execution
    export -f make_request
    export BASE_URL endpoint temp_file
    
    # Start time
    start_time=$(date +%s)
    
    # Run requests in parallel batches
    seq 1 $total | xargs -n1 -P$concurrent -I{} bash -c 'make_request'
    
    # End time
    end_time=$(date +%s)
    total_time=$((end_time - start_time))
    
    # Process results
    local success_count=$(grep -c "^200," "$temp_file")
    local total_requests=$(wc -l < "$temp_file")
    local success_rate=$((success_count * 100 / total_requests))
    local rps=$((total_requests / total_time))
    
    echo "Results:"
    echo "  Total requests: $total_requests"
    echo "  Successful: $success_count"
    echo "  Failed: $((total_requests - success_count))"
    echo "  Success rate: $success_rate%"
    echo "  Total time: ${total_time}s"
    echo "  Requests/second: $rps"
    
    # Clean up
    rm "$temp_file"
}

# Test scenarios
echo ""
echo "Starting test scenarios..."

# Test 1: Basic doctors endpoint
run_load_test "/api/v1/doctors?skip=0&limit=10" 5 25 "Doctors List"

# Test 2: Hospitals endpoint  
run_load_test "/api/v1/hospitals?skip=0&limit=10" 5 25 "Hospitals List"

# Test 3: Treatments endpoint
run_load_test "/api/v1/treatments?skip=0&limit=10" 5 25 "Treatments List"

# Test 4: Filter endpoints
run_load_test "/api/filters/locations" 3 15 "Locations Filter"
run_load_test "/api/filters/treatment-types" 3 15 "Treatment Types Filter"
run_load_test "/api/filters/specializations" 3 15 "Specializations Filter"

# Test 5: High load test
run_load_test "/api/v1/doctors?skip=0&limit=5" 10 50 "High Load Test"

echo ""
echo "🏁 Load testing completed!"
echo "=========================="