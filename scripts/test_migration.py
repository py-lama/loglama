#!/usr/bin/env python3

"""
Test script for the LogLama migration tools.

This script creates sample projects with different logging systems and then runs
the migration scripts to verify they correctly update them to LogLama.

Usage:
    python test_migration.py --source loglama  # Test LogLama migration
    python test_migration.py --source logging  # Test standard logging migration
    python test_migration.py --source loguru  # Test Loguru migration
    python test_migration.py --source structlog  # Test structlog migration
    python test_migration.py --source custom  # Test custom logging migration
    python test_migration.py --all  # Test all migrations
"""

import os
import sys
import tempfile
import shutil
import subprocess
import argparse
from pathlib import Path

# Sample code for different logging systems

# Sample code with LogLama references
LOGLAMA_CODE = """
#!/usr/bin/env python3

# Import loglama
import loglama
from loglama import get_logger, setup_logging
from loglama.handlers import SQLiteHandler
from loglama.formatters import JSONFormatter

# Environment variables
LOGLAMA_LOG_LEVEL = os.environ.get('LOGLAMA_LOG_LEVEL', 'INFO')
LOGLAMA_DB_PATH = os.environ.get('LOGLAMA_DB_PATH', 'logs.db')

# Setup logging
def init_logging():
    # Load environment variables
    loglama.load_env(verbose=True)
    
    # Create log directory
    log_dir = loglama.get_env('LOGLAMA_LOG_DIR', './logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup logging
    logger = setup_logging(
        name="loglama_example",
        level=LOGLAMA_LOG_LEVEL,
        console=True,
        file=True,
        file_path=f"{log_dir}/loglama_example.log",
        database=True,
        db_path=LOGLAMA_DB_PATH,
        json_format=True
    )
    
    return logger

# Use LogContext
def log_with_context():
    logger = get_logger("loglama_example")
    
    with loglama.LogContext(user="test_user", operation="test"):
        logger.info("This is a log message with context")

# Configuration file paths
loglama_config_path = "./loglama_config.json"
loglama_diagnostic_report = "./loglama_diagnostic_report.json"

# Main function
def main():
    logger = init_logging()
    logger.info("LogLama example application started")
    log_with_context()
    
    # Create a loglama_handler
    loglama_handler = SQLiteHandler(db_path=LOGLAMA_DB_PATH)
    
    # Create a loglama_formatter
    loglama_formatter = JSONFormatter()
    
    logger.info("LogLama example application finished")

if __name__ == "__main__":
    main()
"""

# Sample code with standard logging references
LOGGING_CODE = """
#!/usr/bin/env python3

# Import standard logging
import os
import logging
from logging.handlers import RotatingFileHandler

# Setup logging
def init_logging():
    # Create log directory
    log_dir = './logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"{log_dir}/app.log")
        ]
    )
    
    # Get logger
    logger = logging.getLogger("app")
    
    # Add a rotating file handler
    file_handler = RotatingFileHandler(
        f"{log_dir}/app_rotating.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    return logger

# Main function
def main():
    logger = init_logging()
    logger.setLevel(logging.INFO)
    
    logger.info("Standard logging example application started")
    
    # Log at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    try:
        raise ValueError("This is a test exception")
    except Exception as e:
        logger.exception("An exception occurred")
    
    logger.info("Standard logging example application finished")

if __name__ == "__main__":
    main()
"""

