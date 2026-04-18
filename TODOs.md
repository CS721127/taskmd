# TaskMD TODO & Issues 清单

---

## 第一部分：常规问题修复 (General Issues)

### Issue 1: 缺少 clear 命令
描述：无法清除所有当前任务并重新开始
要求：需要二次确认以防误删  
优先级：中

### Issue 2: 缺少版本查询选项
描述：tm -v / --version 不可用
影响：无法清晰检测版本状况
优先级：低

### Issue 3: 任务 ID 显示混淆
当前状态：显示 t_xx (内部ID格式)
用户期望：显示 xx (简短格式)
影响：用户需要输入 xx 但看到 t_xx，容易混淆
优先级：中

### Issue 4: Dashboard 布局异常
表现：格式错乱、对齐问题
示例：
  ```
  [bold white]Inbox[/bold white]  [green]██████████ 100%[/]                    │ 📅 Today     │
  │   [dim]── General[/dim]  [dim]██████ 100%[/dim]                          │   (none)     │
  │   ⚪ [t_01] ✅ My First Task                                               │              │
  │ [bold white]Migrated[/bold white]  [yellow]░░░░░░░░░░   0%[/]            │ 🔴 Overdue   │
  ```
优先级：中

### Issue 5: Export Report 输出异常
问题：tm export report --week 存入 md 文件，而非输出到 stdout
期望：应直接显示到控制台（可选保存）
优先级：低

### Issue 6: 日期输入与精度支持
需求1：支持具体截止时间（不仅是日期）
需求2：灵活的日期输入格式解析
示例：@tomorrow @next-monday @2-weeks 2026-04-25 14:30 Apr 25 2026 ...
优先级：中

### Issue 7: Validate 检测逻辑
问题：tm validate 需要重新确认检测逻辑
优先级：中

---

## 第二部分：Phase 7-8 补全 (Feature Completion)

### 任务 1: Quick Capture Syntax (优先级：高)

功能目标
  tm add "Read paper #research #ml !4 @2026-04-25"

当前状态
  tm add "Read paper" --tags research,ml --pri 4 --due 2026-04-25

缺失内容
需要在 CLI 层实现内联解析器，识别以下语法：

| 符号 | 含义 | 示例 |
|------|------|------|
| #tag | 标签 | #research #ml |
| !priority | 优先级 (0-5) | !4 |
| @date | 截止日期 (YYYY-MM-DD) | @2026-04-25 |
| ^start_date | 开始日期 | ^2026-04-20 |

---

### 任务 2: Recurring Tasks Automation (优先级：中)

功能目标
  - [ ] Daily standup <!-- recur:daily -->
  - [ ] Weekly demo <!-- recur:weekly-mon -->
  - [ ] Monthly review <!-- recur:monthly-1st -->

当前实现状态

| 组件 | 状态 |
|------|------|
| 字段存储 (recur field) | 已实现 |
| Daily Section 自动重置 | 已实现 |
| Cron 解析器 | 缺失 |
| 自动生成/更新逻辑 | 缺失 |

需要实现

1. Recur 字段值规范
   - daily — 每天重置
   - weekly-{day} — 每周指定日期 (mon/tue/wed...)
   - monthly-{date} — 每月指定日期
   - custom-cron — 自定义 cron 表达式

2. 解析与调度逻辑
   - 解析 recur 字段值
   - 判断是否应该重复生成或重置状态

3. 自动生成机制
   - 每日/周/月检查并生成新任务或重置现有任务
