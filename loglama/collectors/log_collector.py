#!/usr/bin/env python3
"""
Log Collector for LogLama

This module provides functionality to collect logs from various PyLama components
and import them into the central LogLama database.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from loglama.config.env_loader import load_env
from loglama.core.env_manager import get_project_path

# Import LogLama components
from loglama.core.logger import get_logger
from loglama.db.models import LogRecord, create_tables, get_session

# Set up logger
logger = get_logger("loglama.collectors.log_collector")

# Define component log paths
COMPONENT_LOG_PATHS = {
    "weblama": {"db_path": "logs/weblama.db", "log_path": "logs/weblama.log"},
    "apilama": {"db_path": "logs/apilama.db", "log_path": "logs/apilama.log"},
    "bexy": {"db_path": "logs/bexy.db", "log_path": "logs/bexy.log"},
    "getllm": {"db_path": "logs/getllm.db", "log_path": "logs/getllm.log"},
    "pylama": {"db_path": "logs/pylama.db", "log_path": "logs/pylama.log"},
}


def get_component_log_paths(
    component: str,
) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Get the paths to the log files for a component.

    Args:
        component: The name of the component (e.g., 'weblama', 'apilama')

    Returns:
        A tuple of (db_path, log_path) for the component
    """
    # Get the component directory
    component_dir = get_project_path(component)
    if not component_dir:
        logger.warning(f"Could not find directory for component {component}")
        return None, None

    # Get the log paths for the component
    component_logs = COMPONENT_LOG_PATHS.get(component, {})
    db_path = component_logs.get("db_path")
    log_path = component_logs.get("log_path")

    # Convert to absolute paths
    if db_path:
        db_path = component_dir / db_path  # type: ignore[assignment]
    if log_path:
        log_path = component_dir / log_path  # type: ignore[assignment]

    return db_path, log_path  # type: ignore[ str | None,return-value,str | None]


def import_logs_from_sqlite(db_path: Path, component: str) -> int:
    """
    Import logs from a SQLite database into the LogLama database.

    Args:
        db_path: Path to the SQLite database
        component: Name of the component the logs are from

    Returns:
        Number of log records imported
    """
    if not db_path.exists():
        logger.warning(f"SQLite database not found at {db_path}")
        return 0

    try:
        # Connect to the source database
        source_conn = sqlite3.connect(str(db_path))
        source_cursor = source_conn.cursor()

        # Check if the logs table exists
        source_cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='logs'"
        )
        if not source_cursor.fetchone():
            # Try log_records table instead (used by newer versions)
            source_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='log_records'"
            )
            if not source_cursor.fetchone():
                logger.warning(f"No logs table found in {db_path}")
                source_conn.close()
                return 0
            else:
                table_name = "log_records"
        else:
            table_name = "logs"

        # Get the column names
        source_cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in source_cursor.fetchall()]

        # Query the logs table
        query = f"SELECT * FROM {table_name}"
        source_cursor.execute(query)
        logs = source_cursor.fetchall()

        # Close the source connection
        source_conn.close()

        # Create a session for the target database
        create_tables()  # Ensure tables exist
        session = get_session()

        # Import each log record
        imported_count = 0
        for log in logs:
            # Create a dictionary from the log record
            log_dict = {columns[i]: log[i] for i in range(len(columns))}

            # Create a LogRecord object
            timestamp_field = log_dict.get("timestamp") or log_dict.get(
                "created"
            )
            if isinstance(timestamp_field, str):
                try:
                    timestamp = datetime.fromisoformat(
                        timestamp_field.replace("Z", "+00:00")
                    )
                except ValueError:
                    # Try other formats
                    try:
                        timestamp = datetime.strptime(
                            timestamp_field, "%Y-%m-%d %H:%M:%S,%"
                        )
                    except ValueError:
                        timestamp = datetime.now()
            elif isinstance(timestamp_field, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp_field)
            else:
                timestamp = datetime.now()

            logger_name = log_dict.get("logger_name") or log_dict.get("name")
            if not logger_name:
                logger_name = "unknown"
            if not logger_name.startswith(component):
                logger_name = f"{component}.{logger_name}"

            level = (
                log_dict.get("level") or log_dict.get("levelname") or "INFO"
            )
            level_number = (
                log_dict.get("level_number") or log_dict.get("levelno") or 20
            )

            log_record = LogRecord(
                timestamp=timestamp,
                logger_name=logger_name,
                level=level,
                level_number=level_number,
                message=log_dict.get("message", ""),
                module=log_dict.get("module", ""),
                function=log_dict.get("function", "")
                or log_dict.get("funcName", ""),
                line_number=log_dict.get("line_number", 0)
                or log_dict.get("lineno", 0),
                process_id=log_dict.get("process_id", 0)
                or log_dict.get("process", 0),
                process_name=log_dict.get("process_name", ""),
                thread_id=log_dict.get("thread_id", 0)
                or log_dict.get("thread", 0),
                thread_name=log_dict.get("thread_name", ""),
                exception_info=log_dict.get("exception_info", None)
                or log_dict.get("exc_text", None),
                context=log_dict.get("context", None),
            )

            # Add the log record to the session
            session.add(log_record)
            imported_count += 1

        # Commit the session
        session.commit()
        session.close()

        logger.info(
            f"Imported {imported_count} log records from {component} database"
        )
        return imported_count

    except Exception as e:
        logger.exception(
            f"Error importing logs from {component} database: {e}"
        )
        return 0


