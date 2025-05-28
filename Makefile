# LogLama Makefile

# Default values that can be overridden
PORT ?= 8081
HOST ?= 127.0.0.1
PYTHON ?= python3
VENV_NAME ?= venv
VENV_ACTIVATE = . $(VENV_NAME)/bin/activate
LOG_DIR ?= ./logs
DB_PATH ?= $(LOG_DIR)/loglama.db
EXAMPLE_DB_PATH ?= $(LOG_DIR)/example.db

.PHONY: all setup venv install test test-unit test-integration test-ansible lint format clean run-api web run-example view-logs run-integration run-examples build publish publish-test check-publish help test-unit-existing test-integration-existing test-existing test-package update-version

all: help

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV_NAME) || true
	@echo "Virtual environment created at $(VENV_NAME)/"

# Install dependencies
install: venv
	@echo "Installing dependencies..."
	@$(VENV_ACTIVATE) && pip install --upgrade pip
	@$(VENV_ACTIVATE) && pip install poetry
	@$(VENV_ACTIVATE) && poetry install --with dev
	@$(VENV_ACTIVATE) && pip install -e .
	@$(VENV_ACTIVATE) && pip install structlog rich click sqlalchemy python-dotenv
	@echo "Dependencies installed."

# Setup the project (create venv and install dependencies)
setup: install
	@echo "LogLama setup completed."

# Run all tests
test: test-unit test-integration
	@echo "All tests completed."

# Run unit tests
test-unit: venv
	@echo "Running unit tests..."
	@$(VENV_ACTIVATE) && pytest tests/unit/ -v

# Run integration tests
test-integration: venv
	@echo "Running integration tests..."
	@$(VENV_ACTIVATE) && pytest tests/integration/ -v

# Run Ansible tests
test-ansible: venv
	@echo "Running Ansible tests..."
	@$(VENV_ACTIVATE) && ansible-playbook tests/ansible/test_loglama.yml -v

# Run linting checks
lint: venv
	@echo "Running linting checks..."
	@$(VENV_ACTIVATE) && flake8 loglama/
	@$(VENV_ACTIVATE) && mypy loglama/

# Run linting checks without mypy
lint-no-mypy: venv
	@echo "Running linting checks (without mypy)..."
	@$(VENV_ACTIVATE) && flake8 loglama/

# Format code
format: venv
	@echo "Formatting code..."
	@$(VENV_ACTIVATE) && black loglama/
	@$(VENV_ACTIVATE) && isort loglama/


