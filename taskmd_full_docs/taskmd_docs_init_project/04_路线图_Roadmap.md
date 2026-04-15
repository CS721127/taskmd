# TaskMD 正式路线图（Formal Roadmap）

## 1. 路线图原则（Roadmap Principles）

TaskMD 的路线图（Roadmap）应遵循：

1. **先基础、后体验、再生态（Foundation → UX → Ecosystem）**
2. **先保证 Markdown / Schema / Round-trip 稳定（Schema Stability First）**
3. **前面阶段的功能必须被保留（Earlier Phases Must Be Preserved）**
4. **极后期连接器与 AI 不能反向绑架核心架构（Late Integrations Must Not Distort the Core）**

---

## Phase 0：架构解耦（Architecture Refactor）

### 目标（Goal）
把当前单文件脚本（Monolithic Script）升级为模块化项目（Modular Project）。

### 关键任务（Key Tasks）
- 拆分 `models / parser / storage / services / ui / commands`
- 去除全局 `DB_FILE`
- 分离输入输出（I/O）与业务逻辑（Business Logic）
- 建立异常体系（Exceptions）
- 引入测试框架（pytest）
- 引入稳定任务 ID（Stable Task ID）

### 验收标准（Acceptance Criteria）
- 不再依赖单文件入口
- 数据层、解析层、业务层可分别单测
- 为 Markdown 迁移打好基础

---

## Phase 1：工具全局化（Packaging & Configuration）

### 目标
安装即用（Installable CLI Tool）。

### 关键任务
- 配置 `pyproject.toml`
- 暴露全局命令 `tm`
- 默认配置目录（Config Directory）自动创建
- 支持 CLI / ENV / Config 优先级
- 提供 `tm config` / `tm doctor`

### 验收标准
- 任意目录运行 `tm`
- 用户无需到处找数据库文件（Task File）

---

## Phase 2：Markdown 原生化（Markdown-Native Storage）

### 目标
从自定义 TXT 格式迁移到 Markdown 主任务文件（Primary Task File）。

### 关键任务
- 设计 `tasks.md` schema
- 设计 HTML 注释元数据（Hidden Metadata）
- 实现 Markdown parser / writer
- 实现 TXT → MD 迁移器（Migration）
- 兼容普通 Markdown 文本（Notes / Comments）

### 验收标准
- 用户可在编辑器中直接管理任务
- 旧 TXT 数据可一键迁移

---

## Phase 3：直接编辑兼容（Direct Edit Compatibility）

### 目标
把“手工编辑 Markdown”升级为正式支持能力（First-Class Workflow）。

### 关键任务
- 自动补全缺失 ID（Auto ID Enrichment）
- 检测并修复重复 ID（Duplicate ID Repair）
- 支持任务手工增删改移（Manual Add/Delete/Edit/Move）
- 低扰动写回（Low-Diff Writeback）
- `tm open`
- `tm validate`
- 建立 round-trip tests

### 验收标准
- 批量手工编辑可稳定同步
- 程序不会因用户手工编辑轻易崩溃

---

## Phase 4：CLI 子命令与基础视图（CLI Subcommands & Core Views）

### 目标
形成标准命令体系（Command System）与高频日常视图（Daily Views）。

### 关键任务
- `list / add / edit / done / todo / rm / move`
- `due / rem / tag / pri`
- `today / next / overdue / stats`
- 搜索与过滤（Search / Filter）
- 归档（Archive）

### 验收标准
- 用户可不进入交互循环（Interactive Loop）也能高效操作
- 命令可脚本化（Scriptable）

---

## Phase 5：Rich UI 与实时编辑体验（Rich UI & Live Editing Experience）

### 目标
让终端体验更现代化（Modern Terminal UX），并与外部编辑器形成无缝联动（Seamless Editor Loop）。

### 关键任务
- Rich Dashboard
- 双栏 / 多区域布局
- Section Progress（分区进度条）
- Live Reload（watchdog）
- 统一警告 / 提示 / 状态面板
- 自适应终端宽度（Responsive Terminal Layout）

### 验收标准
- 用户在 VS Code 修改并保存后，Dashboard 自动刷新
- 终端界面信息密度高且不混乱

---

## Phase 6：自动时间戳、软截止与热力提醒（Auto-Timestamp, Soft Deadlines & Heatmap）

### 目标
让任务的时间状态与紧迫感（Urgency）更直观。

