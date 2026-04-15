# TaskMD 项目骨架（Project Skeleton）

## 1. 骨架目标（Skeleton Goals）

本骨架（Skeleton）用于指导 TaskMD v2/v3 的第一版工程实现（Initial Engineering Implementation）。

目标不是一次性写完所有功能，而是先搭一个能承接未来长期演进（Long-term Evolution）的项目骨架。

---

## 2. 第一版建议包结构（Suggested Package Layout）

```text
src/taskmd/
├─ __init__.py
├─ app.py
├─ cli.py
├─ config.py
├─ constants.py
├─ exceptions.py
├─ models/
│  ├─ __init__.py
│  ├─ task.py
│  ├─ metadata.py
│  ├─ section.py
│  └─ sidecar.py
├─ parser/
│  ├─ __init__.py
│  ├─ markdown_parser.py
│  ├─ markdown_writer.py
│  ├─ txt_legacy_parser.py
│  └─ schema.py
├─ storage/
│  ├─ __init__.py
│  ├─ base.py
│  ├─ local_backend.py
│  ├─ repository.py
│  └─ backup.py
├─ services/
│  ├─ __init__.py
│  ├─ task_service.py
│  ├─ query_service.py
│  ├─ sync_service.py
│  ├─ date_service.py
│  ├─ stats_service.py
│  ├─ progress_service.py
│  ├─ heatmap_service.py
│  ├─ export_service.py
│  ├─ sidecar_service.py
│  └─ action_service.py
├─ commands/
│  ├─ __init__.py
│  ├─ list_cmd.py
│  ├─ add_cmd.py
│  ├─ edit_cmd.py
│  ├─ done_cmd.py
│  ├─ open_cmd.py
│  ├─ export_cmd.py
│  ├─ stats_cmd.py
│  ├─ config_cmd.py
│  ├─ doctor_cmd.py
│  └─ migrate_cmd.py
├─ ui/
│  ├─ __init__.py
│  ├─ terminal.py
│  ├─ rich_view.py
│  ├─ dashboard.py
│  └─ themes.py
├─ integrations/
│  ├─ __init__.py
│  ├─ editor.py
│  ├─ browser.py
│  ├─ pdf.py
│  ├─ notes.py
│  ├─ calendar.py
│  └─ hotkey.py
└─ utils/
   ├─ __init__.py
   ├─ paths.py
   ├─ time.py
   ├─ ids.py
   ├─ text.py
   └─ validation.py
```

---

## 3. 第一版关键模块职责（v2 Core Module Responsibilities）

### 3.1 `cli.py`
- 解析命令行参数（Argument Parsing）
- 路由到具体命令（Command Routing）
- 支持 `tm` 进入 dashboard 与 `tm add` / `tm list` 等子命令模式

### 3.2 `app.py`
- 应用装配（Application Bootstrap）
- 读取配置（Config Loading）
- 初始化 storage backend、repository、services 与 UI

### 3.3 `config.py`
- 读取配置文件（Config File）
- 读取环境变量（Environment Variables）
- 合并 CLI 参数（CLI Overrides）
- 提供统一配置对象（Resolved Settings）

### 3.4 `models/`
- 定义核心实体（Core Entities）
- 建议最先实现 `Task` 与 `TaskMetadata`

### 3.5 `parser/`
- `markdown_parser.py`：从 `tasks.md` 读入结构化对象
- `markdown_writer.py`：把任务写回 Markdown
- `txt_legacy_parser.py`：兼容老 TXT 数据迁移
- `schema.py`：集中定义字段和语法规则

### 3.6 `storage/`
- 负责主任务文件（Main Task File）和 Sidecar 文件（Sidecar Files）的读取与保存
- 提供原子写入（Atomic Write）与基础备份（Backup）

### 3.7 `services/task_service.py`
- 任务层 CRUD
- 状态修改
- due / tags / priority / move
- 自动更新时间戳（updated）

### 3.8 `services/query_service.py`
- list / today / next / overdue / search / filter 的核心逻辑

### 3.9 `services/sync_service.py`
- file watch / live reload
- reload / validate / mtime detection

### 3.10 `services/sidecar_service.py`
- 读取与维护 sidecar 文件
- 确保 Sidecar 与主任务 `id` 对齐

### 3.11 `services/action_service.py`
- 解释 Task Sidecar 中的资源（Resources）与动作（Actions）
- 执行 `tm open <id>` / `tm start <id>`

### 3.12 `ui/`
- `terminal.py`：基础文本渲染
- `rich_view.py`：Rich 风格组件
- `dashboard.py`：dashboard 组合布局
- `themes.py`：主题颜色与图标映射

---

## 4. 最先该实现的最小可运行路径（Minimum Viable Path）

