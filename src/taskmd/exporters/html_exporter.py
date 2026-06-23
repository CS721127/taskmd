"""
HTML Board Exporter for TaskMD.

Generates a single-file HTML kanban board with inline CSS + JS.
No server required — just open the HTML file in a browser.

Default grouping: [ ] Todo | [-] In Progress | [x] Done
Also supports grouping columns by section or subsection
(see TODOs.md Issue 2 — "html 导出的内容应当可以按照section，subsection等分类方式进行").

Supports: --theme light|dark   --group-by status|section|sub
"""
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from taskmd.models import Task
from taskmd.id_utils import short_id
from taskmd.ui.heatmap import get_urgency_level, URGENCY_OVERDUE, URGENCY_DUE_TODAY, URGENCY_DUE_SOON


def _urgency_class(task: Task) -> str:
    level = get_urgency_level(task)
    return {
        URGENCY_OVERDUE: "urgency-overdue",
        URGENCY_DUE_TODAY: "urgency-due-today",
        URGENCY_DUE_SOON: "urgency-due-soon",
    }.get(level, "")


def _status_badge_html(task: Task) -> str:
    """Small status badge shown on cards when columns are NOT grouped by status."""
    label, cls = {
        "[x]": ("Done", "status-done"),
        "[-]": ("In Progress", "status-progress"),
    }.get(task.status, ("Todo", "status-todo"))
    return f'<span class="status-badge {cls}">{label}</span>'


def _task_card_html(task: Task, show_status_badge: bool = False) -> str:
    """Render a single task as an HTML card."""
    urgency_cls = _urgency_class(task)
    pri_stars = "★" * task.pri if task.pri else ""
    tags_html = ""
    if task.tags:
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in task.tags)

    due_html = ""
    if task.due:
        urgency = get_urgency_level(task)
        due_cls = {
            URGENCY_OVERDUE: "due-overdue",
            URGENCY_DUE_TODAY: "due-today",
            URGENCY_DUE_SOON: "due-soon",
        }.get(urgency, "due-normal")
        due_html = f'<div class="due {due_cls}">📅 {task.due}</div>'

    rem_html = ""
    if task.rem:
        rem_html = f'<div class="rem">💬 {task.rem}</div>'

    section_html = f'<div class="section-label">{task.section} / {task.sub}</div>'
    status_html = _status_badge_html(task) if show_status_badge else ""

    return f"""
    <div class="card {urgency_cls}" data-id="{task.id}" data-section="{task.section}" data-sub="{task.sub}" data-status="{task.status}">
      <div class="card-header">
        <span class="task-id">[{short_id(task.id)}]</span>
        {status_html}
        {f'<span class="priority">{pri_stars}</span>' if pri_stars else ""}
      </div>
      <div class="task-name">{task.name}</div>
      {due_html}
      {rem_html}
      <div class="card-footer">
        {section_html}
        <div class="tags">{tags_html}</div>
      </div>
    </div>"""


def _section_filter_buttons(tasks: List[Task]) -> str:
    """Generate HTML filter buttons for each unique section."""
    sections = sorted(set(t.section for t in tasks if t.section))
    buttons = []
    for s in sections:
        safe = s.replace("'", "\\'")
        buttons.append(
            f'<button class="filter-btn" onclick="filterSection(\'{safe}\', this)">{s}</button>'
        )
    return "\n    ".join(buttons)


