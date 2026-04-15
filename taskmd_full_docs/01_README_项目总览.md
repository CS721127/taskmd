# TaskMD（正式项目总览）

## 项目简介（Project Overview）

**TaskMD** 是一个 **Markdown 原生（Markdown-Native）**、**本地优先（Local-First）**、**CLI 优先（CLI-First）**、**编辑器原生兼容（Editor-Native）** 的任务管理与工作流入口系统（Task System + Work Entry Layer）。

它的核心思想是：

> 任务文件本身就是数据库（The file is the database），CLI 只是增强层（Enhancer），不是控制层（Controller）。

## 核心价值（Core Value）

- 任务以 Markdown 保存，长期可读（Readable）、可迁移（Portable）、可版本控制（Versionable）
- 用户可以直接在 VS Code / Obsidian / Vim 中编辑任务文件
- CLI 提供高效查询、排序、修改、导出与上下文动作（Context Actions）
- 复杂上下文通过 Sidecar 文件承载，保持主文件干净
- 后期可通过 Connectors / Plugins / AI Provider 扩展，但不污染核心系统

## 目标用户（Target Users）

- 开发者（Developers）
- 研究者（Researchers）
- 学生 / Tutor（Students / Tutors）
- 习惯 Markdown 和本地工作流的知识工作者（Knowledge Workers）
- 喜欢极简但可扩展工具的人（Minimal but Extensible Tool Users）

## 项目目标（Project Goals）

1. 打造稳定、可读、可编辑的 Markdown 任务系统
2. 让 CLI 与编辑器形成双向兼容（Round-trip Editing）
3. 支持高频生产力场景（Today / Overdue / Reports / Export）
4. 把任务升级为工作入口（Work Entry）
5. 为 AI / Connectors / Remote Backends 预留清晰接口

## 非目标（Non-Goals）

- 不在早期做重型多人协作平台
- 不在早期绑定具体云服务或 SaaS
- 不把地图、天气、财务、AI 直接写死到核心层
- 不为了功能丰富而牺牲主文件可读性

## 项目形态（Project Shape）

TaskMD 最终将由以下部分构成：

- 主任务文件（Primary Task File, `tasks.md`）
- 任务 Sidecar 文件（Task Sidecar Files）
- CLI 命令系统（CLI Command System）
- Rich Dashboard / Live Reload（Terminal UX）
- Export Layer（ICS / PDF / HTML / Image）
- Easy Start / Context Actions（执行入口）
- Connectors / Plugins / AI（极后期扩展）
