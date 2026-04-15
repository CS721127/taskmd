"""Service layer tests for TaskMD Lite."""
import pytest
from datetime import datetime, timedelta
from taskmd.service import TaskService
from taskmd.repository import TaskRepository
from taskmd.exceptions import TaskNotFoundError


class TestAddTask:
    """Test task creation."""

    def test_add_basic(self, service):
        task = service.add_task("New task")
        assert task.name == "New task"
        assert task.id is not None
        assert task.id.startswith("t_")

    def test_add_with_metadata(self, service):
        task = service.add_task(
            "Tagged task",
            section="Research",
            sub="FL",
            due="2026-04-20",
            pri=3,
            tags=["test", "research"],
            rem="A remark",
        )
        assert task.due == "2026-04-20"
        assert task.pri == 3
        assert task.tags == ["test", "research"]
        assert task.rem == "A remark"

    def test_add_sets_created_timestamp(self, service):
        task = service.add_task("Timestamped task")
        assert task.created is not None

    def test_add_increments_id(self, service):
        t1 = service.add_task("First")
        t2 = service.add_task("Second")
        id1 = int(t1.id.split("_")[1])
        id2 = int(t2.id.split("_")[1])
        assert id2 > id1

    def test_add_to_empty(self, empty_service):
        task = empty_service.add_task("First ever task")
        assert task.id == "t_01"


class TestStatusChanges:
    """Test status change operations."""

    def test_done(self, service):
        service.change_status("t_01", "[x]")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.status == "[x]"

    def test_done_sets_timestamp(self, service):
        service.change_status("t_01", "[x]")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.done_ts is not None

    def test_half(self, service):
        service.change_status("t_01", "[-]")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.status == "[-]"

    def test_todo_clears_done_ts(self, service):
        service.change_status("t_01", "[x]")
        service.change_status("t_01", "[ ]")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.status == "[ ]"
        assert t.done_ts is None

    def test_sets_updated(self, service):
        service.change_status("t_01", "[x]")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.updated is not None

    def test_not_found_raises(self, service):
        with pytest.raises(TaskNotFoundError):
            service.change_status("t_99", "[x]")

    def test_numeric_shorthand(self, service):
        """Test that numeric ID like '1' resolves to 't_01'."""
        service.change_status("1", "[x]")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.status == "[x]"


class TestMetadata:
    """Test metadata modification."""

    def test_set_due(self, service):
        service.set_metadata("t_01", "due", "2026-05-01")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.due == "2026-05-01"

    def test_set_start(self, service):
        service.set_metadata("t_01", "start", "2026-04-15")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.start == "2026-04-15"

    def test_set_rem(self, service):
        service.set_metadata("t_01", "rem", "Updated remark")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.rem == "Updated remark"

    def test_set_pri(self, service):
        service.set_metadata("t_01", "pri", 5)
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.pri == 5

    def test_set_name(self, service):
        service.edit_name("t_01", "Renamed task")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.name == "Renamed task"


class TestTags:
    """Test tag management."""

    def test_add_tag(self, service):
        service.set_tags("t_01", "add", "newtag")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert "newtag" in t.tags

    def test_remove_tag(self, service):
        service.set_tags("t_01", "rm", "teaching")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.tags is None or "teaching" not in t.tags

    def test_add_tag_no_duplicates(self, service):
        service.set_tags("t_01", "add", "teaching")  # Already exists
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.tags.count("teaching") == 1

    def test_add_tag_to_untagged(self, service):
        service.set_tags("t_05", "add", "exercise")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_05")
        assert t.tags == ["exercise"]


class TestMoveTask:
    """Test moving tasks across sections."""

    def test_move_section(self, service):
        service.move_task("t_01", section="Research")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.section == "Research"

    def test_move_sub(self, service):
        service.move_task("t_01", sub="COMP1511")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.sub == "COMP1511"

    def test_move_both(self, service):
        service.move_task("t_01", section="Research", sub="FL Project")
        tasks = service.get_all_tasks()
        t = next(t for t in tasks if t.id == "t_01")
        assert t.section == "Research"
        assert t.sub == "FL Project"


