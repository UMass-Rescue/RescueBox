#!/bin/bash

# Output file
OUTPUT_FILE="server_usage_report_$(date +%Y%m%d_%H%M%S).txt"

# Function to collect CPU and memory usage for the server process
get_server_process_usage() {
    # Find the PID of the process listening on port 5000
    SERVER_PID=$(lsof -i :5000 -t)
    
    if [ -z "$SERVER_PID" ]; then
        echo "No process is running on port 5000." >> "$OUTPUT_FILE"
    else
        echo "Server process PID: $SERVER_PID" >> "$OUTPUT_FILE"
        echo "CPU and Memory Usage for Process $SERVER_PID:" >> "$OUTPUT_FILE"
        ps -p $SERVER_PID -o pid,comm,%cpu,%mem,etime >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
}

# Function to collect disk usage related to the server
get_disk_usage() {
    echo "Disk I/O Usage (iostat):" >> "$OUTPUT_FILE"
    iostat -d 1 2 >> "$OUTPUT_FILE"
    echo "-----------------------------" >> "$OUTPUT_FILE"
}

# Function to collect network usage related to the server on port 5000
get_network_usage() {
    echo "### Network Usage ###" >> "$OUTPUT_FILE"
    
    # Get network statistics for the server on port 5000
    netstat -an | grep ':5000 ' >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Show incoming and outgoing packets for the server's port
    netstat -ib >> "$OUTPUT_FILE"
    echo "-----------------------------" >> "$OUTPUT_FILE"
}

# Function to collect overall system information
get_system_info() {
    echo "### System Information ###" >> "$OUTPUT_FILE"
    uname -a >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "Uptime:" >> "$OUTPUT_FILE"
    uptime >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "CPU Details:" >> "$OUTPUT_FILE"
    sysctl -n machdep.cpu.brand_string >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "Memory Details:" >> "$OUTPUT_FILE"
    sysctl -a | grep mem >> "$OUTPUT_FILE"
    echo "-----------------------------" >> "$OUTPUT_FILE"
}

# Execute functions
echo "Server Usage Report for 127.0.0.1:5000 - $(date)" > "$OUTPUT_FILE"
echo "=============================" >> "$OUTPUT_FILE"

get_system_info
get_disk_usage
get_network_usage
get_server_process_usage
# Infinite loop to gather data every 30 seconds
while true
do
    SERVER_PID=$(lsof -i :5000 -t)
    
    if [ -z "$SERVER_PID" ]; then
        echo "No process is running on port 5000." >> "$OUTPUT_FILE"
    else
        ps -p $SERVER_PID -o pid,comm,%cpu,%mem,etime >> "$OUTPUT_FILE"
    fi

    # Wait for 30 seconds before the next iteration
    sleep 30
done

