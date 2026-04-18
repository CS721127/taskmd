"""
CSV Exporter for TaskMD.

Exports tasks to a CSV file with all standard fields.
Uses Python's standard library csv module — no extra dependencies.

Columns: id, name, section, sub, status, due, start, pri, tags, done_ts, created, updated, weight, course, rem
"""
import csv
import io
from pathlib import Path
from typing import List, Optional

from taskmd.models import Task


# Column order for CSV output
CSV_COLUMNS = [
    "id",
    "name",
    "section",
    "sub",
    "status",
    "due",
    "start",
    "pri",
    "tags",
    "done_ts",
    "created",
    "updated",
    "weight",
    "course",
    "rem",
    "est",
    "loc",
]


def _task_to_row(task: Task) -> dict:
    """Convert a Task to a flat dict for CSV output."""
    return {
        "id": task.id or "",
        "name": task.name or "",
        "section": task.section or "",
        "sub": task.sub or "",
        "status": task.status or "[ ]",
        "due": task.due or "",
        "start": task.start or "",
        "pri": str(task.pri) if task.pri is not None else "",
        "tags": ",".join(task.tags) if task.tags else "",
        "done_ts": task.done_ts or "",
        "created": task.created or "",
        "updated": task.updated or "",
        "weight": str(task.weight) if task.weight is not None else "",
        "course": task.course or "",
        "rem": task.rem or "",
        "est": task.est or "",
        "loc": task.loc or "",
    }


def export_csv(
    tasks: List[Task],
    output_path: Optional[Path] = None,
    only_pending: bool = False,
) -> str:
    """
    Export tasks to CSV format.

    Args:
        tasks: List of Task objects to export.
        output_path: If provided, write to this file. Otherwise return as string.
        only_pending: If True, only export non-completed tasks.

    Returns:
        CSV content as a string (also written to file if output_path given).
    """
    if only_pending:
        tasks = [t for t in tasks if t.status != "[x]"]

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for task in tasks:
        writer.writerow(_task_to_row(task))

    content = buf.getvalue()

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return content
