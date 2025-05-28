"""Auto-fix utilities for LogLama.

This module provides utilities for automatically detecting and fixing common issues
in Python projects using LogLama.
"""

import importlib
import inspect
import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List, Union

from loglama.core.logger import get_logger

# Get logger
logger = get_logger(__name__)


def apply_fixes(
    issues: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Apply fixes for detected issues.

    Args:
        issues: List of issues to fix

    Returns:
        Dict[str, List[Dict[str, Any]]]: Results of fix attempts
    """
    from loglama.decorators.auto_fix import (
        apply_fixes as decorator_apply_fixes,
    )

    return decorator_apply_fixes(issues)


def detect_logging_issues(
    module_or_path: Union[str, object],
) -> List[Dict[str, Any]]:
    """Detect common logging issues in a module or file.

    Args:
        module_or_path: Module object or path to Python file

    Returns:
        List[Dict[str, Any]]: List of detected issues
    """
    issues = []  # type: ignore[var-annotated,<type>]

    # Handle module object or path
    if isinstance(module_or_path, str):
        # Path to Python file
        if not module_or_path.endswith(".py"):
            module_or_path += ".py"

        if not os.path.exists(module_or_path):
            logger.error(f"File not found: {module_or_path}")
            return issues

        # Read the file content
        with open(module_or_path, "r") as f:
            content = f.read()

        # Check for common issues in the code
        if (
            "print(" in content
            and "print(" not in content.lower().split("def ")[0]
        ):
            issues.append(
                {
                    "type": "excessive_logging",
                    "message": f"Found print statements in {module_or_path} that should be replaced with logging",
                    "params": {
                        "logger_name": os.path.basename(
                            module_or_path
                        ).replace(".py", "")
                    },
                }
            )

        if "logging.basicConfig" in content:
            issues.append(
                {
                    "type": "duplicate_logging_config",
                    "message": f"Found duplicate logging configuration in {module_or_path}",
                    "params": {"path": module_or_path},
                }
            )

        # Check for hardcoded log paths
        import re

        log_path_pattern = re.compile(r'[\'"](.*\.log[\'"\)])')
        log_paths = log_path_pattern.findall(content)
        if log_paths:
            issues.append(
                {
                    "type": "hardcoded_log_path",
                    "message": f"Found hardcoded log paths in {module_or_path}: {', '.join(log_paths)}",
                    "params": {"path": module_or_path, "log_paths": log_paths},
                }
            )
    else:
        # Module object
        module_name = getattr(module_or_path, "__name__", str(module_or_path))

        # Check for logging objects
        for name, obj in inspect.getmembers(module_or_path):
            # Check for logger objects
            if name == "logger" or name.endswith("_logger"):
                # Check if it's a proper logger
                if not isinstance(obj, logging.Logger) and not hasattr(
                    obj, "info"
                ):
                    issues.append(
                        {
                            "type": "invalid_logger",
                            "message": f"Invalid logger object '{name}' in module {module_name}",
                            "params": {
                                "module": module_name,
                                "logger_name": name,
                            },
                        }
                    )

    return issues


def detect_database_issues(db_path: str) -> List[Dict[str, Any]]:
    """Detect common database issues.

    Args:
        db_path: Path to SQLite database file

    Returns:
        List[Dict[str, Any]]: List of detected issues
    """
    issues = []

    # Check if database file exists
    if not os.path.exists(db_path):
        issues.append(
            {
                "type": "database_connection_error",
                "message": f"Database file not found: {db_path}",
                "params": {"db_path": db_path},
            }
        )
        return issues

    # Check if database is readable
    if not os.access(db_path, os.R_OK):
        issues.append(
            {
                "type": "missing_file_permissions",
                "message": f"Database file is not readable: {db_path}",
                "params": {"path": db_path},
            }
        )

    # Check if database is writable
    if not os.access(db_path, os.W_OK):
        issues.append(
            {
                "type": "missing_file_permissions",
                "message": f"Database file is not writable: {db_path}",
                "params": {"path": db_path},
            }
        )

    # Try to connect to the database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if logs table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='logs'"
        )
        if not cursor.fetchone():
            issues.append(
                {
                    "type": "missing_logs_table",
                    "message": f"Logs table not found in database: {db_path}",
                    "params": {"db_path": db_path},
                }
            )
        else:
            # Check logs table schema
            cursor.execute("PRAGMA table_info(logs)")
            columns = {row[1] for row in cursor.fetchall()}
            required_columns = {
                "id",
                "timestamp",
                "level",
                "logger",
                "message",
            }
            missing_columns = required_columns - columns
            if missing_columns:
                issues.append(
                    {
                        "type": "invalid_logs_schema",
                        "message": f"Logs table is missing required columns: {', '.join(missing_columns)}",
                        "params": {
                            "db_path": db_path,
                            "missing_columns": list(missing_columns),
                        },
                    }
                )

        conn.close()
    except sqlite3.Error as e:
        issues.append(
            {
                "type": "database_connection_error",
                "message": f"Failed to connect to database: {db_path}, error: {str(e)}",
                "params": {"db_path": db_path},
            }
        )

    return issues


def detect_environment_issues() -> List[Dict[str, Any]]:
    """Detect common environment issues.

    Returns:
        List[Dict[str, Any]]: List of detected issues
    """
    issues = []

    # Check for required environment variables
    required_env_vars = {
        "LOGLAMA_LOG_LEVEL": "INFO",
        "LOGLAMA_LOG_FORMAT": "json",
    }

    for var, default_value in required_env_vars.items():
        if var not in os.environ:
            issues.append(
                {
                    "type": "missing_environment_variable",
                    "message": f"Missing environment variable: {var}",
                    "params": {
                        "var_name": var,
                        "default_value": default_value,
                    },
                }
            )

    # Check for invalid log level
    log_level = os.environ.get("LOGLAMA_LOG_LEVEL", "")
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level and log_level not in valid_levels:
        issues.append(
            {
                "type": "invalid_log_level",
                "message": f"Invalid log level: {log_level}",
                "params": {"level": log_level},
            }
        )

    # Check for Python version
    if sys.version_info < (3, 6):
        issues.append(
            {
                "type": "unsupported_python_version",
                "message": f"Unsupported Python version: {sys.version}",
                "params": {},
            }
        )

    # Check for required packages
    required_packages = ["structlog", "click"]
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            issues.append(
                {
                    "type": "missing_dependency",
                    "message": f"Missing required package: {package}",
                    "params": {"package": package},
                }
            )

    return issues


def fix_project_logging(
    project_dir: str, backup: bool = True
) -> Dict[str, Any]:
    """Fix logging issues in a Python project.

    This function will scan a Python project directory for common logging issues
    and attempt to fix them automatically.

    Args:
        project_dir: Path to the project directory
        backup: Whether to backup files before modifying them

    Returns:
        Dict[str, Any]: Results of the fix operation
    """
    results = {
        "scanned_files": 0,
        "modified_files": 0,
        "issues_found": 0,
        "issues_fixed": 0,
        "errors": [],
        "modified_files_list": [],
    }

    # Check if directory exists
    if not os.path.exists(project_dir) or not os.path.isdir(project_dir):
        results["errors"].append(f"Project directory not found: {project_dir}")  # type: ignore[attr-defined]
        return results

    # Walk through the project directory
    for root, dirs, files in os.walk(project_dir):
        # Skip hidden directories and virtual environments
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".")
            and d not in ["venv", "env", "__pycache__"]
        ]

        # Process Python files
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                results["scanned_files"] += 1  # type: ignore[operator]

                try:
                    # Detect issues in the file
                    issues = detect_logging_issues(file_path)
                    results["issues_found"] += len(issues)  # type: ignore[operator]

                    # Skip if no issues found
                    if not issues:
                        continue

                    # Read the file content
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Create backup if requested
                    if backup:
                        backup_path = f"{file_path}.bak"
                        with open(backup_path, "w") as f:
                            f.write(content)

                    # Apply fixes
                    modified = False

                    # Replace print statements with logging
                    if any(
                        issue["type"] == "excessive_logging"
                        for issue in issues
                    ):
                        import re

                        # Add logging import if not present
                        if (
                            "import logging" not in content
                            and "from logging import" not in content
                        ):
                            content = "import logging\n" + content
                            modified = True

                        # Add logger definition if not present
                        logger_name = os.path.basename(file_path).replace(
                            ".py", ""
                        )
                        if "logger = logging.getLogger(" not in content:
                            # Find the right place to add the logger definition
                            import_section_end = 0
                            lines = content.split("\n")
                            for i, line in enumerate(lines):
                                if line.startswith(
                                    "import "
                                ) or line.startswith("from "):
                                    import_section_end = i + 1

                            # Add logger definition after imports
                            logger_def = f"\n# Get logger\nlogger = logging.getLogger('{logger_name}')\n"
                            content = (
                                "\n".join(lines[:import_section_end])
                                + logger_def
                                + "\n".join(lines[import_section_end:])
                            )
                            modified = True

                        # Replace print statements with logging
                        content = re.sub(
                            r"print\((.+?)\)", r"logger.info(\1)", content
                        )
                        modified = True

                    # Remove duplicate logging configuration
                    if any(
                        issue["type"] == "duplicate_logging_config"
                        for issue in issues
                    ):
                        import re

                        # Comment out logging.basicConfig lines
                        content = re.sub(
                            r"(logging\.basicConfig\(.+?\))",
                            r"# \1  # Replaced by LogLama configuration",
                            content,
                        )

                        # Add LogLama import if not present
                        if "from loglama.core.logger import" not in content:
                            # Find the right place to add the import
                            lines = content.split("\n")
                            for i, line in enumerate(lines):
                                if "import logging" in line:
                                    lines.insert(
                                        i + 1,
                                        "from loglama.core.logger import setup_logging, get_logger",
                                    )
                                    content = "\n".join(lines)
                                    break

                        modified = True

                    # Replace hardcoded log paths
                    if any(
                        issue["type"] == "hardcoded_log_path"
                        for issue in issues
                    ):
                        import re

                        # Replace hardcoded log paths with environment variables
                        for issue in issues:
                            if issue["type"] == "hardcoded_log_path":
                                for log_path in issue["params"].get(
                                    "log_paths", []
                                ):
                                    content = content.replace(
                                        log_path,
                                        "os.environ.get('LOGLAMA_LOG_FILE', 'logs/application.log')",
                                    )

                        # Add os import if not present
                        if (
                            "import os" not in content
                            and "from os import" not in content
                        ):
                            content = "import os\n" + content

                        modified = True

                    # Write modified content back to the file if changes were made
                    if modified:
                        with open(file_path, "w") as f:
                            f.write(content)

                        results["modified_files"] += 1  # type: ignore[operator]
                        results["modified_files_list"].append(file_path)  # type: ignore[attr-defined]
                        results["issues_fixed"] += len(issues)  # type: ignore[operator]

                except Exception as e:
                    results["errors"].append(  # type: ignore[attr-defined]
                        f"Error processing file {file_path}: {str(e)}"
                    )

    return results


def fix_project_environment(
    project_dir: str, create_env_file: bool = True
) -> Dict[str, Any]:
    """Fix environment issues in a Python project.

    This function will check for environment configuration in a Python project
    and create or update environment files as needed.

    Args:
        project_dir: Path to the project directory
        create_env_file: Whether to create a .env file if not present

    Returns:
        Dict[str, Any]: Results of the fix operation
    """
    results = {  # type: ignore[var-annotated]
        "env_file_created": False,
        "env_file_updated": False,
        "env_file_path": None,
        "added_variables": [],
        "errors": [],
    }

    # Check if directory exists
    if not os.path.exists(project_dir) or not os.path.isdir(project_dir):
        results["errors"].append(f"Project directory not found: {project_dir}")  # type: ignore[Any,union-attr]
        return results

    # Look for existing environment files
    env_files = [".env", ".env.example", ".env.template", ".env.sample"]
    env_file_path = None

    for env_file in env_files:
        path = os.path.join(project_dir, env_file)
        if os.path.exists(path):
            env_file_path = path
            break

    # Create .env file if not found and requested
    if not env_file_path and create_env_file:
        env_file_path = os.path.join(project_dir, ".env")
        try:
            with open(env_file_path, "w") as f:
                f.write("# LogLama environment configuration\n\n")
            results["env_file_created"] = True
            results["env_file_path"] = env_file_path  # type: ignore[Any,assignment]
        except Exception as e:
            results["errors"].append(f"Failed to create .env file: {str(e)}")  # type: ignore[Any,union-attr]
            return results

    # If we have an env file, check and update it
    if env_file_path:
        try:
            # Read existing content
            with open(env_file_path, "r") as f:
                content = f.read()

            # Check for required variables
            required_vars = {
                "LOGLAMA_LOG_LEVEL": "INFO",
                "LOGLAMA_LOG_FORMAT": "json",
                "LOGLAMA_CONSOLE": "true",
                "LOGLAMA_FILE": "true",
                "LOGLAMA_LOG_FILE": "logs/application.log",
                "LOGLAMA_DATABASE": "false",
                "LOGLAMA_DB_PATH": "logs/logs.db",
            }

            # Add missing variables
            lines = content.split("\n")
            modified = False

            for var, default_value in required_vars.items():
                # Check if variable exists
                if not any(
                    line.strip().startswith(f"{var}=") for line in lines
                ):
                    lines.append(f"{var}={default_value}")
                    results["added_variables"].append(var)  # type: ignore[Any,union-attr]
                    modified = True

            # Write updated content if modified
            if modified:
                with open(env_file_path, "w") as f:
                    f.write("\n".join(lines))
                results["env_file_updated"] = True

        except Exception as e:
            results["errors"].append(f"Failed to update .env file: {str(e)}")  # type: ignore[Any,union-attr]

    return results


def create_loglama_config(project_dir: str) -> Dict[str, Any]:
    """Create a LogLama configuration file for a project.

    This function will create a loglama.yaml configuration file in the project
    directory with recommended settings.

    Args:
        project_dir: Path to the project directory

    Returns:
        Dict[str, Any]: Results of the operation
    """
    results = {  # type: ignore[var-annotated]
        "config_file_created": False,
        "config_file_path": None,
        "errors": [],
    }

    # Check if directory exists
    if not os.path.exists(project_dir) or not os.path.isdir(project_dir):
        results["errors"].append(f"Project directory not found: {project_dir}")  # type: ignore[Any,union-attr]
        return results

    # Check if config file already exists
    config_path = os.path.join(project_dir, "loglama.yaml")
    if os.path.exists(config_path):
        results["errors"].append(  # type: ignore[Any,union-attr]
            f"Configuration file already exists: {config_path}"
        )
        return results

    # Create configuration file
    try:
        # Get project name from directory
        project_name = os.path.basename(os.path.abspath(project_dir))  # noqa: F841

        # Create config content
        config_content = """# LogLama Configuration

# Project information
project:
  name: {project_name}
  version: 0.1.0

# Logging configuration
logging:
  level: ${{LOGLAMA_LOG_LEVEL:INFO}}
  format: ${{LOGLAMA_LOG_FORMAT:json}}
  console: ${{LOGLAMA_CONSOLE:true}}
  file:
    enabled: ${{LOGLAMA_FILE:true}}
    path: ${{LOGLAMA_LOG_FILE:logs/application.log}}
    max_size: ${{LOGLAMA_MAX_LOG_SIZE:10485760}}  # 10 MB
    backup_count: ${{LOGLAMA_BACKUP_COUNT:5}}
  database:
    enabled: ${{LOGLAMA_DATABASE:false}}
    path: ${{LOGLAMA_DB_PATH:logs/logs.db}}
    table: logs

# Context configuration
context:
  default:
    application: {project_name}
    environment: ${{LOGLAMA_ENVIRONMENT:development}}
    hostname: ${{HOSTNAME:unknown}}

# Diagnostic configuration
diagnostics:
  auto_fix: ${{LOGLAMA_AUTO_FIX:true}}
  health_check_interval: ${{LOGLAMA_HEALTH_CHECK_INTERVAL:3600}}  # 1 hour
  report_path: ${{LOGLAMA_REPORT_PATH:logs/diagnostic_reports}}
"""

        # Write configuration file
        with open(config_path, "w") as f:
            f.write(config_content)

        results["config_file_created"] = True
        results["config_file_path"] = config_path  # type: ignore[Any,assignment]

    except Exception as e:
        results["errors"].append(  # type: ignore[Any,union-attr]
            f"Failed to create configuration file: {str(e)}"
        )

    return results
