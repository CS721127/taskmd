# TaskMD Roadmap

## Roadmap strategy

Build in this order:

1. foundation
2. daily usability
3. terminal UX
4. export
5. easy start
6. academic / risk workflows
7. remote / AI / connectors / plugins

## Phases

### Phase 0 — Architecture Refactor
- modularize the codebase
- introduce stable IDs
- create a test skeleton

### Phase 1 — Packaging & Configuration
- `pyproject.toml`
- console script `tm`
- default config directory

### Phase 2 — Markdown-Native Storage
- primary schema
- parser / writer
- txt migration

### Phase 3 — Direct Edit Compatibility
- auto ID enrichment
- duplicate ID repair
- round-trip tests

### Phase 4 — CLI Commands & Daily Views
- list / add / edit / done / due / stats / today / overdue

### Phase 5 — Rich Dashboard & Live Reload
- Rich UI
- section progress
- file watching

### Phase 6 — Time Awareness
- auto timestamp
- soft deadlines
- heatmap

### Phase 7 — Productivity Enhancements
- recurring tasks
- quick capture syntax
- weekly report basics

### Phase 8 — Export Layer
- ICS / PDF / CSV / JSON / image / HTML

### Phase 9+ — Sidecars, Easy Start, Academic Mode, Risk Engine, TODO Harvesting, Remote Backends, Connectors, AI, Plugins