### 关键任务
- 完成任务时自动记录 `done` 时间戳
- 引入 `start` 字段（Attention Start）
- 实现热力颜色逻辑（Heatmap Logic）
- 完善 due / overdue 渲染策略
- 为风险视图（Risk View）做数据铺垫

### 验收标准
- 用户可从颜色直观感知任务紧迫度
- `done` 时间可用于统计 / 导出 / 报告

---

## Phase 7：高频生产力增强（High-Frequency Productivity）

### 目标
加入最常用且最容易形成黏性的功能。

### 关键任务
- Recurring Tasks（重复任务）
- Quick Capture Syntax（快速录入语法）
- Weekly / Daily Report 基础版
- 更强的 stats / completion analytics
- 预留 Focus 模式字段（如 `est`）

### 验收标准
- 用户开始每天真正常用，而不只是“偶尔记录”

---

## Phase 8：导出与共享（Export & Sharing）

### 目标
让 TaskMD 的数据流入用户已有工作流（Calendar / Print / Share / Review）。

### 关键任务
- ICS 日历导出
- PDF 月历导出
- CSV / JSON 导出
- 图片导出（Image Export）
- HTML 看板导出（HTML Board Export）
- 周报 / 日报导出（Report Export）

### 验收标准
- 任务数据可用于展示、打印、汇报和共享

---

## Phase 9：主题与审美完成度（Themes & Aesthetic Polish）

### 目标
提升视觉完成度（Polish）与 GitHub 展示效果（Presentation Value）。

### 关键任务
- Zero-Config Themes
- 主题与 Heatmap / Progress / Icons 统一映射
- 屏幕截图与演示 GIF 素材准备

### 验收标准
- 主题切换稳定
- 界面具有明显产品质感（Product Feel）

---

## Phase 10：Task Sidecar 与 Easy Start 基础版（Task Sidecar & Easy Start Foundations）

### 目标
把任务从“待办项（Todo）”升级为“执行入口（Execution Entry）”。

### 关键任务
- 定义 Task Sidecar 文件结构
- 支持资源链接（Resource Linking）
- 支持动作模板（Action Profiles）
- `tm open <id>`
- 打开 URL / file / folder / pdf / note
- 自定义 opener hook（带确认）

### 验收标准
- 单个任务可以关联复杂上下文，但主任务文件仍然简洁

---

## Phase 11：Easy Start 纵深场景（Deep Easy Start Scenarios）

### 目标
让不同类型任务可以“一键进入工作环境（One-click Start）”。

### 关键任务
- Dev Profile：打开 repo / VS Code / terminal
- Academic Profile：打开 PDF / notes / course folder
- Meeting Profile：打开会议链接 / 纪要 / 汇报文档
- Paper Profile：打开论文 PDF / notes / review draft
- 完成任务时可选知识归档（Knowledge Handoff）

### 验收标准
- 用户不只是“看见任务”，而是“点开就能开始做”

---

## Phase 12：Academic Mode / Semester Mode（学期模式）

### 目标
服务课程型（Course-based）与学术型（Academic）用户。

### 关键任务
- 课程代码高亮（Course Code Highlighting）
- `--course` 聚合视图
- 从 syllabus / course outline 抓取 deadline（需确认）
- 课程资料联动（Material Sync）
- 一键备课 / 复习动作模板（Teaching / Review Bundle）

### 验收标准
- 对高校 / tutoring / research 用户明显有吸引力

---

## Phase 13：Risk Engine / Hard Deadline View（风险引擎）

### 目标
解决“多个 Assignment 一起堆积时，如何合理分配注意力”的问题。

### 关键任务
- 引入 `weight` 字段
- 设计 `Pressure = Weight / max(Time_Left_Days, 1)`
- `tm risk`
- 支持按压力值排序与高亮
- 与 Heatmap 协同渲染

### 验收标准
- 用户能快速看出真正高风险任务，而不是只看最近 due date

---

## Phase 14：外部 TODO 吸取（TODO Harvesting）

### 目标
从代码仓库（Code Repos）或 Markdown 文档中吸取 TODO 线索（TODO Signals）。

### 关键任务
- 扫描 `TODO / FIXME / NOTE`
- 生成候选任务列表
- 用户确认后导入
- 如果可推断日期，仅作为建议（Suggestion）而非自动写入

### 验收标准
- 降低开发者把注释 TODO 手工搬到任务系统的成本

