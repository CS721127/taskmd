"""
Tests for tag-based listing, filtering, and search (TODOs.md Issue 8):
  - TaskService.get_all_tags() / get_tasks_by_tag()
  - TaskService.filter_tasks(tags=...) and date-precision-safe due filters
  - CLI: `tm tags`, `tm tags <name>`, `tm list --tag <name>`
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


# ─── Service-layer tests ────────────────────────────────────────────────────

class TestServiceTags:
    def test_get_all_tags_counts(self, tmp_path):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService

        content = (
            "<!-- taskmd:version=2 -->\n\n"
            "# Work\n## Tasks\n"
            "- [ ] Task A <!-- id:t_01, tags:work,urgent -->\n"
            "- [ ] Task B <!-- id:t_02, tags:work -->\n"
            "- [ ] Task C <!-- id:t_03, tags:home -->\n"
        )
        f = tmp_path / "tasks.md"
        f.write_text(content, encoding="utf-8")
        svc = TaskService(TaskRepository(f))
        tags = svc.get_all_tags()
        assert tags["work"] == 2
        assert tags["urgent"] == 1
        assert tags["home"] == 1

    def test_get_all_tags_empty_when_no_tags(self, tmp_path):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService

        content = (
            "<!-- taskmd:version=2 -->\n\n"
            "# Work\n## Tasks\n"
            "- [ ] Task A <!-- id:t_01 -->\n"
        )
        f = tmp_path / "tasks.md"
        f.write_text(content, encoding="utf-8")
        svc = TaskService(TaskRepository(f))
        assert svc.get_all_tags() == {}

    def test_get_tasks_by_tag_case_insensitive(self, tmp_path):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService

        content = (
            "<!-- taskmd:version=2 -->\n\n"
            "# Work\n## Tasks\n"
            "- [ ] Task A <!-- id:t_01, tags:Work -->\n"
            "- [ ] Task B <!-- id:t_02, tags:home -->\n"
        )
        f = tmp_path / "tasks.md"
        f.write_text(content, encoding="utf-8")
        svc = TaskService(TaskRepository(f))
        matches = svc.get_tasks_by_tag("work")
        assert len(matches) == 1
        assert matches[0].name == "Task A"

    def test_get_tasks_by_tag_no_match(self, tmp_path):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService

        content = (
            "<!-- taskmd:version=2 -->\n\n"
            "# Work\n## Tasks\n"
            "- [ ] Task A <!-- id:t_01, tags:work -->\n"
        )
        f = tmp_path / "tasks.md"
        f.write_text(content, encoding="utf-8")
        svc = TaskService(TaskRepository(f))
        assert svc.get_tasks_by_tag("nonexistent") == []

    def test_filter_tasks_due_before_handles_precise_due(self, tmp_path):
        from taskmd.repository import TaskRepository
        from taskmd.service import TaskService

        content = (
            "<!-- taskmd:version=2 -->\n\n"
            "# Work\n## Tasks\n"
            "- [ ] Task A <!-- id:t_01, due:2026-06-20 14:30 -->\n"
            "- [ ] Task B <!-- id:t_02, due:2026-06-30 -->\n"
        )
        f = tmp_path / "tasks.md"
        f.write_text(content, encoding="utf-8")
        svc = TaskService(TaskRepository(f))
        result = svc.filter_tasks(due_before="2026-06-25")
        names = [t.name for t in result]
        assert "Task A" in names
        assert "Task B" not in names


# ─── CLI integration tests ──────────────────────────────────────────────────

def run_tm(args, env_overrides):
    env = os.environ.copy()
    src_path = str(Path(__file__).parent.parent / "src")
    env["PYTHONPATH"] = src_path + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "taskmd.cli"] + args,
        capture_output=True, text=True, env=env, timeout=10,
    )


@pytest.fixture
def tag_env(tmp_path):
    task_file = tmp_path / "tasks.md"
    task_file.write_text(
        "<!-- taskmd:version=2 -->\n\n"
        "# Work\n## Tasks\n"
        "- [ ] Write report <!-- id:t_01, tags:work,urgent -->\n"
        "- [ ] Buy milk <!-- id:t_02, tags:errand -->\n"
        "- [ ] Plan trip <!-- id:t_03, tags:work,fun -->\n",
        encoding="utf-8",
    )
    return {"TASKMD_DB_PATH": str(task_file)}


class TestTagsCLI:
    def test_tags_summary_lists_all_tags(self, tag_env):
        result = run_tm(["tags"], tag_env)
        assert result.returncode == 0
        assert "work" in result.stdout
        assert "urgent" in result.stdout
        assert "errand" in result.stdout
        assert "fun" in result.stdout

    def test_tags_with_name_filters_tasks(self, tag_env):
        result = run_tm(["tags", "work"], tag_env)
        assert result.returncode == 0
        assert "Write report" in result.stdout
        assert "Plan trip" in result.stdout
        assert "Buy milk" not in result.stdout

    def test_tags_unknown_tag_reports_no_matches(self, tag_env):
        result = run_tm(["tags", "doesnotexist"], tag_env)
        assert result.returncode == 0
        assert "No tasks tagged" in result.stdout

    def test_list_tag_filter(self, tag_env):
        result = run_tm(["list", "--tag", "errand"], tag_env)
        assert result.returncode == 0
        assert "Buy milk" in result.stdout
        assert "Write report" not in result.stdout
