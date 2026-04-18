"""
Tests for Phase 5-8 features.

Phase 5 : Rich UI & Live Editing (heatmap, dashboard rendering)
Phase 6 : Auto-Timestamp, Soft Deadlines & Heatmap Reminders
Phase 7 : High-Frequency Productivity (weekly/daily reports)
Phase 8 : Export & Sharing (CSV, JSON, ICS, HTML)
"""
import json
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from taskmd.models import Task
from taskmd.ui.heatmap import (
    URGENCY_DUE_SOON,
    URGENCY_DUE_TODAY,
    URGENCY_DUE_UPCOMING,
    URGENCY_IN_ATTENTION,
    URGENCY_NORMAL,
    URGENCY_OVERDUE,
    get_ansi_color,
    get_rich_style,
    get_urgency_icon,
    get_urgency_level,
)

TODAY = date.today()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()
TOMORROW = (TODAY + timedelta(days=1)).isoformat()
IN_2_DAYS = (TODAY + timedelta(days=2)).isoformat()
IN_5_DAYS = (TODAY + timedelta(days=5)).isoformat()
TODAY_STR = TODAY.isoformat()


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_tasks():
    return [
        Task(id="t_01", name="Overdue task",   section="Work", sub="Docs",  due=YESTERDAY,  pri=3, tags=["urgent"]),
        Task(id="t_02", name="Due today",       section="Work", sub="Meets", due=TODAY_STR,  status="[-]"),
        Task(id="t_03", name="Due in 2 days",   section="Life", sub="Home",  due=IN_2_DAYS),
        Task(id="t_04", name="Due in 5 days",   section="Life", sub="Home",  due=IN_5_DAYS,  tags=["reading"]),
        Task(id="t_05", name="In attention",    section="Study", sub="Plan", start=YESTERDAY),
        Task(id="t_06", name="Normal task",     section="Study", sub="Plan"),
        Task(id="t_07", name="Done task",       section="Work",  sub="Docs", due=YESTERDAY,  status="[x]",
             done_ts=TODAY_STR + "T09:00:00"),
    ]


@pytest.fixture
def md_file(tmp_path):
    """Create a temporary tasks.md and return its path."""
    far_future = (TODAY + timedelta(days=20)).isoformat()
    md = f"""<!-- taskmd:version=2 -->

# Work

## Docs

- [ ] Write report <!-- id:t_01, due:{YESTERDAY}, pri:3 -->
- [x] Old done <!-- id:t_07, done:{TODAY_STR}T09:00:00 -->

## Meets

- [-] Standup <!-- id:t_02, due:{TODAY_STR} -->

# Life

## Home

- [ ] Buy groceries <!-- id:t_03, due:{TOMORROW}, tags:errand -->
- [ ] Read book <!-- id:t_04, due:{far_future}, start:{YESTERDAY} -->
"""
    p = tmp_path / "tasks.md"
    p.write_text(md)
    return p


# ─── Phase 5 / Phase 6: Heatmap ──────────────────────────────────────────────

class TestHeatmap:

    def test_overdue(self):
        t = Task(name="x", due=YESTERDAY)
        assert get_urgency_level(t) == URGENCY_OVERDUE

    def test_due_today(self):
        t = Task(name="x", due=TODAY_STR)
        assert get_urgency_level(t) == URGENCY_DUE_TODAY

    def test_due_soon(self):
        t = Task(name="x", due=IN_2_DAYS)
        assert get_urgency_level(t) == URGENCY_DUE_SOON

    def test_due_upcoming(self):
        t = Task(name="x", due=IN_5_DAYS)
        assert get_urgency_level(t) == URGENCY_DUE_UPCOMING

    def test_in_attention(self):
        t = Task(name="x", start=YESTERDAY)
        assert get_urgency_level(t) == URGENCY_IN_ATTENTION

    def test_in_attention_not_triggered_before_start(self):
        future = (TODAY + timedelta(days=3)).isoformat()
        t = Task(name="x", start=future)
        assert get_urgency_level(t) == URGENCY_NORMAL

    def test_normal(self):
        t = Task(name="x")
        assert get_urgency_level(t) == URGENCY_NORMAL

    def test_done_is_always_normal(self):
        t = Task(name="x", due=YESTERDAY, status="[x]")
        assert get_urgency_level(t) == URGENCY_NORMAL

    def test_rich_style_returns_string(self, sample_tasks):
        for task in sample_tasks:
            style = get_rich_style(task)
            assert isinstance(style, str), f"expected str, got {type(style)}"

    def test_ansi_color_returns_escape(self, sample_tasks):
        for task in sample_tasks:
            color = get_ansi_color(task)
            assert "\033[" in color, f"expected ANSI escape in {color!r}"

    def test_urgency_icon_returns_emoji(self, sample_tasks):
        for task in sample_tasks:
            icon = get_urgency_icon(task)
            assert len(icon) >= 1

    def test_due_beats_start(self):
        """When both due and start are set, due-based urgency wins."""
        t = Task(name="x", due=YESTERDAY, start=YESTERDAY)
        assert get_urgency_level(t) == URGENCY_OVERDUE

    def test_in_attention_with_future_due(self):
        """start <= today AND due > 7 days → IN_ATTENTION."""
        far_future = (TODAY + timedelta(days=20)).isoformat()
        t = Task(name="x", start=YESTERDAY, due=far_future)
        assert get_urgency_level(t) == URGENCY_IN_ATTENTION


