"""
Custom exceptions for TaskMD Lite.
"""


class TaskMDError(Exception):
    """Base exception for all TaskMD errors."""
    pass


class TaskNotFoundError(TaskMDError):
    """Raised when a task with the given ID cannot be found."""
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id}")


class DuplicateIDError(TaskMDError):
    """Raised when duplicate task IDs are detected."""
    def __init__(self, task_id: str, count: int = 2):
        self.task_id = task_id
        self.count = count
        super().__init__(f"Duplicate ID '{task_id}' found {count} times")


class ParseError(TaskMDError):
    """Raised when the task file cannot be parsed correctly."""
    def __init__(self, message: str, line_number: int = None):
        self.line_number = line_number
        if line_number is not None:
            message = f"Line {line_number}: {message}"
        super().__init__(message)


class ConfigError(TaskMDError):
    """Raised when configuration is invalid or cannot be loaded."""
    pass


class ValidationError(TaskMDError):
    """Raised when task data fails validation checks."""
    def __init__(self, errors: list = None):
        self.errors = errors or []
        msg = f"{len(self.errors)} validation error(s)"
        if self.errors:
            msg += ": " + "; ".join(self.errors[:3])
            if len(self.errors) > 3:
                msg += f" ... and {len(self.errors) - 3} more"
        super().__init__(msg)
