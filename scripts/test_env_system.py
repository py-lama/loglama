#!/usr/bin/env python3
"""
Test script for the centralized environment system.

This script tests that the centralized environment system is working correctly
by verifying that all components can access the same environment variables.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path so we can import the modules
sys.path.append(str(Path(__file__).parent.parent))

# Import the environment manager
from loglama.core.env_manager import (
    load_central_env, ensure_required_env_vars,
    get_central_env_path, get_project_path
)

# Try to import PyLLM modules
try:
    # Add PyLLM to the path
    pyllm_path = get_project_path("pyllm")
    if pyllm_path:
        sys.path.append(str(pyllm_path))
    from pyllm.models import get_default_model, get_models_dir
    PYLLM_AVAILABLE = True
except ImportError:
    PYLLM_AVAILABLE = False

# Try to import BEXY modules
try:
    # Add BEXY to the path
    bexy_path = get_project_path("bexy")
    if bexy_path:
        sys.path.append(str(bexy_path))
    # Import BEXY modules here if needed
    BEXY_AVAILABLE = True
except ImportError:
    BEXY_AVAILABLE = False


def test_central_env_path():
    """
    Test that the central .env path is correctly identified.
    """
    central_env_path = get_central_env_path()
    print(f"Central .env path: {central_env_path}")
    assert central_env_path.exists(), f"Central .env file does not exist at {central_env_path}"
    return True


def test_load_central_env():
    """
    Test that the central .env file can be loaded.
    """
    success = load_central_env()
    print(f"Load central .env: {success}")
    assert success, "Failed to load central .env file"
    return True


def test_required_env_vars():
    """
    Test that all required environment variables are set.
    """
    # This function will add any missing variables to the .env file
    missing_vars = ensure_required_env_vars()
    
    if missing_vars:
        print(f"Added missing environment variables: {json.dumps(missing_vars, indent=2)}")
        print("These variables have been added to the central .env file with default values.")
    else:
        print("All required environment variables are already set.")
    
    # Now check that all required variables are in the environment
    # after ensuring they exist in the .env file
    load_central_env()  # Reload to get the new variables
    
    # Check that all required variables are now set
    from loglama.core.env_manager import _required_env_vars
    missing_after_ensure = {}
    
    for project, vars in _required_env_vars.items():
        for var in vars:
            if var not in os.environ:
                if project not in missing_after_ensure:
                    missing_after_ensure[project] = []
                missing_after_ensure[project].append(var)
    
    if missing_after_ensure:
        print(f"Still missing environment variables: {json.dumps(missing_after_ensure, indent=2)}")
        return False
    
    return True


def test_pyllm_integration():
    """
    Test that PyLLM can access the centralized environment variables.
    """
    if not PYLLM_AVAILABLE:
        print("PyLLM not available, skipping test")
        return True
    
    # Test that PyLLM can get the default model
    default_model = get_default_model()
    print(f"Default model from PyLLM: {default_model}")
    assert default_model is not None, "Default model is None"
    
    # Test that PyLLM can get the models directory
    models_dir = get_models_dir()
    print(f"Models directory from PyLLM: {models_dir}")
    assert models_dir, "Models directory is empty"
    
    return True


def test_env_vars_consistency():
    """
    Test that environment variables are consistent across components.
    """
    # Get the central .env path
    central_env_path = get_central_env_path()
    
    # Load the central .env file
    import dotenv
    central_env = dotenv.dotenv_values(central_env_path)
    
    # Check that the environment variables are set in the current process
    for key, value in central_env.items():
        if key in os.environ:
            assert os.environ[key] == value, f"Environment variable {key} has different value in process: {os.environ[key]} != {value}"
    
    print("Environment variables are consistent across components")
    return True


def run_all_tests():
    """
    Run all tests for the centralized environment system.
    """
    tests = [
        test_central_env_path,
        test_load_central_env,
        test_required_env_vars,
        test_pyllm_integration,
        test_env_vars_consistency
    ]
    
    success = True
    for test in tests:
        print(f"\n=== Running test: {test.__name__} ===")
        try:
            result = test()
            if result:
                print(f"✅ {test.__name__} passed")
            else:
                print(f"❌ {test.__name__} failed")
                success = False
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {e}")
            success = False
    
    return success


if __name__ == "__main__":
    print("Testing centralized environment system...\n")
    success = run_all_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