# ─── Phase 5: Dashboard ──────────────────────────────────────────────────────

class TestDashboard:

    def test_progress_bar_empty(self):
        from taskmd.ui.dashboard import _make_progress_bar
        bar = _make_progress_bar(0, 0)
        assert "0%" in bar

    def test_progress_bar_partial(self):
        from taskmd.ui.dashboard import _make_progress_bar
        bar = _make_progress_bar(3, 7)
        assert "█" in bar
        assert "░" in bar
        assert "42%" in bar

    def test_progress_bar_complete(self):
        from taskmd.ui.dashboard import _make_progress_bar
        bar = _make_progress_bar(5, 5)
        assert "100%" in bar
        assert "░" not in bar

    def test_section_progress(self, sample_tasks):
        from taskmd.ui.dashboard import _section_progress
        done, total = _section_progress(sample_tasks)
        assert total == len(sample_tasks)
        assert done == 1  # only t_07

    def test_group_by_section(self, sample_tasks):
        from taskmd.ui.dashboard import _group_by_section
        groups = _group_by_section(sample_tasks)
        assert "Work" in groups
        assert "Life" in groups
        assert "Study" in groups

    def test_get_dashboard_returns_instance(self):
        from taskmd.ui.dashboard import get_dashboard, RICH_AVAILABLE, RichDashboard, AnsiFallbackDashboard
        d = get_dashboard()
        if RICH_AVAILABLE:
            assert isinstance(d, RichDashboard)
        else:
            assert isinstance(d, AnsiFallbackDashboard)

    def test_dashboard_render_does_not_crash(self, sample_tasks, capsys):
        from taskmd.ui.dashboard import get_dashboard, RICH_AVAILABLE
        d = get_dashboard()
        stats = {
            "total": len(sample_tasks), "done": 1, "in_progress": 1,
            "todo": 5, "overdue": 1, "due_today": 1,
            "completed_today": 1, "urgent": 2, "in_attention": 1,
            "completion_rate": "14.3%",
        }
        # Should not raise
        d.render_full(sample_tasks, stats)

    def test_render_section_progress_no_crash(self, sample_tasks):
        from taskmd.ui.dashboard import get_dashboard, RICH_AVAILABLE
        d = get_dashboard()
        if RICH_AVAILABLE:
            d.render_section_progress(sample_tasks)  # should not raise


# ─── Phase 6: Enhanced service (get_today + get_stats) ───────────────────────

class TestPhase6Service:

    def test_get_today_includes_start_attention(self, md_file):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService
        repo = TaskRepository(md_file)
        svc = TaskService(repo)
        today_tasks = svc.get_today()
        names = [t.name for t in today_tasks]
        # t_02 Standup due today
        assert any("Standup" in n for n in names), names
        # t_04 Read book has start=YESTERDAY → should appear
        assert any("Read book" in n for n in names), names

    def test_get_stats_completed_today(self, md_file):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService
        repo = TaskRepository(md_file)
        svc = TaskService(repo)
        stats = svc.get_stats()
        assert stats["completed_today"] == 1  # t_07 done_ts=today

    def test_get_stats_in_attention(self, md_file):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService
        repo = TaskRepository(md_file)
        svc = TaskService(repo)
        stats = svc.get_stats()
        assert stats["in_attention"] >= 1

    def test_get_stats_overdue(self, md_file):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService
        repo = TaskRepository(md_file)
        svc = TaskService(repo)
        stats = svc.get_stats()
        assert stats["overdue"] >= 1

    def test_get_stats_keys_present(self, md_file):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService
        repo = TaskRepository(md_file)
        svc = TaskService(repo)
        stats = svc.get_stats()
        for key in ("total", "done", "in_progress", "todo", "overdue", "due_today",
                    "completed_today", "urgent", "in_attention", "completion_rate"):
            assert key in stats, f"missing key: {key}"


# ─── Phase 7 / Phase 8: Reports ──────────────────────────────────────────────