---

## Phase 15：专注模式与沉浸式工作入口（Focus & Work Entry）

### 目标
让 TaskMD 从任务系统进化为轻量工作入口（Lightweight Work Launcher）。

### 关键任务
- `tm focus <id>`
- 倒计时 / 番茄钟（Pomodoro）
- 可选背景音频（Optional Audio）
- Focus Session Logging
- `tm start <id>` 与 Action Profiles 联动

### 验收标准
- 用户可从任务直接进入专注工作状态

---

## Phase 16：远程存储与同步（Remote Storage & Sync）

### 目标
允许任务数据不只存在本地（Local-Only）。

### 关键任务
- 优先支持 Synced Folder（OneDrive / iCloud / Dropbox）
- 设计 Storage Backend 抽象
- 后续加入 SSH / SFTP backend
- 处理冲突与锁（Conflict / Lock Strategy）

### 验收标准
- 核心逻辑不绑定本地文件系统
- 用户可选更灵活的数据存放方式

---

## Phase 17：开放接口与连接器（Open Hooks & Connectors）

### 目标
保留很多“口”和“门”，让用户接更多工具。

### 关键任务
- 自定义 Openers
- 自定义 Exporters
- 自定义 Connectors
- Browser / Map / Course / Finance / Commute Hooks
- 文档化扩展点（Documented Extension Points）

### 验收标准
- 项目具备生态演化空间（Ecosystem Expandability）

---

## Phase 18：AI API 集成（AI Intelligence Layer）

### 目标
让 AI 成为可选任务助手（Optional Assistant），而不是接管者（Controller）。

### 关键任务
- Provider 配置（自定义 API）
- 任务整理（Task Grooming）
- 优先级 / 风险建议（Priority / Risk Suggestion）
- 自然语言命令（Natural Language Commands）
- 周报 / 总结生成（Report Generation）
- 所有写操作要求确认（Confirmation before Mutation）

### 验收标准
- AI 增强用户决策与效率，而不破坏可控性（Controllability）

---

## Phase 19：校园 / 通勤 / 生活上下文连接器（Campus / Commute / Ambient Connectors）

### 目标
把现实环境信息接入任务感知（Context-Aware Tasks）。

### 关键任务
- 地图 / 导航链接（Map / Navigation Links）
- 校园位置快捷打开（Campus Context）
- 通勤信息提示（Commute Status）
- 天气图标 / 提醒（Weather Indicators）
- 出发建议（Departure Suggestion）

### 验收标准
- 这些能力以 Connector 形式存在，而不是污染核心任务逻辑

---

## Phase 20：财务 / 采购 / 外部状态连接器（Finance / Procurement / External Signals）

### 目标
让任务具备轻量“决策辅助（Decision Support）”能力。

### 关键任务
- 价格监测 Connector
- 股票代码 / 简要行情 Connector
- URL 状态徽记（Status Badge）

### 验收标准
- 不做重型金融工具，只做轻量任务增强（Lightweight Task Enhancement）

---

## Phase 21：全局快速捕捉（Global Capture Companion）

### 目标
在不打开终端的情况下，低摩擦记录灵感（Low-friction Capture）。

### 关键任务
- Companion Script
- 全局快捷键（Hotkey）
- Inbox Append
- 与 Live Reload 联动
- 多平台文档（Cross-platform Notes）

### 验收标准
- 记录一个想法不需要切完整上下文

---

## Phase 22：插件系统与生态化（Plugin System & Ecosystem）

### 目标
让 TaskMD 最终具备可持续扩展的平台能力（Platform-like Extensibility）。

### 关键任务
- Plugin API
- Connector Registry
- Hook 机制
- 第三方 Provider 接口
- 生态文档（Ecosystem Docs）

### 验收标准
- 后续功能可以以插件形式演化，而不是不断膨胀核心代码

---

## Phase 23：质量保障与开源品牌化（Quality & Open-Source Branding）

### 目标
让项目既稳定，又具备传播力（Shareability）与贡献能力（Contributability）。

### 关键任务
- Parser / Round-trip / Migration / CLI / Export 测试
- README + GIF
- `docs/schema.md`
- `docs/cli.md`
- `docs/roadmap.md`
- LICENSE / CONTRIBUTING / Templates
- GitHub Actions / Release Automation

### 验收标准
- 外部用户可以安装、理解、试用、反馈与贡献
