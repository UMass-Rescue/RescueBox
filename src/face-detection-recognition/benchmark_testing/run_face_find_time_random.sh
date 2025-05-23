#!/bin/bash

if [ $# -ne 1 ]; then
    echo -e "Expected 1 argument\n"
    echo -e "Usage: ./run_face_find_time_random.sh collection_name\n"
    read -p "Press any key to exit..."
    exit 1
fi

source ../.env

collection_name=$1

export PYTHONPATH=$(pwd)/..

# Start the Python server in the background
python ../facematch/facematch/face_match_server.py &
server_pid=$!
echo "Server started with PID $server_pid"

# Wait for the server to start (adjust time as necessary)
sleep 10

# Create an array of files in the directory
files=("$SAMPLE_QUERIES_DIRECTORY"/*)

# Get the number of files
num_files="${#files[@]}"

# Generate a random index
random_index=$((RANDOM % num_files))

# Pick the random file
random_file="${files[random_index]}"

# Start timer
start_time=$(date +%s)

# Call client script to find match for random image
result=$(python ../facematch/Sample_Client/sample_find_face_client.py --file_paths "$random_file" --collection_name "$collection_name")

# Sample file path
# "<path to dataset folder>\\LFWdataset\\sample_queries\\image.jpg"

# Calculate total time taken
end_time=$(date +%s)
total_time=$((end_time - start_time))

# Stop the server
kill $server_pid
echo "Server stopped"

# Print results
echo -e "Chosen File: $random_file \n$result"

# Print total time taken
echo "Total time taken: $total_time seconds"

read -p "Press any key to exit..."