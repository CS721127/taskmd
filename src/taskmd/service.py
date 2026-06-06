"""
Task service layer for TaskMD Lite.

Provides all business logic for task operations:
  - CRUD: add, edit, remove, status changes, move
  - Metadata: due, start, rem, pri, tags
  - Queries: today, next, overdue, search, filter
  - Stats: completion counts, rates
  - Auto-timestamps: created, updated, done_ts
  - ID management: auto-assign, duplicate repair
  - Validation: structural checks
  - Archive: move completed tasks to archive
  - Daily reset: recurring daily task reset
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path

from taskmd.models import Task, TaskDocument
from taskmd.repository import TaskRepository
from taskmd.exceptions import TaskNotFoundError, ValidationError


class TaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    # ─── Helpers ──────────────────────────────────────────────────────────

    def _now_iso(self) -> str:
        """Return current datetime as ISO 8601 string."""
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def _today_str(self) -> str:
        """Return today's date as YYYY-MM-DD."""
        return datetime.now().strftime("%Y-%m-%d")

    def _find_task(self, doc: TaskDocument, task_id: str) -> Optional[Task]:
        """Find a task by ID, supporting both full ID and numeric shorthand."""
        for task in doc.tasks:
            if task.id == task_id:
                return task
        # Try numeric shorthand: "3" -> "t_03"
        if task_id.isdigit():
            target = f"t_{int(task_id):02d}"
            for task in doc.tasks:
                if task.id == target:
                    return task
        return None

    def _get_max_id(self, doc: TaskDocument) -> int:
        """Find the highest numeric task ID."""
        max_id = 0
        for task in doc.tasks:
            if task.id and task.id.startswith("t_"):
                try:
                    num = int(task.id[2:])
                    max_id = max(max_id, num)
                except ValueError:
                    pass
        return max_id

    # ─── ID Management ───────────────────────────────────────────────────

    def _repair_ids(self, doc: TaskDocument) -> bool:
        """Assign IDs to tasks without them and fix duplicate IDs.

        Returns True if any changes were made.
        """
        max_id = self._get_max_id(doc)
        seen = {}
        changed = False

        for task in doc.tasks:
            # Assign missing IDs
            if not task.id:
                max_id += 1
                task.id = f"t_{max_id:02d}"
                changed = True
                continue

            # Fix duplicate IDs
            if task.id in seen:
                old_id = task.id
                max_id += 1
                task.id = f"t_{max_id:02d}"
                doc.warnings.append(
                    f"Duplicate ID '{old_id}' resolved -> '{task.id}'"
                )
                changed = True
            else:
                seen[task.id] = True

        return changed

    # ─── Read Operations ─────────────────────────────────────────────────

    def get_all_tasks(self) -> List[Task]:
        """Load all tasks, repairing IDs as needed."""
        doc = self.repo.load()
        if self._repair_ids(doc):
            self.repo.save(doc)
        return doc.tasks

    def get_today(self) -> List[Task]:
        """Return tasks due today or in attention window (start <= today < due), incomplete only."""
        today = self._today_str()
        tasks = self.get_all_tasks()
        result = []
        for t in tasks:
            if t.status == "[x]":
                continue
            if t.due == today:
                result.append(t)
                continue
            # In attention window: start_date <= today and no due, or due is in the future
            if t.start and t.start <= today:
                if not t.due or t.due > today:
                    result.append(t)
        return result

    def get_next(self, days: int = 7) -> List[Task]:
        """Return incomplete tasks due within the next N days."""
        today = datetime.now().date()
        end = today + timedelta(days=days)
        tasks = self.get_all_tasks()
        result = []
        for t in tasks:
            if t.status == "[x]" or not t.due:
                continue
            try:
                due_date = datetime.strptime(t.due, "%Y-%m-%d").date()
                if today <= due_date <= end:
                    result.append(t)
            except ValueError:
                continue
        result.sort(key=lambda t: t.due)
        return result

    def get_overdue(self) -> List[Task]:
        """Return incomplete tasks past their due date."""
        today = self._today_str()
        tasks = self.get_all_tasks()
        result = []
        for t in tasks:
            if t.status == "[x]" or not t.due:
                continue
            if t.due < today:
                result.append(t)
        result.sort(key=lambda t: t.due)
        return result

    def get_stats(self) -> Dict[str, any]:
        """Return task statistics."""
        tasks = self.get_all_tasks()
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == "[x]")
        in_progress = sum(1 for t in tasks if t.status == "[-]")
        todo = sum(1 for t in tasks if t.status == "[ ]")
        overdue = len(self.get_overdue())
        today_str = self._today_str()
        today_count = sum(1 for t in tasks if t.due == today_str and t.status != "[x]")

        # Completed today (by done_ts date)
        completed_today = sum(
            1 for t in tasks
            if t.status == "[x]" and t.done_ts and t.done_ts[:10] == today_str
        )

        # Urgency breakdown
        from taskmd.ui.heatmap import get_urgency_level, URGENCY_OVERDUE, URGENCY_DUE_TODAY, URGENCY_DUE_SOON, URGENCY_IN_ATTENTION
        urgent = sum(
            1 for t in tasks
            if t.status != "[x]" and get_urgency_level(t) in (
                URGENCY_OVERDUE, URGENCY_DUE_TODAY, URGENCY_DUE_SOON
            )
        )
        in_attention = sum(
            1 for t in tasks
            if t.status != "[x]" and get_urgency_level(t) == URGENCY_IN_ATTENTION
        )

        return {
            "total": total,
            "done": done,
            "in_progress": in_progress,
            "todo": todo,
            "overdue": overdue,
            "due_today": today_count,
            "completed_today": completed_today,
            "urgent": urgent,
            "in_attention": in_attention,
            "completion_rate": f"{done / total * 100:.1f}%" if total > 0 else "0.0%",
        }

    def search(self, keyword: str) -> List[Task]:
        """Search tasks by keyword in name, tags, section, subsection, or remark."""
        keyword_lower = keyword.lower()
        tasks = self.get_all_tasks()
        return [
            t for t in tasks
            if keyword_lower in t.name.lower()
            or keyword_lower in t.section.lower()
            or keyword_lower in t.sub.lower()
            or (t.rem and keyword_lower in t.rem.lower())
            or (t.tags and any(keyword_lower in tag.lower() for tag in t.tags))
            or (t.course and keyword_lower in t.course.lower())
        ]

    def filter_tasks(
        self,
        status: Optional[str] = None,
        section: Optional[str] = None,
        tags: Optional[List[str]] = None,
        due_before: Optional[str] = None,
        due_after: Optional[str] = None,
    ) -> List[Task]:
        """Filter tasks by multiple criteria."""
        tasks = self.get_all_tasks()
        result = tasks

        if status:
            result = [t for t in result if t.status == status]

        if section:
            section_lower = section.lower()
            result = [
                t for t in result
                if t.section.lower() == section_lower
                or t.sub.lower() == section_lower
            ]

        if tags:
            tag_set = {tag.lower() for tag in tags}
            result = [
                t for t in result
                if t.tags and tag_set.intersection(tag.lower() for tag in t.tags)
            ]

        if due_before:
            result = [t for t in result if t.due and t.due <= due_before]

        if due_after:
            result = [t for t in result if t.due and t.due >= due_after]

        return result

    # ─── Write Operations ────────────────────────────────────────────────

    def add_task(
        self,
        name: str,
        section: str = "Uncategorized",
        sub: str = "General",
        due: Optional[str] = None,
        start: Optional[str] = None,
        pri: Optional[int] = None,
        tags: Optional[List[str]] = None,
        rem: Optional[str] = None,
        course: Optional[str] = None,
        recur: Optional[str] = None,
        weight: Optional[int] = None,
    ):
        """Add a new task with auto-generated ID and timestamps."""
        doc = self.repo.load()
        self._repair_ids(doc)

        max_id = self._get_max_id(doc)
        new_id = f"t_{max_id + 1:02d}"

        task = Task(
            name=name,
            section=section,
            sub=sub,
            id=new_id,
            due=due,
            start=start,
            pri=pri,
            tags=tags,
            rem=rem,
            course=course,
            recur=recur,
            weight=weight,
            created=self._now_iso(),
        )

        doc.tasks.append(task)
        self.repo.save(doc)
        return task

    def change_status(self, task_id: str, new_status: str):
        """Change task status: [ ], [-], [x]."""
        doc = self.repo.load()
        task = self._find_task(doc, task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        task.status = new_status
        task.updated = self._now_iso()

        # Auto-set done timestamp
        if new_status == "[x]":
            task.done_ts = self._now_iso()
        elif task.done_ts and new_status != "[x]":
            task.done_ts = None  # Clear if un-done

        self.repo.save(doc)

    def set_metadata(self, task_id: str, field_name: str, value):
        """Set a metadata field on a task."""
        doc = self.repo.load()
        task = self._find_task(doc, task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        if field_name == "due":
            task.due = value
        elif field_name == "start":
            task.start = value
        elif field_name == "rem":
            task.rem = value
        elif field_name == "pri":
            try:
                task.pri = int(value)
            except (ValueError, TypeError):
                pass
        elif field_name == "name":
            task.name = value
        elif field_name == "course":
            task.course = value
        elif field_name == "weight":
            try:
                task.weight = int(value)
            except (ValueError, TypeError):
                pass
        elif field_name == "recur":
            task.recur = value
        elif field_name == "est":
            task.est = value
        elif field_name == "loc":
            task.loc = value

        task.updated = self._now_iso()
        self.repo.save(doc)

    def set_tags(self, task_id: str, action: str, tag: str):
        """Add or remove a tag from a task.

        Args:
            task_id: The task ID.
            action: 'add' or 'rm'.
            tag: The tag to add or remove.
        """
        doc = self.repo.load()
        task = self._find_task(doc, task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        if task.tags is None:
            task.tags = []

        tag = tag.strip().lower()

        if action == "add":
            if tag not in task.tags:
                task.tags.append(tag)
        elif action == "rm":
            task.tags = [t for t in task.tags if t != tag]
            if not task.tags:
                task.tags = None

        task.updated = self._now_iso()
        self.repo.save(doc)

    def move_task(self, task_id: str, section: str = None, sub: str = None):
        """Move a task to a different section/subsection."""
        doc = self.repo.load()
        task = self._find_task(doc, task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        if section:
            task.section = section
        if sub:
            task.sub = sub

        # Moving means we need a new source line (no longer at original position)
        task._source_line = None
        task.updated = self._now_iso()
        self.repo.save(doc)

    def remove_task(self, task_id: str):
        """Remove a task by ID."""
        doc = self.repo.load()
        original_length = len(doc.tasks)
        task = self._find_task(doc, task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        doc.tasks = [t for t in doc.tasks if t is not task]
        if len(doc.tasks) < original_length:
            self.repo.save(doc)

    def remove_done(self):
        """Remove all completed tasks."""
        doc = self.repo.load()
        before = len(doc.tasks)
        doc.tasks = [t for t in doc.tasks if t.status != "[x]"]
        removed = before - len(doc.tasks)
        if removed == 0:
            return 0
        self.repo.save(doc)
        return removed

    def clear_all(self):
        """Remove all tasks from the document."""
        doc = self.repo.load()
        doc.tasks = []
        self.repo.save(doc)

    def edit_name(self, task_id: str, new_name: str):
        """Edit a task's name."""
        self.set_metadata(task_id, "name", new_name)

    # ─── Archive ─────────────────────────────────────────────────────────

    def archive_done(self, archive_path: Path = None) -> int:
        """Move all completed tasks to the archive file.

        Returns the number of tasks archived.
        """
        doc = self.repo.load()
        done_tasks = [t for t in doc.tasks if t.status == "[x]"]
        if not done_tasks:
            return 0

        # Append to archive file
        if archive_path is None:
            from taskmd.paths import get_archive_file
            archive_path = get_archive_file()

        archive_lines = []
        if archive_path.exists():
            archive_lines = archive_path.read_text(encoding="utf-8").splitlines()
        else:
            archive_lines = [
                "<!-- taskmd:archive -->",
                "",
                "# Archived Tasks",
                "",
            ]

        # Add timestamp header
        date_str = self._today_str()
        archive_lines.append(f"## Archived on {date_str}")
        for task in done_tasks:
            from taskmd.writer import _format_task_line
            archive_lines.append(_format_task_line(task))
        archive_lines.append("")

        archive_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path.write_text("\n".join(archive_lines) + "\n", encoding="utf-8")

        # Remove from main doc
        doc.tasks = [t for t in doc.tasks if t.status != "[x]"]
        self.repo.save(doc)
        return len(done_tasks)

    # ─── Migration ───────────────────────────────────────────────────────

    def migrate_txt_to_md(self, txt_path: Path) -> int:
        """Migrate a legacy TXT task list to the new Markdown format.
        
        It attempts to parse lines like:
        [x] Task name
        [-] In progress task
        [ ] Todo task
        Plain task name
        """
        if not txt_path.exists():
            raise FileNotFoundError(f"Legacy TXT file not found: {txt_path}")

        lines = txt_path.read_text(encoding="utf-8").splitlines()
        migrated_count = 0
        doc = self.repo.load()
        self._repair_ids(doc)
        max_id = self._get_max_id(doc)

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Determine status
            status = "[ ]"
            if line.startswith("[x]") or line.startswith("[X]"):
                status = "[x]"
                line = line[3:].strip()
            elif line.startswith("[-]"):
                status = "[-]"
                line = line[3:].strip()
            elif line.startswith("[ ]"):
                status = "[ ]"
                line = line[3:].strip()

            if not line:
                continue
            
            # Create task
            max_id += 1
            new_id = f"t_{max_id:02d}"
            
            from taskmd.models import Task
            task = Task(
                name=line,
                section="Migrated",
                sub="Legacy",
                id=new_id,
                created=self._now_iso(),
                status=status
            )
            if status == "[x]":
                task.done_ts = self._now_iso()
                
            doc.tasks.append(task)
            migrated_count += 1
            
        if migrated_count > 0:
            self.repo.save(doc)
            
        return migrated_count


    # ─── Validation ──────────────────────────────────────────────────────

    def validate(self) -> List[str]:
        """Validate the task file for structural correctness.

        Returns a list of warning/error messages.
        """
        doc = self.repo.load()
        errors = []

        # Check for parsing warnings (duplicate IDs, etc.)
        errors.extend(doc.warnings)

        # Check for tasks without IDs
        no_id = [t for t in doc.tasks if not t.id]
        if no_id:
            errors.append(f"{len(no_id)} task(s) have no ID assigned")

        # Check for invalid date formats and logic
        import re
        from datetime import datetime
        # Allow YYYY-MM-DD or YYYY-MM-DD HH:MM
        date_re = re.compile(r'^\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?$')
        today = datetime.now()

        for task in doc.tasks:
            # Date format checks
            if task.due and not date_re.match(task.due):
                errors.append(f"Task {task.id}: invalid due date format '{task.due}'")
            if task.start and not date_re.match(task.start):
                errors.append(f"Task {task.id}: invalid start date format '{task.start}'")
            
            # Logic: start <= due
            if task.start and task.due and date_re.match(task.start) and date_re.match(task.due):
                try:
                    s_fmt = "%Y-%m-%d %H:%M" if " " in task.start else "%Y-%m-%d"
                    d_fmt = "%Y-%m-%d %H:%M" if " " in task.due else "%Y-%m-%d"
                    s_dt = datetime.strptime(task.start, s_fmt)
                    d_dt = datetime.strptime(task.due, d_fmt)
                    if s_dt > d_dt:
                        errors.append(f"Task {task.id}: start date ({task.start}) is after due date ({task.due})")
                except ValueError:
                    pass

            # Logic: done_ts not in future
            if task.done_ts:
                try:
                    done_dt = datetime.fromisoformat(task.done_ts)
                    if done_dt > today:
                        errors.append(f"Task {task.id}: done timestamp is in the future")
                except ValueError:
                    errors.append(f"Task {task.id}: invalid done timestamp format '{task.done_ts}'")

            # Priority range
            if task.pri is not None and (task.pri < 0 or task.pri > 5):
                errors.append(f"Task {task.id}: priority {task.pri} is outside valid range (0-5)")

            # Recur validity
            if task.recur:
                from taskmd.recurrence import parse_recur
                if not parse_recur(task.recur):
                    errors.append(f"Task {task.id}: invalid recur format '{task.recur}'")

            # Empty names
            if not task.name or not task.name.strip():
                errors.append(f"Task {task.id}: empty task name")

        # Orphan sections (Check if all sections from headers actually have tasks)
        # Assuming sections are in doc.raw_lines as section objects or derived from tasks
        # The parser preserves section/sub for each Task object.
        # If a header has no tasks follow it, the parser might not create a Task object for it.
        # But we can check doc.raw_lines.
        sections_with_tasks = set((t.section, t.sub) for t in doc.tasks)
        # This is a bit complex as raw_lines contains the headers.
        # For now, focus on task-level validation.

        return errors

    # ─── Recurring Tasks ──────────────────────────────────────────────────

    def check_recurring_tasks(self):
        """Check if any tasks need to be reset/regenerated for a new cycle.

        Returns tuple of (needs_action: bool, task_count: int).
        """
        doc = self.repo.load()
        self._repair_ids(doc)

        today_dt = datetime.now().date()
        today_str = self._today_str()
        
        if doc.last_run == today_str:
            return False, 0
        
        # Parse last_run
        try:
            last_run_dt = datetime.strptime(doc.last_run, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            # If never run or invalid, assume yesterday so it triggers today
            last_run_dt = today_dt - timedelta(days=1)

        from taskmd.recurrence import parse_recur, should_trigger
        
        tasks_to_reset = []
        for task in doc.tasks:
            # 1. Traditional 'Daily' section reset
            if task.section.lower() == "daily" and task.status != "[ ]":
                tasks_to_reset.append(task)
                continue
            
            # 2. Modern 'recur' metadata reset
            if task.recur:
                spec = parse_recur(task.recur)
                if spec and should_trigger(spec, last_run_dt, today_dt):
                    if task.status != "[ ]":
                        tasks_to_reset.append(task)

        is_needed = len(tasks_to_reset) > 0 or doc.last_run != today_str
        return is_needed, len(tasks_to_reset)

    def apply_recurring_tasks(self):
        """Perform reset on all tasks that hit their recurring cycle."""
        doc = self.repo.load()
        today_dt = datetime.now().date()
        today_str = self._today_str()

        try:
            last_run_dt = datetime.strptime(doc.last_run, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            last_run_dt = today_dt - timedelta(days=1)

        from taskmd.recurrence import parse_recur, should_trigger, get_next_due
        
        for task in doc.tasks:
            triggered = False
            # Check Daily section
            if task.section.lower() == "daily":
                triggered = True
            # Check recur metadata
            elif task.recur:
                spec = parse_recur(task.recur)
                if spec and should_trigger(spec, last_run_dt, today_dt):
                    triggered = True
                    # Optionally update due date if it has one
                    if task.due:
                        try:
                            current_due = datetime.strptime(task.due[:10], "%Y-%m-%d").date()
                            next_due = get_next_due(spec, current_due)
                            task.due = next_due.isoformat()
                        except ValueError:
                            pass

            if triggered:
                task.status = "[ ]"
                task.done_ts = None
                task.updated = self._now_iso()

        doc.last_run = today_str
        self.repo.save(doc)

    def skip_recurring_reset(self):
        """Skip the cycle reset but update last_run to today."""
        doc = self.repo.load()
        doc.last_run = self._today_str()
        self.repo.save(doc)
