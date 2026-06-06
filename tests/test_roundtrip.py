"""Round-trip tests for TaskMD Lite.

Verifies that parse -> write -> parse produces semantically identical results.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from taskmd.parser import parse_markdown
from taskmd.writer import write_markdown
from taskmd.test_data import BASIC_TASKS_MD, COMPLEX_TASKS_MD


def _tasks_are_equivalent(tasks_a, tasks_b) -> bool:
    """Check if two task lists are semantically equivalent."""
    if len(tasks_a) != len(tasks_b):
        return False

    for a, b in zip(tasks_a, tasks_b):
        if a.name != b.name:
            return False
        if a.id != b.id:
            return False
        if a.status != b.status:
            return False
        if a.section != b.section:
            return False
        if a.sub != b.sub:
            return False
        if a.due != b.due:
            return False
        if a.start != b.start:
            return False
        if a.pri != b.pri:
            return False
        if a.rem != b.rem:
            return False
        if a.done_ts != b.done_ts:
            return False
        if a.weight != b.weight:
            return False
        if a.course != b.course:
            return False
        if a.recur != b.recur:
            return False
        if a.est != b.est:
            return False
        if a.loc != b.loc:
            return False
        # Compare tags (order matters)
        if (a.tags or []) != (b.tags or []):
            return False

    return True


class TestRoundTrip:
    """Test that parse -> write -> parse produces equivalent results."""

    def test_basic_roundtrip(self):
        """parse(write(parse(content))) should be semantically equivalent to parse(content)."""
        doc_1 = parse_markdown(BASIC_TASKS_MD)
        output = write_markdown(doc_1)
        doc_2 = parse_markdown(output)

        assert len(doc_1.tasks) == len(doc_2.tasks)
        assert _tasks_are_equivalent(doc_1.tasks, doc_2.tasks)

    def test_complex_roundtrip(self):
        """Complex file with notes should survive roundtrip."""
        doc_1 = parse_markdown(COMPLEX_TASKS_MD)
        output = write_markdown(doc_1)
        doc_2 = parse_markdown(output)

        # Task count should match (ignoring tasks without IDs which get same treatment)
        assert len(doc_1.tasks) == len(doc_2.tasks)

    def test_double_roundtrip(self):
        """Two roundtrips should produce identical output."""
        doc_1 = parse_markdown(BASIC_TASKS_MD)
        output_1 = write_markdown(doc_1)
        doc_2 = parse_markdown(output_1)
        output_2 = write_markdown(doc_2)

        # After first roundtrip, subsequent roundtrips should be stable
        assert output_1 == output_2

    def test_metadata_preserved(self):
        """All metadata fields should survive roundtrip."""
        doc = parse_markdown(BASIC_TASKS_MD)
        output = write_markdown(doc)
        doc_2 = parse_markdown(output)

        # Check specific tasks
        t1_orig = next(t for t in doc.tasks if t.id == "t_01")
        t1_rt = next(t for t in doc_2.tasks if t.id == "t_01")
        assert t1_orig.due == t1_rt.due
        assert t1_orig.pri == t1_rt.pri
        assert t1_orig.tags == t1_rt.tags

    def test_doc_metadata_preserved(self):
        """Document-level metadata should survive roundtrip."""
        doc = parse_markdown(BASIC_TASKS_MD)
        output = write_markdown(doc)
        doc_2 = parse_markdown(output)

        assert doc.version == doc_2.version
        assert doc.timezone == doc_2.timezone
        assert doc.last_run == doc_2.last_run

    def test_status_preserved(self):
        """Task statuses should survive roundtrip."""
        doc = parse_markdown(BASIC_TASKS_MD)
        output = write_markdown(doc)
        doc_2 = parse_markdown(output)

        statuses_orig = {t.id: t.status for t in doc.tasks if t.id}
        statuses_rt = {t.id: t.status for t in doc_2.tasks if t.id}
        assert statuses_orig == statuses_rt

    def test_modification_roundtrip(self):
        """Modify a task, write, re-parse: changes should persist."""
        doc = parse_markdown(BASIC_TASKS_MD)

        # Modify task t_01
        t = next(t for t in doc.tasks if t.id == "t_01")
        t.status = "[x]"
        t.done_ts = "2026-04-13T12:00:00"
        t.name = "Prepare tutorial (edited)"

        output = write_markdown(doc)
        doc_2 = parse_markdown(output)

        t2 = next(t for t in doc_2.tasks if t.id == "t_01")
        assert t2.status == "[x]"
        assert t2.done_ts == "2026-04-13T12:00:00"
        assert t2.name == "Prepare tutorial (edited)"

    def test_non_task_text_survives(self):
        """Non-task markdown text should survive roundtrip."""
        doc = parse_markdown(COMPLEX_TASKS_MD)
        output = write_markdown(doc)

        assert "This is a note about my tasks." in output
        assert "Some notes about this course." in output
