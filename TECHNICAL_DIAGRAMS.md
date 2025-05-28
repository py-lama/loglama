# LogLama: Diagramy Techniczne

Ten dokument zawiera szczegu00f3u0142owe diagramy techniczne architektury systemu logowania LogLama, przepu0142ywu danych i interakcji miu0119dzy komponentami. LogLama peu0142ni rolu0119 gu0142u00f3wnego serwisu w ekosystemie PyLama, zapewniaju0105c scentralizowane logowanie, zarzu0105dzanie u015brodowiskiem, walidacju0119 zaleu017cnou015bci i orkiestracju0119 usu0142ug.

## Architektura Systemu

### Architektura wysokiego poziomu

```mermaid
graph TB
    subgraph "Gu0142u00f3wny Serwis"
        LL[LogLama]:::primary
        LC[Kolektor Logu00f3w]:::collector
        SC[Zaplanowany Kolektor]:::collector
        DB[(LogLama DB)]:::storage
        WI[Interfejs Web]:::interface
        CLI[Komendy CLI]:::interface
        ENV[Zarzu0105dzanie u015arodowiskiem]:::primary
        DEP[Walidacja Zaleu017cnou015bci]:::primary
        ORCH[Orkiestracja Usu0142ug]:::primary
    end
    
    subgraph "Komponenty"
        WL[WebLama]:::component
        AL[APILama]:::component
        PL[PyLama]:::component
        PB[BEXY]:::component
        PLLM[PyLLM]:::component
    end
    
    LL -->|Uruchamia siu0119 pierwszy| ENV
    ENV -->|Konfiguruje| WL
    ENV -->|Konfiguruje| AL
    ENV -->|Konfiguruje| PL
    ENV -->|Konfiguruje| PB
    ENV -->|Konfiguruje| PLLM
    
    DEP -->|Waliduje| WL
    DEP -->|Waliduje| AL
    DEP -->|Waliduje| PL
    DEP -->|Waliduje| PB
    DEP -->|Waliduje| PLLM
    
    ORCH -->|Uruchamia| WL
    ORCH -->|Uruchamia| AL
    ORCH -->|Uruchamia| PL
    ORCH -->|Uruchamia| PB
    ORCH -->|Uruchamia| PLLM
    
    WL -->|Generuje Logi| LC
    AL -->|Generuje Logi| LC
    PL -->|Generuje Logi| LC
    PB -->|Generuje Logi| LC
    PLLM -->|Generuje Logi| LC
    
    LC -->|Importuje Logi| DB
    SC -->|Zaplanowany Import| LC
    
    DB -->|Zapytanie o Logi| WI
    DB -->|Zapytanie o Logi| CLI
    
    classDef primary fill:#ff9,stroke:#f90,stroke-width:3px
    classDef component fill:#f9f,stroke:#333,stroke-width:2px
    classDef collector fill:#bbf,stroke:#333,stroke-width:2px
    classDef storage fill:#bfb,stroke:#333,stroke-width:2px
    classDef interface fill:#fbb,stroke:#333,stroke-width:2px
```

### Szczegu00f3u0142owa architektura komponentu00f3w

```
+----------------------------------------------+
|                  Ekosystem PyLama            |
+----------------------------------------------+
|                                              |
|  +------------------+  +------------------+  |
|  |     WebLama      |  |     APILama      |  |
|  +------------------+  +------------------+  |
|  | - logging_config |  | - logging_config |  |
|  | - weblama.log    |  | - apilama.log    |  |
|  +------------------+  +------------------+  |
|                                              |
|  +------------------+  +------------------+  |
|  |     PyLama       |  |      BEXY       |  |
|  +------------------+  +------------------+  |
|  | - logging_config |  | - logging_config |  |
|  | - pylama.log     |  | - bexy.log      |  |
|  +------------------+  +------------------+  |
|                                              |
|  +------------------+  +------------------+  |
|  |      PyLLM       |  |     LogLama      |  |
|  +------------------+  +------------------+  |
|  | - logging_config |  | - log_collector  |  |
|  | - getllm.log      |  | - web_interface  |  |
|  +------------------+  | - cli_commands   |  |
|                        | - loglama.db     |  |
|                        +------------------+  |
|                                              |
+----------------------------------------------+
```

## Przepu0142yw Danych

### Przepu0142yw zbierania logu00f3w

```mermaid
sequenceDiagram
    participant Component as Komponent PyLama
    participant Logger as Logger Komponentu
    participant LogFile as Plik Logu00f3w
    participant Collector as Kolektor Logu00f3w
    participant DB as LogLama DB
    
    Component->>Logger: Zdarzenie logowania
    Logger->>LogFile: Zapisz wpis logu
    Note over Logger,LogFile: Format JSON z kontekstem
    
    Collector->>LogFile: Odczytaj wpisy logu00f3w
    Collector->>Collector: Parsuj i formatuj wpisy
    Collector->>DB: Importuj wpisy logu00f3w
    Note over Collector,DB: Wpisy przechowywane z kontekstem komponentu
```

### Przepu0142yw zapytau0144 o logi

```mermaid
sequenceDiagram
    participant User as Uu017cytkownik
    participant CLI as PyLama CLI
    participant Web as LogLama Web UI
    participant DB as LogLama DB
    
    User->>CLI: Uruchom komendu0119 logs
    CLI->>DB: Zapytanie o logi
    DB->>CLI: Zwru00f3u0107 przefiltrowane logi
    CLI->>User: Wyu015bwietl logi
    
    User->>Web: Dostu0119p do interfejsu web
    Web->>DB: Zapytanie o logi
    DB->>Web: Zwru00f3u0107 przefiltrowane logi
    Web->>User: Wyu015bwietl logi
```

