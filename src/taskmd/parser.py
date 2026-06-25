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

# ─── Lenient task patterns (TODOs.md Issue 6) ─────────────────────────────────
# Real-world hand edits don't always use the exact "- [ ] " form. These patterns
# recognize the same intent more forgivingly so a manually-edited file is never
# silently dropped from the task list — the next write-back then normalizes
# the line to the canonical "- [ ] name <!-- meta -->" form automatically.

# Bullet marker (-, *, or +) with an OPTIONAL checkbox whose content may be
# tightly spaced or simply absent (e.g. "- Buy milk", "* [ ] Buy milk",
# "-[ ]Buy milk", "- [] Buy milk"). Requires a bullet marker as the anchor so
# plain prose notes (no leading bullet at all) are never mistaken for tasks.
RE_TASK_LENIENT = re.compile(
    r'^(\*+)?\s*[-*+]\s*(?:\[([ xX\-]?)\])?\s*(.*?)(?:\s*<!--\s*(.+?)\s*-->)?$'
)

# Bullet + brackets that ARE present but whose inner content isn't one of the
# four recognized status markers (e.g. "- [v] Done", "- [done] Thing").
# Used to flag a specific, actionable validation warning instead of silently
# absorbing the bracket text into the task name.
RE_TASK_SUSPICIOUS_CHECKBOX = re.compile(
    r'^(\*+)?\s*[-*+]\s*\[([^\]]*)\]\s*(.*?)(?:\s*<!--\s*(.+?)\s*-->)?$'
)
_VALID_STATUS_MARKERS = {" ", "x", "X", "-", ""}

# Markdown horizontal rules (---, ***, ___, with optional spaces, 3+ chars)
# must never be mistaken for a lenient task line — they're a common section
# divider, including in this very project's own TODOs.md.
RE_HORIZONTAL_RULE = re.compile(r'^([-*_])\s*(?:\1\s*){2,}$')

# Metadata key:value pairs inside <!-- ... -->
# Supports: key:value  OR  key:"quoted value"
RE_META_PAIR = re.compile(
    r'(\w+):"(.*?)"|(\w+):([^,]+)'
)

# Used only to decide whether a hand-written task NAME is confidently using
# quick-capture shortcut syntax (TODOs.md Issue 6, part 2) — see
# `_has_strong_shortcut_signal` below. These mirror the @/^ token regexes in
# quick_capture.py but are duplicated here (rather than imported) to keep
# this module's only coupling to quick_capture.py at the single call site
# that performs the actual extraction.
_RE_SHORTCUT_DUE = re.compile(r'@([\w+\-]+(?:T\d{2}:\d{2})?)')
_RE_SHORTCUT_START = re.compile(r'\^([\w+\-]+(?:T\d{2}:\d{2})?)')


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

        # Markdown horizontal rule (---, ***, ___) — never a task, regardless
        # of how permissive the lenient patterns below are.
        if RE_HORIZONTAL_RULE.match(line_stripped):
            raw.line_type = "text"
            doc.raw_lines.append(raw)
            continue

        # Task line — try strict format first, then lenient fallbacks so a
        # manually-edited file is never silently dropped from the task list
        # (TODOs.md Issue 6, part 1).
        m_task = RE_TASK.match(line_stripped)
        if m_task:
            raw.line_type = "task"
            task = _parse_task_match(m_task, current_section, current_sub, line_num)
            _register_task(doc, task, line_num, seen_ids)
            relocated = _apply_shortcut_tokens(task, line_num, doc)
            if relocated:
                task._source_line = None  # treat as a new task to be physically moved
            doc.raw_lines.append(raw)
            continue

        # Bullet present with brackets, but the marker inside isn't one of
        # the four recognized status characters (e.g. "- [v] Done").
        # Still parse it (defaulting to todo) but flag it during validation
        # rather than silently swallowing the bracket text into the name.
        m_suspicious = RE_TASK_SUSPICIOUS_CHECKBOX.match(line_stripped)
        if m_suspicious and m_suspicious.group(2) not in _VALID_STATUS_MARKERS and m_suspicious.group(3).strip():
            raw.line_type = "task"
            task = _parse_task_match(m_suspicious, current_section, current_sub, line_num)
            doc.warnings.append(
                f"Line {line_num}: unrecognized status marker '[{m_suspicious.group(2)}]' "
                f"in task '{task.name}' — treated as not-started ('[ ]'); "
                f"use ' ', 'x'/'X', or '-' inside the brackets"
            )
            _register_task(doc, task, line_num, seen_ids)
            relocated = _apply_shortcut_tokens(task, line_num, doc)
            if relocated:
                task._source_line = None
            doc.raw_lines.append(raw)
            continue

        # Bullet-prefixed line without a (recognizable) checkbox at all —
        # e.g. "- Buy milk", "* [ ] Buy milk", "+[x]Buy milk". Parsed as a
        # task and flagged so the user knows it will be normalized to the
        # standard "- [ ] name" form on next save.
        m_lenient = RE_TASK_LENIENT.match(line_stripped)
        if m_lenient and m_lenient.group(3).strip():
            raw.line_type = "task"
            task = _parse_task_match(m_lenient, current_section, current_sub, line_num)
            doc.warnings.append(
                f"Line {line_num}: non-standard task format recognized and will be "
                f"normalized to '- [ ] ...' on next save: '{line_stripped}'"
            )
            _register_task(doc, task, line_num, seen_ids)
            relocated = _apply_shortcut_tokens(task, line_num, doc)
            if relocated:
                task._source_line = None
            doc.raw_lines.append(raw)
            continue

        # Everything else is preserved text
        raw.line_type = "text"
        doc.raw_lines.append(raw)

    return doc


