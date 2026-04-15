# Contributing to TaskMD

Thank you for helping improve **TaskMD**.

## Before you contribute

Please read these documents first:

- `README.md`
- `docs/architecture.md`
- `docs/schema.md`
- `docs/cli.md`
- `docs/roadmap.md`

## What the project values most

TaskMD prioritizes:

- stable schema behavior
- safe round-trip editing
- low-diff writeback
- clear module boundaries
- editor-native workflows
- extensibility without early coupling

## Pull request checklist

- [ ] explain the motivation clearly
- [ ] describe the scope of the change
- [ ] add or update tests where appropriate
- [ ] update docs if CLI, schema, or UX behavior changed
- [ ] avoid unrelated refactors in the same PR

## Rules by change type

### If you change parser or writer logic
You must consider:

- round-trip stability
- manual-edit compatibility
- duplicate ID handling
- preservation of non-task markdown where applicable

### If you change CLI behavior
You must update:

- `docs/cli.md`
- examples if relevant
- command tests if they exist

### If you add integrations or AI features
Please keep provider-specific logic out of the core task model unless absolutely necessary.

## Suggested branch naming

- `feature/...`
- `fix/...`
- `docs/...`
- `refactor/...`

## Good issue reports usually include

- expected behavior
- actual behavior
- example task file or reproduction steps
- whether the file was edited manually or through the CLI