## Interakcje Komponentu00f3w

### Integracja WebLama

```mermaid
flowchart TD
    A[Start WebLama] --> B{COLLECT=1?}
    B -->|Tak| C[Uruchom Kolektor Logu00f3w]
    B -->|Nie| D[Pomiu0144 Zbieranie Logu00f3w]
    C --> E[Uruchom WebLama]
    D --> E
    
    subgraph "Logowanie WebLama"
        E --> F[Generuj Logi]
        F --> G[Zapisz do weblama.log]
    end
    
    subgraph "Zbieranie Logu00f3w"
        H[Zaplanowany Kolektor] --> I{Plik Logu00f3w Istnieje?}
        I -->|Tak| J[Odczytaj Plik Logu00f3w]
        I -->|Nie| K[Pomiu0144 Zbieranie]
        J --> L[Parsuj Wpisy Logu00f3w]
        L --> M[Importuj do LogLama DB]
    end
```

### Integracja PyLama CLI

```mermaid
flowchart TD
    A[PyLama CLI] --> B{Komenda?}
    B -->|logs| C[Przeglu0105daj Logi]
    B -->|collect-logs| D[Zbieraj Logi]
    B -->|log-collector| E{Podkomenda?}
    
    C --> F[Zapytanie do LogLama DB]
    F --> G[Wyu015bwietl Logi]
    
    D --> H[Uruchom Kolektor Logu00f3w]
    H --> I[Importuj Logi]
    
    E -->|start| J[Uruchom Kolektor Logu00f3w]
    E -->|stop| K[Zatrzymaj Kolektor Logu00f3w]
    E -->|status| L[Sprawdu017a Status Kolektora]
```

## Schemat Bazy Danych

```
+-------------------+
|    log_records    |
+-------------------+
| id (PK)           |
| timestamp         |
| level             |
| level_number      |
| logger_name       |
| message           |
| component         |
| version           |
| exception         |
| context           |
+-------------------+
```

## Architektura Wdrou017ceniowa

```mermaid
flowchart TD
    subgraph "Serwer PyLama"
        A[WebLama] --> B[Nginx]
        C[APILama] --> B
        D[LogLama] --> B
        
        E[Daemon Kolektora Logu00f3w] --> F[(LogLama DB)]
        G[Pliki Logu00f3w Komponentu00f3w] --> E
        
        H[BEXY] --> C
        I[PyLLM] --> C
        J[PyLama] --> C
    end
    
    subgraph "Klienci"
        K[Przeglu0105darka] --> B
        L[CLI] --> C
    end
```

## Przepu0142yw Uruchamiania Usu0142ug

```mermaid
sequenceDiagram
    participant User as Uu017cytkownik
    participant CLI as PyLama CLI
    participant LogLama as LogLama
    participant Services as Usu0142ugi PyLama
    
    User->>CLI: pylama start-all
    CLI->>LogLama: Uruchom LogLama
    Note over LogLama: Walidacja u015brodowiska
    Note over LogLama: Sprawdzenie zaleu017cnou015bci
    LogLama->>Services: Uruchom usu0142ugi w kolejnou015bci
    Note over LogLama,Services: 1. LogLama, 2. BEXY, 3. PyLLM, 4. PyLama, 5. APILama, 6. WebLama
    Services->>LogLama: Status uruchomienia
    LogLama->>CLI: Status wszystkich usu0142ug
    CLI->>User: Wyu015bwietl status
```

## Architektura Monitorowania

```mermaid
graph TD
    A[LogLama] -->|Monitoruje| B[BEXY]
    A -->|Monitoruje| C[PyLLM]
    A -->|Monitoruje| D[PyLama]
    A -->|Monitoruje| E[APILama]
    A -->|Monitoruje| F[WebLama]
    
    subgraph "Monitorowanie"
        G[Status Usu0142ug]
        H[Zuu017cycie Zasobu00f3w]
        I[Bu0142u0119dy i Ostrzeu017cenia]
        J[Czas Odpowiedzi]
    end
    
    A -->|Zbiera| G
    A -->|Zbiera| H
    A -->|Zbiera| I
    A -->|Zbiera| J
    
    G --> K[Dashboard]
    H --> K
    I --> K
    J --> K
    
    K --> L[Powiadomienia]
    K --> M[Raporty]
```

## Przepu0142yw Zarzu0105dzania u015arodowiskiem

```mermaid
flowchart TD
    A[LogLama] --> B[Odczytaj .env]
    B --> C{Plik Istnieje?}
    C -->|Nie| D[Utwu00f3rz .env z domyu015blnymi wartou015bciami]
    C -->|Tak| E[Waliduj zmienne u015brodowiskowe]
    D --> E
    E --> F{Brakuju0105ce Zmienne?}
    F -->|Tak| G[Dodaj brakuju0105ce zmienne z domyu015blnymi wartou015bciami]
    F -->|Nie| H[Zau0142aduj zmienne do u015brodowiska]
    G --> H
    H --> I[Udostu0119pnij zmienne innym komponentom]
```

## Architektura Bezpieczeu0144stwa

```mermaid
graph TD
    A[LogLama] --> B[Uwierzytelnianie]
    A --> C[Autoryzacja]
    A --> D[Szyfrowanie]
    A --> E[Walidacja Danych]
    
    subgraph "Zabezpieczenia"
        B --> F[Kontrola Dostu0119pu do API]
        C --> G[Kontrola Dostu0119pu do Logu00f3w]
        D --> H[Bezpieczne Przechowywanie Danych Wrau017cliwych]
        E --> I[Sanityzacja Weju015bcia]
    end
    
    F --> J[Bezpieczny Dostu0119p]
    G --> J
    H --> J
    I --> J
```
