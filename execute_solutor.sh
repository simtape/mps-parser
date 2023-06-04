#!/bin/bash

# Define the path to the Python script
python_script="main.py"

# Define the list of MPS files
mps_files=(
  "mps_files/blend2.mps"
  "mps_files/control30-3-2-3.mps"
  "mps_files/gen-ip002.mps"
  "mps_files/gen-ip021.mps"
  "mps_files/graphdraw-gemcutter.mps"
  "mps_files/mas74.mps"
  "mps_files/misc05inf.mps"
  "mps_files/neos-3046601-motu.mps"
  "mps_files/nexp-50-20-1-1.mps"
  "mps_files/rout.mps"
)

# Define the values for X (r, c, n)
x_values=("r" "c" "n")

# Define the execution time limit in seconds
execution_time_limit=180

# Create a log directory if it doesn't exist
log_dir="logs"
mkdir -p "$log_dir"

# Iterate over each MPS file
for mps_file in "${mps_files[@]}"; do
  # Extract the file name without the directory
  mps_file_name=$(basename "$mps_file")

  # Iterate over each X value
  for x_value in "${x_values[@]}"; do
    # Construct the log file name
    log_file="$log_dir/${mps_file_name}_${x_value}.log"

    # Execute the Python script with the given X value and MPS file
    echo "Executing: python3 $python_script -${x_value} $mps_file"
    timeout "$execution_time_limit" python3 "$python_script" "-${x_value}" "$mps_file" > "$log_file" 2>&1

    # Check the exit code of the Python script
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
      echo "Execution timed out. Result saved in $log_file"
    elif [ $exit_code -ne 0 ]; then
      echo "Execution failed with exit code $exit_code"
    else
      echo "Execution completed. Result saved in $log_file"
    fi
  done
done