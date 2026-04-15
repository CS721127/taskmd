# TaskMD Architecture

## 1. Architecture goal

TaskMD should behave like a **Markdown-first task platform** rather than a hidden internal database with a thin UI on top.

The architecture must support:

- direct Markdown editing
- stable task identity
- low-diff writeback
- rich context through sidecar files
- export and terminal UX layers
- late-stage integrations without polluting the core model

## 2. Layered system

### Layer 1 — CLI / UI
Handles terminal interaction, dashboard rendering, prompts, and future Rich views.

### Layer 2 — Commands
Parses subcommands and routes them into application use-cases.

### Layer 3 — Services
Encodes business logic, including:

- task CRUD
- query and views
- progress / risk / heatmap
- export
- sidecar resolution
- action execution

### Layer 4 — Repository / Storage
Reads and writes primary task files and sidecars safely. Future support can include synced folders or remote backends.

### Layer 5 — Parser / Writer
Converts Markdown and sidecars into internal models and writes them back with minimal formatting disruption.

### Layer 6 — Data
- `tasks.md`
- `.taskmd/items/<task_id>.md`

## 3. Key architectural rule

Core logic must not be tightly coupled to:

- any one editor
- any one cloud provider
- any one AI vendor
- any one academic platform
- any one export target

These belong in extension layers, not the task core.

## 4. Suggested module boundaries

- `models/` — task, metadata, section, sidecar
- `parser/` — Markdown and sidecar parsing / writing
- `storage/` — backends, repository, backup, locking
- `services/` — queries, export, sync, actions, stats
- `commands/` — CLI entrypoints
- `ui/` — terminal rendering, Rich dashboard, themes
- `integrations/` — editor, browser, PDF, calendar, connectors

## 5. Why this matters

Without this separation, the project will quickly regress into a monolithic script where every feature increases breakage risk.
