#!/usr/bin/env python3
"""
Model Inference Script

This script demonstrates how to use LogLama for logging in a model inference script.
It loads processed data, performs model inference using PyLLM, and saves the results.
"""

import os
import sys
import json
import glob
from pathlib import Path
from datetime import datetime

# Add the PyLama root directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Import LogLama modules
from loglama.core.logger import get_logger, setup_logging
from loglama.core.env_manager import load_central_env, get_project_path

# Load environment variables from the central .env file
load_central_env()

# Set up logging
setup_logging()

# Get a logger for this script
logger = get_logger("model_inference")

# Try to import PyLLM modules
try:
    # Add PyLLM to the path
    getllm_path = get_project_path("getllm")
    if getllm_path:
        sys.path.append(str(getllm_path))
        from getllm.models import get_default_model
        GETLLM_AVAILABLE = True
        logger.info(f"PyLLM available, default model: {get_default_model()}")
except ImportError as e:
    logger.warning(f"PyLLM not available: {e}")
    GETLLM_AVAILABLE = False


def find_latest_processed_file():
    """Find the most recent processed data file in the data directory."""
    data_dir = Path(__file__).parent / "data"
    data_files = list(data_dir.glob("processed_data_*.json"))
    
    if not data_files:
        logger.error("No processed data files found")
        return None
    
    # Sort by modification time (most recent first)
    latest_file = max(data_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Found latest processed data file: {latest_file.name}")
    return latest_file


def load_processed_data(file_path):
    """Load processed data from a JSON file."""
    logger.info(f"Loading processed data from {file_path.name}")
    
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        logger.info(f"Successfully loaded processed data from {file_path.name}")
        return data
    except Exception as e:
        logger.exception(f"Error loading processed data from {file_path.name}")
        return {}


def simulate_model_inference(data):
    """Simulate model inference on the processed data."""
    if not data:
        logger.warning("No data for model inference")
        return {}
    
    logger.info("Performing model inference on processed data")
    
    try:
        with logger.time("model_inference"):
            # Extract statistics from the processed data
            statistics = data.get("statistics", {})
            
            # Simulate model inference results
            inference_results = {}
            for source, categories in statistics.items():
                inference_results[source] = {}
                for category, stats in categories.items():
                    # Simulate a prediction based on the statistics
                    prediction = stats.get("avg", 0) * 1.5
                    confidence = min(0.95, max(0.5, stats.get("count", 0) / 20))
                    
                    inference_results[source][category] = {
                        "prediction": prediction,
                        "confidence": confidence,
                        "input_stats": stats
                    }
                    
                    logger.debug(f"Inference for {source}/{category}", extra={
                        "prediction": prediction,
                        "confidence": confidence
                    })
            
            # If PyLLM is available, add a summary using the model
            if GETLLM_AVAILABLE:
                logger.info("Generating summary using PyLLM")
                # This is a simulation of using PyLLM
                summary = f"Analysis of {len(statistics)} data sources completed with an average confidence of 0.75."
                inference_results["summary"] = summary
            
        logger.info("Model inference completed")
        return inference_results
    except Exception as e:
        logger.exception("Error during model inference")
        return {}


def save_inference_results(results, filename):
    """Save inference results to a file."""
    file_path = Path(__file__).parent / "data" / filename
    
    logger.info(f"Saving inference results to {filename}", extra={"file_path": str(file_path)})
    
    try:
        with open(file_path, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Inference results successfully saved to {filename}")
        return True
    except Exception as e:
        logger.exception(f"Error saving inference results to {filename}")
        return False


def main():
    """Main function that performs model inference on processed data."""
    logger.info("Starting model inference")
    
    # Find the latest processed data file
    latest_file = find_latest_processed_file()
    if not latest_file:
        logger.error("Model inference failed: No processed data file found")
        return False
    
    # Load the processed data
    processed_data = load_processed_data(latest_file)
    if not processed_data:
        logger.error("Model inference failed: Could not load processed data")
        return False
    
    # Perform model inference
    inference_results = simulate_model_inference(processed_data)
    if not inference_results:
        logger.error("Model inference failed: Inference error")
        return False
    
    # Save the inference results
    results_filename = f"inference_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_success = save_inference_results(inference_results, results_filename)
    
    if save_success:
        logger.info("Model inference completed successfully")
        return True
    else:
        logger.error("Model inference failed: Could not save inference results")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
