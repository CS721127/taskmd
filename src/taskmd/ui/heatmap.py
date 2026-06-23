"""
Heatmap urgency color logic for TaskMD.

Defines urgency levels and maps them to Rich styles and ANSI colors.
Used by both the Rich dashboard and fallback ANSI rendering.

Urgency levels (highest → lowest):
  OVERDUE       → past due date
  DUE_TODAY     → due today
  DUE_SOON      → due within 3 days
  DUE_UPCOMING  → due within 4-7 days
  IN_ATTENTION  → start date <= today < due date
  NORMAL        → everything else
"""
from datetime import datetime, date
from typing import Optional

from taskmd.models import Task
from taskmd.datetime_utils import parse_task_date


# ─── Urgency constants ────────────────────────────────────────────────────────

URGENCY_OVERDUE = "OVERDUE"
URGENCY_DUE_TODAY = "DUE_TODAY"
URGENCY_DUE_SOON = "DUE_SOON"       # ≤ 3 days
URGENCY_DUE_UPCOMING = "DUE_UPCOMING"  # 4-7 days
URGENCY_IN_ATTENTION = "IN_ATTENTION"
URGENCY_NORMAL = "NORMAL"

# Rich styles (used when rich is available)
RICH_STYLES = {
    URGENCY_OVERDUE: "bold red",
    URGENCY_DUE_TODAY: "bold yellow",
    URGENCY_DUE_SOON: "yellow",
    URGENCY_DUE_UPCOMING: "bright_yellow",
    URGENCY_IN_ATTENTION: "cyan",
    URGENCY_NORMAL: "default",
}

# ANSI colors (fallback)
ANSI_COLORS = {
    URGENCY_OVERDUE: "\033[91m",       # bright red
    URGENCY_DUE_TODAY: "\033[93m",     # bright yellow
    URGENCY_DUE_SOON: "\033[33m",      # yellow
    URGENCY_DUE_UPCOMING: "\033[33m",  # yellow
    URGENCY_IN_ATTENTION: "\033[96m",  # bright cyan
    URGENCY_NORMAL: "\033[0m",         # reset
}

ANSI_RESET = "\033[0m"

# Emoji indicators per urgency
URGENCY_ICONS = {
    URGENCY_OVERDUE: "🔴",
    URGENCY_DUE_TODAY: "🟡",
    URGENCY_DUE_SOON: "🟠",
    URGENCY_DUE_UPCOMING: "🔵",
    URGENCY_IN_ATTENTION: "💎",
    URGENCY_NORMAL: "⚪",
}


def get_urgency_level(task: Task) -> str:
    """Determine urgency level for a task.

    Rules (evaluated in priority order):
      1. Completed tasks are always NORMAL
      2. OVERDUE: has due date and it's in the past
      3. DUE_TODAY: due date is today
      4. DUE_SOON: due date within 3 days
      5. DUE_UPCOMING: due date within 4-7 days
      6. IN_ATTENTION: start_date <= today and either no due or due > 7 days
      7. NORMAL: everything else
    """
    if task.status == "[x]":
        return URGENCY_NORMAL

    today = date.today()

    # Parse due date (accepts "YYYY-MM-DD" or "YYYY-MM-DD HH:MM")
    due_date: Optional[date] = parse_task_date(task.due)

    # Parse start date (same flexible format)
    start_date: Optional[date] = parse_task_date(task.start)

    if due_date is not None:
        days_until_due = (due_date - today).days
        if days_until_due < 0:
            return URGENCY_OVERDUE
        elif days_until_due == 0:
            # If the task has a precise due time today that has already
            # passed, treat it as overdue rather than merely "due today"
            # (TODOs.md Issue 5: precise-time awareness).
            from taskmd.datetime_utils import parse_task_datetime, has_time_component
            if has_time_component(task.due):
                due_dt = parse_task_datetime(task.due)
                if due_dt is not None and due_dt < datetime.now():
                    return URGENCY_OVERDUE
            return URGENCY_DUE_TODAY
        elif days_until_due <= 3:
            return URGENCY_DUE_SOON
        elif days_until_due <= 7:
            return URGENCY_DUE_UPCOMING

    if start_date is not None and start_date <= today:
        return URGENCY_IN_ATTENTION

    return URGENCY_NORMAL


def get_rich_style(task: Task) -> str:
    """Return a Rich-compatible style string for a task."""
    return RICH_STYLES[get_urgency_level(task)]


def get_ansi_color(task: Task) -> str:
    """Return an ANSI escape code string for a task's urgency."""
    return ANSI_COLORS[get_urgency_level(task)]


def get_urgency_icon(task: Task) -> str:
    """Return an emoji icon for the task's urgency level."""
    return URGENCY_ICONS[get_urgency_level(task)]


def get_urgency_label(level: str) -> str:
    """Return a human-readable label for an urgency level."""
    labels = {
        URGENCY_OVERDUE: "Overdue",
        URGENCY_DUE_TODAY: "Due Today",
        URGENCY_DUE_SOON: "Due Soon",
        URGENCY_DUE_UPCOMING: "Upcoming",
        URGENCY_IN_ATTENTION: "Attention",
        URGENCY_NORMAL: "Normal",
    }
    return labels.get(level, "Normal")
