# CLI 命令规范（CLI Specification）

## 1. 命令设计目标（CLI Goals）

- 命令简短（Concise）
- 语义稳定（Stable Semantics）
- 支持脚本化（Scriptable）
- 支持交互式 dashboard（Interactive Dashboard）

## 2. 命令模式（Modes）

### 2.1 Dashboard Mode
```bash
tm
```

### 2.2 Subcommand Mode
```bash
tm add "Write report"
tm list --sort due
tm done <id>
```

## 3. 第一批核心命令（Core Commands）

### 任务操作（Task Ops）
- `tm add`
- `tm edit <id>`
- `tm done <id>`
- `tm todo <id>`
- `tm half <id>`
- `tm rm <id>`
- `tm move <id> --section ... --sub ...`

### 查询视图（Views）
- `tm list`
- `tm today`
- `tm next [days]`
- `tm overdue`
- `tm stats`
- `tm risk`

### 元数据（Metadata）
- `tm due <id> <date>`
- `tm start <id> <date>`
- `tm rem <id> <text>`
- `tm tag <id> add <tag>`
- `tm pri <id> <level>`

### 文件与系统（File / System）
- `tm open`
- `tm open <id>`
- `tm validate`
- `tm reload`
- `tm config show`
- `tm config edit`
- `tm doctor`
- `tm migrate txt-to-md`

### 导出（Export）
- `tm export ics`
- `tm export pdf --month 2026-04`
- `tm export csv`
- `tm export json`
- `tm export image`
- `tm export html --view kanban`

### 任务入口（Work Entry）
- `tm start <id>`
- `tm focus <id>`

## 4. 输出风格（Output Style）

- 默认输出以 human-readable 为主
- 后期可增加 `--json` 供脚本调用
- 错误提示（Errors）应短而明确
- 对高风险写操作提供确认（Confirmation）
