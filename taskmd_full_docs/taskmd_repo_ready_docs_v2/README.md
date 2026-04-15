# TaskMD

**TaskMD** is a **Markdown-native**, **local-first**, **CLI-first**, and **editor-friendly** task system.

> Your task file is the database. The CLI is the enhancer.

## Why this project exists

Most task tools optimize for app experience first and data ownership second. TaskMD takes the opposite approach:

- your tasks live in **plain Markdown**
- you can edit them directly in **VS Code / Cursor / Obsidian / Vim**
- the CLI adds **speed, structure, validation, views, export, and workflow entry points**
- richer task context can live in **sidecar files** instead of polluting the main task list

This makes TaskMD suitable for people who want a task system that is:

- readable
- versionable
- scriptable
- portable
- extensible

## Product philosophy

TaskMD is designed around six principles:

1. **Markdown is the source of truth**
2. **Manual editing is first-class**
3. **Writeback must be low-diff**
4. **Rich context belongs in sidecar files**
5. **Integrations should be optional and isolated**
6. **Infrastructure comes before magic**

## What TaskMD aims to become

TaskMD is intended to grow in layers:

### Layer 1 — Core task system
- Markdown task storage
- stable IDs
- metadata (`due`, `start`, `pri`, `tags`, `done`)
- add / edit / move / remove / status changes

### Layer 2 — Daily productivity views
- `today`, `next`, `overdue`, `stats`, `risk`
- filters, tags, sorting, archive

### Layer 3 — Terminal UX
- Rich dashboard
- section progress
- live reload
- soft-deadline heatmap

### Layer 4 — Export layer
- ICS / calendar export
- PDF monthly calendar
- CSV / JSON
- image / HTML board export

### Layer 5 — Work entry layer
- task sidecar files
- `tm open <id>`
- `tm start <id>`
- context-aware launch actions

### Layer 6 — Late-stage extensions
- academic mode
- risk engine
- TODO harvesting
- remote storage backends
- connectors
- AI assistance
- plugin ecosystem

## Project scope

### In scope
- a robust Markdown task schema
- round-trip-safe parsing and writing
- editor/CLI coexistence
- repository-ready CLI tooling
- carefully layered extensibility

### Not in scope (early stage)
- heavy multi-user collaboration
- cloud-first SaaS behavior
- provider-specific integrations hardcoded into the core
- features that reduce source readability

## Quick start (planned)

```bash
pip install taskmd
tm
```

Example future usage:

```bash
tm add "Write report" --section Research --due tomorrow
tm today
tm done <id>
tm export pdf --month 2026-04
tm open <id>
```

## Repository docs

- [`docs/architecture.md`](./docs/architecture.md)
- [`docs/schema.md`](./docs/schema.md)
- [`docs/cli.md`](./docs/cli.md)
- [`docs/roadmap.md`](./docs/roadmap.md)
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`CHANGELOG.md`](./CHANGELOG.md)
- [`LICENSE.md`](./LICENSE.md)

## Recommended implementation order

1. schema
2. parser / writer
3. round-trip tests
4. CLI command system
5. storage abstraction
6. dashboard / export / easy start
