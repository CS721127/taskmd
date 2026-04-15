# Sidecar 与 Action Profiles（Task Sidecar & Context Actions）

## 1. 为什么需要 Sidecar（Why Sidecar）

主 `tasks.md` 应保持极简，而很多任务在真正执行时需要丰富上下文：

- PDF / 笔记 / 文件夹
- 课程链接 / 会议链接 / 代码仓库
- 动作序列（如打开编辑器、打开文件夹、打开浏览器）
- 关联知识沉淀（Knowledge Notes）

因此引入 **Task Sidecar Files**。

## 2. 默认路径（Default Path）
```text
.taskmd/items/<task_id>.md
```

## 3. Sidecar 内容建议（Suggested Sections）
- Summary
- Resources
- Actions
- Context
- Knowledge Handoff

## 4. 示例（Example）
```md
# Task Context: Prepare tutorial

## Resources
- pdf: /path/week5.pdf
- folder: /path/course/
- url: https://canvas.example.edu

## Actions
- profile: academic
- open_pdf
- open_folder
- open_url
```

## 5. Action Profiles（动作模板）

建议内置：
- `dev`
- `academic`
- `meeting`
- `paper`
- `fitness`
- `finance`
- `shopping`
- `commute`

## 6. 命令语义（Command Semantics）
- `tm open <id>`：打开关联资源
- `tm start <id>`：打开资源 + 启动执行上下文（如 editor / timer）

## 7. 设计边界（Boundaries）

- 主文件不塞复杂资源路径
- Sidecar 只描述上下文，不直接承载系统级敏感配置
- 真正的 connector 配置放到 Config / Integrations 层
