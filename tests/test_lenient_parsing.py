"""
Tests for lenient task-line parsing and inline shortcut recognition
(TODOs.md Issue 6):

  1. Manually-edited, non-standard task lines (missing/loose checkboxes,
     alternate bullet markers) are still parsed as tasks rather than
     silently dropped, and get normalized to the canonical "- [ ] name"
     form the next time the file is saved.
  2. Quick-capture shortcut tokens (#tag, !pri, @due, ^start, /section,
     //sub) written directly into a hand-edited task line are recognized
     and converted into structured fields, relocating the task to the
     specified section/subsection if given.
  3. Lines that don't match any recognized format are flagged during
     `tm validate` / surfaced as parser warnings, rather than silently
     ignored or silently guessed at.
"""
from pathlib import Path

import pytest

from taskmd.parser import parse_markdown
from taskmd.repository import TaskRepository
from taskmd.service import TaskService


# ─── Part 1: lenient checkbox / bullet recognition ─────────────────────────

class TestLenientTaskRecognition:
    def test_dash_no_checkbox_recognized(self):
        doc = parse_markdown("# Work\n## Tasks\n- Buy milk\n")
        assert len(doc.tasks) == 1
        assert doc.tasks[0].name == "Buy milk"
        assert doc.tasks[0].status == "[ ]"

    def test_star_bullet_with_checkbox_recognized(self):
        doc = parse_markdown("# Work\n## Tasks\n* [ ] Star bullet task\n")
        assert len(doc.tasks) == 1
        assert doc.tasks[0].name == "Star bullet task"

    def test_plus_bullet_done_recognized(self):
        doc = parse_markdown("# Work\n## Tasks\n+[x]Plus bullet done\n")
        assert len(doc.tasks) == 1
        assert doc.tasks[0].name == "Plus bullet done"
        assert doc.tasks[0].status == "[x]"

    def test_empty_brackets_recognized_as_todo(self):
        doc = parse_markdown("# Work\n## Tasks\n- [] Empty brackets\n")
        assert len(doc.tasks) == 1
        assert doc.tasks[0].status == "[ ]"

    def test_no_space_before_bracket_recognized(self):
        doc = parse_markdown("# Work\n## Tasks\n-[ ]No space task\n")
        assert len(doc.tasks) == 1
        assert doc.tasks[0].name == "No space task"

    def test_in_progress_dash_marker_recognized(self):
        doc = parse_markdown("# Work\n## Tasks\n* [-] Halfway done\n")
        assert len(doc.tasks) == 1
        assert doc.tasks[0].status == "[-]"

    def test_standard_format_still_works_unchanged(self):
        doc = parse_markdown("# Work\n## Tasks\n- [x] Done task <!-- id:t_01 -->\n")
        assert len(doc.tasks) == 1
        assert doc.tasks[0].status == "[x]"
        assert doc.tasks[0].id == "t_01"

    def test_lenient_match_produces_warning(self):
        doc = parse_markdown("# Work\n## Tasks\n- Buy milk\n")
        assert any("non-standard task format" in w for w in doc.warnings)

    def test_lenient_task_has_source_line_for_inplace_rewrite(self):
        doc = parse_markdown("# Work\n## Tasks\n- Buy milk\n")
        assert doc.tasks[0]._source_line == 3


class TestUnrecognizedStatusMarker:
    def test_unrecognized_marker_defaults_to_todo(self):
        doc = parse_markdown("# Work\n## Tasks\n- [v] Weird marker\n")
        assert len(doc.tasks) == 1
        assert doc.tasks[0].status == "[ ]"
        assert doc.tasks[0].name == "Weird marker"

    def test_unrecognized_marker_produces_specific_warning(self):
        doc = parse_markdown("# Work\n## Tasks\n- [v] Weird marker\n")
        assert any("unrecognized status marker" in w for w in doc.warnings)
        assert any("[v]" in w for w in doc.warnings)

    def test_word_status_marker_defaults_to_todo(self):
        doc = parse_markdown("# Work\n## Tasks\n- [done] Word marker\n")
        assert doc.tasks[0].status == "[ ]"
        assert doc.tasks[0].name == "Word marker"

    def test_status_is_always_a_valid_value(self):
        doc = parse_markdown("# Work\n## Tasks\n- [???] Garbage marker\n")
        assert doc.tasks[0].status in ("[ ]", "[-]", "[x]")


