#!/usr/bin/env python3

"""
LogLama Web Interface

This module provides a Flask web application for viewing and querying logs stored in SQLite database.
"""

import math
import os
import socket
import sqlite3
from typing import Any, Dict, Optional

from flask import Flask, g, jsonify, render_template, request

from loglama.config.env_loader import get_env, load_env
from loglama.core.logger import setup_logging


def check_service_running(host: str, port: int, timeout: float = 0.5) -> bool:
    """Check if a service is running on the specified host and port.

    Args:
        host: The host to check.
        port: The port to check.
        timeout: The timeout in seconds.

    Returns:
        True if the service is running, False otherwise.
    """
    try:
        # Create a socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        # Attempt to connect to the host and port
        result = sock.connect_ex((host, port))
        sock.close()

        # If the result is 0, the port is open
        return result == 0
    except Exception:
        return False


def _initialize_db(db_path: str, logger):
    """Initialize the database by creating the log records table if it doesn't exist.

    Args:
        db_path: Path to the SQLite database file
        logger: Logger to use for logging
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the log records table if it doesn't exist
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS log_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            level_number INTEGER NOT NULL,
            logger_name TEXT NOT NULL,
            message TEXT NOT NULL,
            file_path TEXT,
            line_number INTEGER,
            function TEXT,
            module TEXT,
            process_id INTEGER,
            process_name TEXT,
            thread_id INTEGER,
            thread_name TEXT,
            exception_info TEXT,
            context TEXT
        )
        """
        )

        # Create indexes for faster queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_log_records_timestamp ON log_records (timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_log_records_level ON log_records (level_number)"
        )

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {db_path}")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")


