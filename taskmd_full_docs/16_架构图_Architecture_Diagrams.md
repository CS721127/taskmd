# 架构图（Architecture Diagrams）

## 1. 总体架构图（High-Level Architecture）

```mermaid
flowchart TD
    U[User / Editor / Terminal] --> CLI[CLI & UI Layer]
    CLI --> CMD[Command Layer]
    CMD --> SVC[Service Layer]
    SVC --> REPO[Repository / Storage Layer]
    REPO --> PARSER[Parser / Writer Layer]
    PARSER --> DATA[(tasks.md + sidecars)]
    SVC --> INT[Integrations / Connectors]
    SVC --> AI[AI Provider Layer]
```

## 2. 主文件与 Sidecar 关系图（Primary File & Sidecar Relation）

```mermaid
flowchart LR
    A[tasks.md] --> B[Task id:t_01]
    B --> C[.taskmd/items/t_01.md]
    C --> D[Resources]
    C --> E[Actions]
    C --> F[Context]
```

## 3. 读写路径图（Read/Write Flow）

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Service
    participant Repo
    participant Parser
    participant File

    User->>CLI: tm done <id>
    CLI->>Service: set_status(id, done)
    Service->>Repo: load + modify + save
    Repo->>Parser: write markdown
    Parser->>File: safe write tasks.md
```

## 4. 极后期扩展图（Late-Stage Extensibility）

```mermaid
flowchart TD
    Core[Core TaskMD] --> Export[Export Layer]
    Core --> EasyStart[Easy Start]
    Core --> Academic[Academic Mode]
    Core --> Risk[Risk Engine]
    Core --> Remote[Remote Backends]
    Core --> Connectors[Connector Registry]
    Core --> Plugins[Plugin API]
    Core --> AI[AI Assist Layer]
```
