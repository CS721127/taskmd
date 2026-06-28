# TaskMD TODO & Issues 清单

---

## 第一部分：常规问题修复 (General Issues)
### dashboard live
- 应当可以删除subsection和section
-  dashboard时搜索的结果按照原来的section分类，不要去掉section只显示task name
-  refresh 不要影响用户，当用户鼠标到task并且task背景变深后就应当进入editing模式;
-  应当可以排序按照priority等
-  for doing enter to change to add a new task under same section, the new task should be added directly under the editing task, not at the end of the section. 
-  when enter and created new task, altomatically move the mouse to edit the new task
- due日期有日历UI选择时间，下方是时间转盘
- 可以批量操作，比如添加tag，添加priority，due date； 执行删除，done，等等
- 用户Enter时应当保存现有更改，不应该直接退出（现在有的时候修改的没有被保存上）
### CLI
- tm sort 有bug且 和 tm list --sort 功能一样，留一个，简化输入
- sort 如果输入-pd应当先按照priority排再按d排....


## 第二部分：Phase 9-15 补全 (Feature Completion)
## Phase +1 鼓励机制动画
- 制作一个鼓励机制，可以自己设置与打开，当设置后当完成到一定百分比有烟花等等界面特效恭喜再接再厉
## Phase +1 Progress bar (project bar)
- 当用户有相应project planning需求的时候，可以设置project的几个stage，每一个stage有什么任务，何时完成等等一系列；以及可以设置提醒，导出特定project的，review 任务进度，参与度，note等等；并且可以调整基于现实情况
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



