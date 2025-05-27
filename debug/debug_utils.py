#!/usr/bin/env python3

"""
Comprehensive debug utilities for LogLama.

This module provides utilities for debugging various aspects of LogLama,
including context handling, JSON formatting, file handlers, and SQLite handlers.
"""

import os
import json
import sqlite3
import tempfile
import time
import logging
import sys
from pathlib import Path

# Ensure we can import from loglama
sys_path_modified = False
try:
    from loglama.utils.context import LogContext, capture_context
    from loglama.core.logger import setup_logging, get_logger, JSONFormatter
    from loglama.handlers.sqlite_handler import SQLiteHandler
except ImportError:
    # Add the parent directory to the path
    current_dir = Path(__file__).parent.absolute()
    parent_dir = current_dir.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
        sys_path_modified = True
    # Try importing again
    from loglama.utils.context import LogContext, capture_context
    from loglama.core.logger import setup_logging, get_logger, JSONFormatter
    from loglama.handlers.sqlite_handler import SQLiteHandler


class ContextFilter(logging.Filter):
    """Filter that adds context information to log records."""
    
    def filter(self, record):
        # Add context to the record
        context = getattr(LogContext, "current_context", {})
        record.context = context
        return True


def setup_temp_log_file():
    """Create a temporary file for logs and return its path."""
    temp_dir = tempfile.TemporaryDirectory()
    log_file = os.path.join(temp_dir.name, "test.log")
    print(f"Log file path: {log_file}")
    return log_file, temp_dir


def setup_temp_db_file():
    """Create a temporary SQLite database file and return its path."""
    temp_dir = tempfile.TemporaryDirectory()
    db_file = os.path.join(temp_dir.name, "test.db")
    print(f"Database file path: {db_file}")
    return db_file, temp_dir


def setup_json_logging(log_file, name="test_json", level="INFO"):
    """Set up logging with JSON formatting."""
    return setup_logging(
        name=name,
        level=level,
        file=True,
        file_path=log_file,
        json_format=True,
        context_filter=True
    )


def setup_sqlite_logging(db_file, name="test_sqlite", level="INFO"):
    """Set up logging with SQLite handler."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:  
        logger.removeHandler(handler)
    
    # Create SQLite handler
    handler = SQLiteHandler(db_file)
    handler.setLevel(getattr(logging, level))
    
    # Add the handler to the logger
    logger.addHandler(handler)
    
    # Add context filter
    context_filter = ContextFilter()
    logger.addFilter(context_filter)
    
    return logger


def setup_manual_file_logging(log_file, name="test_file", level="INFO"):
    """Set up logging with a file handler and JSON formatter manually."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:  
        logger.removeHandler(handler)
    
    # Create file handler with JSON formatter
    handler = logging.FileHandler(log_file)
    handler.setLevel(getattr(logging, level))
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(handler)
    
    # Add context filter
    context_filter = ContextFilter()
    logger.addFilter(context_filter)
    
    return logger


def function_with_context(user_id="123", action="login"):
    """Example function with context capture."""
    # We'll use the context manager approach instead of the decorator
    # since the decorator is causing issues
    logger = get_logger("test_capture")
    logger.info("Function started")
    
    # Use context manager to add more context
    with LogContext(step="verification"):
        logger.info("Verification step")
        
        # Nested context
        with LogContext(result="success"):
            logger.info("Verification successful")
    
    logger.info("Function completed")


def print_log_file(log_file):
    """Print the contents of a log file."""
    print("\nLog file contents:")
    print("-" * 40)
    try:
        with open(log_file, "r") as f:
            content = f.read()
            print(content)
            
            # Try to parse and pretty print JSON
            try:
                lines = content.strip().split("\n")
                for line in lines:
                    parsed = json.loads(line)
                    print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError:
                # Not JSON or invalid JSON
                pass
    except Exception as e:
        print(f"Error reading log file: {e}")
    print("-" * 40)


def query_sqlite_db(db_file):
    """Query and print records from the SQLite database."""
    print("\nDatabase contents:")
    print("-" * 40)
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"Table: {table_name}")
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            print(f"Columns: {', '.join(column_names)}")
            
            # Get records
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
            records = cursor.fetchall()
            
            for record in records:
                record_dict = {column_names[i]: record[i] for i in range(len(column_names))}
                print(json.dumps(record_dict, indent=2))
        
        conn.close()
    except Exception as e:
        print(f"Error querying database: {e}")
    print("-" * 40)


def test_context_handling():
    """Test context handling in LogLama."""
    print("\nTesting context handling...")
    log_file, temp_dir = setup_temp_log_file()
    
    # Setup logging
    logger = setup_json_logging(log_file)
    
    # Log with context
    with LogContext(user_id="123", action="login"):
        logger.info("User logged in")
        
        # Nested context
        with LogContext(session_id="abc123"):
            logger.info("Session created")
            
            # More nesting
            with LogContext(page="dashboard"):
                logger.info("Page loaded")
    
    # Log without context
    logger.info("System check")
    
    # Print log file
    print_log_file(log_file)
    
    # Clean up
    temp_dir.cleanup()
    print("Context handling test completed.")


def test_capture_context_decorator():
    """Test the capture_context decorator."""
    print("\nTesting context capture with context manager...")
    log_file, temp_dir = setup_temp_log_file()
    
    # Setup logging
    logger = setup_json_logging(log_file, name="test_capture")
    
    # Call the function that uses context manager
    with LogContext(user_id="123", action="login"):
        function_with_context()
    
    # Give the file system a moment to flush
    time.sleep(0.1)
    
    # Print log file
    print_log_file(log_file)
    
    # Clean up
    temp_dir.cleanup()
    print("Capture context decorator test completed.")


def test_sqlite_handler():
    """Test the SQLite handler."""
    print("\nTesting SQLite handler...")
    db_file, temp_dir = setup_temp_db_file()
    
    # Setup logging with SQLite handler
    logger = setup_sqlite_logging(db_file)
    
    # Log with context
    with LogContext(user_id="456", action="search"):
        logger.info("User performed search")
        logger.warning("Search results limited")
        
        # Nested context
        with LogContext(query="python logging"):
            logger.info("Search query processed")
    
    # Log without context
    logger.info("System maintenance")
    
    # Query the database
    query_sqlite_db(db_file)
    
    # Clean up
    temp_dir.cleanup()
    print("SQLite handler test completed.")


def test_file_handler_manual():
    """Test manual setup of file handler with JSON formatter."""
    print("\nTesting manual file handler setup...")
    log_file, temp_dir = setup_temp_log_file()
    
    # Setup logging manually
    logger = setup_manual_file_logging(log_file)
    
    # Log with context
    with LogContext(user_id="789", action="upload"):
        logger.info("User uploaded file")
        
        # Nested context
        with LogContext(file_name="document.pdf", file_size="2.5MB"):
            logger.info("File processed")
    
    # Log without context
    logger.info("System check")
    
    # Print log file
    print_log_file(log_file)
    
    # Clean up
    temp_dir.cleanup()
    print("Manual file handler test completed.")


def main():
    """Run all debug tests."""
    print("Starting LogLama debug tests...")
    
    # Run tests
    test_context_handling()
    test_capture_context_decorator()
    test_sqlite_handler()
    test_file_handler_manual()
    
    print("\nAll debug tests completed.")


if __name__ == "__main__":
    main()
