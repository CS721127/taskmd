"""
Black-box integration tests for TaskMD.
Tests the system purely through the CLI interface.
"""
import os
import subprocess
import sys
import json
from pathlib import Path
from datetime import date, timedelta

import pytest

import re

# Helper to strip ANSI escape codes
def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# Helper to run the CLI
def run_tm(args, db_path, env=None):
    if env is None:
        env = os.environ.copy()
    env["TASKMD_DB_PATH"] = str(db_path)
    # Ensure src is in PYTHONPATH
    src_path = str(Path(__file__).parent.parent / "src")
    env["PYTHONPATH"] = src_path + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
    
    result = subprocess.run(
        [sys.executable, "-m", "taskmd.cli"] + args,
        capture_output=True,
        text=True,
        env=env
    )
    # Automatically strip ANSI for easier testing
    result.stdout = strip_ansi(result.stdout)
    result.stderr = strip_ansi(result.stderr)
    return result

@pytest.fixture
def clean_db(tmp_path):
    return tmp_path / "tasks.md"

def test_blackbox_workflow(clean_db):
    # 1. Initialize and add tasks via quick capture
    run_tm(["add", "Buy coffee #grocery !3 @today /Life //Shopping"], clean_db)
    run_tm(["add", "Write project proposal /Work //Docs @+1d"], clean_db)
    
    # 2. Check list output contains tasks (short IDs)
    res = run_tm(["list"], clean_db)
    assert "[01]" in res.stdout
    assert "Buy coffee" in res.stdout
    # Tree view separate lines
    assert "Life" in res.stdout
    assert "Shopping" in res.stdout
    
    # 3. Mark task as done
    run_tm(["done", "1"], clean_db)  # Uses short ID shorthand
    res = run_tm(["list"], clean_db)
    assert "[x]" in res.stdout
    
    # 4. Check stats
    res = run_tm(["stats"], clean_db)
    assert "Total tasks" in res.stdout
    assert "Completed" in res.stdout

def test_blackbox_recurring(clean_db):
    # Setup a task with recur: daily that was "done" yesterday
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    content = f"""<!-- taskmd:version=2 -->
<!-- taskmd:last_run={yesterday} -->

# Work
## Daily
- [x] Morning check <!-- id:t_01, recur:daily, done:{yesterday}T09:00:00 -->
"""
    clean_db.write_text(content)
    
    # Run a modifying command, should trigger reset
    res = run_tm(["add", "Trigger reset"], clean_db)
    assert "recurring task(s) reset" in res.stdout
    
    # Verify it's now todo
    res = run_tm(["list"], clean_db)
    assert "[ ] Morning check" in res.stdout

def test_blackbox_clear(clean_db):
    clean_db.write_text("# Test\n- [ ] Task <!-- id:t_01 -->")
    
    # Try clear with full "yes" confirmation
    proc = subprocess.Popen(
        [sys.executable, "-m", "taskmd.cli", "clear"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "TASKMD_DB_PATH": str(clean_db), "PYTHONPATH": str(Path(__file__).parent.parent / "src")}
    )
    stdout, stderr = proc.communicate(input="yes\n")
    
    assert "All tasks cleared" in stdout
    # Verify file is effectively empty of tasks
    content = clean_db.read_text()
    assert "- [ ] Task" not in content

def test_blackbox_export_json_file(clean_db, tmp_path):
    run_tm(["add", "API Test !5"], clean_db)
    out_json = tmp_path / "test.json"
    run_tm(["export", "json", "--output", str(out_json)], clean_db)
    
    data = json.loads(out_json.read_text())
    assert data["tasks"][0]["name"] == "API Test"
    assert data["tasks"][0]["pri"] == 5

def test_blackbox_natural_language_dates(clean_db, tmp_path):
    # Test 'next-mon' logic
    run_tm(["add", "Weekly meeting @next-mon"], clean_db)
    out_json = tmp_path / "test2.json"
    run_tm(["export", "json", "--output", str(out_json)], clean_db)
    
    data = json.loads(out_json.read_text())
    due = data["tasks"][0]["due"]
    assert due is not None
    assert len(due) == 10 # YYYY-MM-DD

def test_blackbox_views_filtering(clean_db):
    # Add tasks with various dates
    run_tm(["add", "Task Overdue @-5d"], clean_db)
    run_tm(["add", "Task Today @today"], clean_db)
    run_tm(["add", "Task Next @+2d"], clean_db)
    run_tm(["add", "Task Future @+10d"], clean_db)
    
    # Test overdue
    res = run_tm(["overdue"], clean_db)
    assert "Task Overdue" in res.stdout
    assert "Task Today" not in res.stdout
    
    # Test today
    res = run_tm(["today"], clean_db)
    assert "Task Today" in res.stdout
    assert "Task Overdue" not in res.stdout # our 'today' command usually excludes overdue?
    # Actually 'today' should probably include overdue tasks that are still relevant or just today's.
    # In my implementation, today means precisely today.
    
    # Test next
    res = run_tm(["next", "3"], clean_db)
    assert "Task Today" in res.stdout
    assert "Task Next" in res.stdout
    assert "Task Future" not in res.stdout

def test_blackbox_sorting(clean_db):
    run_tm(["add", "B-Task !1"], clean_db)
    run_tm(["add", "A-Task !5"], clean_db)
    
    # Sort by priority
    res = run_tm(["list", "--sort", "priority"], clean_db)
    # A-Task (pri 5) should come before B-Task (pri 1)
    a_pos = res.stdout.find("A-Task")
    b_pos = res.stdout.find("B-Task")
    assert a_pos < b_pos
    
    # Sort by name
    res = run_tm(["list", "--sort", "name"], clean_db)
    a_pos = res.stdout.find("A-Task")
    b_pos = res.stdout.find("B-Task")
    assert a_pos < b_pos # A before B alphabetically

def test_blackbox_reload_repair(clean_db):
    # Manually create task without ID
    content = """# Section
- [ ] No ID task
- [ ] Another no ID
"""
    clean_db.write_text(content)
    
    # Reload should assign IDs
    run_tm(["reload"], clean_db)
    
    new_content = clean_db.read_text()
    assert "id:t_01" in new_content
    assert "id:t_02" in new_content
