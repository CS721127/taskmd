# TaskMD TODO & Issues 清单

---

## 第一部分：常规问题修复 (General Issues)

### Issue 4: dashboard -live应该可以调出一个控制面板，有UI界面的而不是仅仅CLI，dashboard改为dashboard cli

### Issue 6:
当用户使用tm open直接编辑md文件时，程序不能解析如果用户未按照最标准的储存格式进行编辑。程序应当可以智能解析，检测标准的和不标准的，如是不标准的，如使用 - 而不是 - [ ] 时程序应当也可以解析该内容并写入正确格式当运行时
同时程序应当可以识别写在md文件里的快捷方式（正如add的快捷方式一样，如果包含了subssection，section等元素，程序在运行时应当将他们放回他们所属于的section位置-这要求程序可以识别这些不同的格式）
同时，不属于任何一种的格式在validate时应当有显示。

## 第二部分：Phase 9-15 补全 (Feature Completion)
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