def _build_columns(tasks: List[Task], group_by: str) -> "list[tuple[str, str, str, List[Task]]]":
    """Build (column_id, title, icon, tasks) tuples for the requested grouping.

    group_by:
      "status"  (default) -> Todo / In Progress / Done
      "section" -> one column per top-level section, ordered by first appearance
      "sub"     -> one column per "Section / Sub" pair, ordered by first appearance
    """
    if group_by == "section":
        order: List[str] = []
        groups: Dict[str, List[Task]] = {}
        for t in tasks:
            key = t.section or "Uncategorized"
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(t)
        return [(f"col-{i}", key, "📁", groups[key]) for i, key in enumerate(order)]

    if group_by == "sub":
        order = []
        groups = {}
        for t in tasks:
            key = f"{t.section or 'Uncategorized'} / {t.sub or 'General'}"
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(t)
        return [(f"col-{i}", key, "📂", groups[key]) for i, key in enumerate(order)]

    # default: status
    todo = [t for t in tasks if t.status == "[ ]"]
    in_progress = [t for t in tasks if t.status == "[-]"]
    done = [t for t in tasks if t.status == "[x]"]
    return [
        ("col-todo", "Todo", "☐", sorted(todo, key=lambda t: (t.pri or 0) * -1)),
        ("col-progress", "In Progress", "🔄", in_progress),
        ("col-done", "Done", "✅", done),
    ]