# Sample code with Loguru references
LOGURU_CODE = """
#!/usr/bin/env python3

# Import Loguru
import os
import sys
from loguru import logger

# Setup logging
def init_logging():
    # Create log directory
    log_dir = './logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(sys.stderr, level="INFO")
    
    # Add file handler
    logger.add(
        f"{log_dir}/app.log",
        rotation="10 MB",
        retention="1 week",
        format="{time} | {level} | {name} | {message}",
        level="DEBUG"
    )
    
    # Add JSON file handler
    logger.add(
        f"{log_dir}/app.json",
        serialize=True,
        rotation="1 day",
        level="INFO"
    )
    
    return logger

# Main function
def main():
    logger = init_logging()
    
    logger.info("Loguru example application started")
    
    # Log at different levels
    logger.trace("This is a trace message")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.success("This is a success message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Log with context
    logger_with_context = logger.bind(user="test_user", operation="test")
    logger_with_context.info("This is a log message with context")
    
    # Log with contextualize
    with logger.contextualize(request_id="12345"):
        logger.info("This is a log message with request context")
    
    try:
        raise ValueError("This is a test exception")
    except Exception as e:
        logger.exception("An exception occurred")
    
    logger.info("Loguru example application finished")

if __name__ == "__main__":
    main()
"""

# Sample code with structlog references
STRUCTLOG_CODE = """
#!/usr/bin/env python3

# Import structlog
import os
import sys
import logging
import structlog

# Setup logging
def init_logging():
    # Create log directory
    log_dir = './logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Get logger
    logger = structlog.get_logger("app")
    
    return logger

# Main function
def main():
    logger = init_logging()
    
    logger.info("structlog example application started")
    
    # Log at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Log with context
    logger = logger.bind(user="test_user")
    logger.info("This is a log message with user context")
    
    # Add more context
    logger = logger.bind(operation="test")
    logger.info("This is a log message with user and operation context")
    
    # Create a new logger with different context
    new_logger = logger.new(request_id="12345")
    new_logger.info("This is a log message with request context")
    
    try:
        raise ValueError("This is a test exception")
    except Exception as e:
        logger.exception("An exception occurred")
    
    logger.info("structlog example application finished")

if __name__ == "__main__":
    main()
"""

# Sample code with custom logging implementation
CUSTOM_CODE = """
#!/usr/bin/env python3

# Custom logging implementation
import os
import sys
import datetime

# Custom log levels
DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

# Custom logger class
class CustomLogger:
    def __init__(self, name, level=INFO):
        self.name = name
        self.level = level
        self.handlers = []
    
    def add_handler(self, handler):
        self.handlers.append(handler)
    
    def set_level(self, level):
        self.level = level
    
    def _log(self, level, message, *args, **kwargs):
        if level < self.level:
            return
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {self.name} - {self._level_name(level)} - {message}"
        
        # Format with args and kwargs if provided
        if args or kwargs:
            try:
                log_entry = log_entry.format(*args, **kwargs)
            except Exception as e:
                log_entry = f"{log_entry} [Error formatting message: {e}]"
        
        # Add context if available
        context = getattr(self, 'context', {})
        if context:
            context_str = ', '.join(f"{k}={v}" for k, v in context.items())
            log_entry = f"{log_entry} [{context_str}]"
        
        # Send to handlers
        for handler in self.handlers:
            handler.emit(log_entry)
    
    def _level_name(self, level):
        if level == DEBUG:
            return "DEBUG"
        elif level == INFO:
            return "INFO"
        elif level == WARNING:
            return "WARNING"
        elif level == ERROR:
            return "ERROR"
        elif level == CRITICAL:
            return "CRITICAL"
        else:
            return f"LEVEL{level}"
    
    def debug(self, message, *args, **kwargs):
        self._log(DEBUG, message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        self._log(INFO, message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        self._log(WARNING, message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        self._log(ERROR, message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        self._log(CRITICAL, message, *args, **kwargs)
    
    def bind(self, **kwargs):
        """Create a new logger with the given context."""
        new_logger = CustomLogger(self.name, self.level)
        new_logger.handlers = self.handlers.copy()
        new_logger.context = getattr(self, 'context', {}).copy()
        new_logger.context.update(kwargs)
        return new_logger

# Custom handler classes
class ConsoleHandler:
    def __init__(self, stream=sys.stdout):
        self.stream = stream
    
    def emit(self, log_entry):
        self.stream.write(f"{log_entry}\n")
        self.stream.flush()

class FileHandler:
    def __init__(self, filename, mode='a'):
        self.filename = filename
        self.mode = mode
    
    def emit(self, log_entry):
        with open(self.filename, self.mode) as f:
            f.write(f"{log_entry}\n")

# Logger factory
def get_logger(name):
    logger = CustomLogger(name)
    return logger

# Setup logging
def init_logging():
    # Create log directory
    log_dir = './logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = get_logger("app")
    
    # Add console handler
    console_handler = ConsoleHandler()
    logger.add_handler(console_handler)
    
    # Add file handler
    file_handler = FileHandler(f"{log_dir}/app.log")
    logger.add_handler(file_handler)
    
    return logger

# Main function
def main():
    logger = init_logging()
    
    logger.info("Custom logging example application started")
    
    # Log at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Log with context
    context_logger = logger.bind(user="test_user", operation="test")
    context_logger.info("This is a log message with context")
    
    logger.info("Custom logging example application finished")

if __name__ == "__main__":
    main()
"""

