#!/usr/bin/env python3
"""
Utility to update logger names in the LogLama database.

This script updates existing logs with better logger names based on the log message content.
"""

import re
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

from loglama.config.env_loader import get_env
from loglama.core.logger import get_logger

# Set up logger
logger = get_logger("loglama.cli.commands.update_loggers")


def get_db_path() -> Path:
    """
    Get the path to the LogLama database.

    Returns:
        Path to the LogLama database
    """
    db_path = get_env("LOGLAMA_DB_PATH", None)
    if not db_path:
        log_dir = Path(get_env("LOGLAMA_LOG_DIR", "logs"))
        db_path = log_dir / "loglama.db"
    else:
        db_path = Path(db_path)

    return db_path


def extract_component_from_message(message: str) -> Optional[str]:
    """
    Extract component name from a log message.

    Args:
        message: Log message to extract component from

    Returns:
        Component name if found, None otherwise
    """
    # Extract component from path pattern
    path_pattern = r"/home/tom/github/py-lama/([^/]+)"
    path_match = re.search(path_pattern, message)
    if path_match:
        return path_match.group(1)

    # Extract APILama specific patterns
    apilama_pattern = r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\] \[(INFO|WARNING|ERROR|DEBUG)\]"
    if re.search(apilama_pattern, message):
        return "apilama"

    # Extract component from URL patterns
    url_pattern = r"http://localhost:(\d+)"
    url_match = re.search(url_pattern, message)
    if url_match:
        port = url_match.group(1)
        if port == "9130":
            return "apilama"
        elif port == "8084" or port == "8081":
            return "weblama"
        elif port == "5000" or port == "5002":
            return "loglama"

    # Extract component from common patterns
    if "weblama" in message.lower():
        return "weblama"
    if "apilama" in message.lower() or "APILama initialized" in message:
        return "apilama"
    if "devlama" in message.lower():
        return "devlama"
    if "bexy" in message.lower():
        return "bexy"
    if "getllm" in message.lower():
        return "getllm"
    if "Docker Container Status" in message:
        return "docker"

    return None


def update_logger_names(
    db_path: Path, dry_run: bool = False, all_logs: bool = False
) -> Tuple[int, int]:
    """
    Update logger names in the LogLama database.

    Args:
        db_path: Path to the LogLama database
        dry_run: If True, don't actually update the database
        all_logs: If True, process all logs, not just those with 'unknown' in the name

    Returns:
        Tuple of (total logs, updated logs)
    """
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return (0, 0)

    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get logs to process
        if all_logs:
            # Process all logs
            cursor.execute("SELECT id, message, logger_name FROM log_records")
        else:
            # Only process logs with unknown in the name or specific patterns
            cursor.execute(
                "SELECT id, message, logger_name FROM log_records "
                "WHERE logger_name LIKE '%unknown' OR logger_name = 'unknown' "
                "OR (logger_name LIKE 'apilama%' AND message LIKE '[%] [INFO]%') "
                "OR (message LIKE '%Docker Container Status%' AND logger_name != 'docker') "
                "OR (message LIKE '%APILama initialized%' AND logger_name != 'apilama')"
            )

        logs = cursor.fetchall()

        total_logs = len(logs)
        updated_logs = 0

        for log in logs:
            log_id = log["id"]
            message = log["message"]
            current_logger = log["logger_name"]

            # Extract component from message
            component = extract_component_from_message(message)
            if not component:
                continue

            # Create new logger name
            if current_logger == "unknown":
                new_logger = component
            elif current_logger.endswith(".unknown"):
                prefix = current_logger.split(".")[0]
                if prefix != component:
                    new_logger = f"{component}.{prefix}"
                else:
                    new_logger = component
            elif (
                "APILama initialized" in message
                and current_logger != "apilama"
            ):
                new_logger = "apilama"
            elif (
                "Docker Container Status" in message
                and current_logger != "docker"
            ):
                new_logger = "docker"
            else:
                # Skip if the logger name is already appropriate
                if current_logger == component or (
                    current_logger.startswith(component)
                    and not current_logger.endswith(".unknown")
                ):
                    continue
                new_logger = component

            # Only update if there's a change
            if new_logger != current_logger:
                # Update the database
                if not dry_run:
                    cursor.execute(
                        "UPDATE log_records SET logger_name = ? WHERE id = ?",
                        (new_logger, log_id),
                    )
                    updated_logs += 1
                else:
                    logger.info(
                        f"Would update log {log_id}: {current_logger} -> {new_logger}"
                    )
                    updated_logs += 1

        # Commit changes
        if not dry_run:
            conn.commit()

        # Close connection
        conn.close()

        return (total_logs, updated_logs)

    except Exception as e:
        logger.error(f"Error updating logger names: {e}")
        return (0, 0)


def main(dry_run: bool = False, all_logs: bool = False) -> None:
    """
    Main entry point for the script.

    Args:
        dry_run: If True, don't actually update the database
        all_logs: If True, process all logs, not just those with 'unknown' in the name
    """
    db_path = get_db_path()
    logger.info(f"Updating logger names in {db_path}")

    total_logs, updated_logs = update_logger_names(db_path, dry_run, all_logs)

    if all_logs:
        logger.info(f"Processed {total_logs} total logs")
    else:
        logger.info(
            f"Found {total_logs} logs with unknown or incorrect logger names"
        )

    logger.info(f"Updated {updated_logs} logs with better logger names")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Update logger names in the LogLama database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually update the database",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all logs, not just those with unknown logger names",
    )

    args = parser.parse_args()

    main(args.dry_run, args.all)
