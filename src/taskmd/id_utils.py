"""
Shared task-ID display helpers for TaskMD.

Internally, tasks are stored with a prefixed ID (e.g. "t_01") so that the
storage format is namespaced and future ID schemes (e.g. "p_01" for
projects) don't collide. Every user-facing surface, however, should show
the short form ("01") — this module is the single source of truth for
that conversion so CLI, dashboard, and all exporters stay consistent
(see TODOs.md Issue 2).
"""
from typing import Optional


def short_id(task_id: Optional[str]) -> str:
    """Convert an internal task ID to its short, user-friendly form.

    Examples:
        "t_01"  -> "01"
        "t_123" -> "123"
        "07"    -> "07"   (already short / no recognized prefix)
        None    -> "?"
    """
    if not task_id:
        return "?"
    if task_id.startswith("t_"):
        return task_id[2:]
    return task_id


def display_id(task_id: Optional[str]) -> str:
    """Return the short ID wrapped in brackets for inline display: '[01]'."""
    return f"[{short_id(task_id)}]"
