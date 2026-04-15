# Schema 设计（Schema Design）

## 1. 目标（Goals）

Schema 必须同时保证：
- 人类可读（Human-Readable）
- 机器可解析（Machine-Parseable）
- 适合直接编辑（Editor-Friendly）
- 支持 Round-trip（Round-trip Stable）
- 适配 Sidecar、导出和后续扩展

## 2. 主任务文件（Primary Task File）

默认文件名：`tasks.md`

### 顶部元信息（Header Metadata）
```md
<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->
```

### 层级结构（Hierarchy）
```md
# School
## DPST1092
- [ ] Prepare tutorial
```

## 3. 任务状态（Task Status）
- `[ ]`：Todo
- `[-]`：In Progress
- `[x]`：Done

## 4. 隐藏元数据（Hidden Metadata）
```md
- [ ] Prepare tutorial <!-- id:t_01, due:2026-04-20, pri:4 -->
```

## 5. 推荐字段（Recommended Fields）

### 必选（Required）
- `id`

### 常用（Common Optional）
- `due`
- `start`
- `pri`
- `tags`
- `rem`
- `created`
- `updated`
- `done`

### 进阶（Advanced）
- `weight`
- `course`
- `recur`
- `est`
- `loc`

## 6. 直接编辑规则（Direct Edit Rules）

### 新增任务（Manual Add）
无 `id` 任务由程序自动补 ID。

### 删除任务（Manual Delete）
直接删行即删除。

### 修改任务（Manual Edit）
同一 `id` 视为同一任务。

### 移动任务（Move Across Sections）
带 `id` 的任务跨 section / subsection 移动时，身份不变。

### 重复 ID（Duplicate ID）
默认策略：保留第一项 ID，为后续重复项自动生成新 ID 并告警。

## 7. 写回规则（Writeback Rules）

- 不重排 section / subsection
- 尽量保留非任务文本
- 仅补必要元数据
- 仅在 CLI 写操作时更新 `updated` / `done`
