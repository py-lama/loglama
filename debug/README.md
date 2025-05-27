# LogLama Debug Utilities

This directory contains utilities for debugging and testing various aspects of LogLama.

## Overview

The `debug_utils.py` script provides a comprehensive set of utilities for debugging and testing LogLama's features, including:

- Context handling with `LogContext`
- Context capture with the `@capture_context` decorator
- JSON formatting of log messages
- File handler configuration
- SQLite handler integration

## Usage

You can run the entire test suite by executing the script directly:

```bash
python debug_utils.py
```

Or you can import specific utilities to test individual components:

```python
from debug.debug_utils import test_context_handling, test_sqlite_handler

# Test only context handling
test_context_handling()

# Test only SQLite handler
test_sqlite_handler()
```

## Available Test Functions

- `test_context_handling()`: Tests basic context handling with `LogContext`
- `test_capture_context_decorator()`: Tests the `@capture_context` decorator
- `test_sqlite_handler()`: Tests logging to SQLite database
- `test_file_handler_manual()`: Tests manual setup of file handlers with JSON formatting

## Utility Functions

- `setup_temp_log_file()`: Creates a temporary log file
- `setup_temp_db_file()`: Creates a temporary SQLite database file
- `setup_json_logging()`: Sets up logging with JSON formatting
- `setup_sqlite_logging()`: Sets up logging with SQLite handler
- `setup_manual_file_logging()`: Sets up logging with a file handler and JSON formatter manually
- `print_log_file()`: Prints and parses the contents of a log file
- `query_sqlite_db()`: Queries and prints records from a SQLite database

## Notes

This consolidated debug utility replaces the individual debug scripts that were previously scattered throughout the codebase, making debugging more organized and maintainable.
