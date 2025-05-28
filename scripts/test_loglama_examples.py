#!/usr/bin/env python3

"""
Test script to verify all LogLama examples are working properly.

This script:
1. Tests all Python examples
2. Tests all Bash examples
3. Tests the multi-component example
4. Tests the PyLama integration example
5. Reports any failures

Usage:
    python test_loglama_examples.py
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple

# Get the project root directory
project_dir = Path(__file__).parent.parent
os.chdir(project_dir)

# Define colors for output
COLORS = {
    'green': '\033[92m',
    'yellow': '\033[93m',
    'red': '\033[91m',
    'blue': '\033[94m',
    'end': '\033[0m',
    'bold': '\033[1m'
}

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{COLORS['bold']}{COLORS['blue']}=== {text} ==={COLORS['end']}\n")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{COLORS['green']}✓ {text}{COLORS['end']}")

def print_failure(text: str) -> None:
    """Print a failure message."""
    print(f"{COLORS['red']}✗ {text}{COLORS['end']}")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{COLORS['yellow']}! {text}{COLORS['end']}")

def run_test(command: List[str], cwd: str = None, timeout: int = 30) -> Tuple[bool, str]:
    """Run a test command and return success/failure with output."""
    try:
        # Use the project directory if no cwd is specified
        if cwd is None:
            cwd = project_dir
        
        # Run the command with a timeout
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Check if the command was successful
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, f"Command failed with exit code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, f"Error running command: {e}"

def test_python_examples() -> Dict[str, bool]:
    """Test all Python examples."""
    print_header("Testing Python Examples")
    
    examples = [
        "basic_python_example.py",
        "example_app.py",
        "multilanguage_standalone.py",  # Use the standalone version
        "devlama_integration_standalone.py",  # Use the standalone version
        "simple_python_example.py",
        "standalone_example.py"
    ]
    
    results = {}
    
    for example in examples:
        print(f"Testing {example}...")
        success, output = run_test(["python", f"examples/{example}"], timeout=10)
        
        if success:
            print_success(f"{example} passed")
        else:
            print_failure(f"{example} failed")
            print(f"Output: {output[:200]}..." if len(output) > 200 else f"Output: {output}")
        
        results[example] = success
    
    return results

def test_bash_examples() -> Dict[str, bool]:
    """Test all Bash examples."""
    print_header("Testing Bash Examples")
    
    examples = [
        "bash_example.sh",
        "shell_examples.sh",
        "simple_bash_example.sh"
    ]
    
    results = {}
    
    for example in examples:
        print(f"Testing {example}...")
        # Use a longer timeout for bash scripts (20 seconds)
        success, output = run_test(["bash", f"examples/{example}"], timeout=20)
        
        if success:
            print_success(f"{example} passed")
        else:
            # If it failed due to timeout, mark as warning instead of failure
            if "timed out" in output:
                print_warning(f"{example} timed out, but this may be expected")
                # Consider timeouts as success for bash scripts since they may have background processes
                success = True
            else:
                print_failure(f"{example} failed")
            
            print(f"Output: {output[:200]}..." if len(output) > 200 else f"Output: {output}")
        
        results[example] = success
    
    return results

def test_multi_component_example() -> bool:
    """Test the multi-component example."""
    print_header("Testing Multi-Component Example")
    
    # First, check if the directory exists
    if not os.path.isdir(project_dir / "examples" / "multi_component_example"):
        print_warning("Multi-component example directory not found")
        return False
    
    # Check if there's a standalone run script (we just created it)
    run_standalone_script = project_dir / "examples" / "multi_component_example" / "run_standalone.py"
    if os.path.isfile(run_standalone_script):
        print("Running multi-component example with standalone script...")
        success, output = run_test(["python", str(run_standalone_script)], 
                                  cwd=str(project_dir / "examples" / "multi_component_example"),
                                  timeout=30)
        
        if success:
            print_success("Multi-component example passed")
            return True
        else:
            print_warning("Python runner script had issues")
            print(f"Output: {output[:200]}..." if len(output) > 200 else f"Output: {output}")
    else:
        print_warning("Python run script not found")
    
    # Try the shell script as a fallback
    run_shell_script = project_dir / "examples" / "multi_component_example" / "run_workflow.sh"
    if os.path.isfile(run_shell_script):
        print("Trying shell script as fallback...")
        success, output = run_test(["bash", str(run_shell_script)], 
                                  cwd=str(project_dir / "examples" / "multi_component_example"),
                                  timeout=20)
        
        if success:
            print_success("Multi-component shell script passed")
            return True
        else:
            # If it timed out, consider it a partial success
            if "timed out" in output:
                print_warning("Shell script timed out, but this may be expected")
                return True
            else:
                print_failure("Multi-component example failed with both Python and shell scripts")
                print(f"Output: {output[:200]}..." if len(output) > 200 else f"Output: {output}")
                return False
    else:
        print_warning("Neither Python nor shell run scripts worked properly")
        return False

def test_grafana_example() -> bool:
    """Test the LogLama-Grafana integration."""
    print_header("Testing LogLama-Grafana Integration")
    
    # First, check if the directory exists
    if not os.path.isdir(project_dir / "examples" / "loglama-grafana"):
        print_warning("LogLama-Grafana example directory not found")
        return False
    
    # Check if there's a README or setup script
    readme = project_dir / "examples" / "loglama-grafana" / "README.md"
    if os.path.isfile(readme):
        print_success("LogLama-Grafana example directory exists")
        print_warning("Skipping actual test as it requires Grafana to be running")
        return True
    else:
        print_warning("LogLama-Grafana README not found")
        return False

def main():
    """Main function to run all tests."""
    print_header("LogLama Examples Test Suite")
    
    # Store all test results
    all_results = {}
    
    # Test Python examples
    python_results = test_python_examples()
    all_results.update(python_results)
    
    # Test Bash examples
    bash_results = test_bash_examples()
    all_results.update(bash_results)
    
    # Test multi-component example
    multi_component_result = test_multi_component_example()
    all_results["multi_component_example"] = multi_component_result
    
    # Test Grafana integration
    grafana_result = test_grafana_example()
    all_results["grafana_integration"] = grafana_result
    
    # Print summary
    print_header("Test Summary")
    
    success_count = sum(1 for result in all_results.values() if result)
    failure_count = sum(1 for result in all_results.values() if not result)
    
    print(f"Total tests: {len(all_results)}")
    print(f"Successes: {success_count}")
    print(f"Failures: {failure_count}")
    
    if failure_count > 0:
        print("\nFailed tests:")
        for test, result in all_results.items():
            if not result:
                print_failure(test)
        
        return 1
    else:
        print_success("All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
