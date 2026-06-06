"""Shared test fixtures for TaskMD Lite tests."""
import pytest
import tempfile
from pathlib import Path
from taskmd.models import TaskDocument, Task
from taskmd.repository import TaskRepository
from taskmd.service import TaskService
from taskmd.test_data import BASIC_TASKS_MD, COMPLEX_TASKS_MD, MANUAL_EDIT_MD



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
