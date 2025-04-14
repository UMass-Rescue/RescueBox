#!/bin/bash

# Source environment variables
source ../.env
export PYTHONPATH="$(pwd)/.."

# *************************************************************************************
#
# HANDLE PARAMETERS
#
#**************************************************************************************

# Set default values
collection_name="benchmark-sample"
top_results_dir="./benchmark-results"
results_name="results"
keep_collection="False"

# Display usage information
function show_usage {
    echo "Usage: $0 [OPTIONS]"
    echo "OPTIONS:"
    echo "  -d, --db-name DB_NAME           Collection/database name (default: benchmark-sample)"
    echo "  -o, --results-dir PATH          Top output directory for all results (default: ./benchmark-results)"
    echo "  -n, --results-name RESULTS_NAME  Name differentiator for results output (default: results)"
    echo "  -k, --keep-db                   keep specified collection (default: False)"
    echo "  -h, --help                      Show this help message"
}

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -d|--db-name) collection_name="$2"; shift ;;
        -o|--results-dir) top_results_dir="$2"; shift ;;
        -n|--results-name) results_name="$2"; shift ;;
        -k|--keep-db) keep_collection="True" ;;
        -h|--help) show_usage; exit 0 ;;
        *) echo "Unknown parameter: $1"; show_usage; exit 1 ;;
    esac
    shift
done

database_directory="$DATABASE_DIRECTORY"
queries_directory="$QUERIES_DIRECTORY"

# *************************************************************************************
#
# GET MODEL CONFIG INFO
#
#**************************************************************************************

MODEL_CONFIG=$(python construct_paths.py --path_name model_config)

MODEL_NAME="ArcFace" # Default model name
DETECTOR_NAME="yolov8" # Default detector name

# Read model and detector names from config
if [ -f "$MODEL_CONFIG" ]; then
    # Improved extraction with proper parsing
    MODEL_NAME=$(grep '"model_name"' "$MODEL_CONFIG" | cut -d'"' -f4)
    DETECTOR_NAME=$(grep '"detector_backend"' "$MODEL_CONFIG" | cut -d'"' -f4)
    
    echo "Using model: $MODEL_NAME"
    echo -e "Using detector: $DETECTOR_NAME\n"
    
else
    echo -e "Warning: Could not find model config file, using default model settings\n"
fi


# *************************************************************************************
#
# CLEAR EXISTING RESULTS DIRECTORY
#
#**************************************************************************************


# Results Directory
results_dir=$(python construct_paths.py --path_name results_dir --detector "$DETECTOR_NAME" --embedding "$MODEL_NAME" --results_path "$top_results_dir" --results_name "$results_name")

# Skip if not a writable directory or is root
if [ ! -d "$results_dir" ] || [ ! -w "$results_dir" ] || [ "$results_dir" = "/" ]; then
    echo -e "No benchmarking folder found. Continuing\n"
else
    echo -e "Warning: Results will overwrite results in $results_dir\n"
    read -rp "Continue and clear contents? [y/N] " response
    case "$response" in
        [Yy]*) 
            rm -rf "${results_dir:?}/"*  # Safer: Only delete contents
            echo -e "\nCleared: $results_dir\n"
            ;;
        *)
            echo -e "Exiting\n"
            exit 0
            ;;
    esac
fi

# Create fresh result directory
mkdir -p "$results_dir"

# *************************************************************************************
#
# SERVERS STARTUP
#
#**************************************************************************************

# Configuration
CHROMA_CMD="chroma run --path ../resources/data"
PYTHON_CMD="python ../src/facematch/face_match_server.py"
CHROMA_TIMEOUT=60
FACEMATCH_TIMEOUT=30
CHROMA_STARTUP_MSG="Application startup complete"
FACEMATCH_STARTUP_MSG="Press CTRL+C to quit"

# Function to start a server and wait for it to be active
start_server_and_wait() {
    local start_cmd=$1
    local check_cmd=$2
    local server_name=$3
    local max_attempts=30
    local delay=1

    # Start the server in the background, redirecting output to /dev/null
    eval "$start_cmd  > /dev/null 2>&1 &"
    local server_pid=$!

    # Wait for server to become active
    echo "Waiting for $server_name server to become active..." >&2
    local attempts=0
    while [ $attempts -lt $max_attempts ]; do
        response=$(eval "$check_cmd")
        if [ "$response" -ne 000 ] && [ "$response" -ne 403 ]; then
            echo -e "$server_name server is active\n" >&2
            echo "$server_pid"
            return 1
        fi
        sleep $delay
        attempts=$((attempts + 1))
    done

    echo "Error: $server_name server did not become active after $max_attempts attempts" >&2
    kill $server_pid 2>/dev/null
    exit 1
}


# Start ChromaDB Server
chroma_pid=$(start_server_and_wait "chroma run --path ../resources/data"    "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1 " "ChromaDB")

# Start FaceMatch Server
python ../src/facematch/face_match_server.py &
server_pid=$(pgrep -f "python ../src/facematch/face_match_server.py")

start_server_and_wait ":"     "curl -s -o /dev/null -w '%{http_code}'  http://127.0.0.1:5000/listcollections " "FaceMatch"


# Cleanup function
cleanup() {
    if [ -n "$chroma_pid" ]; then
        kill "$chroma_pid"
        echo "killed ChromaDB at PID $chroma_pid"
    fi
    if [ -n "$server_pid" ]; then
        kill "$server_pid"
        echo "killed FaceMatch Server at PID $server_pid"
    fi
}
trap cleanup EXIT



# *************************************************************************************
#
# BENCHMARKING
#
#**************************************************************************************


# Delete collection if exists
if [ "$keep_collection" = "False" ]; then
    python -m src.Sample_Client.sample_delete_collection_client --collection_name "$collection_name" --model_name "$MODEL_NAME" --detector_backend "$DETECTOR_NAME"
fi

# Benchmark bulk upload
start_time=$(date +%s)
python -m src.Sample_Client.sample_bulk_upload_client --directory_paths "$database_directory" --collection_name "$collection_name"
end_time=$(date +%s)
total_time=$((end_time - start_time))
echo "Bulk Upload Time: $total_time seconds"

# Write results
time_csv_path=$(python construct_paths.py --path_name times_csv --detector "$DETECTOR_NAME" --embedding "$MODEL_NAME" --results_path "$top_results_dir" --results_name "$results_name")
echo "process,time" > "$time_csv_path"
echo "bulk_upload,$total_time" >> "$time_csv_path"

# Benchmark bulk face find
python ./run_face_find_bulk_benchmark.py --query_directory "$queries_directory" --collection_name "$collection_name" --results_path "$top_results_dir" --results_name "$results_name"

# Compute and save results
python ./test_data_metrics_benchmark.py --results_path "$top_results_dir" --results_name "$results_name" --detector "$DETECTOR_NAME" --embedding "$MODEL_NAME"


read -rp "Press any key to exit..." -n1
