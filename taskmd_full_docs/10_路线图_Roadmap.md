# 正式路线图（Formal Roadmap）

## 路线图原则（Roadmap Principles）

- 先打地基（Foundation First）
- 先稳 schema，再做体验，再做生态（Schema → UX → Ecosystem）
- 前面功能必须保留（Preserve Earlier Features）
- 高变动集成功能后置（Postpone Volatile Integrations）

## Phase 0：架构解耦
- 模块化拆分
- 稳定 ID
- 基础测试骨架

## Phase 1：打包与配置
- `pyproject.toml`
- `tm` command
- config / doctor

## Phase 2：Markdown 原生化
- `tasks.md` schema
- parser / writer
- txt -> md migration

## Phase 3：直接编辑兼容
- auto ID
- duplicate ID repair
- low-diff writeback
- round-trip tests

## Phase 4：CLI 子命令与基础视图
- list / add / edit / done / rm
- today / next / overdue / stats
- filter / tags / archive

## Phase 5：Rich UI 与 Live Reload
- dashboard
- progress
- file watch
- refresh

## Phase 6：Auto-Timestamp / Soft Deadlines / Heatmap
- `done`
- `start`
- urgency colors

## Phase 7：高频生产力增强
- recurring tasks
- quick capture syntax
- weekly report basic

## Phase 8：导出与共享
- ICS / PDF / CSV / JSON / Image / HTML

## Phase 9：主题与完成度
- zero-config themes
- polished UI

## Phase 10：Sidecar & Easy Start 基础版
- sidecar files
- `tm open <id>`
- resource linking

## Phase 11：Easy Start 纵深场景
- dev / academic / meeting / paper profiles

## Phase 12：Academic / Semester Mode
- course highlighting
- deadline import (confirmed)
- material sync

## Phase 13：Risk Engine
- `weight`
- pressure score
- `tm risk`

## Phase 14：TODO Harvesting
- scan TODO / FIXME / NOTE
- confirm import

## Phase 15：Focus / Work Entry
- `tm focus <id>`
- `tm start <id>`

## Phase 16：Remote Storage
- synced folder backend
- SSH / SFTP backend

## Phase 17：Connectors & Hooks
- custom openers / exporters / connectors

## Phase 18：AI Layer
- provider config
- suggestions / reports / NL commands

## Phase 19+：校园 / 通勤 / 财务 / Hotkey / Plugin Ecosystem
- optional connectors and ecosystem growth
