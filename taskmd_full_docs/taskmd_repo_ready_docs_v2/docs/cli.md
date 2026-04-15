# TaskMD CLI Specification

## 1. Interaction modes

### Dashboard mode
```bash
tm
```

### Subcommand mode
```bash
tm add "Write report"
tm today
tm done <id>
```

## 2. Core command surface

### Task operations
- `tm add`
- `tm edit <id>`
- `tm done <id>`
- `tm todo <id>`
- `tm half <id>`
- `tm rm <id>`
- `tm move <id> --section ... --sub ...`

### Views
- `tm list`
- `tm today`
- `tm next [days]`
- `tm overdue`
- `tm stats`
- `tm risk`

### Metadata
- `tm due <id> <date>`
- `tm start <id> <date>`
- `tm rem <id> <text>`
- `tm tag <id> add <tag>`
- `tm pri <id> <level>`

### File and system commands
- `tm open`
- `tm open <id>`
- `tm validate`
- `tm reload`
- `tm config show`
- `tm config edit`
- `tm doctor`
- `tm migrate txt-to-md`

### Export commands
- `tm export ics`
- `tm export pdf --month 2026-04`
- `tm export csv`
- `tm export json`
- `tm export image`
- `tm export html --view kanban`

### Work-entry commands
- `tm open <id>`
- `tm start <id>`
- `tm focus <id>`

## 3. CLI rules

- commands should be short and explicit
- defaults should be safe
- destructive actions should be confirmable
- future machine-readable mode may use `--json`

## 4. Long-term command philosophy

TaskMD should support both:

- interactive dashboard workflows
- direct subcommand workflows suitable for scripting and daily shell use