class TestRemove:
    """Test task removal."""

    def test_remove_task(self, service):
        service.remove_task("t_07")
        tasks = service.get_all_tasks()
        ids = [t.id for t in tasks]
        assert "t_07" not in ids

    def test_remove_not_found(self, service):
        with pytest.raises(TaskNotFoundError):
            service.remove_task("t_99")

    def test_remove_done(self, service):
        count = service.remove_done()
        tasks = service.get_all_tasks()
        done = [t for t in tasks if t.status == "[x]"]
        assert len(done) == 0
        assert count > 0


class TestQueries:
    """Test query/view methods."""

    def test_get_all(self, service):
        tasks = service.get_all_tasks()
        assert len(tasks) == 7

    def test_search_by_name(self, service):
        results = service.search("tutorial")
        assert len(results) >= 1
        assert any("tutorial" in t.name.lower() for t in results)

    def test_search_by_tag(self, service):
        results = service.search("shopping")
        assert len(results) >= 1

    def test_search_by_course(self, service):
        results = service.search("COMP1511")
        assert len(results) >= 1

    def test_search_no_results(self, service):
        results = service.search("nonexistent_xyz")
        assert len(results) == 0

    def test_filter_by_status(self, service):
        done = service.filter_tasks(status="[x]")
        assert all(t.status == "[x]" for t in done)

    def test_filter_by_section(self, service):
        school = service.filter_tasks(section="School")
        assert all(t.section == "School" for t in school)

    def test_filter_by_tags(self, service):
        research = service.filter_tasks(tags=["research"])
        assert len(research) >= 1


class TestStats:
    """Test statistics."""

    def test_stats_structure(self, service):
        stats = service.get_stats()
        assert "total" in stats
        assert "done" in stats
        assert "in_progress" in stats
        assert "todo" in stats
        assert "overdue" in stats
        assert "completion_rate" in stats

    def test_stats_total(self, service):
        stats = service.get_stats()
        assert stats["total"] == 7


class TestIDRepair:
    """Test ID assignment and duplicate repair."""

    def test_assign_missing_ids(self, tmp_path):
        from conftest import COMPLEX_TASKS_MD
        task_file = tmp_path / "tasks.md"
        task_file.write_text(COMPLEX_TASKS_MD, encoding="utf-8")
        repo = TaskRepository(task_file)
        service = TaskService(repo)

        tasks = service.get_all_tasks()
        for task in tasks:
            assert task.id is not None

    def test_fix_duplicate_ids(self, manual_edit_file):
        repo = TaskRepository(manual_edit_file)
        service = TaskService(repo)

        tasks = service.get_all_tasks()
        ids = [t.id for t in tasks]
        assert len(ids) == len(set(ids)), "All IDs should be unique after repair"


class TestValidation:
    """Test file validation."""

    def test_valid_file(self, service):
        errors = service.validate()
        # Basic file should have no errors
        assert isinstance(errors, list)

    def test_invalid_dates_detected(self, tmp_path):
        content = """\
<!-- taskmd:version=2 -->
# Test
## General
- [ ] Bad date <!-- id:t_01, due:not-a-date -->
"""
        task_file = tmp_path / "tasks.md"
        task_file.write_text(content, encoding="utf-8")
        repo = TaskRepository(task_file)
        service = TaskService(repo)
        errors = service.validate()
        assert any("invalid due date" in e for e in errors)


class TestArchive:
    """Test task archiving."""

    def test_archive_done(self, service, tmp_path):
        archive_file = tmp_path / "archive.md"
        count = service.archive_done(archive_file)
        assert count > 0
        assert archive_file.exists()

        # Check main file no longer has done tasks
        tasks = service.get_all_tasks()
        done = [t for t in tasks if t.status == "[x]"]
        assert len(done) == 0

    def test_archive_none_done(self, service, tmp_path):
        # Remove all done tasks first
        service.remove_done()
        archive_file = tmp_path / "archive.md"
        count = service.archive_done(archive_file)
        assert count == 0
