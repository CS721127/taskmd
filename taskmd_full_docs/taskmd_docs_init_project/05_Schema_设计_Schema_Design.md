# TaskMD Schema 设计（Schema Design）

## 1. 设计目标（Schema Goals）

TaskMD 的 Schema（Schema）必须同时满足以下要求：

1. **人类可读（Human-Readable）**
2. **程序可解析（Machine-Parseable）**
3. **适合编辑器直接修改（Editor-Friendly）**
4. **支持低扰动写回（Low-Diff Writeback）**
5. **支持 Sidecar 与上下文动作（Sidecar / Context Actions）**
6. **支持后续导出与 AI（Export / AI Ready）**

---

## 2. 主任务文件（Primary Task File）

### 2.1 文件名称（Filename）
默认主任务文件：

```text
tasks.md
```

### 2.2 顶部元信息（Header Metadata）
文件顶部允许出现系统级别注释（System Metadata）：

```md
<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->
<!-- taskmd:profile=default -->
```

这些注释（Comments）不显示在 Markdown 预览中，但对程序可见。

---

## 3. 主结构语法（Primary Structure Syntax）

### 3.1 一级标题（Section）
使用 Markdown 一级标题：

```md
# School
# Research
# Daily
# Inbox
```

### 3.2 二级标题（Subsection）
使用 Markdown 二级标题：

```md
## DPST1092
## FL Project
## Routine
```

### 3.3 任务行（Task Item）
标准任务行格式：

```md
- [ ] Write report
- [-] Draft experiment notes
- [x] Submit assignment
```

状态（Status）说明：
- `[ ]`：未完成（Todo）
- `[-]`：进行中（In Progress）
- `[x]`：已完成（Done）

---

## 4. 隐藏元数据（Hidden Metadata）

### 4.1 基本形式（Basic Form）
任务元数据使用 HTML 注释（HTML Comments）表示：

```md
- [ ] Write report <!-- id:t_01HZ9A, due:2026-04-20, pri:4 -->
```

### 4.2 设计原则（Design Principle）
- 正文尽量简洁（Clean Visible Text）
- 元数据尽量隐藏（Hidden Metadata）
- 所有结构字段都可由程序读取

---

## 5. 核心字段（Core Fields）

下面是主任务文件中建议支持的字段。

### 5.1 必选字段（Required Fields）

#### `id`
任务唯一标识（Stable Task ID）。

示例：
```text
id:t_01HZ9A
```

要求：
- 持久化（Persistent）
- 全局唯一（Globally Unique within Project Scope）
- 用户手工移动任务后不变

---

### 5.2 常用可选字段（Common Optional Fields）

#### `due`
截止日期（Due Date）。

```text
due:2026-04-20
```

#### `start`
开始关注日期（Soft Deadline / Attention Start）。

```text
start:2026-04-15
```

#### `pri`
优先级（Priority），建议为数字。

```text
pri:4
```

推荐内部规则：
- `0`：none
- `1`：low
- `2`：medium
- `3`：high
- `4`：very high
- `5`：critical

#### `tags`
标签（Tags），建议使用逗号分隔。

```text
tags:research,fl,paper
```

#### `rem`
简短备注（Short Remark）。

```text
rem:"Need prof feedback"
```

#### `done`
完成时间戳（Completion Timestamp）。

```text
done:2026-04-11T20:35:10+10:00
```

#### `created`
创建时间戳（Created Timestamp）。

#### `updated`
更新时间戳（Updated Timestamp）。

---

## 6. 进阶字段（Advanced Fields）

### 6.1 `weight`
任务权重（Weight），用于 Assignment / Project Risk View。

```text
weight:20
```

### 6.2 `course`
课程代码（Course Code）。

```text
course:DPST1092
```

### 6.3 `recur`
重复规则（Recurrence Rule）。

```text
recur:daily
recur:weekly@fri
recur:monthly@1
```

### 6.4 `est`
预计时长（Estimated Time）。

```text
est:50m
```

### 6.5 `loc`
地点（Location / Campus / Gym / Address）。

```text
loc:K17
```

### 6.6 `sidecar`
是否显式关联 sidecar 文件（通常可由 `id` 推断，不强制显式写）。

```text
sidecar:true
```

---

## 7. 主文件示例（Primary File Example）

```md
<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->

# Inbox
- [ ] Buy adapter for monitor <!-- id:t_01HZA1, created:2026-04-11T21:30:00+10:00, tags:shopping -->

# School
## DPST1092
- [ ] Prepare tutoring material <!-- id:t_01HZA2, due:2026-04-20, start:2026-04-15, pri:4, course:DPST1092, tags:teaching,course -->
- [x] Submit lab solution <!-- id:t_01HZA3, due:2026-04-10, done:2026-04-10T18:20:00+10:00, pri:5, weight:10 -->

# Research
## FL Project
- [-] Draft experiment notes <!-- id:t_01HZA4, due:2026-04-16, pri:3, tags:research,fl -->
```

---

## 8. Sidecar 设计（Task Sidecar Design）

为了保持 `tasks.md` 简洁（Clean Main File），每个任务可以可选关联一个 Sidecar 文件（Task Sidecar File）。

