"""
Tests for precise due/start time support (TODOs.md Issue 5):
  - datetime_utils parsing/formatting helpers
  - heatmap urgency detection with HH:MM precision
  - service layer (get_today/get_next/get_overdue/get_stats) precision safety
  - quick_capture shorthand + explicit time tokens
  - cli.get_time_left precision formatting
  - ics export of timed vs all-day events
"""
from datetime import datetime, timedelta, date

import pytest

from taskmd.datetime_utils import (
    parse_task_date,
    parse_task_datetime,
    has_time_component,
    format_remaining,
    is_valid_task_datetime_str,
)
from taskmd.models import Task
from taskmd.ui.heatmap import (
    get_urgency_level,
    URGENCY_OVERDUE,
    URGENCY_DUE_TODAY,
    URGENCY_DUE_SOON,
)


# ─── datetime_utils ────────────────────────────────────────────────────────

class TestDatetimeUtils:
    def test_parse_date_only(self):
        assert parse_task_date("2026-06-25") == date(2026, 6, 25)

    def test_parse_datetime_with_time(self):
        dt = parse_task_datetime("2026-06-25 14:30")
        assert dt == datetime(2026, 6, 25, 14, 30)

    def test_parse_date_drops_time(self):
        assert parse_task_date("2026-06-25 14:30") == date(2026, 6, 25)

    def test_parse_invalid_returns_none(self):
        assert parse_task_date("not-a-date") is None
        assert parse_task_datetime("not-a-date") is None

    def test_parse_none_returns_none(self):
        assert parse_task_date(None) is None
        assert parse_task_datetime(None) is None

    def test_has_time_component(self):
        assert has_time_component("2026-06-25 14:30") is True
        assert has_time_component("2026-06-25") is False
        assert has_time_component(None) is False

    def test_is_valid_task_datetime_str(self):
        assert is_valid_task_datetime_str("2026-06-25") is True
        assert is_valid_task_datetime_str("2026-06-25 09:00") is True
        assert is_valid_task_datetime_str("garbage") is False

    def test_format_remaining_date_only_days(self):
        ref = datetime(2026, 6, 23, 12, 0)
        assert format_remaining("2026-06-25", ref) == "2d"

    def test_format_remaining_date_only_today_not_negative(self):
        # Even late in the day, "today" (date-only) should not appear negative.
        ref = datetime(2026, 6, 23, 23, 59)
        assert format_remaining("2026-06-23", ref) == "0d"

    def test_format_remaining_precise_hours(self):
        ref = datetime(2026, 6, 23, 9, 0)
        assert format_remaining("2026-06-23 14:30", ref) == "5h 30m"

    def test_format_remaining_precise_days_and_hours(self):
        ref = datetime(2026, 6, 23, 9, 0)
        assert format_remaining("2026-06-25 11:00", ref) == "2d 2h"

    def test_format_remaining_precise_overdue(self):
        ref = datetime(2026, 6, 23, 14, 0)
        result = format_remaining("2026-06-23 09:00", ref)
        assert result.startswith("-")
        assert "5h" in result

    def test_format_remaining_date_only_overdue(self):
        ref = datetime(2026, 6, 25, 9, 0)
        result = format_remaining("2026-06-23", ref)
        assert result == "-2d"

    def test_format_remaining_unparseable_is_empty(self):
        assert format_remaining("garbage") == ""

    def test_format_remaining_minutes_only(self):
        ref = datetime(2026, 6, 23, 9, 50)
        assert format_remaining("2026-06-23 10:00", ref) == "10m"


# ─── heatmap urgency with precise times ────────────────────────────────────

