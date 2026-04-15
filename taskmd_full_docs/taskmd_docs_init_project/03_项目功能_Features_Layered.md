# TaskMD 项目功能（Features, Layer by Layer）

## 1. 功能设计总原则（Feature Design Principles）

TaskMD 的功能设计（Feature Design）应遵循以下原则：

1. **先保证核心稳定（Core Stability First）**
2. **先支持真实高频场景（Real High-Frequency Use Cases First）**
3. **复杂能力通过 Sidecar / Connector / Plugin 延展（Extend via Sidecar / Connector / Plugin）**
4. **避免把所有集成硬编码进核心（Avoid Hardcoding Integrations into Core）**

---

## 2. Layer A：核心任务系统（Core Task System）

这是最基础也最重要的功能层（Foundational Layer）。

### 2.1 Markdown 主任务文件（Markdown Primary Task File）
- 使用 `#` / `##` / `- [ ]` 表达层级和任务
- 文件可直接用编辑器打开与修改

### 2.2 稳定任务 ID（Stable Task ID）
- 每个任务都有持久身份（Persistent Identity）
- 支持移动、重命名、批量编辑与 Sidecar 关联

### 2.3 基础元数据（Core Metadata）
- `due` 截止日期（Due Date）
- `start` 开始关注日期（Soft Deadline / Attention Start）
- `pri` 优先级（Priority）
- `tags` 标签（Tags）
- `rem` 备注（Remark）
- `done` 完成时间戳（Completion Timestamp）

### 2.4 CLI 基础操作（CLI CRUD）
- `add`
- `edit`
- `done`
- `todo`
- `half`
- `rm`
- `move`
- `due`
- `rem`

### 2.5 直接编辑兼容（Direct Editing Compatibility）
- 支持用户手工在 Markdown 中新增任务
- 自动补元数据（Auto Enrichment）
- 自动修复重复 ID（Duplicate ID Repair）
- 低扰动写回（Low-Diff Writeback）

---

## 3. Layer B：查询、视图与日常效率（Query, Views, Daily Productivity）

这一层负责“用户每天最常用的能力（Daily High-Frequency Capabilities）”。

### 3.1 任务视图（Task Views）
- `tm list`
- `tm today`
- `tm next`
- `tm overdue`
- `tm stats`
- `tm risk`

### 3.2 搜索与过滤（Search & Filter）
- 按关键字（Keyword）
- 按标签（Tags）
- 按课程代码（Course Code）
- 按 section / subsection
- 按状态（Status）
- 按风险值（Pressure / Risk）

### 3.3 归档（Archive）
- `archive done`
- `archive --before <date>`
- 保留完成记录，而不是直接删除

### 3.4 快速录入（Quick Capture Syntax）
例如：

```bash
tm add "Read paper #research !4 @tomorrow"
```

解析出：
- 标题（Title）
- 标签（Tags）
- 优先级（Priority）
- 日期（Date）

---

## 4. Layer C：终端 UI 与可视感知（Terminal UI & Visual Perception）

### 4.1 Rich Dashboard（Rich Dashboard）
- 双栏或多区域布局（Multi-Region Layout）
- Today / Upcoming / Overdue 视图
- 紧凑统计卡片（Compact Stats Cards）

### 4.2 Section Progress（分区进度）
- 自动计算每个 `Subsection` 的完成比例（Completion Ratio）
- 在 CLI / Rich UI 中显示极简进度条（Minimal Progress Bar）

### 4.3 Live Reload（实时文件监视）
- 使用文件监视（File Watch）检测 `tasks.md` 被编辑器保存后的变化
- Dashboard 自动刷新（Auto Refresh）

### 4.4 Heatmap & Soft Deadlines（热力提醒与软截止）
- 根据 `start` 和 `due` 渐变显示紧迫程度（Urgency Gradient）
- 让用户靠颜色感知风险，而不是只读文本日期

### 4.5 Zero-Config Themes（零配置主题）
- Nord
- Dracula
- Catppuccin
- Monokai
- Solarized

---

## 5. Layer D：时间管理与专注（Time Management & Focus）

### 5.1 Auto-Timestamp（自动完成时间戳）
- 执行 `done <id>` 时自动写入 `done` 时间戳（Timestamp）
- 支持后续统计和周报（Reports）

### 5.2 Recurring Tasks（重复任务）
- `daily`
- `weekly@mon`
- `monthly@1`
- 将当前的 Daily Reset 演化为通用重复规则引擎（Recurrence Engine）

### 5.3 Focus Mode（专注模式）
- `tm focus <id>`
- 倒计时（Timer / Pomodoro）
- 可选背景音乐 / 白噪音（Optional Audio / White Noise）
- 记录专注 Session（Focus Session Logging）

### 5.4 Global Capture（全局快速捕捉，极后期）
- 通过全局快捷键（Global Hotkey）把想法写入 Inbox
- 作为 Companion Tool 独立实现

---

## 6. Layer E：导出与分享（Export & Sharing）

### 6.1 Calendar Export（ICS 日历导出）
- 导出 `.ics`
- 同步 due 任务到日历（Calendar）

