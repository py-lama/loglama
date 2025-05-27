# LogLama Examples

This directory contains examples of how to use LogLama in different scenarios, from simple Python scripts to complex multi-component workflows. These examples demonstrate how to use LogLama as the primary service for centralized environment management and logging in the PyLama ecosystem.

## Basic Examples

### Basic Python Example

The `basic_python_example.py` script demonstrates how to use LogLama for logging in a simple Python script. It shows how to initialize the logger, set log levels, and log messages at different levels.

```bash
python basic_python_example.py
```

### Standalone Example

The `standalone_example.py` script is a self-contained example that includes all necessary imports and fallback mechanisms to use LogLama in a single file. This makes it easy to copy and use in any project, even if the full PyLama ecosystem is not installed.

```bash
python standalone_example.py
```

### Bash Example

The `bash_example.sh` script demonstrates how to use LogLama from a Bash script. It shows how to initialize the LogLama environment and log messages at different levels from a shell script.

```bash
chmod +x bash_example.sh
./bash_example.sh
```

### PyLama Integration Example

The `pylama_integration_example.py` script demonstrates how to use LogLama in a script that interacts with other PyLama components like PyLLM and BEXY. It shows how to leverage the centralized environment system to access shared configuration and dependencies.

```bash
python pylama_integration_example.py
```

## Multi-Component Workflow Example

The `multi_component_example` directory contains a comprehensive example of using LogLama in a multi-component workflow. It demonstrates how to use LogLama to coordinate and log a workflow that involves multiple components and scripts.

### Components

1. `run_workflow.sh` - The main script that orchestrates the workflow
2. `data_collector.py` - Collects data from various sources
3. `data_processor.py` - Processes the collected data
4. `model_inference.py` - Performs model inference on the processed data
5. `results_analyzer.py` - Analyzes the inference results and generates a report

### Running the Workflow

```bash
cd multi_component_example
chmod +x run_workflow.sh
./run_workflow.sh
```

### Viewing the Logs

After running any of these examples, you can view the logs using the LogLama CLI:

```bash
python -m loglama.cli.main logs
```

Or view them in the web interface:

```bash
python -m loglama.cli.main web
```

## Using LogLama in Your Own Projects

To use LogLama in your own projects, follow these steps:

1. Import the necessary modules:

```python
from loglama.core.logger import get_logger, setup_logging
from loglama.core.env_manager import load_central_env
```

2. Load the centralized environment:

```python
load_central_env()
```

3. Set up logging:

```python
setup_logging()
```

4. Get a logger for your module:

```python
logger = get_logger("your_module_name")
```

5. Use the logger in your code:

```python
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")

# Log with context
# Note: Avoid using reserved LogRecord attributes in 'extra'
# Reserved names include: 'args', 'asctime', 'created', 'exc_info', 'exc_text',
# 'filename', 'funcName', 'levelname', 'levelno', 'lineno', 'module',
# 'msecs', 'message', 'msg', 'name', 'pathname', 'process',
# 'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'
logger.info("Processing file", extra={"file_name": "example.txt", "file_size": 1024})

# Log with timing
with logger.time("operation_time"):
    # Your code here
    pass
```

## Integrating with Bash Scripts

To use LogLama from a Bash script, you can use the following pattern:

```bash
#!/bin/bash

# Set the path to the PyLama root directory
PYLAMA_ROOT="/path/to/py-lama"

# Function to log a message using LogLama
log_message() {
    local level="$1"
    local message="$2"
    local component="${3:-bash_script}"
    
    # Use Python to call LogLama's logger
    python3 -c "import sys; sys.path.append('$PYLAMA_ROOT'); from loglama.core.logger import get_logger; logger = get_logger('$component'); logger.$level('$message')" 
}

# Initialize LogLama environment
initialize_loglama() {
    python3 -c "import sys; sys.path.append('$PYLAMA_ROOT'); from loglama.core.env_manager import load_central_env; load_central_env()"
}

# Initialize LogLama
initialize_loglama

# Log messages
log_message "info" "Starting script"
log_message "warning" "This is a warning"
log_message "error" "This is an error"
```
