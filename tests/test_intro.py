"""
Tests for the `tm intro` command (TODOs.md Issue 10):
  - Describes what the project does, author, version info
  - Is read-only (doesn't trigger recurring-task side effects / file creation)
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


def run_tm(args, env_overrides):
    env = os.environ.copy()
    src_path = str(Path(__file__).parent.parent / "src")
    env["PYTHONPATH"] = src_path + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "taskmd.cli"] + args,
        capture_output=True, text=True, env=env, timeout=10,
    )


class TestIntroCommand:
    def test_intro_runs_successfully(self, tmp_path):
        env = {"TASKMD_DB_PATH": str(tmp_path / "tasks.md")}
        result = run_tm(["intro"], env)
        assert result.returncode == 0

    def test_intro_mentions_project_name(self, tmp_path):
        env = {"TASKMD_DB_PATH": str(tmp_path / "tasks.md")}
        result = run_tm(["intro"], env)
        assert "TaskMD" in result.stdout

    def test_intro_mentions_version(self, tmp_path):
        from taskmd import __version__
        env = {"TASKMD_DB_PATH": str(tmp_path / "tasks.md")}
        result = run_tm(["intro"], env)
        assert __version__ in result.stdout

    def test_intro_mentions_authors(self, tmp_path):
        env = {"TASKMD_DB_PATH": str(tmp_path / "tasks.md")}
        result = run_tm(["intro"], env)
        assert "Authors" in result.stdout

    def test_intro_mentions_license(self, tmp_path):
        env = {"TASKMD_DB_PATH": str(tmp_path / "tasks.md")}
        result = run_tm(["intro"], env)
        assert "License" in result.stdout
        assert "MIT" in result.stdout

    def test_intro_does_not_create_task_file(self, tmp_path):
        """Intro is a read-only/informational command and shouldn't have the
        side effect of creating the task file (consistent with doctor/help)."""
        task_file = tmp_path / "tasks.md"
        env = {"TASKMD_DB_PATH": str(task_file)}
        assert not task_file.exists()
        result = run_tm(["intro"], env)
        assert result.returncode == 0
        assert not task_file.exists()

    def test_intro_listed_in_help(self, tmp_path):
        env = {"TASKMD_DB_PATH": str(tmp_path / "tasks.md")}
        result = run_tm(["help"], env)
        assert "tm intro" in result.stdout
