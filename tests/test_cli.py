"""CLI integration tests for TaskMD Lite."""
import pytest
import subprocess
import sys
from pathlib import Path


@pytest.fixture
def cli_env(tmp_path):
    """Set up environment for CLI tests."""
    task_file = tmp_path / "tasks.md"
    task_file.write_text("""\
<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->

# School
## DPST1092
- [ ] Test task one <!-- id:t_01, due:2026-04-20, pri:3 -->
- [x] Done task <!-- id:t_02, done:2026-04-10T18:00:00 -->

# Inbox
- [ ] Buy stuff <!-- id:t_03, tags:shopping -->
""", encoding="utf-8")

    config_dir = tmp_path / "config"
    config_dir.mkdir()

    return {
        "task_file": task_file,
        "tmp_path": tmp_path,
        "env": {
            "TASKMD_DB_PATH": str(task_file),
        },
    }


def run_tm(args: list, env_overrides: dict = None):
    """Run the tm CLI as a subprocess."""
    import os
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    result = subprocess.run(
        [sys.executable, "-m", "taskmd.cli"] + args,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    return result


class TestCLICommands:
    """Test CLI commands via subprocess."""

    def test_help(self, cli_env):
        result = run_tm(["help"], cli_env["env"])
        assert result.returncode == 0
        assert "Task Operations" in result.stdout

    def test_validate(self, cli_env):
        result = run_tm(["validate"], cli_env["env"])
        assert "Validation" in result.stdout or "OK" in result.stdout

    def test_stats(self, cli_env):
        result = run_tm(["stats"], cli_env["env"])
        assert "Total" in result.stdout or "total" in result.stdout.lower()

    def test_add_inline(self, cli_env):
        result = run_tm(
            ["add", "New test task", "-s", "Inbox"],
            cli_env["env"],
        )
        assert "OK" in result.stdout or "added" in result.stdout.lower()

        # Verify task was added
        content = cli_env["task_file"].read_text()
        assert "New test task" in content

    def test_done(self, cli_env):
        result = run_tm(["done", "t_01"], cli_env["env"])
        assert "OK" in result.stdout or "completed" in result.stdout.lower()

        content = cli_env["task_file"].read_text()
        assert "[x] Test task one" in content

    def test_todo(self, cli_env):
        result = run_tm(["todo", "t_02"], cli_env["env"])
        assert "OK" in result.stdout

    def test_rm(self, cli_env):
        result = run_tm(["rm", "t_03"], cli_env["env"])
        assert "OK" in result.stdout

        content = cli_env["task_file"].read_text()
        assert "Buy stuff" not in content

    def test_due(self, cli_env):
        result = run_tm(["due", "t_01", "2026-05-01"], cli_env["env"])
        assert "OK" in result.stdout

        content = cli_env["task_file"].read_text()
        assert "2026-05-01" in content

    def test_due_invalid(self, cli_env):
        result = run_tm(["due", "t_01", "not-a-date"], cli_env["env"])
        assert "Invalid" in result.stdout

    def test_rem(self, cli_env):
        result = run_tm(["rem", "t_01", "Important note"], cli_env["env"])
        assert "OK" in result.stdout

    def test_pri(self, cli_env):
        result = run_tm(["pri", "t_01", "5"], cli_env["env"])
        assert "OK" in result.stdout

    def test_edit(self, cli_env):
        result = run_tm(["edit", "t_01", "Renamed task"], cli_env["env"])
        assert "OK" in result.stdout

        content = cli_env["task_file"].read_text()
        assert "Renamed task" in content

    def test_tag_add(self, cli_env):
        result = run_tm(["tag", "t_01", "add", "urgent"], cli_env["env"])
        assert "OK" in result.stdout

    def test_not_found(self, cli_env):
        result = run_tm(["done", "t_99"], cli_env["env"])
        assert "not found" in result.stdout.lower()

    def test_search(self, cli_env):
        result = run_tm(["search", "task"], cli_env["env"])
        # Should find "Test task one"
        assert "result" in result.stdout.lower() or "task" in result.stdout.lower()

    def test_config_show(self, cli_env):
        result = run_tm(["config", "show"], cli_env["env"])
        assert "CONFIG" in result.stdout or "Task file" in result.stdout

    def test_doctor(self, cli_env):
        result = run_tm(["doctor"], cli_env["env"])
        assert "DOCTOR" in result.stdout or "Python" in result.stdout