def _register_task(doc: TaskDocument, task: Task, line_num: int, seen_ids: Dict[str, int]):
    """Append a parsed task to the document, tracking duplicate IDs."""
    if task.id:
        seen_ids[task.id] = seen_ids.get(task.id, 0) + 1
        if seen_ids[task.id] > 1:
            doc.warnings.append(
                f"Duplicate ID '{task.id}' at line {line_num} "
                f"(seen {seen_ids[task.id]} times)"
            )
    doc.tasks.append(task)


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

    # Normalize status — any character outside the four recognized markers
    # (space/empty, x, X, -) safely defaults to "not started" rather than
    # ever producing an invalid status like "[v]" or "[done]" (this path is
    # reached for RE_TASK_SUSPICIOUS_CHECKBOX matches, which is exactly the
    # case TODOs.md Issue 6 asks to flag rather than silently mis-render).
    if status_char in ("x", "X"):
        status_char = "x"
    elif status_char not in (" ", "-", "", None):
        status_char = " "
    elif not status_char:
        status_char = " "
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


def _has_strong_shortcut_signal(name: str) -> bool:
    """Decide whether a hand-written task name confidently uses quick-capture
    shortcut syntax (#tag, !pri, @due, ^start, /section, //sub), rather than
    just happening to contain a '#', '!', '@', or '/' character incidentally
    (e.g. "Fix bug #1234", "Email me@example.com", "Pay rent / utilities").

    Requires at least one @due or ^start token that actually resolves to a
    real date via the same shorthand grammar `tm add` uses — dates almost
    never appear in this exact form by coincidence in ordinary prose, so
    this is a safe, conservative anchor. Only once this anchor is present do
    we trust the other token types (#tag, !pri, /section, //sub) enough to
    rewrite the name.
    """
    from taskmd.quick_capture import _parse_date_token

    for m in _RE_SHORTCUT_DUE.finditer(name):
        if _parse_date_token(m.group(1)) is not None:
            return True
    for m in _RE_SHORTCUT_START.finditer(name):
        if _parse_date_token(m.group(1)) is not None:
            return True
    return False


def _apply_shortcut_tokens(task: Task, line_num: int, doc: "TaskDocument") -> bool:
    """If a hand-written task's name confidently uses quick-capture shortcut
    syntax, extract those tokens into proper fields (tags/pri/due/start) and
    relocate the task to the section/subsection the shortcut specifies, if
    any (TODOs.md Issue 6, part 2).

    Returns True if the task's section/sub was changed (i.e. it needs to be
    physically relocated to the right place in the file on next write,
    rather than rewritten in place).
    """
    if not _has_strong_shortcut_signal(task.name):
        return False

    from taskmd.quick_capture import parse_quick_capture

    result = parse_quick_capture(task.name)
    if not result.name:
        # Token extraction consumed the entire name — too risky to apply,
        # leave the original name untouched.
        return False

    original_section, original_sub = task.section, task.sub

    task.name = result.name
    if result.tags:
        task.tags = (task.tags or []) + [t for t in result.tags if t not in (task.tags or [])]
    if result.pri is not None and task.pri is None:
        task.pri = result.pri
    if result.due and not task.due:
        task.due = result.due
    if result.start and not task.start:
        task.start = result.start
    if result.rem and not task.rem:
        task.rem = result.rem

    relocated = False
    if result.section and result.section.strip() and result.section.strip() != original_section:
        task.section = result.section.strip()
        task.sub = (result.sub or "General").strip() if result.sub else "General"
        relocated = True
    elif result.sub and result.sub.strip() and result.sub.strip() != original_sub:
        task.sub = result.sub.strip()
        relocated = True

    doc.warnings.append(
        f"Line {line_num}: recognized inline shortcut syntax in task name "
        f"and converted it to structured fields"
        + (f" (moved to {task.section}/{task.sub})" if relocated else "")
    )
    return relocated

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
