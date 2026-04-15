# TaskMD 项目介绍（Project Introduction）

## 1. 项目定义（Project Definition）

**TaskMD** 是一个以 **Markdown（Markdown）** 为原生存储格式（Source of Truth）、以 **命令行（CLI, Command-Line Interface）** 为主要交互方式、并且对 **编辑器直接编辑（Editor-Native Editing）** 提供正式支持的任务管理工具（Task Manager）与任务执行入口层（Task Execution Entry Layer）。

它不是一个把任务锁进黑盒数据库（Black-Box Database）的应用，而是一个把任务保存到你自己可读、可编辑、可版本控制（Version-Controlled）的纯文本文件（Plain Text Files）中的系统。

---

## 2. 一句话价值主张（One-line Value Proposition）

> **你的任务文件就是数据库（The file is the database），CLI 只是增强层（Enhancer），不是控制层（Controller）。**

---

## 3. 问题背景（Problem Statement）

很多任务管理工具（Task Managers）在以下方面存在问题：

- 数据封闭（Closed Data）：任务被锁在 App 内部，迁移困难
- 编辑不自由（Poor Editability）：无法直接用 VS Code / Obsidian / Vim 批量编辑
- 过于“应用化”（Too App-Centric）：用户必须进入固定界面才能操作
- 缺少工程化可持续性（Poor Engineering Longevity）：不适合 Git、自动化（Automation）与脚本化（Scripting）
- 难以延展到“任务 → 执行环境”（Task → Execution Context）

TaskMD 的目标就是解决这些痛点：

1. 用 Markdown（Markdown）保存任务
2. 用 CLI（CLI）高效操作任务
3. 允许用户直接修改 `.md` 文件
4. 用 Sidecar 文件（Task Sidecar Files）扩展复杂上下文（Context）
5. 用连接器（Connectors）和动作模板（Action Profiles）接入更多工作流（Workflows）

---

## 4. 产品定位（Product Positioning）

TaskMD 的定位可以概括为：

### 4.1 Markdown 原生（Markdown-Native）
任务数据首先是一份人类可读的 Markdown 文档（Human-Readable Markdown Document），而不是工具私有格式（Proprietary Format）。

### 4.2 本地优先（Local-First）
默认以本地文件（Local Files）为数据源，强调可控性（Control）、持久性（Longevity）与离线可用性（Offline Availability）。

### 4.3 命令行优先（CLI-First）
TaskMD 首先是一个命令行工具（CLI Tool），支持快速录入（Quick Capture）、查询（Query）、过滤（Filtering）、导出（Export）和一键动作（Easy Start）。

### 4.4 编辑器原生（Editor-Native）
用户可以直接在 VS Code / Cursor / Obsidian / Vim / Notepad 中编辑 `tasks.md`，程序需要稳健支持：

- 批量添加（Bulk Add）
- 批量删除（Bulk Delete）
- 批量修改（Bulk Edit）
- 移动任务（Move Across Sections）
- 任务排序重构（Reordering / Refactoring）

### 4.5 可扩展连接（Extensible by Design）
TaskMD 不应把所有功能硬编码（Hardcode）进核心，而应保留大量扩展点（Extension Points），允许后期接入：

- 课程系统（Course Connectors）
- 地图 / 通勤 / 天气（Map / Commute / Weather）
- 开发环境（Dev Environment）
- PDF / 笔记 / 文献管理（PDF / Notes / Paper Workflows）
- AI API（AI Providers）
- 远程存储（Remote Storage Backends）

---

## 5. 目标用户（Target Users）

### 5.1 开发者（Developers）
- 偏好终端（Terminal）和文本工作流（Text-Based Workflow）
- 希望任务与代码仓库（Code Repository）/ TODO 注释（TODO Comments）联动
- 需要从任务快速进入代码环境（Project Context）

### 5.2 学术用户（Academic Users）
- 学生（Students）
- 导师 / Tutor
- 研究者（Researchers）
- 教学相关用户（Teaching-Related Users）

典型需求包括：
- 课程代码高亮（Course Code Highlighting）
- 作业与考试的硬截止（Hard Deadlines）
- 风险排序（Risk Ranking）
- 课程资料联动（Material Sync）
- 文献 / PDF / 笔记一键打开（Paper/PDF/Notes Openers）

### 5.3 知识工作者（Knowledge Workers）
- 想用纯文本（Plain Text）管理长期任务系统
- 希望任务与 Obsidian / Notion / PDF / 日历 / Git / 周报导出联动

### 5.4 极简效率用户（Minimal Productivity Users）
- 喜欢简单但强大的工具（Simple but Powerful Tools）
- 不想进入复杂 UI，只想快速记录并开始做事

---

## 6. 核心设计原则（Core Design Principles）

### 6.1 文件即数据库（The File Is the Database）
`tasks.md` 是最终事实来源（Source of Truth）。所有 CLI 操作最终都落回这份文件。

### 6.2 CLI 是增强器（CLI as Enhancer）
CLI 不垄断编辑，而是提供：
- 快速操作（Fast Commands）
- 智能补元数据（Auto Metadata Enrichment）
- 过滤 / 排序 / 统计（Filtering / Sorting / Stats）
- 导出（Export）
- 一键动作（Easy Start / Context Actions）

### 6.3 手工编辑是一等公民（Manual Editing Is First-Class）
用户手工编辑 Markdown 文件不应被视为“异常场景（Edge Case）”，而应被视为正式工作流（First-Class Workflow）。

### 6.4 低扰动写回（Low-Diff Writeback）
程序写回文件时应尽量：
- 保持原有结构（Preserve Structure）
- 减少大面积 diff（Minimize Git Diff Noise）
- 保持非任务说明文本（Notes Blocks）

### 6.5 复杂上下文外置（Externalize Complex Context）
为了保持主任务文件简洁（Clean Main File），复杂上下文（Complex Context）应放入 **Task Sidecar Files**。

### 6.6 可选智能层（Optional Intelligence Layer）
AI、地图、价格追踪、天气等能力属于可选增强层（Optional Integrations），不应反向污染核心任务系统（Core Task System）。

---

## 7. 长期愿景（Long-term Vision）

TaskMD 最终希望演化为：

> **Markdown-Native Task System + CLI Efficiency + Editor Round-Trip + Work Entry Actions + Extensible Integrations + Optional AI Assistance**

也就是说，它不仅是一个“任务清单工具（Task List Tool）”，更是一个：

- 任务数据库（Task Database）
- 工作入口（Work Entry Point）
- 本地工作流连接器（Local Workflow Connector）
- 导出与展示工具（Export & Presentation Tool）
- 可演进的个人效率基础设施（Personal Productivity Infrastructure）

---

## 8. 非目标（Non-Goals）

为了保持项目边界清晰（Clear Scope），TaskMD **不以以下方向为第一优先目标**：

- 重型多人协作平台（Heavy Multi-user Collaboration Platform）
- 云端任务 SaaS（Cloud-first SaaS Product）
- 替代 IDE / 笔记软件 / 日历 / 音乐播放器本身
- 在早期版本中实现所有连接器（All Connectors at Once）

TaskMD 的策略应是：

1. 先把核心文件系统（Core File System）做好
2. 再把 CLI 与编辑器 round-trip 做稳
3. 再逐步加导出、UI、上下文动作与连接器
4. 最后加 AI 和生态层（Ecosystem Layer）
