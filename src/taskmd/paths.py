"""
Paths resolution for TaskMD Lite.

Provides default locations for:
  - Config directory and file
  - Task file
  - Backup directory
  - Archive file

Respects XDG_CONFIG_HOME on Linux/macOS.
"""
import os
import sys
from pathlib import Path


def get_config_dir() -> Path:
    """Return the TaskMD config directory, creating it if needed."""
    if sys.platform == "win32":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))

    config_dir = base / "taskmd"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    """Return path to the TOML config file."""
    return get_config_dir() / "config.toml"


def get_default_task_file() -> Path:
    """Return path to the default tasks.md file, creating it if needed."""
    config_dir = get_config_dir()
    task_file = config_dir / "tasks.md"

    if not task_file.exists():
        task_file.write_text(
            "<!-- taskmd:version=2 -->\n"
            "<!-- taskmd:timezone=Australia/Sydney -->\n"
            "\n"
            "# Inbox\n"
            "## General\n"
            "- [ ] My First Task\n",
            encoding="utf-8",
        )

    return task_file


def get_backup_dir() -> Path:
    """Return path to the backup directory, creating it if needed."""
    backup_dir = get_config_dir() / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def get_archive_file() -> Path:
    """Return path to the archive file."""
    return get_config_dir() / "archive.md"
