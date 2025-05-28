#!/bin/bash

# Comprehensive example of using LogLama in a multi-component workflow
# This script demonstrates how to use LogLama to coordinate and log a workflow
# that involves multiple components and scripts

# Set the path to the PyLama root directory
DEVLAMA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
EXAMPLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to log a message using LogLama
log_message() {
    local level="$1"
    local message="$2"
    local component="${3:-workflow_manager}"
    
    # Use Python to call LogLama's logger
    python3 -c "import sys; sys.path.append('$DEVLAMA_ROOT'); from loglama.core.logger import get_logger; logger = get_logger('$component'); logger.$level('$message')"
}

# Function to initialize LogLama environment
initialize_loglama() {
    echo "Initializing LogLama environment..."
    python3 -c "import sys; sys.path.append('$DEVLAMA_ROOT'); from loglama.core.env_manager import load_central_env, ensure_required_env_vars; load_central_env(); ensure_required_env_vars()"
    echo "LogLama environment initialized"
}

# Function to run a Python script with proper logging
run_python_script() {
    local script_name="$1"
    local script_path="$EXAMPLE_DIR/$script_name"
    
    log_message "info" "Starting Python script: $script_name"
    echo "Running $script_name..."
    
    # Run the script and capture its exit code
    python3 "$script_path"
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_message "info" "Python script completed successfully: $script_name"
    else
        log_message "error" "Python script failed with exit code $exit_code: $script_name"
    fi
    
    return $exit_code
}

# Create necessary directories
mkdir -p "$EXAMPLE_DIR/data"
mkdir -p "$EXAMPLE_DIR/output"

# Main workflow
echo "Starting multi-component workflow"

# Initialize LogLama environment
initialize_loglama

# Log workflow start
log_message "info" "Starting multi-component workflow"

# Step 1: Data Collection
log_message "info" "Step 1: Data Collection"
run_python_script "data_collector.py"
if [ $? -ne 0 ]; then
    log_message "error" "Workflow failed at Step 1: Data Collection"
    exit 1
fi

# Step 2: Data Processing
log_message "info" "Step 2: Data Processing"
run_python_script "data_processor.py"
if [ $? -ne 0 ]; then
    log_message "error" "Workflow failed at Step 2: Data Processing"
    exit 1
fi

# Step 3: Model Inference
log_message "info" "Step 3: Model Inference"
run_python_script "model_inference.py"
if [ $? -ne 0 ]; then
    log_message "error" "Workflow failed at Step 3: Model Inference"
    exit 1
fi

# Step 4: Results Analysis
log_message "info" "Step 4: Results Analysis"
run_python_script "results_analyzer.py"
if [ $? -ne 0 ]; then
    log_message "error" "Workflow failed at Step 4: Results Analysis"
    exit 1
fi

# Log workflow completion
log_message "info" "Multi-component workflow completed successfully"

echo "Workflow completed successfully"
echo "Check the logs using: python -m loglama.cli.main logs"
