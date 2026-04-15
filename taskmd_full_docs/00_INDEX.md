# TaskMD 全量文档索引（Full Documentation Index）

这是一套面向 **TaskMD 正式项目（Formal Project）** 的完整文档设计稿，目标是让项目在产品定位（Product Positioning）、架构边界（Architecture Boundaries）、工程推进（Implementation Guidance）与开源治理（Open-Source Governance）上都足够清晰。

## 文档清单（Document Set）

1. `01_README_项目总览.md`
2. `02_产品定位与设计原则.md`
3. `03_架构总览与分层.md`
4. `04_仓库结构与模块职责.md`
5. `05_CLI_命令规范.md`
6. `06_配置与存储后端.md`
7. `07_Schema_设计.md`
8. `08_Sidecar_与_Action_Profiles.md`
9. `09_功能全景图.md`
10. `10_路线图_Roadmap.md`
11. `11_测试与质量保障.md`
12. `12_导出与集成设计.md`
13. `13_AI_与_可扩展性设计.md`
14. `14_贡献指南与发布流程.md`
15. `15_开源准备检查清单.md`
16. `16_架构图_Architecture_Diagrams.md`

## 推荐阅读顺序（Recommended Reading Order）

1. `01_README_项目总览.md`
2. `02_产品定位与设计原则.md`
3. `07_Schema_设计.md`
4. `03_架构总览与分层.md`
5. `04_仓库结构与模块职责.md`
6. `05_CLI_命令规范.md`
7. `10_路线图_Roadmap.md`
8. 其余专题文档

## 实施建议（Implementation Advice）

如果要立刻开工，最推荐先落实：

1. Schema（Schema）
2. Parser / Writer（解析与写回）
3. Round-trip Tests（语义往返测试）
4. CLI 命令系统（CLI Commands）
5. Storage Backend 抽象（Storage Abstraction）
