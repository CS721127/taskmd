"""
Markdown parser for TaskMD Lite.

Parses tasks.md files following the Schema Design specification:
  - Header metadata (<!-- taskmd:key=value --> or <!-- taskmd:key=value -->)
  - Section headers (# ...)
  - Subsection headers (## ...)
  - Task lines (- [ ] / - [-] / - [x])
  - Hidden metadata in HTML comments (<!-- id:..., due:..., ... -->)
  - Non-task text preservation for low-diff writeback

Supports all schema fields:
  Required: id
  Common: due, start, pri, tags, rem, done, created, updated
  Advanced: weight, course, recur, est, loc
"""
import re
from typing import List, Tuple, Dict, Optional
from taskmd.models import Task, TaskDocument, RawLine


# ─── Regex Patterns ───────────────────────────────────────────────────────────

# Document-level metadata: <!-- taskmd:key=value --> or <!-- taskmd:key=value -->
RE_DOC_META = re.compile(
    r'^<!--\s*taskmd(?:-lite)?:([a-zA-Z0-9_]+)=(.+?)\s*-->$'
)

# Section header: # Title
RE_SECTION = re.compile(r'^#\s+(.+)$')

# Subsection header: ## Title
RE_SUBSECTION = re.compile(r'^##\s+(.+)$')

# Task line: optional leading **... or stars, then - [status] name <!-- metadata -->
# Captures: (priority_stars, status_char, task_name, metadata_comment)
RE_TASK = re.compile(
    r'^(\*+)?\s*-\s*\[([ xX\-])\]\s+(.*?)(?:\s+<!--\s+(.+?)\s+-->)?$'
)

# Metadata key:value pairs inside <!-- ... -->
# Supports: key:value  OR  key:"quoted value"
RE_META_PAIR = re.compile(
    r'(\w+):"(.*?)"|(\w+):([^,]+)'
)


# ─── Public API ───────────────────────────────────────────────────────────────

def parse_markdown(content: str) -> TaskDocument:
    """Parse a tasks.md file into a TaskDocument.

    Args:
        content: Raw file content as a string.

    Returns:
        TaskDocument with all tasks, metadata, and raw lines preserved.
    """
    doc = TaskDocument()
    lines = content.splitlines()

    current_section = "Uncategorized"
    current_sub = "General"
    seen_ids: Dict[str, int] = {}  # id -> count for duplicate detection

    for line_num, line in enumerate(lines, start=1):
        line_stripped = line.strip()
        raw = RawLine(content=line, line_number=line_num)

        # Blank line
        if not line_stripped:
            raw.line_type = "blank"
            doc.raw_lines.append(raw)
            continue

        # Document metadata
        m_doc = RE_DOC_META.match(line_stripped)
        if m_doc:
            key, val = m_doc.group(1), m_doc.group(2).strip()
            raw.line_type = "header_meta"
            _apply_doc_meta(doc, key, val)
            doc.raw_lines.append(raw)
            continue

        # Subsection header (must check before section — ## before #)
        m_sub = RE_SUBSECTION.match(line_stripped)
        if m_sub:
            current_sub = m_sub.group(1).strip()
            raw.line_type = "subsection"
            doc.raw_lines.append(raw)
            continue

        # Section header
        m_sec = RE_SECTION.match(line_stripped)
        if m_sec:
            current_section = m_sec.group(1).strip()
            current_sub = "General"
            raw.line_type = "section"
            doc.raw_lines.append(raw)
            continue

        # Task line
        m_task = RE_TASK.match(line_stripped)
        if m_task:
            raw.line_type = "task"
            task = _parse_task_match(m_task, current_section, current_sub, line_num)

            # Duplicate ID tracking
            if task.id:
                seen_ids[task.id] = seen_ids.get(task.id, 0) + 1
                if seen_ids[task.id] > 1:
                    doc.warnings.append(
                        f"Duplicate ID '{task.id}' at line {line_num} "
                        f"(seen {seen_ids[task.id]} times)"
                    )

            doc.tasks.append(task)
            doc.raw_lines.append(raw)
            continue

        # Everything else is preserved text
        raw.line_type = "text"
        doc.raw_lines.append(raw)

    return doc


