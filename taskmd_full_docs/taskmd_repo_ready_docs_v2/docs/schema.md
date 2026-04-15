# TaskMD Schema

## 1. Schema objectives

The schema must be:

- human-readable
- machine-parseable
- editor-friendly
- round-trip-safe
- future-proof without becoming noisy

## 2. Primary task file

Default file name:

```text
tasks.md
```

### Header metadata

```md
<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->
```

## 3. Structural syntax

```md
# School
## DPST1092
- [ ] Prepare tutorial <!-- id:t_01, due:2026-04-20, pri:4 -->
```

## 4. Status markers

- `[ ]` = todo
- `[-]` = in progress
- `[x]` = done

## 5. Recommended metadata fields

### Required
- `id`

### Common optional
- `due`
- `start`
- `pri`
- `tags`
- `rem`
- `created`
- `updated`
- `done`

### Advanced
- `weight`
- `course`
- `recur`
- `est`
- `loc`

## 6. Direct edit rules

- tasks added without `id` receive an ID during save
- deleting a task line means delete the task
- moving a task with the same `id` preserves identity
- duplicate IDs must be detected and repaired
- non-task Markdown should be preserved whenever possible

## 7. Writeback rules

- minimize reformatting
- avoid unnecessary reordering
- write only necessary metadata changes
- keep display-only information out of the main file

## 8. Sidecar relationship

Rich context should live in:

```text
.taskmd/items/<task_id>.md
```

The main task file stays readable; detailed resources and actions move into sidecars.
