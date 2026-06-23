"""
Report Generator for TaskMD.

Generates weekly and daily Markdown reports from task data.
Covers Phase 7 (weekly report base) and Phase 8 (report export).
"""
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import List, Optional, Dict

from taskmd.models import Task
from taskmd.id_utils import short_id
from taskmd.datetime_utils import parse_task_date
from taskmd.ui.heatmap import get_urgency_level, URGENCY_OVERDUE, URGENCY_DUE_TODAY, URGENCY_DUE_SOON, URGENCY_DUE_UPCOMING


def _today() -> date:
    return date.today()


def _week_bounds(offset: int = 0) -> tuple[date, date]:
    """Return (monday, sunday) for the current week (offset=0) or past weeks."""
    today = _today()
    monday = today - timedelta(days=today.weekday()) - timedelta(weeks=offset)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _status_label(status: str) -> str:
    return {"[x]": "✅ Done", "[-]": "🔄 In Progress", "[ ]": "☐ Todo"}.get(status, status)


def generate_weekly_report(
    tasks: List[Task],
    week_offset: int = 0,
    output_path: Optional[Path] = None,
) -> str:
    """
    Generate a weekly Markdown report.

    Args:
        tasks: All tasks.
        week_offset: 0 = current week, 1 = last week, etc.
        output_path: If provided, write report to this file.

    Returns:
        Markdown report as a string.
    """
    monday, sunday = _week_bounds(week_offset)
    now = datetime.now()

    lines = []
    lines.append(f"# TaskMD Weekly Report")
    lines.append(f"**Week:** {monday.isoformat()} → {sunday.isoformat()}")
    lines.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # ── Completed this week ──────────────────────────────────────────────
    completed_this_week = []
    for t in tasks:
        if t.status == "[x]" and t.done_ts:
            try:
                done_date = datetime.strptime(t.done_ts[:10], "%Y-%m-%d").date()
                if monday <= done_date <= sunday:
                    completed_this_week.append(t)
            except ValueError:
                pass

    lines.append(f"## ✅ Completed This Week ({len(completed_this_week)})")
    lines.append("")
    if completed_this_week:
        # Group by section
        by_section: Dict[str, List[Task]] = {}
        for t in completed_this_week:
            by_section.setdefault(t.section, []).append(t)
        for sec, sec_tasks in sorted(by_section.items()):
            lines.append(f"**{sec}**")
            for t in sec_tasks:
                done_on = t.done_ts[:10] if t.done_ts else "?"
                lines.append(f"- {t.name} `[{short_id(t.id)}]` _(completed {done_on})_")
            lines.append("")
    else:
        lines.append("_No tasks completed this week._")
        lines.append("")

    # ── Due this week ────────────────────────────────────────────────────
    due_this_week = []
    for t in tasks:
        if t.due and t.status != "[x]":
            due_date = parse_task_date(t.due)
            if due_date is not None and monday <= due_date <= sunday:
                due_this_week.append(t)

    lines.append(f"## 📅 Due This Week ({len(due_this_week)})")
    lines.append("")
    if due_this_week:
        due_this_week.sort(key=lambda t: t.due)
        for t in due_this_week:
            urgency = get_urgency_level(t)
            urgency_mark = "🔴" if urgency == URGENCY_OVERDUE else "⚡" if urgency == URGENCY_DUE_TODAY else "📌"
            pri_str = f" Pri:{t.pri}" if t.pri else ""
            tags_str = f" [{', '.join(t.tags)}]" if t.tags else ""
            lines.append(f"- {urgency_mark} **{t.name}** `[{short_id(t.id)}]` Due: {t.due}{pri_str}{tags_str}")
        lines.append("")
    else:
        lines.append("_No tasks due this week._")
        lines.append("")

    # ── Overdue ──────────────────────────────────────────────────────────
    overdue = [
        t for t in tasks
        if t.due and t.status != "[x]"
        and (parse_task_date(t.due) is not None)
        and parse_task_date(t.due) < monday
    ]
    overdue.sort(key=lambda t: t.due)

    lines.append(f"## 🔴 Overdue ({len(overdue)})")
    lines.append("")
    if overdue:
        for t in overdue:
            due_date = parse_task_date(t.due)
            days_late = (_today() - due_date).days
            lines.append(f"- **{t.name}** `[{short_id(t.id)}]` Due: {t.due} _(+{days_late}d)_")
        lines.append("")
    else:
        lines.append("_No overdue tasks. Great work!_ 🎉")
        lines.append("")

    # ── In Progress ──────────────────────────────────────────────────────
    in_progress = [t for t in tasks if t.status == "[-]"]
    lines.append(f"## 🔄 In Progress ({len(in_progress)})")
    lines.append("")
    if in_progress:
        for t in in_progress:
            lines.append(f"- {t.name} `[{short_id(t.id)}]` _{t.section}/{t.sub}_")
        lines.append("")
    else:
        lines.append("_None._")
        lines.append("")

    # ── Statistics ───────────────────────────────────────────────────────
    total = len(tasks)
    done_all = sum(1 for t in tasks if t.status == "[x]")
    rate = f"{done_all / total * 100:.1f}%" if total else "0.0%"

    lines.append("## 📊 Statistics")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total tasks | {total} |")
    lines.append(f"| Completed (all time) | {done_all} |")
    lines.append(f"| Completed this week | {len(completed_this_week)} |")
    lines.append(f"| Overdue | {len(overdue)} |")
    lines.append(f"| In progress | {len(in_progress)} |")
    lines.append(f"| Completion rate | {rate} |")
    lines.append("")

    # ── Section breakdown ────────────────────────────────────────────────
    lines.append("## 📁 Section Breakdown")
    lines.append("")

    by_section: Dict[str, List[Task]] = {}
    for t in tasks:
        by_section.setdefault(t.section, []).append(t)

    lines.append("| Section | Total | Done | Rate |")
    lines.append("|---------|-------|------|------|")
    for sec, sec_tasks in sorted(by_section.items()):
        sec_total = len(sec_tasks)
        sec_done = sum(1 for t in sec_tasks if t.status == "[x]")
        sec_rate = f"{sec_done / sec_total * 100:.0f}%" if sec_total else "0%"
        lines.append(f"| {sec} | {sec_total} | {sec_done} | {sec_rate} |")
    lines.append("")

    content = "\n".join(lines)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return content


