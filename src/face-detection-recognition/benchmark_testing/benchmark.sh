#!/bin/bash

# Source environment variables
source ../../../.env

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

MODEL_CONFIG=$(poetry run python construct_paths.py --path_name model_config)

MODEL_NAME="Facenet512" # Default model name
DETECTOR_NAME="retinaface" # Default detector name

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
results_dir=$(poetry run python construct_paths.py --path_name results_dir --detector "$DETECTOR_NAME" --embedding "$MODEL_NAME" --results_path "$top_results_dir" --results_name "$results_name")

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
# BENCHMARKING
#
#**************************************************************************************


SERVER_PATH=$(poetry run python construct_paths.py --path_name facematch_server)

cd ../../../

# Delete collection if exists
if [ "$keep_collection" = "False" ]; then
    poetry run python $SERVER_PATH /face-match/deletecollection "$collection_name,$MODEL_NAME,$DETECTOR_NAME"
fi

# Benchmark bulk upload
start_time=$(date +%s)
poetry run python $SERVER_PATH /face-match/bulkupload "$database_directory" "Create a new collection,$collection_name"
end_time=$(date +%s)
total_time=$((end_time - start_time))
echo "Bulk Upload Time: $total_time seconds"

# Write results
time_csv_path=$(poetry run python src/face-detection-recognition/benchmark_testing/construct_paths.py --path_name times_csv --detector "$DETECTOR_NAME" --embedding "$MODEL_NAME" --results_path "$top_results_dir" --results_name "$results_name")
echo "process,time" > "$time_csv_path"
echo "bulk_upload,$total_time" >> "$time_csv_path"

# Benchmark bulk face find
poetry run python src/face-detection-recognition/benchmark_testing/run_face_find_bulk_benchmark.py --query_directory "$queries_directory" --collection_name "$collection_name" --results_path "$top_results_dir" --results_name "$results_name"

# Compute and save results
poetry run python src/face-detection-recognition/benchmark_testing/calc_data_metrics_benchmark.py --results_path "$top_results_dir" --results_name "$results_name" --detector "$DETECTOR_NAME" --embedding "$MODEL_NAME"


read -rp "Press any key to exit..." -n1
