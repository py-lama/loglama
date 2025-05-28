# Detailed Feature Command Comparison

This document provides a detailed comparison of LogLama features with example command(s) for each functionality.

| Feature                     | Example Command(s)                                                                                  |
|-----------------------------|-----------------------------------------------------------------------------------------------------|
| Centralized Env Management  | `python -m loglama.cli.main env`                                                                    |
| Dependency Validation       | `python -m loglama.cli.main check-deps`                                                             |
| Service Orchestration       | `python -m loglama.cli.main start-all`                                                              |
| Multi-output Logging        | `python -m loglama.cli.main logs --output console,file,db`                                          |
| Structured Logging          | `python -m loglama.cli.main logs --format structured`                                               |
| Context-aware Logging       | `python -m loglama.cli.main logs --context user_id=123`                                             |
| Log Rotation/Backup         | `python -m loglama.cli.main logs --rotate`                                                          |
| JSON/Colored Formatting     | `python -m loglama.cli.main logs --format json`<br>`python -m loglama.cli.main logs --format color` |
| Bash Integration            | `bash examples/simple_bash_example.sh`                                                              |
| Multi-language Support      | `python examples/multilanguage_examples.py`                                                         |
| Web Interface               | `PYTHONPATH=. python loglama/cli/web_viewer.py --host 127.0.0.1 --port 8081 --db ./logs/loglama.db` |
| Real-time Dashboard         | (Open the web interface, real-time updates are visible in browser)                                  |
| Log Filtering/Pagination    | `python -m loglama.cli.main logs --level WARNING --page 2 --page-size 50`                           |
| Export Logs (CSV)           | `python -m loglama.cli.main logs --export csv --output-file logs.csv`                               |
| RESTful API                 | `curl http://127.0.0.1:5000/api/logs`                                                               |
| CLI Tools                   | `python -m loglama.cli.main --help`                                                                 |
| Unit/Integration Tests      | `pytest tests/`                                                                                     |
| Auto-diagnostics/Repair     | `python -m loglama.cli.main diagnose`                                                               |
| Health Checks/Reports       | `python -m loglama.cli.main stats`                                                                  |
| Integration Scripts         | `python examples/devlama_integration_example.py`                                                     |
| Cluster/K8s Support         | `kubectl apply -f k8s/loglama-deployment.yaml`                                                      |
| Grafana/Loki Integration    | `docker-compose -f examples/loglama-grafana/docker-compose.yml up`                                  |
| Prometheus Integration      | (See Prometheus integration guide in docs)                                                          |
| Context Capture Decorators  | (Use `@loglama.capture_context` in your Python code)                                                |
| Customizable via Env Vars   | `export LOGLAMA_DB_PATH=./logs/loglama.db`<br>`python -m loglama.cli.main logs`                     |
| Production DB Support       | `python -m loglama.cli.main logs --db postgresql://user:pass@host:5432/loglama`                     |
| Eliminate Duplicated Code   | (Follow LogLama integration patterns and shared utils)                                              |

---

For more details on each feature, see the main [README.md](README.md) and [Component Integration Guide](COMPONENT_INTEGRATION.md).
