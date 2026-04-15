# TaskMD 项目结构（Project Structure）

## 1. 设计目标（Design Goals）

正式项目结构（Formal Project Structure）需要满足以下目标：

1. **模块边界清晰（Clear Module Boundaries）**
2. **支持测试（Testability）**
3. **支持 Markdown 主文件 + Sidecar 文件（Main File + Sidecar Files）**
4. **支持多种存储后端（Storage Backends）**
5. **支持连接器（Connectors）与动作模板（Action Profiles）**
6. **允许未来引入插件系统（Plugin System）**

---

## 2. 推荐仓库结构（Recommended Repository Layout）

```text
TaskMD/
├─ pyproject.toml
├─ README.md
├─ LICENSE
├─ CHANGELOG.md
├─ .gitignore
├─ .github/
│  ├─ workflows/
│  │  ├─ ci.yml
│  │  ├─ release.yml
│  │  └─ docs.yml
│  ├─ ISSUE_TEMPLATE/
│  └─ PULL_REQUEST_TEMPLATE.md
├─ docs/
│  ├─ roadmap.md
│  ├─ schema.md
│  ├─ cli.md
│  ├─ architecture.md
│  └─ design-principles.md
├─ examples/
│  ├─ basic_tasks.md
│  ├─ academic_mode.md
│  ├─ sidecar_examples/
│  └─ config_examples/
├─ src/
│  └─ taskmd/
│     ├─ __init__.py
│     ├─ app.py
│     ├─ cli.py
│     ├─ config.py
│     ├─ constants.py
│     ├─ exceptions.py
│     ├─ models/
│     │  ├─ __init__.py
│     │  ├─ task.py
│     │  ├─ section.py
│     │  ├─ metadata.py
│     │  ├─ sidecar.py
│     │  ├─ profile.py
│     │  └─ export_models.py
│     ├─ parser/
│     │  ├─ __init__.py
│     │  ├─ markdown_parser.py
│     │  ├─ markdown_writer.py
│     │  ├─ txt_legacy_parser.py
│     │  ├─ sidecar_parser.py
│     │  └─ schema.py
│     ├─ storage/
│     │  ├─ __init__.py
│     │  ├─ base.py
│     │  ├─ local_backend.py
│     │  ├─ synced_folder_backend.py
│     │  ├─ ssh_backend.py
│     │  ├─ repository.py
│     │  ├─ backup.py
│     │  └─ locking.py
│     ├─ services/
│     │  ├─ __init__.py
│     │  ├─ task_service.py
│     │  ├─ query_service.py
│     │  ├─ sync_service.py
│     │  ├─ metadata_service.py
│     │  ├─ date_service.py
│     │  ├─ risk_service.py
│     │  ├─ progress_service.py
│     │  ├─ heatmap_service.py
│     │  ├─ stats_service.py
│     │  ├─ export_service.py
│     │  ├─ focus_service.py
│     │  ├─ sidecar_service.py
│     │  ├─ action_service.py
│     │  ├─ ai_service.py
│     │  └─ course_service.py
│     ├─ commands/
│     │  ├─ __init__.py
│     │  ├─ list_cmd.py
│     │  ├─ add_cmd.py
│     │  ├─ edit_cmd.py
│     │  ├─ done_cmd.py
│     │  ├─ open_cmd.py
│     │  ├─ start_cmd.py
│     │  ├─ export_cmd.py
│     │  ├─ risk_cmd.py
│     │  ├─ course_cmd.py
│     │  ├─ config_cmd.py
│     │  ├─ doctor_cmd.py
│     │  └─ migrate_cmd.py
│     ├─ ui/
│     │  ├─ __init__.py
│     │  ├─ terminal.py
│     │  ├─ rich_view.py
│     │  ├─ dashboard.py
│     │  ├─ themes.py
│     │  ├─ formatters.py
│     │  └─ widgets.py
│     ├─ integrations/
│     │  ├─ __init__.py
│     │  ├─ editor.py
│     │  ├─ browser.py
│     │  ├─ pdf.py
│     │  ├─ notes.py
│     │  ├─ audio.py
│     │  ├─ calendar.py
│     │  ├─ maps.py
│     │  ├─ weather.py
│     │  ├─ finance.py
│     │  ├─ course_portals.py
│     │  ├─ commute.py
│     │  ├─ ai_provider.py
│     │  └─ hotkey.py
│     ├─ plugins/
│     │  ├─ __init__.py
│     │  ├─ registry.py
│     │  ├─ hooks.py
│     │  └─ interfaces.py
│     └─ utils/
│        ├─ __init__.py
│        ├─ paths.py
│        ├─ text.py
│        ├─ time.py
│        ├─ ids.py
│        ├─ fs.py
│        └─ validation.py
├─ tests/
│  ├─ parser/
│  ├─ storage/
│  ├─ services/
│  ├─ commands/
│  ├─ roundtrip/
│  ├─ integration/
│  ├─ snapshot/
│  └─ fixtures/
└─ assets/
   ├─ demo/
   ├─ themes/
   ├─ icons/
   └─ audio/
```