def import_logs_from_file(log_path: Path, component: str) -> int:
    """
    Import logs from a log file into the LogLama database.

    Args:
        log_path: Path to the log file
        component: Name of the component the logs are from

    Returns:
        Number of log records imported
    """
    if not log_path.exists():
        logger.warning(f"Log file not found at {log_path}")
        return 0

    try:
        # Create a session for the target database
        create_tables()  # Ensure tables exist
        session = get_session()

        # Read the log file
        with open(log_path, "r") as f:
            log_lines = f.readlines()

        # Import each log line
        imported_count = 0
        for line in log_lines:
            line = line.strip()
            if not line:
                continue

            # Try to parse as JSON
            try:
                log_data = json.loads(line)

                # Create a LogRecord object from the JSON data
                timestamp = log_data.get("timestamp") or log_data.get(
                    "created"
                )
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )
                    except ValueError:
                        # Try other formats
                        try:
                            timestamp = datetime.strptime(
                                timestamp, "%Y-%m-%d %H:%M:%S,%"
                            )
                        except ValueError:
                            timestamp = datetime.now()
                elif isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp)
                else:
                    timestamp = datetime.now()

                # Extract logger name with fallbacks
                logger_name = (
                    log_data.get("name")
                    or log_data.get("logger_name")
                    or log_data.get("module")
                )

                # If still no logger name, try to extract from message
                if not logger_name and "message" in log_data:
                    # Try to extract module name from message if it follows common patterns
                    message = log_data["message"]
                    if " - " in message:
                        parts = message.split(" - ", 1)
                        potential_logger = parts[0].strip()
                        if (
                            "." in potential_logger
                            and not potential_logger.isdigit()
                        ):
                            logger_name = potential_logger

                # Use component name as fallback
                if not logger_name or logger_name == "unknown":
                    logger_name = component
                elif not logger_name.startswith(component):
                    logger_name = f"{component}.{logger_name}"

                level = (
                    log_data.get("level")
                    or log_data.get("levelname")
                    or "INFO"
                )
                level_number = (
                    log_data.get("level_no") or log_data.get("levelno") or 20
                )

                log_record = LogRecord(
                    timestamp=timestamp,
                    logger_name=logger_name,
                    level=level,
                    level_number=level_number,
                    message=log_data.get("message", line),
                    module=log_data.get("module", ""),
                    function=log_data.get("function", "")
                    or log_data.get("funcName", ""),
                    line_number=log_data.get("line_number", 0)
                    or log_data.get("lineno", 0),
                    process_id=log_data.get("process", 0)
                    or log_data.get("process_id", 0),
                    process_name=log_data.get("process_name", ""),
                    thread_id=log_data.get("thread", 0)
                    or log_data.get("thread_id", 0),
                    thread_name=log_data.get("thread_name", ""),
                    exception_info=log_data.get("exception", None)
                    or log_data.get("exc_text", None),
                    context=json.dumps(log_data.get("context", {})),
                )
            except json.JSONDecodeError:
                # Parse as plain text
                # Try to extract timestamp and level
                parts = line.split(" - ")
                if len(parts) >= 3:
                    try:
                        timestamp = datetime.strptime(
                            parts[0], "%Y-%m-%d %H:%M:%S,%"
                        )
                    except ValueError:
                        try:
                            timestamp = datetime.strptime(
                                parts[0], "%Y-%m-%d %H:%M:%S"
                            )
                        except ValueError:
                            timestamp = datetime.now()

                    level = parts[1].strip()
                    message = " - ".join(parts[2:])
                else:
                    timestamp = datetime.now()
                    level = "INFO"
                    message = line

                log_record = LogRecord(
                    timestamp=timestamp,
                    logger_name=f"{component}.unknown",
                    level=level,
                    level_number=logging.getLevelName(level),
                    message=message,
                    module="",
                    function="",
                    line_number=0,
                    process_id=0,
                    process_name="",
                    thread_id=0,
                    thread_name="",
                    exception_info=None,
                    context=None,
                )

            # Add the log record to the session
            session.add(log_record)
            imported_count += 1

        # Commit the session
        session.commit()
        session.close()

        logger.info(
            f"Imported {imported_count} log records from {component} log file"
        )
        return imported_count

    except Exception as e:
        logger.exception(
            f"Error importing logs from {component} log file: {e}"
        )
        return 0


def collect_logs_from_component(component: str) -> int:
    """
    Collect logs from a component and import them into the LogLama database.

    Args:
        component: Name of the component to collect logs from

    Returns:
        Number of log records imported
    """
    logger.info(f"Collecting logs from {component}")

    # Get the log paths for the component
    db_path, log_path = get_component_log_paths(component)

    # Import logs from the database if available
    db_count = 0
    if db_path and db_path.exists():
        db_count = import_logs_from_sqlite(db_path, component)

    # Import logs from the log file if available
    file_count = 0
    if log_path and log_path.exists():
        file_count = import_logs_from_file(log_path, component)

    total_count = db_count + file_count
    logger.info(
        f"Collected {total_count} logs from {component} ({db_count} from database, {file_count} from log file)"
    )

    return total_count


def collect_all_logs() -> Dict[str, int]:
    """
    Collect logs from all components and import them into the LogLama database.

    Returns:
        Dictionary mapping component names to the number of log records imported
    """
    logger.info("Collecting logs from all components")

    # Ensure environment variables are loaded
    load_env(verbose=False)

    # Collect logs from each component
    results = {}
    for component in COMPONENT_LOG_PATHS.keys():
        count = collect_logs_from_component(component)
        results[component] = count

    # Log the results
    total_count = sum(results.values())
    logger.info(f"Collected {total_count} logs from all components")

    return results


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Collect logs from all components
    results = collect_all_logs()

    # Print the results
    print("Collected logs from components:")
    for component, count in results.items():
        print(f"  {component}: {count} log records")
