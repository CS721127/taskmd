# TaskMD 文档索引（Documentation Index）

这是一套为 **TaskMD** 准备的正式项目文档（Project Documentation）草案，面向后续工程实现（Engineering Implementation）、开源准备（Open-Source Readiness）与长期演进（Long-term Evolution）。

## 文档列表（Document List）

1. [`01_项目介绍_Project_Introduction.md`](./01_项目介绍_Project_Introduction.md)
   - 项目定位（Positioning）
   - 目标用户（Target Users）
   - 设计哲学（Design Philosophy）
   - 长期愿景（Long-term Vision）

2. [`02_项目结构_Project_Structure.md`](./02_项目结构_Project_Structure.md)
   - 整体仓库结构（Repository Layout）
   - 模块边界（Module Boundaries）
   - 运行时层级（Runtime Layers）
   - 文档、测试与资源组织（Docs / Tests / Assets Layout）

3. [`03_项目功能_Features_Layered.md`](./03_项目功能_Features_Layered.md)
   - 按层次梳理的功能体系（Layered Feature System）
   - 核心能力（Core Capabilities）
   - 中后期能力（Mid/Late-Stage Capabilities）
   - 极后期生态能力（Very Late-Stage Ecosystem Features）

4. [`04_路线图_Roadmap.md`](./04_路线图_Roadmap.md)
   - 正式路线图（Formal Roadmap）
   - 阶段目标（Phase Goals）
   - 优先级（Prioritization）
   - 验收标准（Acceptance Criteria）

5. [`05_Schema_设计_Schema_Design.md`](./05_Schema_设计_Schema_Design.md)
   - Markdown 主任务文件（Primary Task File）
   - Sidecar 任务上下文文件（Task Sidecar Files）
   - 元数据字段（Metadata Fields）
   - 直接编辑兼容规则（Direct Edit Rules）
   - 连接器（Connectors）与动作模板（Action Profiles）

6. [`06_项目骨架_Project_Skeleton.md`](./06_项目骨架_Project_Skeleton.md)
   - 第一版项目骨架（v2/v3 Skeleton）
   - Python 包布局（Package Layout）
   - 命令体系（CLI Commands）
   - 服务层草图（Service Layer Sketch）
   - 测试骨架（Testing Skeleton）

---

## 建议阅读顺序（Recommended Reading Order）

如果你准备正式开始实现（Implementation），建议按以下顺序阅读：

1. **项目介绍（Project Introduction）**：先对齐定位（Positioning）和边界（Scope）
2. **Schema 设计（Schema Design）**：这是整个系统的基础
3. **项目结构（Project Structure）**：明确模块怎么拆
4. **项目骨架（Project Skeleton）**：进入工程层（Engineering Layer）
5. **项目功能（Features）**：建立中长期能力地图
6. **路线图（Roadmap）**：按阶段推进

---

## 推荐后续动作（Recommended Next Steps）

完成这套文档后，最推荐的实现顺序是：

1. 落定 `Schema` 与 `Task Sidecar` 规范
2. 先写 `parser / writer / round-trip tests`
3. 再做 `CLI command system` 与 `storage abstraction`
4. 最后逐步加 `Rich UI / Live Reload / Export / Easy Start / AI`
