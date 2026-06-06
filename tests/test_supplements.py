"""
Tests for the three supplementary Phase 7/8 features:
  1. Quick Capture Syntax  (taskmd.quick_capture)
  2. PDF Export            (taskmd.exporters.pdf_exporter)
  3. SVG/PNG Image Export  (taskmd.exporters.image_exporter)
"""
import json
import re
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from taskmd.models import Task
from taskmd.quick_capture import parse_quick_capture, CaptureResult

TODAY = date.today()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()
TOMORROW  = (TODAY + timedelta(days=1)).isoformat()
TODAY_STR = TODAY.isoformat()
IN_5_DAYS = (TODAY + timedelta(days=5)).isoformat()


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_tasks():
    return [
        Task(id="t_01", name="Overdue report",  section="Work",  sub="Docs",  due=YESTERDAY, pri=3, tags=["urgent"]),
        Task(id="t_02", name="Team standup",    section="Work",  sub="Meets", due=TODAY_STR, status="[-]"),
        Task(id="t_03", name="Buy groceries",   section="Life",  sub="Home",  due=TOMORROW,  tags=["errand"]),
        Task(id="t_04", name="Read book",       section="Study", sub="Books", due=IN_5_DAYS),
        Task(id="t_05", name="Done old task",   section="Work",  sub="Docs",  status="[x]",  done_ts=TODAY_STR + "T09:00:00"),
    ]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _has_fpdf2():
    try:
        from fpdf import FPDF
        return True
    except ImportError:
        return False

def _has_icalendar():
    try:
        import icalendar
        return True
    except ImportError:
        return False

def _has_cairosvg():
    try:
        import cairosvg
        return True
    except ImportError:
        return False

def _has_pillow():
    try:
        from PIL import Image
        return True
    except ImportError:
        return False


# ─── Quick Capture ─────────────────────────────────────────────────────────────

class TestQuickCapture:

    def test_plain_name(self):
        r = parse_quick_capture("Write report")
        assert r.name == "Write report"
        assert r.tags == []
        assert r.pri is None
        assert r.due is None

    def test_single_tag(self):
        r = parse_quick_capture("Write report #work")
        assert r.name == "Write report"
        assert r.tags == ["work"]

    def test_multiple_tags(self):
        r = parse_quick_capture("Task #tag1 #tag2 #tag3")
        assert r.tags == ["tag1", "tag2", "tag3"]

    def test_priority_with_digit(self):
        r = parse_quick_capture("Task !3")
        assert r.pri == 3

    def test_priority_bare_bang(self):
        r = parse_quick_capture("Task !")
        assert r.pri == 1

    def test_priority_all_levels(self):
        for n in range(1, 6):
            r = parse_quick_capture(f"Task !{n}")
            assert r.pri == n

    def test_due_iso_date(self):
        r = parse_quick_capture("Task @2026-04-25")
        assert r.due == "2026-04-25"

    def test_due_today(self):
        r = parse_quick_capture("Task @today")
        assert r.due == TODAY_STR

    def test_due_tomorrow(self):
        r = parse_quick_capture("Task @tomorrow")
        assert r.due == TOMORROW

    def test_due_yesterday(self):
        r = parse_quick_capture("Task @yesterday")
        assert r.due == YESTERDAY

    def test_due_relative_days(self):
        for n in (1, 3, 7, 14):
            r = parse_quick_capture(f"Task @+{n}d")
            expected = (TODAY + timedelta(days=n)).isoformat()
            assert r.due == expected, f"+{n}d: {r.due} != {expected}"

    def test_due_weekday(self):
        for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
            r = parse_quick_capture(f"Task @{day}")
            assert r.due is not None
            assert re.match(r"\d{4}-\d{2}-\d{2}", r.due)
            # must be in the future (next occurrence)
            assert r.due > TODAY_STR

    def test_due_unknown_warns(self):
        r = parse_quick_capture("Task @next-year")
        assert r.due is None
        assert any("Unrecognised" in w for w in r.warnings)

    def test_start_date(self):
        r = parse_quick_capture("Task ^2026-04-10")
        assert r.start == "2026-04-10"

    def test_start_today_shorthand(self):
        r = parse_quick_capture("Task ^today")
        assert r.start == TODAY_STR

    def test_section(self):
        r = parse_quick_capture("Task /School")
        assert r.section == "School"

    def test_subsection(self):
        r = parse_quick_capture("Task //DPST1092")
        assert r.sub == "DPST1092"

    def test_reminder_note(self):
        r = parse_quick_capture("Task [Need help with this]")
        assert r.rem == "Need help with this"

    def test_all_tokens_combined(self):
        # Mixed order, multiple tags, notes, dates
        text = "Task /School //Lab #tag1 #tag2 !4 @tomorrow ^today [Some note]"
        r = parse_quick_capture(text)
        assert r.name == "Task"
        assert r.section == "School"
        assert r.sub == "Lab"
        assert sorted(r.tags) == ["tag1", "tag2"]
        assert r.pri == 4
        assert r.due == TOMORROW
        assert r.start == TODAY_STR
        assert r.rem == "Some note"

    def test_empty_string_warns(self):
        r = parse_quick_capture("")
        assert any("Empty" in w for w in r.warnings)

    def test_tags_lowercased(self):
        r = parse_quick_capture("Task #TAGS")
        assert r.tags == ["tags"]

    def test_returns_capture_result(self):
        r = parse_quick_capture("Task")
        assert isinstance(r, CaptureResult)

    def test_cli_flags_override_inline_tokens(self, tmp_path):
        """CLI -d / -p flags must override parsed tokens."""
        import subprocess, sys, os
        md = "<!-- taskmd:version=2 -->\n\n# Inbox\n\n## General\n\n"
        md_file = tmp_path / "tasks.md"
        md_file.write_text(md)
        src_path = str(Path(__file__).parent.parent / "src")
        env = {**os.environ, "TASKMD_DB_PATH": str(md_file), "PYTHONPATH": src_path}

        explicit_due = (TODAY + timedelta(days=10)).isoformat()
        r = subprocess.run(
            [sys.executable, "-m", "taskmd.cli", "add",
             f"Task #tag !1 @tomorrow",  # inline says !1, @tomorrow
             "-p", "5",                  # CLI says pri=5
             "-d", explicit_due],        # CLI says explicit_due
            capture_output=True, text=True, env=env,
        )
        assert "[OK]" in r.stdout + r.stderr

        j = tmp_path / "out.json"
        subprocess.run([sys.executable, "-m", "taskmd.cli", "export", "json", "--output", str(j)],
                       env=env, capture_output=True)
        data = json.loads(j.read_text())
        task = next(t for t in data["tasks"] if "Task" in t["name"])
        assert task["pri"] == 5,          f"expected pri=5, got {task['pri']}"
        assert task["due"] == explicit_due, f"expected {explicit_due}, got {task['due']}"