class TestReports:

    def test_weekly_report_structure(self, sample_tasks):
        from taskmd.exporters.report import generate_weekly_report
        report = generate_weekly_report(sample_tasks)
        assert "# TaskMD Weekly Report" in report
        assert "## ✅ Completed This Week" in report
        assert "## 📅 Due This Week" in report
        assert "## 🔴 Overdue" in report
        assert "## 🔄 In Progress" in report
        assert "## 📊 Statistics" in report
        assert "## 📁 Section Breakdown" in report

    def test_weekly_report_shows_done_task(self, sample_tasks):
        from taskmd.exporters.report import generate_weekly_report
        # t_07 is done with done_ts = today → in this week's completed
        report = generate_weekly_report(sample_tasks)
        assert "Done task" in report

    def test_weekly_report_section_breakdown(self, sample_tasks):
        from taskmd.exporters.report import generate_weekly_report
        report = generate_weekly_report(sample_tasks)
        assert "Work" in report
        assert "Life" in report

    def test_weekly_report_file_output(self, sample_tasks, tmp_path):
        from taskmd.exporters.report import generate_weekly_report
        out = tmp_path / "report.md"
        content = generate_weekly_report(sample_tasks, output_path=out)
        assert out.exists()
        assert out.read_text() == content

    def test_daily_report_structure(self, sample_tasks):
        from taskmd.exporters.report import generate_daily_report
        report = generate_daily_report(sample_tasks)
        assert "Daily Report" in report
        assert "## 📅 Due Today" in report
        assert "## ✅ Completed Today" in report

    def test_daily_report_due_today(self, sample_tasks):
        from taskmd.exporters.report import generate_daily_report
        report = generate_daily_report(sample_tasks)
        assert "Due today" in report  # t_02

    def test_daily_report_completed_today(self, sample_tasks):
        from taskmd.exporters.report import generate_daily_report
        report = generate_daily_report(sample_tasks)
        # t_07 done_ts = today
        assert "Done task" in report


# ─── Phase 8: CSV Exporter ───────────────────────────────────────────────────

class TestCsvExporter:

    def test_header_present(self, sample_tasks):
        from taskmd.exporters.csv_exporter import export_csv
        csv = export_csv(sample_tasks)
        assert csv.startswith("id,name,section")

    def test_all_tasks_exported(self, sample_tasks):
        from taskmd.exporters.csv_exporter import export_csv
        csv = export_csv(sample_tasks)
        lines = [l for l in csv.strip().split("\n") if l]
        assert len(lines) == len(sample_tasks) + 1  # +1 header

    def test_only_pending_filter(self, sample_tasks):
        from taskmd.exporters.csv_exporter import export_csv
        csv = export_csv(sample_tasks, only_pending=True)
        lines = [l for l in csv.strip().split("\n") if l]
        pending = sum(1 for t in sample_tasks if t.status != "[x]")
        assert len(lines) == pending + 1

    def test_tags_serialized(self, sample_tasks):
        from taskmd.exporters.csv_exporter import export_csv
        csv = export_csv(sample_tasks)
        assert "urgent" in csv

    def test_file_output(self, sample_tasks, tmp_path):
        from taskmd.exporters.csv_exporter import export_csv
        out = tmp_path / "tasks.csv"
        content = export_csv(sample_tasks, output_path=out)
        assert out.exists()
        assert out.read_text() == content

    def test_pri_serialized(self, sample_tasks):
        from taskmd.exporters.csv_exporter import export_csv
        csv = export_csv(sample_tasks)
        assert ",3," in csv  # t_01 has pri=3


# ─── Phase 8: JSON Exporter ──────────────────────────────────────────────────

class TestJsonExporter:

    def test_total_count(self, sample_tasks):
        from taskmd.exporters.json_exporter import export_json
        data = json.loads(export_json(sample_tasks))
        assert data["total"] == len(sample_tasks)

    def test_tasks_list(self, sample_tasks):
        from taskmd.exporters.json_exporter import export_json
        data = json.loads(export_json(sample_tasks))
        assert len(data["tasks"]) == len(sample_tasks)

    def test_tags_list(self, sample_tasks):
        from taskmd.exporters.json_exporter import export_json
        data = json.loads(export_json(sample_tasks))
        t01 = next(t for t in data["tasks"] if t["id"] == "t_01")
        assert t01["tags"] == ["urgent"]

    def test_only_pending(self, sample_tasks):
        from taskmd.exporters.json_exporter import export_json
        data = json.loads(export_json(sample_tasks, only_pending=True))
        pending = sum(1 for t in sample_tasks if t.status != "[x]")
        assert data["total"] == pending

    def test_pretty_format(self, sample_tasks):
        from taskmd.exporters.json_exporter import export_json
        pretty = export_json(sample_tasks, pretty=True)
        compact = export_json(sample_tasks, pretty=False)
        assert len(pretty) > len(compact)
        assert "\n" in pretty
        assert "\n" not in compact

    def test_file_output(self, sample_tasks, tmp_path):
        from taskmd.exporters.json_exporter import export_json
        out = tmp_path / "tasks.json"
        content = export_json(sample_tasks, output_path=out)
        assert out.exists()
        assert json.loads(out.read_text())["total"] == len(sample_tasks)

    def test_exported_at_field(self, sample_tasks):
        from taskmd.exporters.json_exporter import export_json
        data = json.loads(export_json(sample_tasks))
        assert "exported_at" in data


