"""
Shared date/datetime helpers for TaskMD.

Task `due` and `start` fields may be stored as either:
  - A date only:      "YYYY-MM-DD"
  - A date and time:  "YYYY-MM-DD HH:MM"

This module is the single place that knows how to parse either form into
a `datetime`, and how to render the time-remaining-until-due text with
hour/minute precision when a time component is present (TODOs.md Issue 5:
"事件截止时间应当可以精确到几点几分 ... today，next 等如果有精确时间应当写为
xx天xx小时").
"""
from datetime import datetime, date, timedelta
from typing import Optional


DATE_FMT = "%Y-%m-%d"
DATETIME_FMT = "%Y-%m-%d %H:%M"


def has_time_component(value: Optional[str]) -> bool:
    """Return True if a due/start string includes an HH:MM time component."""
    if not value:
        return False
    return " " in value.strip()


def parse_task_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse a due/start string into a datetime.

    Accepts "YYYY-MM-DD" (interpreted as midnight) or "YYYY-MM-DD HH:MM".
    Returns None if the value is missing or doesn't match either format.
    """
    if not value:
        return None
    value = value.strip()
    fmt = DATETIME_FMT if " " in value else DATE_FMT
    try:
        return datetime.strptime(value, fmt)
    except ValueError:
        return None


def parse_task_date(value: Optional[str]) -> Optional[date]:
    """Parse a due/start string into a plain date (drops any time component)."""
    dt = parse_task_datetime(value)
    return dt.date() if dt else None


def now() -> datetime:
    """Return the current local datetime. Exists so call sites are patchable in tests."""
    return datetime.now()


def format_remaining(target: Optional[str], reference: Optional[datetime] = None) -> str:
    """Format the time remaining until a due/start string as a short label.

    - If `target` has no time component: "Nd" (days), matching legacy behaviour.
    - If `target` has an HH:MM time component: "Xd Yh" or "Yh Zm" once under a day,
      giving hour/minute precision as requested in Issue 5.
    - Past-due values are returned with a leading "-" so the caller can decide
      how to present overdue vs upcoming.

    Returns "" if target can't be parsed.
    """
    dt = parse_task_datetime(target)
    if dt is None:
        return ""
    ref = reference or now()
    delta = dt - ref
    total_seconds = delta.total_seconds()
    precise = has_time_component(target)
    # For date-only values, "past" is determined by calendar-day comparison
    # (today is never "past" even after midnight). For precise values, the
    # exact due moment determines past/future.
    past = (dt.date() < ref.date()) if not precise else (total_seconds < 0)
    total_seconds = abs(total_seconds)

    if not precise:
        # Date-only precision: report whole calendar days (legacy behaviour).
        days = abs((dt.date() - ref.date()).days)
        label = f"{days}d"
    else:
        days = int(total_seconds // 86400)
        remainder = total_seconds - days * 86400
        hours = int(remainder // 3600)
        minutes = int((remainder % 3600) // 60)
        if days > 0:
            label = f"{days}d {hours}h"
        elif hours > 0:
            label = f"{hours}h {minutes}m"
        else:
            label = f"{minutes}m"

    return f"-{label}" if past else label


def is_valid_task_datetime_str(value: str) -> bool:
    """Check if a string is a valid 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM' value."""
    return parse_task_datetime(value) is not None