# ─── PDF Export ────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not _has_fpdf2(), reason="fpdf2 not installed")
class TestPdfExporter:

    def test_valid_pdf_header(self, sample_tasks, tmp_path):
        from taskmd.exporters.pdf_exporter import export_pdf
        out = tmp_path / "r.pdf"
        export_pdf(sample_tasks, output_path=out)
        assert out.exists()
        assert out.read_bytes()[:4] == b"%PDF"

    def test_returns_bytes(self, sample_tasks, tmp_path):
        from taskmd.exporters.pdf_exporter import export_pdf
        out = tmp_path / "r.pdf"
        result = export_pdf(sample_tasks, output_path=out)
        assert isinstance(result, (bytes, bytearray))
        assert len(result) > 1000

    def test_dark_theme(self, sample_tasks, tmp_path):
        from taskmd.exporters.pdf_exporter import export_pdf
        out = tmp_path / "dark.pdf"
        export_pdf(sample_tasks, output_path=out, theme="dark")
        assert out.read_bytes()[:4] == b"%PDF"

    def test_month_filter(self, sample_tasks, tmp_path):
        from taskmd.exporters.pdf_exporter import export_pdf, _filter_by_month
        month = TODAY_STR[:7]
        filtered = _filter_by_month(sample_tasks, month)
        # t_02 due today, t_05 done today — both in this month
        assert any(t.id == "t_02" for t in filtered)
        assert any(t.id == "t_05" for t in filtered)
        out = tmp_path / "month.pdf"
        export_pdf(sample_tasks, output_path=out, month=month)
        assert out.read_bytes()[:4] == b"%PDF"

    def test_only_pending_filter(self, sample_tasks, tmp_path):
        from taskmd.exporters.pdf_exporter import export_pdf
        out = tmp_path / "pending.pdf"
        export_pdf(sample_tasks, output_path=out, only_pending=True)
        assert out.read_bytes()[:4] == b"%PDF"

    def test_empty_tasks_does_not_crash(self, tmp_path):
        from taskmd.exporters.pdf_exporter import export_pdf
        out = tmp_path / "empty.pdf"
        export_pdf([], output_path=out)
        assert out.read_bytes()[:4] == b"%PDF"

    def test_missing_fpdf2_raises_import_error(self, monkeypatch):
        from taskmd.exporters import pdf_exporter
        monkeypatch.setattr(pdf_exporter, "_check_fpdf", lambda: (_ for _ in ()).throw(
            ImportError("The 'fpdf2' package is required")
        ))
        with pytest.raises(ImportError, match="fpdf2"):
            pdf_exporter.export_pdf([], output_path=Path("/tmp/x.pdf"))

    def test_filter_by_month_logic(self, sample_tasks):
        from taskmd.exporters.pdf_exporter import _filter_by_month
        next_month = f"{TODAY.year + (TODAY.month // 12)}-{TODAY.month % 12 + 1:02d}"
        result = _filter_by_month(sample_tasks, next_month)
        # None of our sample tasks are due/done in next month
        assert len(result) == 0

    def test_stats_in_cover(self, sample_tasks, tmp_path):
        """PDF must be larger when there are tasks (cover + task page)."""
        from taskmd.exporters.pdf_exporter import export_pdf
        out_full  = tmp_path / "full.pdf"
        out_empty = tmp_path / "empty.pdf"
        export_pdf(sample_tasks, output_path=out_full)
        export_pdf([], output_path=out_empty)
        assert out_full.stat().st_size > out_empty.stat().st_size