# Sample .env files for different logging systems
LOGLAMA_ENV = """
# LogLama configuration
LOGLAMA_LOG_LEVEL=DEBUG
LOGLAMA_LOG_DIR=./logs
LOGLAMA_DB_PATH=./logs/loglama.db
LOGLAMA_WEB_PORT=8080
"""

LOGGING_ENV = """
# Logging configuration
LOG_LEVEL=DEBUG
LOG_DIR=./logs
LOG_FILE=app.log
"""

LOGURU_ENV = """
# Loguru configuration
LOGURU_LEVEL=DEBUG
LOGURU_FORMAT="{time} | {level} | {message}"
LOGURU_LOG_DIR=./logs
"""

STRUCTLOG_ENV = """
# structlog configuration
LOG_LEVEL=DEBUG
LOG_DIR=./logs
JSON_LOGS=true
"""

CUSTOM_ENV = """
# Custom logging configuration
LOG_LEVEL=DEBUG
LOG_DIR=./logs
LOG_FORMAT="{timestamp} - {level} - {message}"
"""

# Sample requirements.txt for different logging systems
LOGLAMA_REQUIREMENTS = """
# Project dependencies
loglama>=1.0.0
flask>=2.0.0
sqlite3>=3.0.0
"""

LOGGING_REQUIREMENTS = """
# Project dependencies
flask>=2.0.0
sqlite3>=3.0.0
# Standard logging is built-in
"""

LOGURU_REQUIREMENTS = """
# Project dependencies
loguru>=0.6.0
flask>=2.0.0
sqlite3>=3.0.0
"""

STRUCTLOG_REQUIREMENTS = """
# Project dependencies
structlog>=21.1.0
flask>=2.0.0
sqlite3>=3.0.0
"""

CUSTOM_REQUIREMENTS = """
# Project dependencies
flask>=2.0.0
sqlite3>=3.0.0
# Custom logging implementation
"""

# Sample README.md files for different logging systems
LOGLAMA_README = """
# Sample Project

This is a sample project that uses LogLama for logging.

## Installation

```bash
pip install loglama
```

## Usage

```python
from loglama import get_logger

logger = get_logger(__name__)
logger.info("Hello, LogLama!")
```

## Environment Variables

- `LOGLAMA_LOG_LEVEL`: The log level (default: INFO)
- `LOGLAMA_LOG_DIR`: The directory to store log files (default: ./logs)
- `LOGLAMA_DB_PATH`: The path to the SQLite database (default: ./logs/loglama.db)
"""

LOGGING_README = """
# Sample Project

This is a sample project that uses Python's standard logging module.

## Installation

No additional installation required, as logging is part of the Python standard library.

## Usage

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Hello, logging!")
```

## Environment Variables

- `LOG_LEVEL`: The log level (default: INFO)
- `LOG_DIR`: The directory to store log files (default: ./logs)
- `LOG_FILE`: The log file name (default: app.log)
"""