# ─── Phase 8: ICS Exporter ───────────────────────────────────────────────────

class TestIcsExporter:

    def test_vcalendar_header(self, sample_tasks):
        from taskmd.exporters.ics_exporter import export_ics
        ics = export_ics(sample_tasks)
        assert "BEGIN:VCALENDAR" in ics
        assert "END:VCALENDAR" in ics

    def test_only_tasks_with_due_dates(self, sample_tasks):
        from taskmd.exporters.ics_exporter import export_ics
        ics = export_ics(sample_tasks)
        tasks_with_due = [t for t in sample_tasks if t.due]
        assert ics.count("BEGIN:VEVENT") == len(tasks_with_due)

    def test_only_pending_excludes_done(self, sample_tasks):
        from taskmd.exporters.ics_exporter import export_ics
        ics = export_ics(sample_tasks, only_pending=True)
        pending_with_due = [t for t in sample_tasks if t.due and t.status != "[x]"]
        assert ics.count("BEGIN:VEVENT") == len(pending_with_due)

    def test_task_name_in_summary(self, sample_tasks):
        from taskmd.exporters.ics_exporter import export_ics
        ics = export_ics(sample_tasks)
        assert "Overdue task" in ics

    def test_status_mapping(self, sample_tasks):
        from taskmd.exporters.ics_exporter import export_ics
        ics = export_ics(sample_tasks)
        assert "NEEDS-ACTION" in ics
        assert "IN-PROCESS" in ics

    def test_file_output(self, sample_tasks, tmp_path):
        from taskmd.exporters.ics_exporter import export_ics
        out = tmp_path / "tasks.ics"
        export_ics(sample_tasks, output_path=out)
        assert out.exists()
        assert "BEGIN:VCALENDAR" in out.read_text()


# ─── Phase 8: HTML Exporter ──────────────────────────────────────────────────

class TestHtmlExporter:

    def test_three_columns_present(self, sample_tasks):
        from taskmd.exporters.html_exporter import export_html
        html = export_html(sample_tasks)
        assert "col-todo" in html
        assert "col-progress" in html
        assert "col-done" in html

    def test_task_names_present(self, sample_tasks):
        from taskmd.exporters.html_exporter import export_html
        html = export_html(sample_tasks)
        assert "Overdue task" in html
        assert "Due today" in html

    def test_light_theme(self, sample_tasks):
        from taskmd.exporters.html_exporter import export_html
        html = export_html(sample_tasks, theme="light")
        assert "f0f2f5" in html  # light bg

    def test_dark_theme(self, sample_tasks):
        from taskmd.exporters.html_exporter import export_html
        html = export_html(sample_tasks, theme="dark")
        assert "1a1a2e" in html  # dark bg

    def test_js_filter_present(self, sample_tasks):
        from taskmd.exporters.html_exporter import export_html
        html = export_html(sample_tasks)
        assert "filterCards" in html
        assert "filterSection" in html

    def test_section_filter_buttons(self, sample_tasks):
        from taskmd.exporters.html_exporter import export_html
        html = export_html(sample_tasks)
        # Sections in sample_tasks: Work, Life, Study
        assert "Work" in html
        assert "Life" in html

    def test_urgency_classes(self, sample_tasks):
        from taskmd.exporters.html_exporter import export_html
        html = export_html(sample_tasks)
        assert "urgency-overdue" in html

    def test_standalone_no_external_deps(self, sample_tasks):
        """Single-file HTML must not reference external JS/CSS files."""
        from taskmd.exporters.html_exporter import export_html
        html = export_html(sample_tasks)
        assert "<script src=" not in html
        assert '<link rel="stylesheet"' not in html

    def test_file_output(self, sample_tasks, tmp_path):
        from taskmd.exporters.html_exporter import export_html
        out = tmp_path / "board.html"
        export_html(sample_tasks, output_path=out)
        assert out.exists()
        assert "col-todo" in out.read_text()
