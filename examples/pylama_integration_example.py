#!/usr/bin/env python3
"""
Example of using LogLama with other PyLama components.

This example demonstrates how to use LogLama in a script that interacts with
other PyLama components like PyLLM and BEXY, leveraging the centralized
environment system.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import LogLama and other components
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import LogLama modules
try:
    # Try importing from installed package first
    from loglama.core.logger import get_logger, setup_logging
    from loglama.core.env_manager import (
        load_central_env, ensure_required_env_vars, 
        get_project_path, check_project_dependencies
    )
except ImportError:
    # Fall back to local import if package is not installed
    from loglama.logger import get_logger, setup_logging
    # Simplified environment management for local imports
    def load_central_env(): print("Using simplified env loading")
    def ensure_required_env_vars(): return True
    def get_project_path(): return Path(__file__).parent.parent.parent
    def check_project_dependencies(name): return True

# Load environment variables from the central .env file
load_central_env()

# Ensure all required environment variables are set
ensure_required_env_vars()

# Set up logging
setup_logging()

# Get a logger for this script
logger = get_logger("pylama_integration")


def check_dependencies():
    """Check dependencies for PyLLM and BEXY."""
    logger.info("Checking dependencies for PyLLM and BEXY...")
    
    # Check PyLLM dependencies
    getllm_success, getllm_missing, _ = check_project_dependencies("getllm")
    if getllm_success:
        logger.info("PyLLM dependencies are satisfied")
    else:
        logger.warning(f"Missing PyLLM dependencies: {getllm_missing}")
    
    # Check BEXY dependencies
    bexy_success, bexy_missing, _ = check_project_dependencies("bexy")
    if bexy_success:
        logger.info("BEXY dependencies are satisfied")
    else:
        logger.warning(f"Missing BEXY dependencies: {bexy_missing}")
    
    return getllm_success and bexy_success


def import_getllm():
    """Import PyLLM modules."""
    try:
        # Add PyLLM to the path
        getllm_path = get_project_path("getllm")
        if getllm_path:
            sys.path.append(str(getllm_path))
            from getllm.models import get_default_model, get_models
            
            default_model = get_default_model()
            models = get_models()
            
            logger.info(f"Default model: {default_model}")
            logger.info(f"Available models: {[model['name'] for model in models]}")
            
            return True
    except ImportError as e:
        logger.error(f"Failed to import PyLLM modules: {e}")
    except Exception as e:
        logger.exception(f"Error accessing PyLLM: {e}")
    
    return False


def main():
    """Main function that demonstrates LogLama integration with PyLama components."""
    logger.info("Starting PyLama integration example")
    
    # Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        logger.warning("Some dependencies are missing. Results may be limited.")
    
    # Try to import and use PyLLM
    getllm_ok = import_getllm()
    
    # Log the results
    if getllm_ok:
        logger.info("Successfully integrated with PyLLM")
    else:
        logger.error("Failed to integrate with PyLLM")
    
    logger.info("PyLama integration example completed")


if __name__ == "__main__":
    main()
    print("\nCheck the logs to see the output. You can use the LogLama CLI to view them:")
    print("python -m loglama.cli.main logs")