# ─── SVG / PNG Image Exporter ─────────────────────────────────────────────────

class TestImageExporter:

    def test_svg_is_valid_xml(self, sample_tasks, tmp_path):
        from taskmd.exporters.image_exporter import export_svg
        out = tmp_path / "board.svg"
        svg = export_svg(sample_tasks, output_path=out)
        assert svg.strip().startswith("<svg")
        assert "</svg>" in svg

    def test_svg_file_written(self, sample_tasks, tmp_path):
        from taskmd.exporters.image_exporter import export_svg
        out = tmp_path / "board.svg"
        export_svg(sample_tasks, output_path=out)
        assert out.exists()
        assert out.stat().st_size > 500

    def test_svg_contains_header(self, sample_tasks):
        from taskmd.exporters.image_exporter import export_svg
        svg = export_svg(sample_tasks)
        assert "TaskMD Board" in svg

    def test_svg_contains_task_names(self, sample_tasks):
        from taskmd.exporters.image_exporter import export_svg
        svg = export_svg(sample_tasks)
        assert "Overdue report" in svg
        assert "Team standup" in svg

    def test_svg_light_theme(self, sample_tasks):
        from taskmd.exporters.image_exporter import export_svg
        svg = export_svg(sample_tasks, theme="light")
        assert "f0f2f5" in svg   # light page bg

    def test_svg_dark_theme(self, sample_tasks):
        from taskmd.exporters.image_exporter import export_svg
        svg = export_svg(sample_tasks, theme="dark")
        assert "1a1a2e" in svg   # dark page bg

    def test_svg_urgency_accent_colors(self, sample_tasks):
        from taskmd.exporters.image_exporter import export_svg
        svg = export_svg(sample_tasks, theme="light")
        # overdue task → red accent
        assert "e53935" in svg

    def test_svg_three_columns_represented(self, sample_tasks):
        from taskmd.exporters.image_exporter import export_svg
        svg = export_svg(sample_tasks)
        # Column headers
        assert "Todo" in svg
        assert "In Progress" in svg
        assert "Done" in svg

    def test_svg_returns_string(self, sample_tasks):
        from taskmd.exporters.image_exporter import export_svg
        svg = export_svg(sample_tasks)
        assert isinstance(svg, str)

    def test_svg_empty_tasks(self, tmp_path):
        from taskmd.exporters.image_exporter import export_svg
        svg = export_svg([], output_path=tmp_path / "empty.svg")
        assert "<svg" in svg  # should not crash

    @pytest.mark.skipif(not _has_cairosvg(), reason="cairosvg not installed")
    def test_svg_to_png_conversion(self, sample_tasks, tmp_path):
        from taskmd.exporters.image_exporter import export_png
        out = tmp_path / "board.png"
        png = export_png(sample_tasks, output_path=out)
        assert out.read_bytes().startswith(b"\x89PNG")

    @pytest.mark.skipif(not _has_pillow(), reason="Pillow not installed")
    def test_calendar_png(self, sample_tasks, tmp_path):
        from taskmd.exporters.image_exporter import export_png
        out = tmp_path / "cal.png"
        png = export_png(sample_tasks, output_path=out, month=TODAY_STR[:7])
        assert out.read_bytes().startswith(b"\x89PNG")

    def test_svg_task_ids_shown(self, sample_tasks):
        from taskmd.exporters.image_exporter import export_svg
        svg = export_svg(sample_tasks)
        # We display short IDs [01] now
        assert "[01]" in svg
        assert "[02]" in svg

    def test_svg_tags_shown(self, sample_tasks):
        from taskmd.exporters.image_exporter import export_svg
        svg = export_svg(sample_tasks)
        assert "urgent" in svg

    def test_svg_priority_stars(self, sample_tasks):
        from taskmd.exporters.image_exporter import export_svg
        svg = export_svg(sample_tasks)
        assert "★★★" in svg
