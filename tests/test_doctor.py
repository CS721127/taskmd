"""
Tests for the expanded `tm doctor` command (TODOs.md Issue 9):
  - Covers all optional dependency groups with install hints
  - Reports export_dir and permission checks
  - Reports task file health
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


@pytest.fixture
def doctor_env(tmp_path):
    task_file = tmp_path / "tasks.md"
    task_file.write_text(
        "<!-- taskmd:version=2 -->\n\n# Work\n## Tasks\n- [ ] Task A <!-- id:t_01 -->\n",
        encoding="utf-8",
    )
    return {"TASKMD_DB_PATH": str(task_file)}


class TestDoctorCommand:
    def test_doctor_runs_successfully(self, doctor_env):
        result = run_tm(["doctor"], doctor_env)
        assert result.returncode == 0

    def test_doctor_reports_system_section(self, doctor_env):
        result = run_tm(["doctor"], doctor_env)
        assert "System" in result.stdout
        assert "Python" in result.stdout
        assert "Platform" in result.stdout

    def test_doctor_reports_dependency_groups(self, doctor_env):
        result = run_tm(["doctor"], doctor_env)
        assert "Dependencies" in result.stdout
        assert "rich" in result.stdout
        assert "watchdog" in result.stdout
        assert "icalendar" in result.stdout
        assert "fpdf2" in result.stdout
        assert "cairosvg" in result.stdout
        assert "Pillow" in result.stdout

    def test_doctor_reports_install_hints_for_missing_deps(self, doctor_env):
        result = run_tm(["doctor"], doctor_env)
        # Whether or not deps are installed in this environment, taskmd should
        # always mention how to install them as a group.
        assert "taskmd[ui]" in result.stdout or "taskmd[export]" in result.stdout

    def test_doctor_reports_export_dir(self, doctor_env):
        result = run_tm(["doctor"], doctor_env)
        assert "Export dir" in result.stdout

    def test_doctor_reports_permissions_section(self, doctor_env):
        result = run_tm(["doctor"], doctor_env)
        assert "Permissions" in result.stdout
        assert "writable" in result.stdout

    def test_doctor_reports_task_file_health(self, doctor_env):
        result = run_tm(["doctor"], doctor_env)
        assert "Task File Health" in result.stdout
        assert "Tasks loaded" in result.stdout

    def test_doctor_handles_missing_task_file_gracefully(self, tmp_path):
        env = {"TASKMD_DB_PATH": str(tmp_path / "does_not_exist.md")}
        result = run_tm(["doctor"], env)
        assert result.returncode == 0
        assert "NOT FOUND" in result.stdout or "No task file yet" in result.stdout