# Build package
build: setup
	@echo "Building package..."
	@. venv/bin/activate && pip install -e . && pip install wheel twine build
	@. venv/bin/activate && rm -rf dist/* && python setup.py sdist bdist_wheel

# Update version
update-version:
	@echo "Updating package version..."
	@python ../scripts/update_version.py

# Publish package to PyPI
publish: build update-version
	@echo "Publishing package to PyPI..."
	@. venv/bin/activate && twine check dist/* && twine upload dist/*

# Publish package to TestPyPI
publish-test: build update-version
	@echo "Publishing package to TestPyPI..."
	@. venv/bin/activate && twine check dist/* && twine upload --repository testpypi dist/*

# Dry run of publishing (no actual upload)
publish-dry-run: venv check-publish build
	@echo "Testing publishing process (dry run)..."
	@$(VENV_ACTIVATE) && echo y | poetry publish --dry-run
	@echo "Publishing process tested successfully."

# Publish to PyPI with version bump (recommended)
publish-with-bump: venv check-publish
	@echo "Publishing to PyPI with version bump..."
	@$(VENV_ACTIVATE) && python scripts/simple_publish.py

# Publish to PyPI (production)
publish: publish-with-bump

# Publish to PyPI without confirmation (for CI/CD)
publish-ci: venv check-publish build
	@echo "Publishing to PyPI without confirmation..."
	@$(VENV_ACTIVATE) && poetry publish --username=__token__ --password=$(PYPI_TOKEN)
	@echo "Published to PyPI. Install with: pip install loglama"

# Full publishing workflow using the publish script
publish-full: venv
	@echo "Running full publishing workflow..."
	@chmod +x scripts/publish.sh
	@./scripts/publish.sh

# This section intentionally left blank
# The publish-dry-run target is already defined above

# Quick publish (skip tests and TestPyPI)
# This section intentionally left blank
# publish-quick has been replaced by publish-with-bump

# Docker image building and publishing
docker-build: venv
	@echo "Building Docker image..."
	@docker build -t loglama/loglama:$$($(VENV_ACTIVATE) && poetry version -s) .
	@echo "Docker image built successfully."

docker-push: docker-build
	@echo "Publishing Docker image..."
	@$(VENV_ACTIVATE) && python scripts/publish_docker.py

docker-push-no-latest: docker-build
	@echo "Publishing Docker image (without latest tag)..."
	@$(VENV_ACTIVATE) && python scripts/publish_docker.py --no-latest

# Configure PyPI credentials
configure-pypi: venv
	@echo "Configuring PyPI credentials..."
	@echo "You'll need API tokens from PyPI and TestPyPI"
	@echo "Get them from:"
	@echo "  PyPI: https://pypi.org/manage/account/token/"
	@echo "  TestPyPI: https://test.pypi.org/manage/account/token/"
	@echo ""
	@read -p "Enter PyPI token: " pypi_token && \
		$(VENV_ACTIVATE) && poetry config pypi-token.pypi $$pypi_token
	@read -p "Enter TestPyPI token: " testpypi_token && \
		$(VENV_ACTIVATE) && poetry config pypi-token.testpypi $$testpypi_token
	@echo "Credentials configured successfully."

# Show current version
version: venv
	@echo "Current version:"
	@$(VENV_ACTIVATE) && poetry version

# Bump version (patch)
version-patch: venv
	@echo "Bumping patch version..."
	@$(VENV_ACTIVATE) && poetry version patch
	@git add pyproject.toml
	@git commit -m "Bump version to $$($(VENV_ACTIVATE) && poetry version -s)"

# Bump version (minor)
version-minor: venv
	@echo "Bumping minor version..."
	@$(VENV_ACTIVATE) && poetry version minor
	@git add pyproject.toml
	@git commit -m "Bump version to $$($(VENV_ACTIVATE) && poetry version -s)"

# Bump version (major)
version-major: venv
	@echo "Bumping major version..."
	@$(VENV_ACTIVATE) && poetry version major
	@git add pyproject.toml
	@git commit -m "Bump version to $$($(VENV_ACTIVATE) && poetry version -s)"

# Run API server
run-api: venv
	@echo "Starting LogLama API server on $(HOST):$(PORT)..."
	@$(VENV_ACTIVATE) && python -m loglama.api.server --host $(HOST) --port $(PORT)

# Run web interface (legacy method)
run-web: web

# Run web interface with new command
web: venv
	@echo "Starting LogLama web interface on $(HOST):$(PORT)..."
	@$(VENV_ACTIVATE) && python -m loglama.cli.main web --host $(HOST) --port $(PORT) --db $(DB_PATH)

# Run CLI
run-cli: venv
	@echo "Starting LogLama CLI..."
	@$(VENV_ACTIVATE) && python -m loglama.cli.main

# === Examples Section ===

# Run example application
run-example: setup
	@echo "Running example application..."
	@$(VENV_ACTIVATE) && python examples/example_app.py --requests 20 --log-dir $(LOG_DIR) --db-path $(EXAMPLE_DB_PATH) --json

# Run multi-language examples
run-examples: setup
	@echo "Running multi-language examples..."
	@$(VENV_ACTIVATE) && python examples/multilanguage_examples.py

# Run shell examples
run-shell-examples: setup
	@echo "Running shell examples..."
	@$(VENV_ACTIVATE) && bash examples/shell_examples.sh

# Run basic Python example
run-basic-example: setup
	@echo "Running basic Python example..."
	@$(VENV_ACTIVATE) && python examples/basic_python_example.py

# Run standalone example
run-standalone-example: setup
	@echo "Running standalone example..."
	@$(VENV_ACTIVATE) && python examples/standalone_example.py

# Run bash example
run-bash-example: setup
	@echo "Running bash example..."
	@$(VENV_ACTIVATE) && bash examples/bash_example.sh

# Run simple Python example (with simplified interface)
run-simple-python-example: setup
	@echo "Running simple Python example with simplified interface..."
	@$(VENV_ACTIVATE) && python examples/simple_python_example.py

# Run simple Python example with web interface
run-simple-python-web-example: setup
	@echo "Running simple Python example with web interface..."
	@$(VENV_ACTIVATE) && python examples/simple_python_example.py --web

# Run simple bash example (with simplified interface)
run-simple-bash-example: setup
	@echo "Running simple bash example with simplified interface..."
	@$(VENV_ACTIVATE) && bash examples/simple_bash_example.sh

# Run simple bash example with web interface
run-simple-bash-web-example: setup
	@echo "Running simple bash example with web interface..."
	@$(VENV_ACTIVATE) && bash examples/simple_bash_example.sh --web

# Run PyLama integration example
run-devlama-integration-example: setup
	@echo "Running PyLama integration example..."
	@$(VENV_ACTIVATE) && python examples/devlama_integration_example.py

# Run multi-component workflow example
run-multi-component-example: setup
	@echo "Running multi-component workflow example..."
	@$(VENV_ACTIVATE) && cd examples/multi_component_example && bash run_workflow.sh

# Run LogLama + Grafana Docker Compose example
run-grafana-example:
	@echo "Starting LogLama + Grafana Docker Compose example..."
	@cd examples/loglama-grafana && ./setup-fixed-dashboard.sh

# Stop LogLama + Grafana Docker Compose example
stop-grafana-example:
	@echo "Stopping LogLama + Grafana Docker Compose example..."
	@cd examples/loglama-grafana && docker compose down -v

# Generate diverse logs for Grafana visualization
generate-grafana-logs:
	@echo "Generating diverse logs for Grafana visualization..."
	@docker exec loglama python /generate_diverse_logs_fixed.py

# Run continuous web log monitoring for Grafana
run-grafana-web-monitor:
	@echo "Starting continuous web log monitoring for Grafana..."
	@docker exec -d loglama python /monitor_web_logs.py

# Stop continuous web log monitoring for Grafana
stop-grafana-web-monitor:
	@echo "Stopping continuous web log monitoring for Grafana..."
	@docker exec loglama ps aux | grep monitor_web_logs.py | grep -v grep | awk '{print $$2}' | xargs -r docker exec loglama kill 2>/dev/null || echo "No monitoring process found to stop."

# View logs from example application
view-example-logs: setup
	@echo "Starting web interface to view example logs on $(HOST):$(PORT)..."
	@$(VENV_ACTIVATE) && python -m loglama.cli.web_viewer --host $(HOST) --port $(PORT) --db $(EXAMPLE_DB_PATH)

# Run integration script to integrate LogLama into a component
run-integration: venv
	@echo "Running LogLama integration script..."
	@$(VENV_ACTIVATE) && python scripts/integrate_loglama.py --all

# Run debug utilities
run-debug: venv
	@echo "Running LogLama debug utilities..."
	@$(VENV_ACTIVATE) && python debug/debug_utils.py

# Run specific debug test for context handling
run-debug-context: venv
	@echo "Running LogLama context handling debug test..."
	@$(VENV_ACTIVATE) && python -c "from debug.debug_utils import test_context_handling; test_context_handling()"

# Run specific debug test for capture context decorator
run-debug-capture-context: venv
	@echo "Running LogLama capture context decorator debug test..."
	@$(VENV_ACTIVATE) && python -c "from debug.debug_utils import test_capture_context_decorator; test_capture_context_decorator()"

# Run specific debug test for SQLite handler
run-debug-sqlite: venv
	@echo "Running LogLama SQLite handler debug test..."
	@$(VENV_ACTIVATE) && python -c "from debug.debug_utils import test_sqlite_handler; test_sqlite_handler()"

# Run specific debug test for file handler
run-debug-file: venv
	@echo "Running LogLama file handler debug test..."
	@$(VENV_ACTIVATE) && python -c "from debug.debug_utils import test_file_handler_manual; test_file_handler_manual()"

# Run unit tests with existing venv (no recreation)
test-unit-existing:
	@echo "Running unit tests with existing venv..."
	@$(VENV_ACTIVATE) && pytest tests/unit/ -v

# Run integration tests with existing venv (no recreation)
test-integration-existing:
	@echo "Running integration tests with existing venv..."
	@$(VENV_ACTIVATE) && pytest tests/integration/ -v

# Run all tests with existing venv (no recreation)
test-existing: test-unit-existing test-integration-existing
	@echo "All tests completed using existing venv."

# Clean up generated files
clean:
	@echo "Cleaning up generated files..."
	@rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "Cleanup completed."

# Display help information
help:
	@echo "LogLama Makefile Commands:"
	@echo ""
	@echo "Setup and Development:"
	@echo "  make setup          - Set up the project (create venv and install dependencies)"
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-ansible   - Run Ansible tests"
	@echo "  make lint           - Run linting checks"
	@echo "  make format         - Format code"
	@echo "  make clean          - Clean up generated files"
	@echo ""
	@echo "Version Management:"
	@echo "  make version        - Show current version"
	@echo "  make version-patch  - Bump patch version (0.1.0 -> 0.1.1)"
	@echo "  make version-minor  - Bump minor version (0.1.0 -> 0.2.0)"
	@echo "  make version-major  - Bump major version (0.1.0 -> 1.0.0)"
	@echo ""
	@echo "Building and Publishing:"
	@echo "  make build          - Build package with Poetry"
	@echo "  make check-publish  - Check if package is ready for publishing"
	@echo "  make configure-pypi - Configure PyPI and TestPyPI credentials"
	@echo "  make publish-test   - Publish to TestPyPI"
	@echo "  make publish-with-bump - Publish to PyPI with automatic version bump (recommended)"
	@echo "  make publish        - Alias for publish-with-bump"
	@echo "  make publish-full   - Run full publishing workflow with checks"
	@echo "  make publish-dry-run - Dry run of publishing process"
	@echo "  make docker-build    - Build Docker image with current version tag"
	@echo "  make docker-push     - Build and publish Docker image to Docker Hub"
	@echo "  make docker-push-no-latest - Publish Docker image without updating latest tag"
	@echo ""
	@echo "Running LogLama:"
	@echo "  make run-api        - Run API server"
	@echo "  make web            - Run web interface"
	@echo "  make run-cli        - Run CLI"
	@echo ""
	@echo "Examples and Integration:"
	@echo "  make run-example    - Run example application"
	@echo "  make run-examples   - Run multi-language examples"
	@echo "  make run-shell-examples - Run shell examples"
	@echo "  make run-basic-example - Run basic Python example"
	@echo "  make run-standalone-example - Run standalone example"
	@echo "  make run-bash-example - Run bash example"
	@echo "  make run-simple-python-example - Run simple Python example with simplified interface"
	@echo "  make run-simple-python-web-example - Run simple Python example with web interface"
	@echo "  make run-simple-bash-example - Run simple bash example with simplified interface"
	@echo "  make run-simple-bash-web-example - Run simple bash example with web interface"
	@echo "  make run-devlama-integration-example - Run PyLama integration example"
	@echo "  make run-multi-component-example - Run multi-component workflow example"
	@echo "  make run-grafana-example - Run LogLama + Grafana Docker Compose example"
	@echo "  make stop-grafana-example - Stop LogLama + Grafana Docker Compose example"
	@echo "  make generate-grafana-logs - Generate diverse logs for Grafana visualization"
	@echo "  make run-grafana-web-monitor - Run continuous web log monitoring for Grafana"
	@echo "  make stop-grafana-web-monitor - Stop continuous web log monitoring for Grafana"
	@echo "  make view-example-logs - View logs from example application"
	@echo "  make run-integration - Run integration script"
	@echo ""
	@echo "Debug Utilities:"
	@echo "  make run-debug - Run all LogLama debug utilities"
	@echo "  make run-debug-context - Run context handling debug test"
	@echo "  make run-debug-capture-context - Run capture context decorator debug test"
	@echo "  make run-debug-sqlite - Run SQLite handler debug test"
	@echo "  make run-debug-file - Run file handler debug test"
	@echo ""
	@echo "Environment variables that can be set:"
	@echo "  PORT              - Port for web/API server (default: 8081)"
	@echo "  HOST              - Host for web/API server (default: 127.0.0.1)"
	@echo "  PYTHON            - Python interpreter to use (default: python3)"
	@echo "  VENV_NAME         - Name of virtual environment (default: venv)"
	@echo "  LOG_DIR           - Directory for logs (default: ./logs)"
	@echo "  DB_PATH           - Path to SQLite database (default: ./logs/loglama.db)"
	@echo "  EXAMPLE_DB_PATH   - Path to example SQLite database (default: ./logs/example.db)"
	@echo ""
	@echo "Example usage:"
	@echo "  make web PORT=8081 HOST=0.0.0.0"
	@echo "  make run-examples LOG_DIR=/tmp/logs"
	@echo "  make publish-test"
	@echo "  make version-patch && make publish-full"