"""
JSON Exporter for TaskMD.

Exports tasks to JSON format.
Uses Python's standard library json module — no extra dependencies.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from taskmd.models import Task


def _task_to_dict(task: Task) -> dict:
    """Convert a Task to a JSON-serializable dict."""
    return {
        "id": task.id,
        "name": task.name,
        "section": task.section,
        "sub": task.sub,
        "status": task.status,
        "due": task.due,
        "start": task.start,
        "pri": task.pri,
        "tags": task.tags,
        "done_ts": task.done_ts,
        "created": task.created,
        "updated": task.updated,
        "weight": task.weight,
        "course": task.course,
        "rem": task.rem,
        "est": task.est,
        "loc": task.loc,
    }


def export_json(
    tasks: List[Task],
    output_path: Optional[Path] = None,
    pretty: bool = True,
    only_pending: bool = False,
) -> str:
    """
    Export tasks to JSON format.

    Args:
        tasks: List of Task objects to export.
        output_path: If provided, write to this file. Otherwise return as string.
        pretty: If True, use indented formatting.
        only_pending: If True, only export non-completed tasks.

    Returns:
        JSON content as a string (also written to file if output_path given).
    """
    if only_pending:
        tasks = [t for t in tasks if t.status != "[x]"]

    payload = {
        "exported_at": datetime.now().isoformat(),
        "total": len(tasks),
        "tasks": [_task_to_dict(t) for t in tasks],
    }

    indent = 2 if pretty else None
    content = json.dumps(payload, indent=indent, ensure_ascii=False)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return content