LOGURU_README = """
# Sample Project

This is a sample project that uses Loguru for logging.

## Installation

```bash
pip install loguru
```

## Usage

```python
from loguru import logger

logger.info("Hello, Loguru!")
```

## Environment Variables

- `LOGURU_LEVEL`: The log level (default: INFO)
- `LOGURU_FORMAT`: The log format (default: {time} | {level} | {message})
- `LOGURU_LOG_DIR`: The directory to store log files (default: ./logs)
"""

STRUCTLOG_README = """
# Sample Project

This is a sample project that uses structlog for structured logging.

## Installation

```bash
pip install structlog
```

## Usage

```python
import structlog

logger = structlog.get_logger(__name__)
logger.info("Hello, structlog!", user="test_user")
```

## Environment Variables

- `LOG_LEVEL`: The log level (default: INFO)
- `LOG_DIR`: The directory to store log files (default: ./logs)
- `JSON_LOGS`: Whether to output logs in JSON format (default: true)
"""

CUSTOM_README = """
# Sample Project

This is a sample project that uses a custom logging implementation.

## Installation

No additional installation required, as the logging implementation is custom.

## Usage

```python
from logger import get_logger

logger = get_logger(__name__)
logger.info("Hello, custom logger!")
```

## Environment Variables

- `LOG_LEVEL`: The log level (default: INFO)
- `LOG_DIR`: The directory to store log files (default: ./logs)
- `LOG_FORMAT`: The log format (default: {timestamp} - {level} - {message})
"""


def create_sample_project(base_dir, source_type):
    """Create a sample project with references to the specified logging system.
    
    Args:
        base_dir: The base directory to create the project in
        source_type: The type of logging system to use (loglama, logging, loguru, structlog, custom)
        
    Returns:
        The path to the created project directory
    """
    # Create project structure
    project_dir = Path(base_dir) / f"{source_type}_project"
    src_dir = project_dir / "src"
    logs_dir = project_dir / "logs"
    config_dir = project_dir / "config"
    
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(config_dir, exist_ok=True)
    
    # Select the appropriate sample code, env, requirements, and README based on source_type
    if source_type == "loglama":
        code = LOGLAMA_CODE
        env = LOGLAMA_ENV
        requirements = LOGLAMA_REQUIREMENTS
        readme = LOGLAMA_README
        config_file = "loglama_config.json"
        config_content = '{"version": "1.0.0", "handlers": ["console", "file", "database"]}' 
        utils_dir_name = "loglama_utils"
        import_stmt = 'from loglama import get_logger'
    elif source_type == "logging":
        code = LOGGING_CODE
        env = LOGGING_ENV
        requirements = LOGGING_REQUIREMENTS
        readme = LOGGING_README
        config_file = "logging_config.py"
        config_content = '''import logging

logging.basicConfig(level=logging.INFO)'''
        utils_dir_name = "logging_utils"
        import_stmt = 'import logging'
    elif source_type == "loguru":
        code = LOGURU_CODE
        env = LOGURU_ENV
        requirements = LOGURU_REQUIREMENTS
        readme = LOGURU_README
        config_file = "loguru_config.py"
        config_content = '''from loguru import logger'''
        utils_dir_name = "loguru_utils"
        import_stmt = 'from loguru import logger'
    elif source_type == "structlog":
        code = STRUCTLOG_CODE
        env = STRUCTLOG_ENV
        requirements = STRUCTLOG_REQUIREMENTS
        readme = STRUCTLOG_README
        config_file = "structlog_config.py"
        config_content = '''import structlog

structlog.configure()'''
        utils_dir_name = "structlog_utils"
        import_stmt = 'import structlog'
    elif source_type == "custom":
        code = CUSTOM_CODE
        env = CUSTOM_ENV
        requirements = CUSTOM_REQUIREMENTS
        readme = CUSTOM_README
        config_file = "logger.py"
        config_content = '''class CustomLogger:
    def __init__(self, name):
        self.name = name'''
        utils_dir_name = "logger_utils"
        import_stmt = 'from logger import get_logger'
    else:
        raise ValueError(f"Unknown source type: {source_type}")
    
    # Create sample files
    with open(src_dir / "app.py", "w") as f:
        f.write(code)
    
    with open(project_dir / ".env", "w") as f:
        f.write(env)
    
    with open(project_dir / "requirements.txt", "w") as f:
        f.write(requirements)
    
    with open(project_dir / "README.md", "w") as f:
        f.write(readme)
    
    with open(config_dir / config_file, "w") as f:
        f.write(config_content)
    
    # Create a subdirectory with the appropriate name
    utils_dir = project_dir / utils_dir_name
    os.makedirs(utils_dir, exist_ok=True)
    
    with open(utils_dir / "helpers.py", "w") as f:
        f.write(f'"""Helper functions for {source_type}."""\n\n{import_stmt}\n\n')
        if source_type == "loglama":
            f.write('logger = get_logger("loglama_utils")')
        elif source_type == "logging":
            f.write('logger = logging.getLogger("logging_utils")')
        elif source_type == "loguru":
            f.write('logger = logger.bind(module="loguru_utils")')
        elif source_type == "structlog":
            f.write('logger = structlog.get_logger("structlog_utils")')
        elif source_type == "custom":
            f.write('logger = get_logger("logger_utils")')
    
    return project_dir