# ─── Internal Helpers ─────────────────────────────────────────────────────────

def _apply_doc_meta(doc: TaskDocument, key: str, val: str):
    """Apply a document-level metadata key to the TaskDocument."""
    if key == "version":
        doc.version = val
    elif key == "timezone":
        doc.timezone = val
    elif key == "last_run":
        doc.last_run = val
    elif key == "profile":
        doc.profile = val


def _parse_task_match(
    match: re.Match,
    section: str,
    sub: str,
    line_num: int,
) -> Task:
    """Parse a regex match into a Task object."""
    pri_str, status_char, name, meta_str = match.groups()

    # Normalize status
    status_char = status_char if status_char else " "
    if status_char in ("x", "X"):
        status_char = "x"
    status = f"[{status_char}]"

    task = Task(
        name=name.strip(),
        section=section,
        sub=sub,
        status=status,
        _source_line=line_num,
    )

    # Star-prefix priority (e.g. *** - [ ] task)
    if pri_str:
        task.pri = len(pri_str)

    # Parse hidden metadata
    if meta_str:
        _parse_metadata_into_task(task, meta_str)

    return task


def _parse_metadata_into_task(task: Task, meta_str: str):
    """Parse the metadata comment string and populate task fields.

    The metadata format is: key1:val1, key2:val2, key3:"quoted val"
    Commas INSIDE tag values (tags:a,b,c) are distinguished from
    pair separators by splitting on ', ' (comma followed by space)
    since tag values use commas without trailing spaces.
    """
    # Split on ", " to get individual key:value pairs
    # This correctly handles tags:teaching,course because there's no space after the comma
    raw_pairs = _split_metadata(meta_str)

    for pair in raw_pairs:
        pair = pair.strip()
        if ':' not in pair:
            continue

        key, _, val = pair.partition(':')
        key = key.strip()
        val = val.strip()

        # Remove surrounding quotes if present
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]

        if key == "id":
            task.id = val
        elif key == "due":
            task.due = val
        elif key == "start":
            task.start = val
        elif key == "pri":
            try:
                task.pri = int(val)
            except ValueError:
                pass
        elif key == "tags":
            task.tags = [t.strip() for t in val.split(",") if t.strip()]
        elif key == "rem":
            task.rem = val
        elif key == "done":
            task.done_ts = val
        elif key == "created":
            task.created = val
        elif key == "updated":
            task.updated = val
        elif key == "weight":
            try:
                task.weight = int(val)
            except ValueError:
                pass
        elif key == "course":
            task.course = val
        elif key == "recur":
            task.recur = val
        elif key == "est":
            task.est = val
        elif key == "loc":
            task.loc = val


def _split_metadata(meta_str: str) -> list:
    """Split metadata string into key:value pairs.

    Handles:
      - Simple: id:t_01, due:2026-04-20
      - Quoted values: rem:"Hello, world"
      - Comma-containing values: tags:a,b,c
    """
    pairs = []
    current = []
    in_quotes = False

    i = 0
    while i < len(meta_str):
        ch = meta_str[i]

        if ch == '"':
            in_quotes = not in_quotes
            current.append(ch)
        elif ch == ',' and not in_quotes:
            # Check if this comma is followed by a space and then a key:
            # If so, it's a pair separator. Otherwise it's within a value.
            rest = meta_str[i+1:]
            # Look ahead: if after optional spaces we find word:, it's a separator
            m = re.match(r'\s+(\w+):', rest)
            if m:
                pairs.append(''.join(current))
                current = []
                i += 1
                continue
            else:
                current.append(ch)
        else:
            current.append(ch)

        i += 1

    if current:
        pairs.append(''.join(current))

    return pairs
