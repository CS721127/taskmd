"""Shared test fixtures for TaskMD Lite tests."""
import pytest
import tempfile
from pathlib import Path
from taskmd.models import TaskDocument, Task
from taskmd.repository import TaskRepository
from taskmd.service import TaskService


BASIC_TASKS_MD = """\
<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->
<!-- taskmd:last_run=2026-04-10 -->

# School
## DPST1092
- [ ] Prepare tutorial <!-- id:t_01, due:2026-04-20, pri:4, tags:teaching,course -->
- [x] Submit lab solution <!-- id:t_02, due:2026-04-10, done:2026-04-10T18:20:00, pri:5, weight:10 -->

## COMP1511
- [-] Write assignment <!-- id:t_03, due:2026-04-15, pri:3, course:COMP1511 -->

# Research
## FL Project
- [ ] Draft experiment notes <!-- id:t_04, due:2026-04-16, pri:3, tags:research,fl, rem:"Need data" -->

# Daily
## Routine
- [x] Morning exercise <!-- id:t_05 -->
- [ ] Review tasks <!-- id:t_06 -->

# Inbox
- [ ] Buy adapter for monitor <!-- id:t_07, tags:shopping -->
"""

COMPLEX_TASKS_MD = """\
<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->

This is a note about my tasks.

# School
## DPST1092

Some notes about this course.

- [ ] Task without ID
- [ ] Prepare tutorial <!-- id:t_01, due:2026-04-20, pri:4 -->
- [x] Submit lab <!-- id:t_02, done:2026-04-10T18:20:00 -->

## COMP1511
- [ ] Another task without ID

# Research
## FL Project
- [ ] Draft notes <!-- id:t_04, start:2026-04-12, est:50m, loc:K17 -->
"""

MANUAL_EDIT_MD = """\
<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->

# School
## DPST1092
- [ ] Original task <!-- id:t_01 -->
- [ ] Duplicate ID task <!-- id:t_01 -->
- [ ] Task with no ID
- [x] Completed task <!-- id:t_03 -->
"""


@pytest.fixture
def tmp_task_file(tmp_path):
    """Create a temporary task file with basic content."""
    task_file = tmp_path / "tasks.md"
    task_file.write_text(BASIC_TASKS_MD, encoding="utf-8")
    return task_file


@pytest.fixture
def complex_task_file(tmp_path):
    """Create a temporary task file with complex content."""
    task_file = tmp_path / "tasks.md"
    task_file.write_text(COMPLEX_TASKS_MD, encoding="utf-8")
    return task_file


@pytest.fixture
def manual_edit_file(tmp_path):
    """Create a task file simulating manual edits."""
    task_file = tmp_path / "tasks.md"
    task_file.write_text(MANUAL_EDIT_MD, encoding="utf-8")
    return task_file


@pytest.fixture
def repo(tmp_task_file):
    """Create a TaskRepository with the basic task file."""
    return TaskRepository(tmp_task_file)


@pytest.fixture
def service(repo):
    """Create a TaskService with the basic task file."""
    return TaskService(repo)


@pytest.fixture
def empty_service(tmp_path):
    """Create a TaskService with an empty task file."""
    task_file = tmp_path / "tasks.md"
    repo = TaskRepository(task_file)
    return TaskService(repo)