def get_db(db_path: str):
    """Get database connection."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
    return db


def create_app(
    db_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None
) -> Flask:
    """Create Flask application for LogLama web interface.

    Args:
        db_path: Path to SQLite database file. If None, it will be loaded from environment variables.
        config: Additional configuration options.

    Returns:
        Flask application instance.
    """
    # Load environment variables
    load_env(verbose=False)

    # Get database path from environment or use default
    db_path = db_path or get_env("LOGLAMA_DB_PATH", "./logs/loglama.db")

    # Initialize logging
    logger = setup_logging(
        name="loglama_web", level="INFO", database=True, db_path=db_path
    )

    # Create Flask app
    app = Flask(__name__)

    # Add request logger
    @app.after_request
    def log_request(response):
        """Log each request to the database."""
        # Don't log requests for static files or API endpoints that are used for auto-refresh
        if not request.path.startswith("/static/") and not (
            request.path.startswith("/api/logs")
            and "newest_first=true" in request.query_string.decode("utf-8")
        ):
            try:
                logger.info(
                    f"{request.remote_addr} - {request.method} {request.path} {response.status_code}",
                    extra={
                        "remote_addr": request.remote_addr,
                        "method": request.method,
                        "path": request.path,
                        "status_code": response.status_code,
                        "request_type": "http",
                    },
                )
            except Exception as e:
                print(f"Error logging request: {e}")
        return response

    app.config.from_mapping(
        SECRET_KEY=os.urandom(24),
        DB_PATH=db_path or get_env("LOGLAMA_DB_PATH", "./logs/loglama.db"),
        PAGE_SIZE=int(get_env("LOGLAMA_WEB_PAGE_SIZE", "100")),
        DEBUG=get_env("LOGLAMA_WEB_DEBUG", "false").lower()
        in ("true", "yes", "1"),
    )

    # Apply additional configuration if provided
    if config:
        app.config.update(config)

    # Ensure database exists
    db_path = app.config["DB_PATH"]
    if not os.path.exists(db_path):  # type: ignore[arg-type,str]
        logger.warning(f"Database file not found at {db_path}")
        db_dir = os.path.dirname(db_path)  # type: ignore[type-var]
        if not os.path.exists(db_dir):  # type: ignore[arg-type,str]
            os.makedirs(db_dir, exist_ok=True)  # type: ignore[arg-type,str]
            logger.info(f"Created directory {db_dir}")

    # Initialize database with required tables
    _initialize_db(db_path, logger)  # type: ignore[arg-type]

    # Register teardown function
    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(g, "_database", None)
        if db is not None:
            db.close()

    # Routes
    @app.route("/")
    def index():
        """Main page."""
        return render_template("index.html")

    @app.route("/services")
    def services():
        """Services dashboard."""
        return render_template("services.html")

    @app.route("/api/logs")
    def get_logs():
        """Get logs from database."""
        try:
            db = get_db(app.config["DB_PATH"])
            cursor = db.cursor()

            # Get pagination parameters
            page = int(request.args.get("page", 1))
            page_size = int(
                request.args.get("page_size", app.config.get("PAGE_SIZE", 100))
            )

            # Get filter parameters
            level = request.args.get("level", None)
            search = request.args.get("search", None)
            start_date = request.args.get("start_date", None)
            end_date = request.args.get("end_date", None)
            component = request.args.get("component", None)

            # Get sorting parameters
            sort_by = request.args.get("sort_by", "timestamp")
            sort_direction = request.args.get("sort_direction", "desc")

            # Validate sort parameters to prevent SQL injection
            valid_sort_columns = [
                "timestamp",
                "level",
                "level_number",
                "logger_name",
                "message",
            ]
            if sort_by not in valid_sort_columns:
                sort_by = "timestamp"  # Default to timestamp if invalid column

            if sort_direction.lower() not in ["asc", "desc"]:
                sort_direction = (
                    "desc"  # Default to descending if invalid direction
                )

            # Build query
            query = "SELECT * FROM log_records WHERE 1=1"
            params = []

            if level:
                query += " AND level = ?"
                params.append(level)

            if component:
                query += " AND logger_name = ?"
                params.append(component)

            if search:
                query += " AND (message LIKE ? OR logger_name LIKE ?)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param])

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            # Add ORDER BY clause for sorting
            query += f" ORDER BY {sort_by} {sort_direction}"

            # Count total matching logs for pagination
            count_query = query.replace("SELECT *", "SELECT COUNT(*) as count")
            count_query = count_query.split(" ORDER BY ")[
                0
            ]  # Remove ORDER BY clause for counting

            cursor.execute(count_query, params)
            total = cursor.fetchone()["count"]

            # Calculate pagination
            offset = (page - 1) * page_size
            pages = math.ceil(total / page_size) if total > 0 else 1

            # Add pagination to query
            query += " LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            # Execute query
            cursor.execute(query, params)
            logs = [dict(row) for row in cursor.fetchall()]

            # Apply maximum message length if configured
            max_message_length = int(
                get_env("LOGLAMA_MAX_MESSAGE_LENGTH", "200")
            )
            for log in logs:
                if len(log["message"]) > max_message_length:
                    log["message"] = (
                        log["message"][:max_message_length] + "..."
                    )
                    log["truncated"] = True
                else:
                    log["truncated"] = False

            return jsonify(
                {
                    "logs": logs,
                    "page": page,
                    "pages": pages,
                    "page_size": page_size,
                    "total": total,
                }
            )
        except Exception as e:
            logger.error(f"Error getting logs: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/services")
    def get_services():
        """Get status of all services in the PyLama ecosystem."""
        try:
            # Define the known services in the PyLama ecosystem
            services = [
                {
                    "name": "LogLama",
                    "description": "Logging and monitoring service",
                    "default_port": 5002,
                    "url": f"http://{get_env('HOST', '127.0.0.1')}:{get_env('PORT', '5002')}",
                    "active": True,  # LogLama is always active if this endpoint is called
                    "icon": "fa-solid fa-list",
                },
                {
                    "name": "WebLama",
                    "description": "Web interface for PyLama",
                    "default_port": 8081,
                    "url": f"http://{get_env('HOST', '127.0.0.1')}:8081",
                    "active": check_service_running("127.0.0.1", 8081),
                    "icon": "fa-solid fa-globe",
                },
                {
                    "name": "APILama",
                    "description": "API service for PyLama",
                    "default_port": 8082,
                    "url": f"http://{get_env('HOST', '127.0.0.1')}:8082",
                    "active": check_service_running("127.0.0.1", 8082),
                    "icon": "fa-solid fa-server",
                },
                {
                    "name": "PyLLM",
                    "description": "LLM service for PyLama",
                    "default_port": 8083,
                    "url": f"http://{get_env('HOST', '127.0.0.1')}:8083",
                    "active": check_service_running("127.0.0.1", 8083),
                    "icon": "fa-solid fa-brain",
                },
                {
                    "name": "BEXY",
                    "description": "File storage service for PyLama",
                    "default_port": 8084,
                    "url": f"http://{get_env('HOST', '127.0.0.1')}:8084",
                    "active": check_service_running("127.0.0.1", 8084),
                    "icon": "fa-solid fa-box",
                },
            ]

            return jsonify({"services": services})
        except Exception as e:
            logger.error(f"Error getting services: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/stats")
    def get_stats():
        """Get log statistics."""
        try:
            db = get_db(app.config["DB_PATH"])
            cursor = db.cursor()

            # Get level counts
            cursor.execute(
                "SELECT level, COUNT(*) as count FROM log_records GROUP BY level"
            )
            level_counts = {
                row["level"]: row["count"] for row in cursor.fetchall()
            }

            # Get component counts
            cursor.execute(
                "SELECT logger_name, COUNT(*) as count FROM log_records GROUP BY logger_name"
            )
            component_counts = {
                row["logger_name"]: row["count"] for row in cursor.fetchall()
            }

            # Get date range
            cursor.execute(
                "SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date FROM log_records"
            )
            date_range = dict(cursor.fetchone())

            # Get total count
            cursor.execute("SELECT COUNT(*) as count FROM log_records")
            total = cursor.fetchone()["count"]

            return jsonify(
                {
                    "level_counts": level_counts,
                    "component_counts": component_counts,
                    "date_range": date_range,
                    "total": total,
                }
            )
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/levels")
    def get_levels():
        """Get available log levels."""
        try:
            db = get_db(app.config["DB_PATH"])
            cursor = db.cursor()
            cursor.execute("SELECT DISTINCT level FROM log_records")
            levels = [row["level"] for row in cursor.fetchall()]
            return jsonify(levels)
        except Exception as e:
            logger.error(f"Error getting levels: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/components")
    def get_components():
        """Get available components (logger names)."""
        try:
            db = get_db(app.config["DB_PATH"])
            cursor = db.cursor()
            cursor.execute("SELECT DISTINCT logger_name FROM log_records")
            components = [row["logger_name"] for row in cursor.fetchall()]
            return jsonify(components)
        except Exception as e:
            logger.error(f"Error getting components: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/log/<int:log_id>")
    def get_log(log_id):
        """Get log details by ID."""
        try:
            db = get_db(app.config["DB_PATH"])
            cursor = db.cursor()
            cursor.execute("SELECT * FROM log_records WHERE id = ?", [log_id])
            log = dict(cursor.fetchone() or {})
            return jsonify(log)
        except Exception as e:
            logger.error(f"Error getting log {log_id}: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/logs/clear", methods=["POST"])
    def clear_logs():
        """Clear all logs from the database."""
        try:
            db = get_db(app.config["DB_PATH"])
            cursor = db.cursor()
            cursor.execute("DELETE FROM log_records")
            db.commit()
            logger.info("All logs cleared from database")
            return jsonify(
                {"success": True, "message": "All logs cleared successfully"}
            )
        except Exception as e:
            logger.error(f"Error clearing logs: {str(e)}")
            return jsonify({"error": str(e)}), 500

    logger.info(
        f"LogLama Web Interface initialized with database at {db_path}"
    )
    return app


def run_app(
    host: str = "127.0.0.1", port: int = 5000, db_path: Optional[str] = None
):
    """Run the LogLama web interface.

    Args:
        host: Host to bind to.
        port: Port to listen on.
        db_path: Path to SQLite database file.
    """
    app = create_app(db_path=db_path)
    app.run(host=host, port=port, debug=app.config["DEBUG"])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LogLama Web Interface")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument(
        "--port", type=int, default=5000, help="Port to listen on"
    )
    parser.add_argument("--db", help="Path to SQLite database file")

    args = parser.parse_args()
    run_app(host=args.host, port=args.port, db_path=args.db)
