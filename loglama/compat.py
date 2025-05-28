#!/usr/bin/env python3

"""
Compatibility layer for transitioning from LogLama to LogLama.

This module provides compatibility functions and classes to help projects
transition from LogLama to LogLama without breaking existing code.

Example usage:
    # Instead of importing directly from loglama or loglama
    from loglama.compat import get_logger, setup_logging, LogContext

    # Then use as normal
    logger = get_logger(__name__)
    logger.info("This works with both LogLama and LogLama!")
"""

import importlib.util
import os
import warnings
from typing import Any, Optional

# Check if loglama is available
LOGLAMA_AVAILABLE = importlib.util.find_spec("loglama") is not None

# Check if loglama is available (for backwards compatibility)
LOGLAMA_AVAILABLE = importlib.util.find_spec("loglama") is not None

# Determine which package to use
if LOGLAMA_AVAILABLE:
    import loglama

    _logging_lib = loglama
    _package_name = "loglama"
elif LOGLAMA_AVAILABLE:
    import loglama

    _logging_lib = loglama
    _package_name = "loglama"
    warnings.warn(
        "Using loglama package which has been renamed to loglama. "
        "Please update your dependencies to use loglama instead.",
        DeprecationWarning,
        stacklevel=2,
    )
else:
    raise ImportError(
        "Neither loglama nor loglama package is available. "
        "Please install loglama using 'pip install loglama'."
    )


# Export all public functions and classes from the chosen library
def get_logger(name: str):
    """Get a logger instance."""
    return _logging_lib.get_logger(name)


def setup_logging(
    name: str,
    level: str = "INFO",
    console: bool = True,
    file: bool = False,
    file_path: Optional[str] = None,
    database: bool = False,
    db_path: Optional[str] = None,
    json_format: bool = False,
    log_dir: Optional[str] = None,
):
    """Set up logging with the specified configuration."""
    return _logging_lib.setup_logging(  # type: ignore[call-arg]
        name=name,
        level=level,
        console=console,
        file=file,
        file_path=file_path,
        database=database,
        db_path=db_path,
        json_format=json_format,
        log_dir=log_dir,
    )


def load_env(verbose: bool = False, env_file: Optional[str] = None):
    """Load environment variables from .env file."""
    return _logging_lib.load_env(verbose=verbose, env_file=env_file)


def get_env(key: str, default: Any = None):
    """Get an environment variable with a default value."""
    return _logging_lib.get_env(key, default)


# Export the LogContext class
LogContext = _logging_lib.LogContext  # type: ignore[attr-defined]


# Export handler classes
SQLiteHandler = getattr(_logging_lib.handlers, "SQLiteHandler", None)
JSONFormatter = getattr(_logging_lib.formatters, "JSONFormatter", None)


# Helper function to convert environment variable names
def get_env_with_fallback(key: str, default: Any = None):
    """
    Get an environment variable with fallback to the old naming convention.

    This function first checks for the LOGLAMA_ prefixed variable, and if not found,
    falls back to checking for the LOGLAMA_ prefixed variable.

    Args:
        key: The environment variable name without the prefix
        default: The default value to return if neither variable is found

    Returns:
        The value of the environment variable or the default
    """
    loglama_key = f"LOGLAMA_{key}"
    loglama_key = f"LOGLAMA_{key}"

    # First try with LOGLAMA_ prefix
    value = os.environ.get(loglama_key)

    # If not found, try with LOGLAMA_ prefix
    if value is None:
        value = os.environ.get(loglama_key)
        if value is not None:
            warnings.warn(
                f"Using deprecated environment variable {loglama_key}. "
                f"Please update to {loglama_key} instead.",
                DeprecationWarning,
                stacklevel=2,
            )

    # If still not found, return the default
    if value is None:
        return default

    return value


# Helper function to convert config file paths
def get_config_path_with_fallback(
    base_name: str, default_dir: Optional[str] = None
):
    """
    Get a config file path with fallback to the old naming convention.

    This function first checks for the loglama_ prefixed file, and if not found,
    falls back to checking for the loglama_ prefixed file.

    Args:
        base_name: The base name of the config file without the prefix
        default_dir: The default directory to look in if not specified

    Returns:
        The path to the config file or None if not found
    """
    if default_dir is None:
        default_dir = os.getcwd()

    loglama_path = os.path.join(default_dir, f"loglama_{base_name}")
    loglama_path = os.path.join(default_dir, f"loglama_{base_name}")

    # First try with loglama_ prefix
    if os.path.exists(loglama_path):
        return loglama_path

    # If not found, try with loglama_ prefix
    if os.path.exists(loglama_path):
        warnings.warn(
            f"Using deprecated config file {loglama_path}. "
            f"Please rename to {loglama_path} instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return loglama_path

    return None


# Version information
__version__ = getattr(_logging_lib, "__version__", "unknown")