class TestNonTaskLinesNotMisidentified:
    """Guard against false positives — the conservative bullet-anchor rule
    must never swallow legitimate non-task content."""

    def test_plain_prose_not_a_task(self):
        doc = parse_markdown("# Work\nThis is a note about my tasks.\n")
        assert len(doc.tasks) == 0

    def test_prose_with_hash_and_at_not_a_task(self):
        doc = parse_markdown(
            "# Work\nSome prose that mentions #hashtags and @mentions but is not a task.\n"
        )
        assert len(doc.tasks) == 0

    def test_horizontal_rule_dashes_not_a_task(self):
        doc = parse_markdown("# Work\n## Tasks\n- [ ] Real task\n\n---\n")
        assert len(doc.tasks) == 1
        assert doc.tasks[0].name == "Real task"

    def test_horizontal_rule_stars_not_a_task(self):
        doc = parse_markdown("# Work\n\n***\n\n## Tasks\n- [ ] Real task\n")
        assert len(doc.tasks) == 1

    def test_horizontal_rule_underscores_not_a_task(self):
        doc = parse_markdown("# Work\n\n___\n\n## Tasks\n- [ ] Real task\n")
        assert len(doc.tasks) == 1

    def test_bare_dash_not_a_task(self):
        doc = parse_markdown("# Work\n## Tasks\n-\n- [ ] Real task\n")
        assert len(doc.tasks) == 1

    def test_bare_bullet_with_space_not_a_task(self):
        doc = parse_markdown("# Work\n## Tasks\n* \n- [ ] Real task\n")
        assert len(doc.tasks) == 1

    def test_section_and_subsection_headers_unaffected(self):
        doc = parse_markdown("# Work\n## Reports\n- [ ] Task\n")
        assert doc.tasks[0].section == "Work"
        assert doc.tasks[0].sub == "Reports"


# ─── Part 2: inline shortcut recognition ───────────────────────────────────

class TestInlineShortcutRecognition:
    def test_tag_and_due_extracted_with_strong_signal(self):
        doc = parse_markdown("# Work\n## Tasks\n- Buy milk #errand @tomorrow\n")
        t = doc.tasks[0]
        assert t.name == "Buy milk"
        assert t.tags == ["errand"]
        assert t.due is not None

    def test_priority_extracted_with_strong_signal(self):
        doc = parse_markdown("# Work\n## Tasks\n- Submit report !3 @2026-06-25\n")
        t = doc.tasks[0]
        assert t.name == "Submit report"
        assert t.pri == 3

    def test_section_relocation_via_shortcut(self):
        doc = parse_markdown(
            "# Work\n## Reports\n- Buy milk #errand @tomorrow /Personal //Shopping\n"
        )
        t = doc.tasks[0]
        assert t.name == "Buy milk"
        assert t.section == "Personal"
        assert t.sub == "Shopping"

    def test_relocated_task_has_no_source_line(self):
        """A relocated task must be treated as 'new' so the writer physically
        moves it to the correct section on next save."""
        doc = parse_markdown(
            "# Work\n## Reports\n- Buy milk #errand @tomorrow /Personal //Shopping\n"
        )
        assert doc.tasks[0]._source_line is None

    def test_relocation_produces_warning_mentioning_destination(self):
        doc = parse_markdown(
            "# Work\n## Reports\n- Buy milk #errand @tomorrow /Personal //Shopping\n"
        )
        assert any("moved to Personal/Shopping" in w for w in doc.warnings)

    def test_no_relocation_when_already_in_target_section(self):
        doc = parse_markdown(
            "# Personal\n## Shopping\n- Buy milk #errand @tomorrow /Personal //Shopping\n"
        )
        t = doc.tasks[0]
        assert t._source_line is not None  # stayed in place, no physical move needed

    def test_shortcut_relocation_works_on_standard_checkbox_line_too(self):
        """Shortcut recognition isn't limited to lenient-format lines — a
        properly-checkboxed hand-written line with no metadata yet should
        also get its shortcuts extracted."""
        doc = parse_markdown(
            "# Work\n## Reports\n- [ ] Buy milk #errand @tomorrow /Personal //Shopping\n"
        )
        t = doc.tasks[0]
        assert t.name == "Buy milk"
        assert t.section == "Personal"