class TestUrgencyPrecision:
    def test_due_today_date_only_is_due_today(self):
        today = date.today().isoformat()
        t = Task(name="x", section="S", sub="B", status="[ ]", due=today)
        assert get_urgency_level(t) == URGENCY_DUE_TODAY

    def test_due_today_with_future_time_is_due_today(self):
        future = datetime.now() + timedelta(hours=2)
        due = future.strftime("%Y-%m-%d %H:%M")
        t = Task(name="x", section="S", sub="B", status="[ ]", due=due)
        assert get_urgency_level(t) == URGENCY_DUE_TODAY

    def test_due_today_with_past_time_is_overdue(self):
        past = datetime.now() - timedelta(hours=1)
        due = past.strftime("%Y-%m-%d %H:%M")
        t = Task(name="x", section="S", sub="B", status="[ ]", due=due)
        assert get_urgency_level(t) == URGENCY_OVERDUE

    def test_due_yesterday_is_overdue_regardless_of_time(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        t = Task(name="x", section="S", sub="B", status="[ ]", due=f"{yesterday} 23:59")
        assert get_urgency_level(t) == URGENCY_OVERDUE

    def test_completed_task_always_normal(self):
        past = (date.today() - timedelta(days=5)).isoformat()
        t = Task(name="x", section="S", sub="B", status="[x]", due=past)
        from taskmd.ui.heatmap import URGENCY_NORMAL
        assert get_urgency_level(t) == URGENCY_NORMAL

    def test_due_in_two_days_with_time_is_due_soon(self):
        target = datetime.now() + timedelta(days=2)
        due = target.strftime("%Y-%m-%d %H:%M")
        t = Task(name="x", section="S", sub="B", status="[ ]", due=due)
        assert get_urgency_level(t) == URGENCY_DUE_SOON


# ─── service layer precision safety ────────────────────────────────────────

class TestServicePrecision:
    def test_get_today_matches_precise_due_today(self, tmp_path):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService

        today = date.today().isoformat()
        content = (
            "<!-- taskmd:version=2 -->\n\n"
            "# Work\n## Tasks\n"
            f"- [ ] Precise today task <!-- id:t_01, due:{today} 18:00 -->\n"
        )
        f = tmp_path / "tasks.md"
        f.write_text(content, encoding="utf-8")
        svc = TaskService(TaskRepository(f))
        today_tasks = svc.get_today()
        assert any("Precise today task" in t.name for t in today_tasks)

    def test_get_next_includes_precise_due(self, tmp_path):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService

        target = (date.today() + timedelta(days=3)).isoformat()
        content = (
            "<!-- taskmd:version=2 -->\n\n"
            "# Work\n## Tasks\n"
            f"- [ ] Precise upcoming task <!-- id:t_01, due:{target} 09:15 -->\n"
        )
        f = tmp_path / "tasks.md"
        f.write_text(content, encoding="utf-8")
        svc = TaskService(TaskRepository(f))
        next_tasks = svc.get_next(days=7)
        assert any("Precise upcoming task" in t.name for t in next_tasks)

    def test_get_overdue_detects_precise_past_time_today(self, tmp_path):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService

        past_time = (datetime.now() - timedelta(hours=1)).strftime("%H:%M")
        today = date.today().isoformat()
        content = (
            "<!-- taskmd:version=2 -->\n\n"
            "# Work\n## Tasks\n"
            f"- [ ] Overdue precise task <!-- id:t_01, due:{today} {past_time} -->\n"
        )
        f = tmp_path / "tasks.md"
        f.write_text(content, encoding="utf-8")
        svc = TaskService(TaskRepository(f))
        overdue = svc.get_overdue()
        assert any("Overdue precise task" in t.name for t in overdue)

    def test_get_overdue_does_not_flag_precise_future_time_today(self, tmp_path):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService

        future_time = (datetime.now() + timedelta(hours=2)).strftime("%H:%M")
        today = date.today().isoformat()
        content = (
            "<!-- taskmd:version=2 -->\n\n"
            "# Work\n## Tasks\n"
            f"- [ ] Future precise task <!-- id:t_01, due:{today} {future_time} -->\n"
        )
        f = tmp_path / "tasks.md"
        f.write_text(content, encoding="utf-8")
        svc = TaskService(TaskRepository(f))
        overdue = svc.get_overdue()
        assert not any("Future precise task" in t.name for t in overdue)


# ─── quick_capture precise time tokens ─────────────────────────────────────

class TestQuickCapturePrecision:
    def test_explicit_datetime_literal(self):
        from taskmd.quick_capture import parse_quick_capture
        r = parse_quick_capture("Submit report @2026-06-25 14:30")
        # Space-containing literal due values aren't part of the @token grammar;
        # explicit times are entered via `tm due` instead. This just confirms
        # the date portion is still captured without crashing.
        assert r.due is not None

    def test_shorthand_with_time_suffix_tomorrow(self):
        from taskmd.quick_capture import parse_quick_capture
        r = parse_quick_capture("Submit report @tomorrowT14:30")
        assert r.due is not None
        assert " " in r.due
        assert r.due.endswith("14:30")

    def test_shorthand_with_time_suffix_weekday(self):
        from taskmd.quick_capture import _parse_date_token
        result = _parse_date_token("monT08:15")
        assert result is not None
        assert result.endswith("08:15")

    def test_shorthand_with_time_suffix_relative_days(self):
        from taskmd.quick_capture import _parse_date_token
        result = _parse_date_token("+3dT23:59")
        assert result is not None
        assert result.endswith("23:59")

    def test_start_token_with_time_suffix(self):
        from taskmd.quick_capture import parse_quick_capture
        r = parse_quick_capture("Call dentist ^todayT08:00")
        assert r.start is not None
        assert r.start.endswith("08:00")

    def test_literal_iso_datetime_with_t_suffix_passthrough(self):
        from taskmd.quick_capture import _parse_date_token
        result = _parse_date_token("2026-06-25T10:00")
        assert result == "2026-06-25 10:00"


# ─── cli.get_time_left precision formatting ────────────────────────────────

class TestGetTimeLeftPrecision:
    def test_date_only_due_today_not_overdue(self):
        from taskmd.cli import get_time_left
        today = date.today().isoformat()
        result = get_time_left(today)
        assert "OVERDUE" not in result
        assert "DUE TODAY" in result

    def test_precise_future_shows_hour_minute(self):
        from taskmd.cli import get_time_left
        future = (datetime.now() + timedelta(hours=3, minutes=15)).strftime("%Y-%m-%d %H:%M")
        result = get_time_left(future)
        assert "h" in result and "m" in result
        assert "OVERDUE" not in result

    def test_precise_past_shows_overdue_with_magnitude(self):
        from taskmd.cli import get_time_left
        past = (datetime.now() - timedelta(hours=1, minutes=30)).strftime("%Y-%m-%d %H:%M")
        result = get_time_left(past)
        assert "OVERDUE" in result

    def test_invalid_date_reports_invalid(self):
        from taskmd.cli import get_time_left
        result = get_time_left("not-a-real-date")
        assert "Invalid Date" in result

    def test_empty_due_returns_empty(self):
        from taskmd.cli import get_time_left
        assert get_time_left("") == ""


# ─── ICS export precision ───────────────────────────────────────────────────

class TestIcsPrecision:
    def test_precise_due_creates_timed_event(self):
        icalendar = pytest.importorskip("icalendar")
        from taskmd.exporters.ics_exporter import export_ics
        t = Task(name="Standup", section="Work", sub="Meetings", status="[ ]",
                 id="t_01", due="2026-06-25 09:30")
        content = export_ics([t])
        assert "DTSTART:20260625T093000" in content
        assert "VALUE=DATE" not in content

    def test_date_only_due_creates_all_day_event(self):
        icalendar = pytest.importorskip("icalendar")
        from taskmd.exporters.ics_exporter import export_ics
        t = Task(name="Submit report", section="Work", sub="Reports", status="[ ]",
                 id="t_02", due="2026-06-26")
        content = export_ics([t])
        assert "DTSTART;VALUE=DATE:20260626" in content
