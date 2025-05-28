# Component Integration with LogLama

This document has been merged into the main README.md for improved clarity and maintainability.

For up-to-date information and integration diagrams, please refer to the [README.md](./README.md).

---

## Legacy Diagram (for reference)

```mermaid
graph TB
    subgraph "PyLama Ecosystem"
        subgraph "LogLama Primary Service"
            LL_ENV[Environment Management] --> LL_DEP[Dependency Validation]
            LL_DEP --> LL_ORCH[Service Orchestration]
            LL_ORCH --> LL_COLL[Log Collector]
            LL_COLL --> LL_DB[(LogLama DB)]
            LL_DB --> LL_WEB[Web Interface]
            LL_DB --> LL_CLI[CLI Commands]
        end
        
        subgraph "WebLama"
            WL[Web UI] --> WL_LOG[Logging Module]
            WL_LOG --> WL_FILE[weblama.log]
        end
        
        subgraph "APILama"
            API[API Server] --> API_LOG[Logging Module]
            API_LOG --> API_FILE[apilama.log]
        end
        
        subgraph "PyLama Core"
            PL[Core Engine] --> PL_LOG[Logging Module]
            PL_LOG --> PL_FILE[devlama.log]
        end
        
        subgraph "BEXY"
            PB[Sandbox] --> PB_LOG[Logging Module]
            PB_LOG --> PB_FILE[bexy.log]
        end
        
        subgraph "PyLLM"
            PLLM[LLM Interface] --> PLLM_LOG[Logging Module]
            PLLM_LOG --> PLLM_FILE[getllm.log]
        end
        
        %% Environment Management
        LL_ENV -->|Configures| WL
        LL_ENV -->|Configures| API
        LL_ENV -->|Configures| PL
        LL_ENV -->|Configures| PB
        LL_ENV -->|Configures| PLLM
        
        %% Dependency Validation
        LL_DEP -->|Validates| WL
        LL_DEP -->|Validates| API
        LL_DEP -->|Validates| PL
        LL_DEP -->|Validates| PB
        LL_DEP -->|Validates| PLLM
        
        %% Service Orchestration
        LL_ORCH -->|Starts| WL
        LL_ORCH -->|Starts| API
        LL_ORCH -->|Starts| PL
        LL_ORCH -->|Starts| PB
        LL_ORCH -->|Starts| PLLM
        
        %% Log Collection
        LL_COLL --> WL_FILE
        LL_COLL --> API_FILE
        LL_COLL --> PL_FILE
        LL_COLL --> PB_FILE
        LL_COLL --> PLLM_FILE
    end
```

For integration code samples, see the README.md and codebase examples.