### 6.2 PDF Monthly Calendar（PDF 月历导出）
- 生成可打印（Printable）的月历视图
- 适合月度计划与展示（Planning / Presentation）

### 6.3 CSV / JSON Export（结构化导出）
- 用于分析（Analysis）
- 用于二次处理（Post-processing）

### 6.4 Image Export（图片导出）
- 将当前 dashboard 或任务快照导出为长图（Shareable Image）

### 6.5 HTML Board Export（HTML 看板导出）
- 导出本地 HTML 页面（Local HTML Board）
- 支持 Kanban / Monthly / Project Views

### 6.6 Weekly / Daily Report（周报 / 日报导出）
- 从 done 时间戳、due 状态与 Sidecar 内容生成汇报文档（Reports）

---

## 7. Layer F：Task Sidecar 与 Easy Start（Task Sidecar & Easy Start）

这是 TaskMD 最有特色的一组能力之一。

### 7.1 Task Sidecar（任务侧边文件）
每个任务可以关联一个独立 Markdown 文件（Sidecar File），用于保存：
- 长备注（Long Notes）
- 资源链接（Resources）
- 动作模板（Action Profiles）
- 项目上下文（Execution Context）
- 相关知识沉淀（Knowledge Notes）

### 7.2 Easy Start / Context Actions（一键开工 / 上下文动作）
支持：
- `tm open <id>`
- `tm start <id>`

触发对应动作：
- 打开 VS Code / Cursor / repo folder
- 打开 PDF / 笔记 / 网站 / Canvas / WebCMS
- 打开会议链接 / Meet / Zoom / Teams
- 打开地图 / 导航 / 课程资料

### 7.3 场景化动作模板（Action Profiles）
- `dev`
- `academic`
- `meeting`
- `paper`
- `fitness`
- `finance`
- `shopping`
- `commute`

---

## 8. Layer G：Academic Mode（学期 / 学术模式）

### 8.1 课程代码识别（Course Code Highlighting）
自动高亮诸如 `DPST1092`、`COMPxxxx` 等课程代码。

### 8.2 Deadline 导入（Deadline Import with Confirmation）
从课程大纲（Syllabus / Course Outline）或 Markdown 中抓取 deadline，
**经用户确认后** 导入到任务系统。

### 8.3 课程资料联动（Course Material Sync）
- 一键打开课程目录（Course Folder）
- 一键打开本周实验题（Lab Sheet）
- 一键打开上周答案（Previous Solution）
- 一键打开讲义与笔记（Lecture Notes / Notes）

### 8.4 风险视图（Risk View）
结合 `weight` 与 `time_left` 计算压力值（Pressure Score），避免把时间浪费在低权重任务上。

---

## 9. Layer H：外部 TODO 吸取（TODO Harvesting）

### 9.1 从代码 / Markdown 抽取 TODO
- 扫描 `TODO / FIXME / NOTE`
- 生成候选任务（Candidate Tasks）
- 用户确认后导入 TaskMD

### 9.2 与日历的桥接（Late-Stage Bridge）
当代码注释中能推断日期时，可建议导入到日历（需用户确认）。

---

## 10. Layer I：远程存储与同步（Remote Storage & Sync）

### 10.1 Synced Folder（优先）
允许将数据目录放在：
- OneDrive
- Dropbox
- iCloud
- NAS 同步目录

### 10.2 SSH / SFTP Backend（后续）
允许通过 SSH 连接远程任务文件。

### 10.3 Storage Backend 抽象
确保核心逻辑不绑定本地路径（Local Paths）。

---

## 11. Layer J：AI 辅助层（AI Assistance Layer）

### 11.1 AI Task Grooming（任务整理）
- 自动建议分类（Section / Subsection）
- 合并重复任务（Duplicate Merge Suggestion）
- 拆分过长任务（Task Decomposition Suggestion）

### 11.2 AI Priority / Risk Suggestion（优先级 / 风险建议）
- 根据 due / weight / tags / workload 给建议

### 11.3 自然语言命令（Natural Language Commands）
例如：
> “列出下周前到期的研究任务，并按压力值排序。”

### 11.4 报告生成（Report Generation）
- 周报（Weekly Review）
- 项目总结（Project Summary）
- 完成回顾（Completion Review）

### 11.5 边界约束（Boundaries）
AI 必须：
- 由用户配置（User-configured）
- 默认关闭（Opt-in）
- 涉及写操作时要求确认（User Confirmation Required）

---

## 12. Layer K：连接器与生态（Connectors & Ecosystem）

极后期功能（Very Late-Stage Features）建议以连接器（Connector）/ 插件（Plugin）方式实现：

- 地图 / 通勤（Maps / Commute）
- 天气（Weather）
- 财务 / 价格（Finance / Price Tracking）
- 校园位置（Campus Context）
- 课程平台（Course Portals）
- 会议系统（Meeting Systems）
- 自定义 Shell 命令（Shell Hooks）

这样既保留灵活性（Flexibility），也不污染核心任务系统（Core Task System）。
