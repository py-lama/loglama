#!/usr/bin/env python3
"""
Centralized environment manager for the PyLama ecosystem.

This module provides functionality for managing a centralized .env file
that is shared across all PyLama projects and components.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Try to import dotenv for environment variable loading
try:
    from dotenv import find_dotenv, load_dotenv, set_key

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

    def load_dotenv(*args, **kwargs):  # type: ignore[misc]
        logging.warning(
            "python-dotenv package not found, environment variables from .env will not be loaded"
        )
        return False

    def set_key(*args, **kwargs):  # type: ignore[misc]
        logging.warning(
            "python-dotenv package not found, cannot set environment variables"
        )
        return False

    def find_dotenv(*args, **kwargs):  # type: ignore[misc]
        return None


# Try to import toml for pyproject.toml parsing
try:
    import tomli as toml  # type: ignore[import-not-found]

    TOML_AVAILABLE = True
except ImportError:
    try:
        import toml  # type: ignore[import-untyped]

        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False

# Set up logger
logger = logging.getLogger("loglama.core.env_manager")

# Cache for project paths
_project_paths_cache: Dict[str, Path] = {}

# Required environment variables for each project
_required_env_vars: Dict[str, Set[str]] = {
    "loglama": {
        "LOGLAMA_LOG_LEVEL",
        "LOGLAMA_LOG_DIR",
        "LOGLAMA_DB_LOGGING",
        "LOGLAMA_DB_PATH",
        "LOGLAMA_JSON_LOGS",
        "LOGLAMA_STRUCTURED_LOGGING",
        "LOGLAMA_MAX_LOG_SIZE",
        "LOGLAMA_BACKUP_COUNT",
    },
    "devlama": {
        "OLLAMA_MODEL",
        "OLLAMA_FALLBACK_MODELS",
        "OLLAMA_AUTO_SELECT_MODEL",
        "OLLAMA_TIMEOUT",
        "OLLAMA_PATH",
        "PYTHON_PATH",
        "PYTHON_VENV",
        "LOG_DIR",
        "OUTPUT_DIR",
        "SCRIPTS_DIR",
        "MODELS_DIR",
        "DEBUG_MODE",
    },
    "getllm": {"OLLAMA_MODEL", "MODELS_DIR"},
    "bexy": {"PYTHON_PATH"},
}


def find_devlama_root() -> Path:
    """
    Find the PyLama project root directory.

    Returns:
        Path to the PyLama project root directory.
    """
    # Start from the current directory and go up to find the py-lama directory
    current_dir = Path.cwd().absolute()

    # First check if we're already in a py-lama directory
    if current_dir.name == "py-lama":
        return current_dir

    # Check if we're in a subdirectory of py-lama
    parts = current_dir.parts
    for i in range(len(parts) - 1, 0, -1):
        if parts[i] == "py-lama":
            return Path(*parts[: i + 1])

    # If not found, look for the directory structure
    while current_dir != current_dir.parent:  # Stop at the root directory
        # Check if this looks like the py-lama directory
        if (current_dir / "devlama").exists() and (
            current_dir / "loglama"
        ).exists():
            return current_dir
        if (current_dir / "devlama").exists() and (
            current_dir / "getllm"
        ).exists():
            return current_dir

        # Move up one directory
        current_dir = current_dir.parent

    # If not found, use the current directory as fallback
    logger.warning(
        f"Could not find py-lama root, using current directory {Path.cwd()} as fallback"
    )
    return Path.cwd()


def get_project_path(project_name: str) -> Optional[Path]:
    """
    Get the path to a specific project within the PyLama ecosystem.

    Args:
        project_name: The name of the project (e.g., "loglama", "devlama", "getllm", "bexy")

    Returns:
        Path to the project directory, or None if not found.
    """
    # Check cache first
    if project_name in _project_paths_cache:
        return _project_paths_cache[project_name]

    # Find the PyLama root directory
    devlama_root = find_devlama_root()

    # Check if the project directory exists directly
    project_dir = devlama_root / project_name
    if project_dir.exists() and project_dir.is_dir():
        _project_paths_cache[project_name] = project_dir
        return project_dir

    # Check if it's a symlink
    symlink_path = devlama_root / f"{project_name}-link"
    if symlink_path.exists():
        target = symlink_path.resolve()
        if target.exists() and target.is_dir():
            _project_paths_cache[project_name] = target
            return target

    # Try to find it using pyproject.toml if available
    if TOML_AVAILABLE:
        for subdir in devlama_root.iterdir():
            if not subdir.is_dir():
                continue

            pyproject_path = subdir / "pyproject.toml"
            if not pyproject_path.exists():
                continue

            try:
                with open(pyproject_path, "rb") as f:
                    pyproject_data = toml.load(f)

                # Check project name in pyproject.toml
                project_info = pyproject_data.get("project", {})
                if (
                    project_info.get("name", "").lower()
                    == project_name.lower()
                ):
                    _project_paths_cache[project_name] = subdir
                    return subdir
            except Exception as e:
                logger.warning(f"Error parsing {pyproject_path}: {e}")

    # Not found
    logger.warning(f"Could not find project directory for {project_name}")
    return None


def get_central_env_path() -> Path:
    """
    Get the path to the central .env file.

    Returns:
        Path to the central .env file.
    """
    devlama_root = find_devlama_root()
    return devlama_root / "devlama" / ".env"


def load_central_env(override: bool = True) -> bool:
    """
    Load environment variables from the central .env file.

    Args:
        override: Whether to override existing environment variables.

    Returns:
        True if environment variables were loaded successfully, False otherwise.
    """
    if not DOTENV_AVAILABLE:
        logger.warning(
            "python-dotenv package not found. Install it with 'pip install python-dotenv' for .env file support."
        )
        return False

    # Get the path to the central .env file
    env_path = get_central_env_path()

    # Check if the file exists
    if not env_path.exists():
        logger.warning(f"Central .env file not found at {env_path}")
        return False

    # Load the .env file
    logger.info(
        f"Loading environment variables from central .env file: {env_path}"
    )
    success = load_dotenv(env_path, override=override)

    return success


def ensure_env_var(
    key: str, default_value: str = "", description: str = ""
) -> str:
    """
    Ensure that an environment variable exists in the central .env file.
    If it doesn't exist, add it with the default value.

    Args:
        key: The name of the environment variable.
        default_value: The default value to use if the variable doesn't exist.
        description: A description of the variable to add as a comment.

    Returns:
        The current value of the environment variable.
    """
    if not DOTENV_AVAILABLE:
        logger.warning(
            "python-dotenv package not found. Cannot ensure environment variables."
        )
        return os.environ.get(key, default_value)

    # Get the path to the central .env file
    env_path = get_central_env_path()

    # Create the directory if it doesn't exist
    env_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the file if it doesn't exist
    if not env_path.exists():
        env_path.touch()

    # Check if the variable already exists in the environment
    current_value = os.environ.get(key)

    # If the variable doesn't exist, add it to the .env file
    if current_value is None:
        logger.info(f"Adding environment variable {key} to central .env file")

        # Add a comment if provided
        if description:
            with open(env_path, "a") as f:
                f.write(f"\n# {description}\n")

        # Set the key in the .env file
        set_key(str(env_path), key, default_value)

        # Update the environment
        os.environ[key] = default_value
        current_value = default_value

    return current_value


def ensure_required_env_vars() -> Dict[str, Dict[str, str]]:
    """
    Ensure that all required environment variables for all projects exist.

    Returns:
        A dictionary mapping project names to dictionaries of missing variables and their default values.
    """
    missing_vars: Dict[str, Dict[str, str]] = {}

    # Load the central .env file first
    load_central_env()

    # Check each project's required variables
    for project, required_vars in _required_env_vars.items():
        project_missing_vars = {}

        for var in required_vars:
            if var not in os.environ:
                # Generate a default value based on the variable name
                if "LOG_LEVEL" in var:
                    default_value = "INFO"
                elif (
                    "LOG_DIR" in var
                    or "OUTPUT_DIR" in var
                    or "SCRIPTS_DIR" in var
                    or "MODELS_DIR" in var
                ):
                    default_value = "./logs"
                elif "DB_PATH" in var:
                    default_value = f"./logs/{project}.db"
                elif "_LOGGING" in var or "DEBUG" in var:
                    default_value = "false"
                elif "TIMEOUT" in var or "MAX_" in var or "COUNT" in var:
                    default_value = "10"
                else:
                    default_value = ""

                # Add to missing variables
                project_missing_vars[var] = default_value

                # Ensure the variable exists in the central .env file
                ensure_env_var(var, default_value, f"Required by {project}")

        if project_missing_vars:
            missing_vars[project] = project_missing_vars

    return missing_vars


def run_project_tests(project_name: str) -> Tuple[bool, str]:
    """
    Run tests for a specific project.

    Args:
        project_name: The name of the project to test.

    Returns:
        A tuple of (success, output) where success is True if all tests passed,
        and output is the command output.
    """
    # Get the project path
    project_path = get_project_path(project_name)
    if project_path is None:
        return False, f"Project {project_name} not found"

    # Determine the test command based on the project
    try:
        # Run the tests using make
        logger.info(f"Running tests for {project_name}...")
        process = subprocess.run(
            ["make", "test"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )

        # Check if the tests passed
        success = process.returncode == 0
        output = process.stdout + process.stderr

        if success:
            logger.info(f"Tests for {project_name} passed")
        else:
            logger.warning(f"Tests for {project_name} failed")

        return success, output
    except Exception as e:
        logger.error(f"Error running tests for {project_name}: {e}")
        return False, str(e)


def check_project_dependencies(
    project_name: str,
) -> Tuple[bool, List[str], str]:
    """
    Check if all dependencies for a project are installed.

    Args:
        project_name: The name of the project to check.

    Returns:
        A tuple of (success, missing_deps, output) where success is True if all
        dependencies are installed, missing_deps is a list of missing dependencies,
        and output is the command output.
    """
    # Get the project path
    project_path = get_project_path(project_name)
    if project_path is None:
        return False, [], f"Project {project_name} not found"

    # Find the requirements file
    requirements_file = project_path / "requirements.txt"
    if not requirements_file.exists():
        # Try pyproject.toml
        pyproject_file = project_path / "pyproject.toml"
        if pyproject_file.exists() and TOML_AVAILABLE:
            try:
                with open(pyproject_file, "rb") as f:
                    pyproject_data = toml.load(f)

                # Extract dependencies from pyproject.toml
                dependencies = []
                if (
                    "project" in pyproject_data
                    and "dependencies" in pyproject_data["project"]
                ):
                    dependencies = pyproject_data["project"]["dependencies"]

                if dependencies:
                    # Create a temporary requirements file
                    temp_requirements = project_path / "temp_requirements.txt"
                    with open(temp_requirements, "w") as f:
                        for dep in dependencies:
                            f.write(f"{dep}\n")

                    requirements_file = temp_requirements
                else:
                    return True, [], "No dependencies found in pyproject.toml"
            except Exception as e:
                logger.error(f"Error parsing pyproject.toml: {e}")
                return False, [], f"Error parsing pyproject.toml: {e}"
        else:
            return True, [], "No requirements.txt or pyproject.toml found"

    # Check dependencies using pip
    try:
        logger.info(f"Checking dependencies for {project_name}...")
        process = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )

        # Parse the output to find missing dependencies
        output = process.stdout + process.stderr
        missing_deps = []

        if "No broken requirements found" not in output:
            # Parse the output to extract missing dependencies
            for line in output.splitlines():
                if "which is not installed" in line:
                    parts = line.split("requires", 1)
                    if len(parts) > 1:
                        dep = parts[1].split(",")[0].strip()
                        missing_deps.append(dep)

        success = len(missing_deps) == 0

        if success:
            logger.info(f"All dependencies for {project_name} are installed")
        else:
            logger.warning(
                f"Missing dependencies for {project_name}: {missing_deps}"
            )

        return success, missing_deps, output
    except Exception as e:
        logger.error(f"Error checking dependencies for {project_name}: {e}")
        return False, [], str(e)


def install_project_dependencies(project_name: str) -> Tuple[bool, str]:
    """
    Install dependencies for a specific project.

    Args:
        project_name: The name of the project to install dependencies for.

    Returns:
        A tuple of (success, output) where success is True if all dependencies were installed,
        and output is the command output.
    """
    # Get the project path
    project_path = get_project_path(project_name)
    if project_path is None:
        return False, f"Project {project_name} not found"

    # Find the requirements file
    requirements_file = project_path / "requirements.txt"
    if not requirements_file.exists():
        # Try pyproject.toml
        pyproject_file = project_path / "pyproject.toml"
        if pyproject_file.exists() and TOML_AVAILABLE:
            try:
                with open(pyproject_file, "rb") as f:
                    pyproject_data = toml.load(f)

                # Check if it's a poetry project
                if (
                    "tool" in pyproject_data
                    and "poetry" in pyproject_data["tool"]
                ):
                    # Use poetry to install dependencies
                    logger.info(
                        f"Installing dependencies for {project_name} using poetry..."
                    )
                    process = subprocess.run(
                        ["poetry", "install"],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    success = process.returncode == 0
                    output = process.stdout + process.stderr

                    if success:
                        logger.info(
                            f"Dependencies for {project_name} installed successfully using poetry"
                        )
                    else:
                        logger.warning(
                            f"Failed to install dependencies for {project_name} using poetry"
                        )

                    return success, output
                else:
                    # Extract dependencies from pyproject.toml
                    dependencies = []
                    if (
                        "project" in pyproject_data
                        and "dependencies" in pyproject_data["project"]
                    ):
                        dependencies = pyproject_data["project"][
                            "dependencies"
                        ]

                    if dependencies:
                        # Create a temporary requirements file
                        temp_requirements = (
                            project_path / "temp_requirements.txt"
                        )
                        with open(temp_requirements, "w") as f:
                            for dep in dependencies:
                                f.write(f"{dep}\n")

                        requirements_file = temp_requirements
                    else:
                        return True, "No dependencies found in pyproject.toml"
            except Exception as e:
                logger.error(f"Error parsing pyproject.toml: {e}")
                return False, f"Error parsing pyproject.toml: {e}"
        else:
            return True, "No requirements.txt or pyproject.toml found"

    # Install dependencies using pip
    try:
        logger.info(f"Installing dependencies for {project_name}...")
        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(requirements_file),
            ],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )

        success = process.returncode == 0
        output = process.stdout + process.stderr

        if success:
            logger.info(
                f"Dependencies for {project_name} installed successfully"
            )
        else:
            logger.warning(
                f"Failed to install dependencies for {project_name}"
            )

        return success, output
    except Exception as e:
        logger.error(f"Error installing dependencies for {project_name}: {e}")
        return False, str(e)


def start_project(
    project_name: str, args: List[str] = None  # type: ignore[assignment,str]
) -> Tuple[bool, Any, str]:
    """
    Start a specific project.

    Args:
        project_name: The name of the project to start.
        args: Additional arguments to pass to the project.

    Returns:
        A tuple of (success, process, output) where success is True if the project was started,
        process is the subprocess.Popen object if the project was started as a background process,
        and output is the command output.
    """
    # Get the project path
    project_path = get_project_path(project_name)
    if project_path is None:
        return False, None, f"Project {project_name} not found"

    # Determine the start command based on the project
    if project_name == "loglama":
        cmd = [sys.executable, "-m", "loglama.cli.main"]
        if args:
            cmd.extend(args)
        else:
            cmd.extend(["web"])
    elif project_name == "devlama":
        cmd = [sys.executable, "devlama.py"]
        if args:
            cmd.extend(args)
    elif project_name == "getllm":
        cmd = [sys.executable, "-m", "getllm.cli"]
        if args:
            cmd.extend(args)
    elif project_name == "bexy":
        cmd = [sys.executable, "-m", "bexy"]
        if args:
            cmd.extend(args)
    else:
        return False, None, f"Unknown project: {project_name}"

    # Start the project
    try:
        logger.info(f"Starting {project_name}...")
        process = subprocess.Popen(
            cmd,
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        # Wait a bit to see if the process crashes immediately
        try:
            return_code = process.poll()
            if return_code is not None:
                # Process has already terminated
                stdout, stderr = process.communicate()
                output = stdout + stderr
                logger.error(
                    f"{project_name} terminated with code {return_code}: {output}"
                )
                return False, None, output
        except Exception:
            pass

        logger.info(f"{project_name} started successfully")
        return True, process, f"{project_name} started successfully"
    except Exception as e:
        logger.error(f"Error starting {project_name}: {e}")
        return False, None, str(e)
