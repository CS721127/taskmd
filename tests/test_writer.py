"""Writer tests for TaskMD Lite."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from taskmd.parser import parse_markdown
from taskmd.writer import write_markdown, _format_task_line
from taskmd.models import Task, TaskDocument
from taskmd.test_data import BASIC_TASKS_MD, COMPLEX_TASKS_MD


class TestFullRegeneration:
    """Test full file regeneration for new documents."""

    def test_empty_document(self):
        doc = TaskDocument()
        output = write_markdown(doc)
        assert "taskmd:version=2" in output
        assert "taskmd:timezone=" in output

    def test_basic_structure(self):
        doc = TaskDocument()
        doc.tasks.append(Task(
            name="Test task", id="t_01", section="School", sub="General",
        ))
        output = write_markdown(doc)
        assert "# School" in output
        assert "## General" in output
        assert "- [ ] Test task <!-- id:t_01 -->" in output

    def test_all_metadata_fields(self):
        doc = TaskDocument()
        doc.tasks.append(Task(
            name="Full task",
            id="t_01",
            due="2026-04-20",
            start="2026-04-15",
            pri=4,
            tags=["research", "fl"],
            rem="Some note",
            done_ts="2026-04-10T18:20:00",
            created="2026-04-01",
            updated="2026-04-05",
            weight=20,
            course="COMP1511",
            recur="daily",
            est="50m",
            loc="K17",
        ))
        output = write_markdown(doc)
        assert "id:t_01" in output
        assert "due:2026-04-20" in output
        assert "start:2026-04-15" in output
        assert "pri:4" in output
        assert "tags:research,fl" in output
        assert 'rem:"Some note"' in output
        assert "done:2026-04-10T18:20:00" in output
        assert "weight:20" in output
        assert "course:COMP1511" in output
        assert "recur:daily" in output
        assert "est:50m" in output
        assert "loc:K17" in output


class TestLowDiffWriteback:
    """Test low-diff writeback mode."""

    def test_preserves_section_order(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        output = write_markdown(doc)
        school_pos = output.index("# School")
        research_pos = output.index("# Research")
        daily_pos = output.index("# Daily")
        assert school_pos < research_pos < daily_pos

    def test_preserves_blank_lines(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        output = write_markdown(doc)
        # Original has blank line after header metadata
        lines = output.splitlines()
        # There should be blank lines in the output
        blank_count = sum(1 for l in lines if not l.strip())
        assert blank_count > 0

    def test_preserves_non_task_text(self):
        doc = parse_markdown(COMPLEX_TASKS_MD)
        output = write_markdown(doc)
        assert "This is a note about my tasks." in output
        assert "Some notes about this course." in output

    def test_task_modification_reflected(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        # Mark a task as done
        for task in doc.tasks:
            if task.id == "t_01":
                task.status = "[x]"
                task.done_ts = "2026-04-13T10:00:00"
                break
        output = write_markdown(doc)
        assert "[x] Prepare tutorial" in output
        assert "done:2026-04-13T10:00:00" in output

    def test_task_removal_reflected(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        original_count = len(doc.tasks)
        doc.tasks = [t for t in doc.tasks if t.id != "t_07"]
        output = write_markdown(doc)
        assert "Buy adapter" not in output

    def test_new_task_appended(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        doc.tasks.append(Task(
            name="Brand new task",
            id="t_99",
            section="Inbox",
            sub="General",
        ))
        output = write_markdown(doc)
        assert "Brand new task" in output
        assert "t_99" in output

    def test_header_metadata_updated(self):
        doc = parse_markdown(BASIC_TASKS_MD)
        doc.last_run = "2026-04-13"
        output = write_markdown(doc)
        assert "2026-04-13" in output


class TestFormatTaskLine:
    """Test the task line formatter."""

    def test_minimal_task(self):
        task = Task(name="Simple task", id="t_01")
        line = _format_task_line(task)
        assert line == "- [ ] Simple task <!-- id:t_01 -->"

    def test_done_task(self):
        task = Task(name="Done task", id="t_01", status="[x]")
        line = _format_task_line(task)
        assert "- [x] Done task" in line

    def test_in_progress_task(self):
        task = Task(name="WIP", id="t_01", status="[-]")
        line = _format_task_line(task)
        assert "- [-] WIP" in line

    def test_no_metadata_no_comment(self):
        task = Task(name="Bare task")
        line = _format_task_line(task)
        assert line == "- [ ] Bare task"
        assert "<!--" not in line