推荐先做一个 **TaskMD v2 MVP（Minimum Viable Product）**：

### Step 1：配置与路径（Config & Paths）
- `pyproject.toml`
- `tm` console script
- 默认任务文件路径（如 `~/.config/taskmd/tasks.md`）

### Step 2：Task 模型与 Schema
- `Task`
- `TaskMetadata`
- `Section / Subsection`
- Hidden Metadata 规则

### Step 3：Markdown Parser / Writer
- 解析主任务文件
- 保持低扰动写回
- 支持自动补 ID

### Step 4：Repository + Task Service
- `load_tasks()`
- `save_tasks()`
- `add_task()`
- `set_status()`
- `set_due()`
- `set_remark()`
- `move_task()`

### Step 5：基础 CLI 子命令
- `list`
- `add`
- `done`
- `todo`
- `rm`
- `due`
- `open`
- `validate`

### Step 6：Round-trip Tests
- 用 fixtures 验证 “读 → 写 → 再读” 的语义稳定性

### Step 7：Rich Dashboard（第一版）
- today / overdue / stats
- progress
- live reload（可稍后）

---

## 5. CLI 命令骨架（CLI Command Skeleton）

第一版建议支持以下命令：

```bash
tm
tm list
tm add "Write report"
tm edit <id>
tm done <id>
tm todo <id>
tm rm <id>
tm due <id> 2026-04-20
tm rem <id> "Need professor feedback"
tm move <id> --section Research --sub FL
tm open
tm open <id>
tm validate
tm stats
tm config show
tm doctor
tm migrate txt-to-md
```

第二版再逐步加入：

```bash
tm today
tm next 7
tm overdue
tm risk
tm export ics
tm export pdf --month 2026-04
tm focus <id>
tm start <id>
```

---

## 6. 第一版数据流（Data Flow）

### 6.1 读流程（Read Flow）
```text
Storage Backend -> Repository -> Markdown Parser -> Task Models -> Service Layer -> UI / CLI
```

### 6.2 写流程（Write Flow）
```text
CLI / UI -> Command -> Service Layer -> Repository -> Markdown Writer -> Storage Backend
```

### 6.3 Sidecar 流程（Sidecar Flow）
```text
Task ID -> Sidecar Service -> .taskmd/items/<id>.md -> Action / Resource Resolution
```

---

## 7. 配置骨架（Configuration Skeleton）

建议配置优先级（Precedence）：

1. CLI 参数（CLI Args）
2. 环境变量（ENV）
3. 配置文件（Config File）
4. 默认值（Defaults）

### 示例配置（Example Config）

```toml
db_path = "~/.config/taskmd/tasks.md"
theme = "dracula"
editor = "code"
timezone = "Australia/Sydney"
auto_git_backup = false
default_view = "today"
live_reload = true
```

后续再加入：
- storage backend
- AI provider config
- course connector settings
- default openers / action profiles

---

## 8. 测试骨架（Testing Skeleton）

### 8.1 第一批必须的测试（Must-have Tests）

#### Parser Tests
- section / subsection / task parsing
- metadata parsing
- invalid metadata tolerance

#### Writer Tests
- stable writeback
- auto-add ID
- preserve non-task text where possible

#### Round-trip Tests
- `read -> write -> read`
- `manual edit -> reload -> save -> reload`

#### CLI Tests
- add / done / due / rm / open / validate

---

## 9. 项目实现顺序建议（Suggested Build Order）

### 第一阶段（打地基）
1. `config.py`
2. `models/`
3. `parser/`
4. `storage/`
5. `task_service.py`
6. `commands/` 基础命令
7. round-trip tests

### 第二阶段（形成产品）
8. `ui/rich_view.py`
9. `dashboard.py`
10. `progress_service.py`
11. `sync_service.py`
12. `stats_service.py`

### 第三阶段（形成特色）
13. `sidecar_service.py`
14. `action_service.py`
15. `open_cmd.py`
16. `start_cmd.py`
17. export / focus / risk

---

## 10. 最终建议（Final Recommendation）

TaskMD 的第一版骨架（Initial Skeleton）最重要的不是“看起来功能很多”，而是：

1. **Schema 定义稳（Stable Schema）**
2. **Parser / Writer 稳（Stable Round-trip）**
3. **Task ID 稳（Stable Identity）**
4. **Sidecar 模型清晰（Clear Sidecar Model）**
5. **连接器与 AI 留口但不早耦合（Leave Hooks, Avoid Early Coupling）**

只要这个骨架搭稳，后面的：
- Live Reload
- Risk Engine
- Easy Start
- Academic Mode
- Remote Storage
- AI API
- Plugin System

都能在不推翻架构的情况下逐步叠加。