---

## 3. 核心目录说明（Core Directory Responsibilities）

### 3.1 `src/taskmd/models/`
负责数据模型（Data Models）定义。

典型实体包括：
- `Task`：单个任务（Single Task）
- `TaskMetadata`：任务元数据（Metadata）
- `TaskSidecar`：任务侧边文件（Sidecar Context）
- `TaskProfile`：动作配置模板（Action Profile）
- `Section` / `Subsection`：层级组织（Hierarchy）

### 3.2 `src/taskmd/parser/`
负责解析与写回（Parsing & Writing）。

包括：
- Markdown 主任务文件解析（Primary Markdown Parsing）
- Sidecar 文件解析（Sidecar Parsing）
- 旧 TXT 格式迁移解析（Legacy TXT Parsing）
- schema 规则定义（Schema Rules）

### 3.3 `src/taskmd/storage/`
负责存储抽象（Storage Abstraction）。

目标是让上层不依赖具体存储方式（Local / SSH / Synced Folder）。

### 3.4 `src/taskmd/services/`
负责业务逻辑（Business Logic）。

这一层是整个系统的“中枢（Core Application Logic）”，包括：
- 任务 CRUD（Create / Read / Update / Delete）
- 统计（Stats）
- 风险评估（Risk Evaluation）
- 热力提醒（Heatmap）
- 导出（Export）
- Focus 模式（Focus Mode）
- AI 辅助（AI Assistance）

### 3.5 `src/taskmd/commands/`
负责 CLI 子命令（CLI Subcommands）入口，实现“命令层（Command Layer）”。

### 3.6 `src/taskmd/ui/`
负责终端展示（Terminal Rendering）与 Rich 界面（Rich UI）。

### 3.7 `src/taskmd/integrations/`
负责对外部系统的轻耦合集成（Lightly Coupled Integrations）。

所有地图、天气、财务、课程系统、AI 等建议都集中在这一层，以免污染核心逻辑。

### 3.8 `src/taskmd/plugins/`
极后期使用，用于实现：
- 插件注册（Plugin Registry）
- Hook 系统（Hooks）
- 第三方扩展（Third-party Extensions）

---

## 4. 运行时分层（Runtime Layers）

推荐将运行逻辑划分为以下 6 层：

### Layer 1：CLI / UI 层（CLI / UI Layer）
处理用户输入（Input）和终端输出（Output）。

### Layer 2：命令层（Command Layer）
负责参数解析（Argument Parsing）和命令路由（Routing）。

### Layer 3：服务层（Service Layer）
负责业务规则（Business Rules）和用例逻辑（Use Cases）。

### Layer 4：存储 / 仓储层（Repository / Storage Layer）
负责文件读写（Read / Write）、原子写入（Atomic Write）、锁（Locking）与后端切换（Backend Selection）。

### Layer 5：解析层（Parser Layer）
负责从 Markdown / Sidecar / Legacy TXT 读取结构化数据。

### Layer 6：数据层（Data Layer）
即主任务文件（Primary Task File）和 Sidecar 文件（Sidecar Files）。

---

## 5. 文档结构建议（Documentation Layout）

项目文档（Project Docs）建议单独维护：

- `docs/schema.md`：定义字段、语法、规则
- `docs/cli.md`：定义命令、参数、输出风格
- `docs/architecture.md`：系统架构说明
- `docs/roadmap.md`：路线图
- `docs/design-principles.md`：设计哲学

这样后续开源（Open Source）时，新贡献者（Contributors）能快速理解项目。

---

## 6. 测试结构建议（Testing Layout）

### 6.1 `tests/parser/`
- 主文件解析测试（Primary File Parsing）
- Sidecar 解析测试（Sidecar Parsing）
- Legacy TXT 迁移测试（Migration Parsing）

### 6.2 `tests/roundtrip/`
- `read -> parse -> write -> read` 语义稳定性测试（Round-trip Stability）

### 6.3 `tests/services/`
- 风险值（Risk Score）
- 热力颜色（Heatmap Rules）
- 进度计算（Section Progress）
- 自动时间戳（Auto-Timestamp）

### 6.4 `tests/commands/`
- CLI 参数与命令行为（CLI Integration Behavior）

### 6.5 `tests/snapshot/`
- Rich 输出快照（Rich Output Snapshots）

---

## 7. 为什么这个结构适合 TaskMD（Why This Structure Fits）

这个结构适合 TaskMD 的原因是：

1. **能支撑 Markdown 核心（Supports Markdown-Centric Core）**
2. **能支撑直接编辑兼容（Supports Direct-Edit Compatibility）**
3. **能支撑 Sidecar 与 Easy Start（Supports Sidecar / Easy Start）**
4. **能将连接器隔离到集成层（Keeps Integrations Isolated）**
5. **能为远程存储与插件系统预留空间（Leaves Room for Backends / Plugins）**
6. **能让中后期 AI 层保持可选（Keeps AI Optional）**