def generate_daily_report(
    tasks: List[Task],
    target_date: Optional[date] = None,
    output_path: Optional[Path] = None,
) -> str:
    """
    Generate a daily Markdown report.

    Args:
        tasks: All tasks.
        target_date: Date to report on (default: today).
        output_path: If provided, write report to this file.

    Returns:
        Markdown report as a string.
    """
    if target_date is None:
        target_date = _today()

    date_str = target_date.isoformat()
    now = datetime.now()

    lines = []
    lines.append(f"# TaskMD Daily Report — {date_str}")
    lines.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Due today
    due_today = [t for t in tasks if t.due == date_str and t.status != "[x]"]
    lines.append(f"## 📅 Due Today ({len(due_today)})")
    lines.append("")
    if due_today:
        for t in sorted(due_today, key=lambda t: (t.pri or 0) * -1):
            pri = f" `P{t.pri}`" if t.pri else ""
            lines.append(f"- {_status_label(t.status)} **{t.name}** `[{short_id(t.id)}]`{pri}")
        lines.append("")
    else:
        lines.append("_Nothing due today._")
        lines.append("")

    # Completed today
    completed_today = []
    for t in tasks:
        if t.status == "[x]" and t.done_ts and t.done_ts[:10] == date_str:
            completed_today.append(t)

    lines.append(f"## ✅ Completed Today ({len(completed_today)})")
    lines.append("")
    if completed_today:
        for t in completed_today:
            lines.append(f"- {t.name} `[{short_id(t.id)}]`")
        lines.append("")
    else:
        lines.append("_None yet._")
        lines.append("")

    # Overdue
    overdue = [
        t for t in tasks
        if t.due and t.status != "[x]"
        and parse_task_date(t.due) is not None
        and parse_task_date(t.due) < target_date
    ]
    if overdue:
        overdue.sort(key=lambda t: t.due)
        lines.append(f"## 🔴 Overdue ({len(overdue)})")
        lines.append("")
        for t in overdue[:10]:
            days_late = (target_date - parse_task_date(t.due)).days
            lines.append(f"- **{t.name}** `[{short_id(t.id)}]` _{t.due} (+{days_late}d)_")
        if len(overdue) > 10:
            lines.append(f"_...and {len(overdue) - 10} more._")
        lines.append("")

    content = "\n".join(lines)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return content