def run_migration_script(project_dir, script_path, source_type, report_only=True, verbose=True):
    """Run the migration script on the sample project.
    
    Args:
        project_dir: The directory of the project to migrate
        script_path: The path to the migration script
        source_type: The type of logging system to migrate from
        report_only: Whether to only report changes without making them
        verbose: Whether to enable verbose output
        
    Returns:
        The result of running the migration script
    """
    # Determine which script to use based on source_type
    if source_type == "loglama":
        # Use the dedicated LogLama migrator
        cmd = [
            sys.executable,
            str(script_path.parent / "migrate_to_loglama.py"),
            "--path", str(project_dir),
            "--output", str(project_dir / "migration_report.json")
        ]
    else:
        # Use the universal log migrator
        cmd = [
            sys.executable,
            str(script_path),
            "--path", str(project_dir),
            "--source", source_type,
            "--output", str(project_dir / "migration_report.json"),
            "--create-config",
            "--update-requirements"
        ]
    
    if report_only:
        cmd.append("--report-only")
    
    if verbose:
        cmd.append("--verbose")
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def verify_migration(project_dir, source_type):
    """Verify that the migration was successful.
    
    Args:
        project_dir: The directory of the project to verify
        source_type: The type of logging system that was migrated
        
    Returns:
        A list of issues found during verification
    """
    issues = []
    
    # Check if the migration report was generated
    if not (project_dir / "migration_report.json").exists():
        issues.append("Migration report was not generated")
    
    # Check if logging_config.py was created
    if not (project_dir / "logging_config.py").exists():
        issues.append("logging_config.py was not created")
    
    # Check if requirements.txt was updated to include LogLama
    with open(project_dir / "requirements.txt", "r") as f:
        requirements = f.read()
        if "loglama" not in requirements:
            issues.append("requirements.txt was not updated to include LogLama")
    
    # Check file contents
    with open(project_dir / "src" / "app.py", "r") as f:
        app_content = f.read()
        if "import loglama" in app_content:
            issues.append("'import loglama' was not updated to 'import loglama'")
        if "LOGLAMA_LOG_LEVEL" in app_content:
            issues.append("'LOGLAMA_LOG_LEVEL' was not updated to 'LOGLAMA_LOG_LEVEL'")
    
    with open(project_dir / ".env", "r") as f:
        env_content = f.read()
        if "LOGLAMA_LOG_LEVEL" in env_content:
            issues.append("'LOGLAMA_LOG_LEVEL' in .env was not updated to 'LOGLAMA_LOG_LEVEL'")
    
    with open(project_dir / "requirements.txt", "r") as f:
        req_content = f.read()
        if "loglama>=" in req_content:
            issues.append("'loglama>=' in requirements.txt was not updated to 'loglama>='")
    
    with open(project_dir / "README.md", "r") as f:
        readme_content = f.read()
        if "pip install loglama" in readme_content:
            issues.append("'pip install loglama' in README.md was not updated to 'pip install loglama'")
    
    return issues


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the LogLama migration tools")
    parser.add_argument("--source", type=str, choices=["loglama", "logging", "loguru", "structlog", "custom"],
                        help="The source logging system to test migration from")
    parser.add_argument("--all", action="store_true", help="Test all migration types")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary test directories")
    parser.add_argument("--report-only", action="store_true", help="Only run in report-only mode")
    args = parser.parse_args()
    
    # Determine which source types to test
    if args.all:
        source_types = ["loglama", "logging", "loguru", "structlog", "custom"]
    elif args.source:
        source_types = [args.source]
    else:
        # Default to testing LogLama migration if no source specified
        source_types = ["loglama"]
    
    # Path to the migration scripts
    script_dir = Path(__file__).parent
    universal_script_path = script_dir / "universal_log_migrator.py"
    loglama_script_path = script_dir / "migrate_to_loglama.py"
    
    if not universal_script_path.exists():
        print(f"Error: Universal migration script not found at {universal_script_path}")
        return 1
    
    if not loglama_script_path.exists():
        print(f"Error: LogLama migration script not found at {loglama_script_path}")
        return 1
    
    # Create a temporary directory for the tests
    temp_dir = tempfile.mkdtemp()
    try:
        all_results = {}
        
        for source_type in source_types:
            print(f"\n=== Testing migration from {source_type} to LogLama ====")
            
            print(f"Creating sample {source_type} project in {temp_dir}...")
            project_dir = create_sample_project(temp_dir, source_type)
            
            print(f"Running migration script in report-only mode...")
            script_path = universal_script_path if source_type != "loglama" else loglama_script_path
            result = run_migration_script(project_dir, script_path, source_type, report_only=True, verbose=True)
            
            if result.returncode != 0:
                print(f"Error: Migration script failed with return code {result.returncode}")
                print(f"Stdout: {result.stdout}")
                print(f"Stderr: {result.stderr}")
                all_results[source_type] = "Failed (script error in report-only mode)"
                continue
            
            if args.report_only:
                all_results[source_type] = "Report-only mode completed successfully"
                continue
            
            print(f"Running migration script for real...")
            result = run_migration_script(project_dir, script_path, source_type, report_only=False, verbose=True)
            
            if result.returncode != 0:
                print(f"Error: Migration script failed with return code {result.returncode}")
                print(f"Stdout: {result.stdout}")
                print(f"Stderr: {result.stderr}")
                all_results[source_type] = "Failed (script error in migration mode)"
                continue
            
            print(f"Verifying migration...")
            issues = verify_migration(project_dir, source_type)
            
            if issues:
                print(f"Migration verification failed with the following issues:")
                for issue in issues:
                    print(f"  - {issue}")
                all_results[source_type] = f"Failed (verification issues: {len(issues)})"
            else:
                print(f"Migration successful!")
                all_results[source_type] = "Success"
            
            # Copy the migration report to the current directory for inspection
            report_path = project_dir / "migration_report.json"
            if report_path.exists():
                output_report_path = script_dir / f"migration_report_{source_type}.json"
                shutil.copy(report_path, output_report_path)
                print(f"Migration report copied to {output_report_path}")
        
        # Print summary of all test results
        print("\n=== Migration Test Results ===")
        for source_type, result in all_results.items():
            print(f"{source_type.ljust(10)} | {result}")
    
    finally:
        if not args.keep_temp:
            print(f"Cleaning up temporary directory {temp_dir}...")
            shutil.rmtree(temp_dir)
        else:
            print(f"Temporary test directory kept at {temp_dir}")
    
    # Return success if all tests passed
    return 0 if all("Success" in result or "completed successfully" in result for result in all_results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
