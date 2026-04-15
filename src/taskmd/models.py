"""
Core data models for TaskMD Lite.

Defines all entities as per Schema Design doc §5:
  - Task: single task with full metadata
  - TaskDocument: the parsed representation of tasks.md
  - RawLine: preserves original file lines for low-diff writeback
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class RawLine:
    """Preserves an original line from the file for low-diff writeback."""
    content: str
    line_number: int
    line_type: str = "text"  # "text", "header_meta", "section", "subsection", "task", "blank"


@dataclass
class Task:
    """A single task entry.

    Fields follow Schema Design §5:
      Required: id
      Common Optional: due, start, pri, tags, rem, done_ts, created, updated
      Advanced: weight, course, recur, est, loc
    """
    name: str
    section: str = "Uncategorized"
    sub: str = "General"
    status: str = "[ ]"
    id: Optional[str] = None

    # Common optional fields
    due: Optional[str] = None
    start: Optional[str] = None
    pri: Optional[int] = None
    tags: Optional[List[str]] = None
    rem: Optional[str] = None
    done_ts: Optional[str] = None      # completion timestamp
    created: Optional[str] = None
    updated: Optional[str] = None

    # Advanced fields
    weight: Optional[int] = None
    course: Optional[str] = None
    recur: Optional[str] = None
    est: Optional[str] = None
    loc: Optional[str] = None

    # Internal tracking for low-diff writeback
    _source_line: Optional[int] = field(default=None, repr=False, compare=False)


@dataclass
class TaskDocument:
    """Represents the full parsed tasks.md file."""
    version: str = "2"
    timezone: str = "Australia/Sydney"
    last_run: str = "1970-01-01"
    profile: str = "default"
    tasks: List[Task] = field(default_factory=list)

    # Preserved raw lines for low-diff writeback
    raw_lines: List[RawLine] = field(default_factory=list, repr=False, compare=False)
    # Track warnings found during parsing
    warnings: List[str] = field(default_factory=list, repr=False, compare=False)