def export_html(
    tasks: List[Task],
    output_path: Optional[Path] = None,
    theme: str = "light",
    group_by: str = "status",
) -> str:
    """
    Export tasks as a single-file HTML kanban board.

    Args:
        tasks: List of Task objects to export.
        output_path: If provided, write to this file. Otherwise return as string.
        theme: "light" or "dark".
        group_by: "status" (default), "section", or "sub" — controls how
            tasks are split into board columns (TODOs.md Issue 2).

    Returns:
        HTML content as a string (also written to file if output_path given).
    """
    group_by = group_by if group_by in ("status", "section", "sub") else "status"
    show_status_badge = group_by != "status"

    columns = _build_columns(tasks, group_by)

    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    column_html_parts = []
    for col_id, title, icon, col_tasks in columns:
        cards_html = "".join(_task_card_html(t, show_status_badge) for t in col_tasks)
        empty_msg = f'<div class="empty-col">No tasks</div>'
        column_html_parts.append(f"""
    <div class="column">
      <div class="column-header">
        <span class="column-title">{icon} {title}</span>
        <span class="badge">{len(col_tasks)}</span>
      </div>
      <div class="cards" id="{col_id}">
        {cards_html if cards_html else empty_msg}
      </div>
    </div>""")
    columns_html = "".join(column_html_parts)
    num_cols = max(len(columns), 1)

    is_dark = theme == "dark"
    bg = "#1a1a2e" if is_dark else "#f0f2f5"
    card_bg = "#16213e" if is_dark else "#ffffff"
    col_bg = "#0f3460" if is_dark else "#e8ecf0"
    text_color = "#eaeaea" if is_dark else "#1a1a2e"
    border_color = "#444" if is_dark else "#d0d4da"
    header_bg = "#e94560" if is_dark else "#4a6fa5"
    tag_bg = "#0f3460" if is_dark else "#dde3f0"
    tag_color = "#eaeaea" if is_dark else "#4a6fa5"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TaskMD Board</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: {bg};
      color: {text_color};
      min-height: 100vh;
    }}
    header {{
      background: {header_bg};
      color: white;
      padding: 16px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}
    header h1 {{ font-size: 1.4rem; font-weight: 700; }}
    header .meta {{ font-size: 0.85rem; opacity: 0.8; }}
    .board {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      padding: 24px;
      max-width: 1400px;
      margin: 0 auto;
    }}
    @media (max-width: 900px) {{
      .board {{ grid-template-columns: 1fr; }}
    }}
    .column {{
      background: {col_bg};
      border-radius: 12px;
      padding: 16px;
      min-height: 300px;
    }}
    .column-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 2px solid {border_color};
    }}
    .column-title {{ font-size: 1rem; font-weight: 700; color: {header_bg}; }}
    .badge {{
      background: {header_bg};
      color: white;
      border-radius: 12px;
      padding: 2px 10px;
      font-size: 0.8rem;
      font-weight: 600;
    }}
    .status-badge {{
      font-size: 0.68rem;
      padding: 1px 7px;
      border-radius: 8px;
      font-weight: 600;
    }}
    .status-todo {{ background: #e3eefe; color: #2868c7; }}
    .status-progress {{ background: #fff3e0; color: #c77700; }}
    .status-done {{ background: #e3f7e6; color: #2e8b3d; }}
    .card {{
      background: {card_bg};
      border: 1px solid {border_color};
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 12px;
      transition: transform 0.15s, box-shadow 0.15s;
      border-left: 4px solid transparent;
    }}
    .card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }}
    .urgency-overdue {{ border-left-color: #e53935; }}
    .urgency-due-today {{ border-left-color: #f5a623; }}
    .urgency-due-soon {{ border-left-color: #fdd835; }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}
    .task-id {{ font-size: 0.75rem; color: #888; font-family: monospace; }}
    .priority {{ color: #e53935; font-size: 0.85rem; }}
    .task-name {{ font-size: 0.95rem; font-weight: 500; margin-bottom: 8px; line-height: 1.4; }}
    .due {{
      font-size: 0.8rem;
      margin-bottom: 6px;
      padding: 2px 8px;
      border-radius: 4px;
      display: inline-block;
    }}
    .due-overdue {{ background: #ffebee; color: #e53935; }}
    .due-today {{ background: #fff8e1; color: #f57c00; }}
    .due-soon {{ background: #fffde7; color: #f9a825; }}
    .due-normal {{ color: #888; }}
    .rem {{ font-size: 0.8rem; color: #888; margin-bottom: 6px; font-style: italic; }}
    .card-footer {{ margin-top: 8px; display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 4px; }}
    .section-label {{ font-size: 0.72rem; color: #888; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 4px; }}
    .tag {{
      background: {tag_bg};
      color: {tag_color};
      font-size: 0.72rem;
      padding: 2px 8px;
      border-radius: 10px;
    }}
    .search-bar {{
      display: flex;
      gap: 10px;
      padding: 12px 24px;
      background: {col_bg};
      border-bottom: 1px solid {border_color};
    }}
    .search-bar input {{
      flex: 1;
      padding: 8px 14px;
      border: 1px solid {border_color};
      border-radius: 6px;
      background: {card_bg};
      color: {text_color};
      font-size: 0.9rem;
    }}
    .filter-btn {{
      padding: 8px 14px;
      border: 1px solid {border_color};
      border-radius: 6px;
      background: {card_bg};
      color: {text_color};
      cursor: pointer;
      font-size: 0.85rem;
    }}
    .filter-btn.active {{ background: {header_bg}; color: white; border-color: {header_bg}; }}
    .empty-col {{ color: #888; text-align: center; padding: 30px; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <header>
    <h1>📋 TaskMD Board</h1>
    <div class="meta">Exported: {exported_at} &nbsp;|&nbsp; Total: {len(tasks)} tasks &nbsp;|&nbsp; Grouped by: {group_by}</div>
  </header>

  <div class="search-bar">
    <input type="text" id="search" placeholder="Search tasks..." oninput="filterCards()">
    <button class="filter-btn active" onclick="filterSection(null, this)">All</button>
    {_section_filter_buttons(tasks)}
  </div>

  <div class="board" style="grid-template-columns: repeat({num_cols}, 1fr);">{columns_html}
  </div>

  <script>
    let activeSection = null;

    function filterCards() {{
      const q = document.getElementById('search').value.toLowerCase();
      document.querySelectorAll('.card').forEach(card => {{
        const text = card.textContent.toLowerCase();
        const section = card.dataset.section;
        const matchSearch = !q || text.includes(q);
        const matchSection = !activeSection || section === activeSection;
        card.style.display = (matchSearch && matchSection) ? '' : 'none';
      }});
    }}

    function filterSection(section, btn) {{
      activeSection = section;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filterCards();
    }}
  </script>
</body>
</html>"""

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

    return html
