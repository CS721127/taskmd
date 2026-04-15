"""
File repository for TaskMD Lite.

Handles:
  - Loading and saving the task file via parser/writer
  - Atomic writes (write to .tmp then rename)
  - Automatic backup before destructive writes
  - File modification time tracking for live reload groundwork
"""
import shutil
from datetime import datetime
from pathlib import Path

from taskmd.models import TaskDocument
from taskmd.parser import parse_markdown
from taskmd.writer import write_markdown
from taskmd.paths import get_backup_dir
from taskmd.exceptions import TaskMDError


class TaskRepository:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._last_mtime: float = 0.0

    def load(self) -> TaskDocument:
        """Load and parse the task file.

        Returns:
            TaskDocument with all tasks and raw lines.
        """
        if not self.file_path.exists():
            return TaskDocument()

        content = self.file_path.read_text(encoding="utf-8")
        self._last_mtime = self.file_path.stat().st_mtime
        return parse_markdown(content)

    def save(self, doc: TaskDocument, backup: bool = True):
        """Save the task document back to file.

        Args:
            doc: The TaskDocument to write.
            backup: If True, create a backup before writing.
        """
        if backup and self.file_path.exists():
            self._create_backup()

        content = write_markdown(doc)
        tmp_path = self.file_path.with_suffix('.tmp')

        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_text(content, encoding="utf-8")
            tmp_path.replace(self.file_path)
            self._last_mtime = self.file_path.stat().st_mtime
        except OSError as e:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise TaskMDError(f"Failed to save tasks: {e}")

    def mtime(self) -> float:
        """Return the modification time of the task file."""
        if self.file_path.exists():
            return self.file_path.stat().st_mtime
        return 0.0

    def has_changed(self) -> bool:
        """Check if the file has been modified since last load."""
        return self.mtime() > self._last_mtime

    def _create_backup(self):
        """Create a timestamped backup of the current task file."""
        try:
            backup_dir = get_backup_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"tasks_{timestamp}.md"
            backup_path = backup_dir / backup_name
            shutil.copy2(self.file_path, backup_path)

            # Keep only last 20 backups
            backups = sorted(backup_dir.glob("tasks_*.md"), reverse=True)
            for old in backups[20:]:
                try:
                    old.unlink()
                except OSError:
                    pass
        except OSError:
            pass  # Don't fail the save if backup fails
