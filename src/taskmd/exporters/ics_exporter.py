"""
ICS Calendar Exporter for TaskMD.

Exports tasks with due dates as iCalendar (.ics) events.
Compatible with Google Calendar, Apple Calendar, Outlook, etc.

Requires: pip install 'taskmd[export]'  (icalendar>=5.0)
"""
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional
import hashlib

from taskmd.models import Task


def _check_icalendar():
    """Check if icalendar is installed, raise helpful error if not."""
    try:
        import icalendar
        return icalendar
    except ImportError:
        raise ImportError(
            "The 'icalendar' package is required for ICS export.\n"
            "Install it with: pip install 'taskmd[export]'\n"
            "or: pip install icalendar>=5.0"
        )


def _make_uid(task: Task) -> str:
    """Generate a stable UID for a task."""
    key = f"{task.id}-{task.name}"
    return hashlib.md5(key.encode()).hexdigest() + "@taskmd"


def export_ics(
    tasks: List[Task],
    output_path: Optional[Path] = None,
    only_pending: bool = False,
    calendar_name: str = "TaskMD",
) -> str:
    """
    Export tasks to ICS (iCalendar) format.

    Only tasks with a `due` date are included — tasks without
    a due date cannot be represented as calendar events.

    Args:
        tasks: List of Task objects to export.
        output_path: If provided, write to this file. Otherwise return as string.
        only_pending: If True, exclude completed tasks.
        calendar_name: Display name of the calendar.

    Returns:
        ICS content as a string (also written to file if output_path given).
    """
    icalendar = _check_icalendar()
    from icalendar import Calendar, Event, vDate, vText, vDatetime

    if only_pending:
        tasks = [t for t in tasks if t.status != "[x]"]

    # Only export tasks with due dates
    due_tasks = [t for t in tasks if t.due]

    cal = Calendar()
    cal.add("prodid", "-//TaskMD//TaskMD//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", calendar_name)

    for task in due_tasks:
        try:
            if " " in task.due:
                due_dt = datetime.strptime(task.due, "%Y-%m-%d %H:%M")
                is_all_day = False
            else:
                due_dt = datetime.strptime(task.due, "%Y-%m-%d").date()
                is_all_day = True
        except ValueError:
            continue

        event = Event()
        event.add("uid", _make_uid(task))
        event.add("summary", task.name)
        event.add("dtstart", due_dt)
        if is_all_day:
            event.add("dtend", due_dt)  # All-day event
        else:
            # For timed events, default duration 1 hour or just use same time?
            # iCal usually needs dtend.
            from datetime import timedelta
            event.add("dtend", due_dt + timedelta(hours=1))

        # Description with full task metadata
        desc_parts = [f"TaskMD ID: {task.id}"]
        if task.section:
            desc_parts.append(f"Section: {task.section}/{task.sub}")
        if task.status:
            status_label = {
                "[x]": "Done", "[-]": "In Progress", "[ ]": "Todo"
            }.get(task.status, task.status)
            desc_parts.append(f"Status: {status_label}")
        if task.pri:
            desc_parts.append(f"Priority: {'★' * task.pri}")
        if task.tags:
            desc_parts.append(f"Tags: {', '.join(task.tags)}")
        if task.rem:
            desc_parts.append(f"Note: {task.rem}")
        if task.course:
            desc_parts.append(f"Course: {task.course}")

        event.add("description", "\n".join(desc_parts))
        event.add("dtstamp", datetime.now())

        # Status mapping
        if task.status == "[x]":
            event.add("status", "COMPLETED")
        elif task.status == "[-]":
            event.add("status", "IN-PROCESS")
        else:
            event.add("status", "NEEDS-ACTION")

        # Priority (iCal 0=undefined, 1=high, 5=medium, 9=low)
        if task.pri:
            ical_pri = max(1, min(9, 10 - task.pri * 2))
            event.add("priority", ical_pri)

        cal.add_component(event)

    content = cal.to_ical().decode("utf-8")

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return content