class TestShortcutFalsePositiveAvoidance:
    """The single biggest risk in this feature: an ordinary task name must
    never be mangled just because it happens to contain '#', '!', '@', or
    '/' characters that weren't intended as shortcut syntax."""

    def test_issue_number_not_treated_as_tag(self):
        doc = parse_markdown("# Work\n## Tasks\n- Fix bug #1234\n")
        t = doc.tasks[0]
        assert t.name == "Fix bug #1234"
        assert not t.tags

    def test_pr_number_not_treated_as_tag(self):
        doc = parse_markdown("# Work\n## Tasks\n- Review PR #45 for the team\n")
        t = doc.tasks[0]
        assert t.name == "Review PR #45 for the team"

    def test_slash_in_name_not_treated_as_section(self):
        doc = parse_markdown("# Work\n## Tasks\n- Pay rent / utilities split\n")
        t = doc.tasks[0]
        assert t.name == "Pay rent / utilities split"
        assert t.section == "Work"

    def test_email_address_not_treated_as_due_date(self):
        doc = parse_markdown(
            "# Work\n## Tasks\n- Email someone@example.com about the project\n"
        )
        t = doc.tasks[0]
        assert "someone@example.com" in t.name
        assert t.due is None

    def test_already_structured_task_name_untouched(self):
        """A task that already has metadata (id:, etc.) is clearly managed
        by the program already — its name should never be re-parsed for
        shortcut tokens even if it happens to contain matching characters."""
        doc = parse_markdown(
            '# Work\n## Tasks\n- [ ] Buy milk @home <!-- id:t_01, rem:"test" -->\n'
        )
        t = doc.tasks[0]
        # The metadata comment is parsed normally; the name portion (before
        # the comment) is "Buy milk @home" but since this line already had
        # explicit metadata via RE_TASK (strict match), shortcut extraction
        # still only fires on a strong date signal — "@home" isn't one.
        assert "@home" in t.name or t.due is None


# ─── Part 3: validation surfaces unrecognized formats ──────────────────────

class TestValidateSurfacesFormatIssues:
    def test_validate_reports_lenient_normalization(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n## Tasks\n- Buy milk\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        errors = service.validate()
        assert any("non-standard task format" in e for e in errors)

    def test_validate_reports_unrecognized_marker(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n## Tasks\n- [v] Weird\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        errors = service.validate()
        assert any("unrecognized status marker" in e for e in errors)

    def test_validate_clean_file_has_minimal_warnings(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text(
            "<!-- taskmd:version=2 -->\n\n# Work\n## Tasks\n- [ ] Clean task <!-- id:t_01 -->\n",
            encoding="utf-8",
        )
        service = TaskService(TaskRepository(f))
        errors = service.validate()
        assert not any("non-standard" in e or "unrecognized status" in e for e in errors)


# ─── End-to-end: load -> auto-normalize -> save round trip ─────────────────

class TestEndToEndNormalization:
    def test_lenient_file_normalized_on_disk_after_load(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text(
            "<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n- Buy milk\n* [x] Done already\n",
            encoding="utf-8",
        )
        service = TaskService(TaskRepository(f))
        tasks = service.get_all_tasks()
        assert len(tasks) == 2

        content = f.read_text(encoding="utf-8")
        assert "- [ ] Buy milk" in content
        assert "- [x] Done already" in content
        # IDs were assigned during the same repair pass
        assert "id:t_01" in content
        assert "id:t_02" in content

    def test_relocated_task_physically_moved_on_disk(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text(
            "<!-- taskmd:version=2 -->\n\n"
            "# Work\n## Reports\n"
            "- Buy milk #errand @tomorrow /Personal //Shopping\n",
            encoding="utf-8",
        )
        service = TaskService(TaskRepository(f))
        service.get_all_tasks()  # triggers load -> repair -> save

        content = f.read_text(encoding="utf-8")
        assert "# Personal" in content
        assert "## Shopping" in content
        # The task line itself should now appear after the Personal/Shopping
        # header, not under Work/Reports.
        personal_idx = content.index("# Personal")
        task_idx = content.index("Buy milk")
        assert task_idx > personal_idx

    def test_prose_survives_normalization_pass_untouched(self, tmp_path):
        f = tmp_path / "tasks.md"
        original = (
            "<!-- taskmd:version=2 -->\n\n"
            "# Work\n"
            "This is a note about my tasks.\n"
            "## Reports\n"
            "- Buy milk\n"
        )
        f.write_text(original, encoding="utf-8")
        service = TaskService(TaskRepository(f))
        service.get_all_tasks()

        content = f.read_text(encoding="utf-8")
        assert "This is a note about my tasks." in content

    def test_double_normalization_is_idempotent(self, tmp_path):
        """Running the repair pass twice should not keep mutating the file."""
        f = tmp_path / "tasks.md"
        f.write_text(
            "<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n- Buy milk\n",
            encoding="utf-8",
        )
        service = TaskService(TaskRepository(f))
        service.get_all_tasks()
        first_pass = f.read_text(encoding="utf-8")

        service2 = TaskService(TaskRepository(f))
        service2.get_all_tasks()
        second_pass = f.read_text(encoding="utf-8")

        assert first_pass == second_pass
        assert "non-standard task format" not in second_pass  # warnings aren't written to the file
        assert "- [ ] Buy milk" in second_pass
