#!/usr/bin/env python3

"""
Test script to verify logging integration across the PyLama ecosystem.
"""

import os
import sys
import time

# Add the parent directory to the path so we can import the components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the simplified logging interface
from loglama.core.simple_logger import (
    info, debug, warning, error, critical, exception,
    timed, logged, configure_db_logging, set_global_context
)

# Configure database logging
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "ecosystem_test.db")
configure_db_logging(db_path)

# Set global context for all log messages
set_global_context(test_name="ecosystem_logging_test", timestamp=time.time())


@timed
def test_devlama_logging():
    """Test logging from PyLama component."""
    info("Testing PyLama logging", logger_name="devlama.test")
    debug("Debug message from PyLama", logger_name="devlama.test")
    warning("Warning message from PyLama", logger_name="devlama.test")
    time.sleep(0.5)  # Simulate some work
    return "PyLama logging test completed"


@timed
def test_apilama_logging():
    """Test logging from APILama component."""
    info("Testing APILama logging", logger_name="apilama.test")
    debug("Debug message from APILama", logger_name="apilama.test")
    warning("Warning message from APILama", logger_name="apilama.test")
    time.sleep(0.5)  # Simulate some work
    return "APILama logging test completed"


@timed
def test_weblama_logging():
    """Test logging from WebLama component."""
    info("Testing WebLama logging", logger_name="weblama.test")
    debug("Debug message from WebLama", logger_name="weblama.test")
    warning("Warning message from WebLama", logger_name="weblama.test")
    time.sleep(0.5)  # Simulate some work
    return "WebLama logging test completed"


@logged(comment="Main test function")
def main():
    """Main test function."""
    info("Starting ecosystem logging test")
    
    # Test logging from different components
    devlama_result = test_devlama_logging()
    info(f"PyLama test result: {devlama_result}")
    
    apilama_result = test_apilama_logging()
    info(f"APILama test result: {apilama_result}")
    
    weblama_result = test_weblama_logging()
    info(f"WebLama test result: {weblama_result}")
    
    # Test error logging
    try:
        # Simulate an error
        raise ValueError("Test error")
    except Exception as e:
        error(f"Error during test: {str(e)}")
        exception("Exception details", exc_info=True)
    
    info("Ecosystem logging test completed")
    print(f"\nTest completed successfully!")
    print(f"Logs are stored in the database: {db_path}")
    print(f"You can view the logs using the LogLama web interface:")
    print(f"  python -m loglama.cli.main web --db {db_path}")


if __name__ == "__main__":
    main()
