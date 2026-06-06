"""Parser tests for TaskMD Lite."""
import pytest
import sys
import os

# Allow importing from tests directory
sys.path.insert(0, os.path.dirname(__file__))

from taskmd.parser import parse_markdown
from taskmd.test_data import BASIC_TASKS_MD, COMPLEX_TASKS_MD, MANUAL_EDIT_MD


class TestDocumentMetadata:
    """Test parsing of document-level metadata."""

    def test_parse_version(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        assert doc.version == "2"

    def test_parse_timezone(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        assert doc.timezone == "Australia/Sydney"

    def test_parse_last_run(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        assert doc.last_run == "2026-04-10"

    def test_v1_format_compat(self):
        """Test that taskmd: prefix is also recognized."""
        content = "<!-- taskmd:version=1 -->\n<!-- taskmd:timezone=UTC -->\n"
        doc = parse_markdown(content)
        assert doc.version == "1"
        assert doc.timezone == "UTC"


class TestSectionParsing:
    """Test parsing of sections and subsections."""

    def test_section_assignment(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        sections = {t.section for t in doc.tasks}
        assert "School" in sections
        assert "Research" in sections
        assert "Daily" in sections
        assert "Inbox" in sections

    def test_subsection_assignment(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        subs = {t.sub for t in doc.tasks}
        assert "DPST1092" in subs
        assert "COMP1511" in subs
        assert "FL Project" in subs

    def test_default_subsection(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        inbox_tasks = [t for t in doc.tasks if t.section == "Inbox"]
        # Inbox has no ## header, so sub should default to General
        assert len(inbox_tasks) == 1
        assert inbox_tasks[0].sub == "General"


class TestTaskParsing:
    """Test parsing of individual task lines."""

    def test_task_count(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        assert len(doc.tasks) == 7

    def test_status_todo(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_01")
        assert t.status == "[ ]"

    def test_status_done(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_02")
        assert t.status == "[x]"

    def test_status_in_progress(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_03")
        assert t.status == "[-]"

    def test_task_name(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_01")
        assert t.name == "Prepare tutorial"


class TestMetadataParsing:
    """Test parsing of hidden metadata fields."""

    def test_id(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        ids = [t.id for t in doc.tasks if t.id]
        assert "t_01" in ids
        assert "t_07" in ids

    def test_due(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_01")
        assert t.due == "2026-04-20"

    def test_pri(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_01")
        assert t.pri == 4

    def test_tags(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_01")
        assert t.tags == ["teaching", "course"]

    def test_done_timestamp(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_02")
        assert t.done_ts == "2026-04-10T18:20:00"

    def test_weight(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_02")
        assert t.weight == 10

    def test_rem_quoted(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_04")
        assert t.rem == "Need data"

    def test_course(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_03")
        assert t.course == "COMP1511"

    def test_start_field(self):
        doc = parse_markdown(COMPLEX_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_04")
        assert t.start == "2026-04-12"

    def test_est_field(self):
        doc = parse_markdown(COMPLEX_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_04")
        assert t.est == "50m"

    def test_loc_field(self):
        doc = parse_markdown(COMPLEX_TASKS_MD)
        t = next(t for t in doc.tasks if t.id == "t_04")
        assert t.loc == "K17"

    def test_task_without_metadata(self):
        doc = parse_markdown(COMPLEX_TASKS_MD)
        no_id = [t for t in doc.tasks if not t.id]
        assert len(no_id) == 2  # Two tasks without IDs


class TestDuplicateDetection:
    """Test duplicate ID detection."""

    def test_duplicate_id_warning(self):
        doc = parse_markdown(MANUAL_EDIT_MD)
        assert len(doc.warnings) > 0
        assert any("Duplicate" in w for w in doc.warnings)


class TestRawLines:
    """Test that raw lines are preserved for low-diff writeback."""

    def test_raw_lines_count(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        assert len(doc.raw_lines) > 0

    def test_raw_line_types(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        types = {rl.line_type for rl in doc.raw_lines}
        assert "header_meta" in types
        assert "section" in types
        assert "subsection" in types
        assert "task" in types

    def test_non_task_text_preserved(self):
        doc = parse_markdown(COMPLEX_TASKS_MD)
        text_lines = [rl for rl in doc.raw_lines if rl.line_type == "text"]
        texts = [rl.content.strip() for rl in text_lines if rl.content.strip()]
        assert "This is a note about my tasks." in texts
        assert "Some notes about this course." in texts

    def test_source_line_tracking(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        for task in doc.tasks:
            assert task._source_line is not None
            assert task._source_line > 0