### 8.1 默认路径（Default Sidecar Path）

```text
.taskmd/items/<task_id>.md
```

例如：

```text
.taskmd/items/t_01HZA2.md
```

### 8.2 Sidecar 的用途（Use Cases）
- 长备注（Long Notes）
- 链接和资源（Resources）
- 动作模板（Action Profiles）
- 课程资料 / 代码项目 / 会议上下文（Context）
- 知识沉淀（Knowledge Capture）

### 8.3 Sidecar 示例（Example）

```md
# Task Context: Prepare tutoring material

## Summary
Need to prepare Week 5 tutoring notes and example solutions.

## Resources
- pdf: /Users/cen/materials/dpst1092/week5.pdf
- url: https://canvas.example.edu/course/DPST1092
- note: obsidian://open?vault=Knowledge&file=DPST1092_Tutorial_Week5
- folder: /Users/cen/teaching/dpst1092/

## Actions
- profile: academic
- open_pdf
- open_note
- open_folder

## Context
- course: DPST1092
- project: tutoring
- tags: teaching,academic

## Knowledge Handoff
- on_complete: ask_to_append_knowledge_base
```

---

## 9. 动作模板（Action Profiles）

### 9.1 目标（Goal）
为不同类型任务定义一组“打开方式（Openers）”与“启动动作（Start Actions）”。

### 9.2 建议内置 Profile（Suggested Built-in Profiles）
- `dev`
- `academic`
- `meeting`
- `paper`
- `fitness`
- `finance`
- `shopping`
- `commute`

### 9.3 示例（Example）

```md
## Actions
- profile: dev
- open_folder
- open_editor
- open_terminal
```

### 9.4 使用方式（Usage）
- `tm open <id>`：打开资源（Resources）
- `tm start <id>`：进入执行上下文（Execution Context）

---

## 10. 直接编辑兼容规则（Direct Edit Rules）

这是 Schema 的关键部分。

### 10.1 用户手工新增任务（Manual Add）
如果用户手工写入：

```md
- [ ] Read paper
```

程序下次保存时应自动补：

```md
- [ ] Read paper <!-- id:t_01HZNEW -->
```

### 10.2 用户手工删除任务（Manual Delete）
直接删掉某行任务，程序应理解为删除该任务。

### 10.3 用户手工修改标题 / 状态 / due（Manual Edit）
若 `id` 未变，则视为同一任务被修改，而非新建任务。

### 10.4 用户移动任务（Move Across Sections）
如果带 `id` 的任务被移动到别的 section / subsection，程序应保留其身份（Identity）。

### 10.5 重复 ID（Duplicate ID）
如果用户复制粘贴导致两个任务拥有同一 `id`：
- 程序应警告（Warn）
- 自动为后出现项生成新 ID（默认策略）
- 保留原始文本语义（Preserve User Intent）

### 10.6 非任务 Markdown 文本（Non-task Markdown Text）
普通说明文本（Notes / Comments）应尽可能保留，而不是丢弃。

---

## 11. 写回规则（Writeback Rules）

### 11.1 低扰动写回（Low-Diff Writeback）
默认应尽量：
- 不重排 section / subsection
- 不重写无关文本
- 不擅自改变空行风格

### 11.2 自动更新字段（Auto-updated Fields）
当通过 CLI 修改任务时，程序可更新：
- `updated`
- `done`
- 缺失的 `id`

### 11.3 显示层与数据层分离（Display vs Data Separation）
像 Section Progress、Heatmap 颜色这类信息默认只在 UI 渲染，不写回主文件。

---

## 12. Remote Storage 对 Schema 的影响（Remote Storage Considerations）

Schema 本身不应依赖“文件一定在本地”。
只要 storage backend 能提供：
- 读取文本（Read Text）
- 原子写入或类原子写入（Atomic / Safe Write）
- mtime / version 信息（for Sync / Live Reload）

则同一 Schema 可用于：
- 本地文件（Local File）
- 同步目录（Synced Folder）
- SSH / SFTP 远程路径（Remote Backend）

---

## 13. AI 与 Connector 对 Schema 的影响（AI / Connector Considerations）

### 13.1 主文件中不应塞入过多 API 细节
例如地图 API、股票 API、课程平台 token 等配置，不应写进主任务文件。

### 13.2 复杂集成数据应放：
- 配置文件（Config）
- Sidecar 文件（Sidecar）
- Connector 配置（Connector Profile）

这样能保持 `tasks.md` 清爽，并减少用户理解负担。

---

## 14. 最终建议（Final Recommendations）

TaskMD 的 Schema 设计应坚持：

1. **主文件最小必要信息（Minimal Main File）**
2. **复杂上下文移入 Sidecar（Move Rich Context to Sidecar）**
3. **ID 稳定（Stable Identity）**
4. **Round-trip 稳定（Stable Read/Write Cycle）**
5. **可扩展但不臃肿（Extensible but not bloated）**

只有把这些规则先立稳，后续的：
- Live Reload
- Export
- Easy Start
- Academic Mode
- Risk Engine
- Remote Storage
- AI

才能真正站得住。
