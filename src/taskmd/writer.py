"""
Markdown writer for TaskMD Lite.

Supports two modes:
  1. Low-diff writeback (default): When raw_lines are available from parsing,
     preserves section order, blank lines, and non-task text. Only regenerates
     task lines and updates header metadata.
  2. Full regeneration: For new documents or when structure changes require it.

Writes all schema v2 metadata fields into HTML comments.
"""
from taskmd.models import Task, TaskDocument


def write_markdown(doc: TaskDocument) -> str:
    """Write a TaskDocument back to Markdown.

    Uses low-diff mode if raw_lines are available, otherwise full regeneration.
    """
    if doc.raw_lines:
        return _write_low_diff(doc)
    return _write_full(doc)


# ─── Task Line Formatting ────────────────────────────────────────────────────

def _format_task_line(task: Task) -> str:
    """Format a single task as a Markdown line with hidden metadata."""
    meta = _build_metadata_pairs(task)
    meta_str = f" <!-- {', '.join(meta)} -->" if meta else ""
    status = task.status if task.status in ("[ ]", "[-]", "[x]") else "[ ]"
    return f"- {status} {task.name}{meta_str}"


def _build_metadata_pairs(task: Task) -> list:
    """Build the list of key:value metadata strings for a task."""
    meta = []
    if task.id:
        meta.append(f"id:{task.id}")
    if task.due:
        meta.append(f"due:{task.due}")
    if task.start:
        meta.append(f"start:{task.start}")
    if task.pri is not None:
        meta.append(f"pri:{task.pri}")
    if task.tags:
        meta.append(f"tags:{','.join(task.tags)}")
    if task.rem:
        clean_rem = task.rem.replace('"', '')
        meta.append(f'rem:"{clean_rem}"')
    if task.done_ts:
        meta.append(f"done:{task.done_ts}")
    if task.created:
        meta.append(f"created:{task.created}")
    if task.updated:
        meta.append(f"updated:{task.updated}")
    if task.weight is not None:
        meta.append(f"weight:{task.weight}")
    if task.course:
        meta.append(f"course:{task.course}")
    if task.recur:
        meta.append(f"recur:{task.recur}")
    if task.est:
        meta.append(f"est:{task.est}")
    if task.loc:
        meta.append(f"loc:{task.loc}")
    return meta


# ─── Low-Diff Writeback ──────────────────────────────────────────────────────

def _write_low_diff(doc: TaskDocument) -> str:
    """Low-diff writeback: preserve original structure, only update changed lines.

    Strategy:
      - Rebuild header metadata lines in-place
      - Replace task lines with their current state
      - Preserve all other lines (sections, subsections, text, blanks) as-is
      - Append any new tasks that have no source line
    """
    # Build a map from source_line -> task for quick lookup
    task_by_line = {}
    new_tasks = []
    for task in doc.tasks:
        if task._source_line is not None:
            task_by_line[task._source_line] = task
        else:
            new_tasks.append(task)

    output_lines = []

    for raw in doc.raw_lines:
        if raw.line_type == "header_meta":
            # Regenerate header metadata with current values
            line = _regenerate_header_meta(raw.content, doc)
            output_lines.append(line)

        elif raw.line_type == "task":
            # Check if this task still exists
            task = task_by_line.get(raw.line_number)
            if task is not None:
                output_lines.append(_format_task_line(task))
            # If task was removed, skip the line (don't output it)

        else:
            # Preserve sections, subsections, text, blanks as-is
            output_lines.append(raw.content)

    # Insert new tasks into their proper sections
    if new_tasks:
        # Group new tasks by section/sub
        groups = {}
        for task in new_tasks:
            key = (task.section, task.sub)
            groups.setdefault(key, []).append(task)

        for (section, sub), tasks in groups.items():
            task_lines = [_format_task_line(t) for t in tasks]

            # Try to find the insertion point: right after the last task
            # in the matching section/sub
            insert_idx = _find_insertion_point(output_lines, section, sub)

            if insert_idx is not None:
                for i, tl in enumerate(task_lines):
                    output_lines.insert(insert_idx + i, tl)
            else:
                # Section/sub doesn't exist yet
                section_exists = _section_exists_in_output(output_lines, section)
                if section_exists:
                    # Section exists but subsection doesn't — find end of section
                    end_of_section = _find_section_end(output_lines, section)
                    insert_at = end_of_section
                    output_lines.insert(insert_at, f"## {sub}")
                    insert_at += 1
                    for tl in task_lines:
                        output_lines.insert(insert_at, tl)
                        insert_at += 1
                else:
                    # Neither exists — append at end
                    output_lines.append("")
                    output_lines.append(f"# {section}")
                    output_lines.append(f"## {sub}")
                    output_lines.extend(task_lines)

    # Clean trailing whitespace
    while output_lines and not output_lines[-1].strip():
        output_lines.pop()

    return "\n".join(output_lines) + "\n"


def _regenerate_header_meta(original_line: str, doc: TaskDocument) -> str:
    """Regenerate a header metadata line with current doc values."""
    import re
    m = re.match(r'^(<!--\s*taskmd(?:-lite)?:)([a-zA-Z0-9_]+)=(.+?)(\s*-->)$', original_line.strip())
    if not m:
        return original_line

    prefix = m.group(1)
    key = m.group(2)
    suffix = m.group(4)

    val_map = {
        "version": doc.version,
        "timezone": doc.timezone,
        "last_run": doc.last_run,
        "profile": doc.profile,
    }

    if key in val_map:
        return f"{prefix}{key}={val_map[key]}{suffix}"
    return original_line


def _section_exists_in_output(lines: list, section: str) -> bool:
    """Check if a section header already exists in output."""
    import re
    for line in lines:
        m = re.match(r'^#\s+(.+)$', line.strip())
        if m and m.group(1).strip() == section:
            return True
    return False


def _subsection_exists_in_output(lines: list, sub: str, section: str) -> bool:
    """Check if a subsection header exists under the given section."""
    import re
    in_section = False
    for line in lines:
        m_sec = re.match(r'^#\s+(.+)$', line.strip())
        if m_sec:
            in_section = (m_sec.group(1).strip() == section)
            continue
        if in_section:
            m_sub = re.match(r'^##\s+(.+)$', line.strip())
            if m_sub and m_sub.group(1).strip() == sub:
                return True
    return False


def _find_section_end(lines: list, section: str) -> int:
    """Find the index right before the next section header after the given section.

    Returns the insertion index (0-based) where content can be added at the
    end of the specified section.
    """
    import re
    found_section = False
    last_content_idx = len(lines)

    for i, line in enumerate(lines):
        stripped = line.strip()
        m_sec = re.match(r'^#\s+(.+)$', stripped)
        if m_sec and not re.match(r'^##', stripped):
            if found_section:
                # We've reached the NEXT section — insert before it
                # Skip back past any trailing blank lines
                insert_at = i
                while insert_at > 0 and not lines[insert_at - 1].strip():
                    insert_at -= 1
                return insert_at
            if m_sec.group(1).strip() == section:
                found_section = True

    # Section is the last one — return end of file
    return len(lines)


def _find_insertion_point(lines: list, section: str, sub: str) -> int:
    """Find the line index where new tasks should be inserted for a given section/sub.

    Returns the index (0-based) after the last task line in the matching
    section/subsection, or None if the section/sub doesn't exist.
    """
    import re

    in_section = False
    in_sub = False
    last_task_idx = None
    sub_header_idx = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for section header
        m_sec = re.match(r'^#\s+(.+)$', stripped)
        if m_sec and not re.match(r'^##', stripped):
            if m_sec.group(1).strip() == section:
                in_section = True
                in_sub = (sub == "General")  # If sub is General and no ## exists
                if in_sub:
                    sub_header_idx = i
            else:
                if in_section:
                    # We've left the target section
                    break
                in_section = False
                in_sub = False
            continue

        # Check for subsection header
        m_sub = re.match(r'^##\s+(.+)$', stripped)
        if m_sub:
            if in_section and m_sub.group(1).strip() == sub:
                in_sub = True
                sub_header_idx = i
            elif in_section:
                if in_sub:
                    # We've left the target subsection
                    break
                in_sub = False
            continue

        # Track task lines within our target section/sub
        if in_section and in_sub:
            if re.match(r'^-\s*\[', stripped):
                last_task_idx = i + 1  # Insert after this line

    if last_task_idx is not None:
        return last_task_idx
    if sub_header_idx is not None:
        return sub_header_idx + 1  # Insert right after the subsection header

    return None


# ─── Full Regeneration ────────────────────────────────────────────────────────

def _write_full(doc: TaskDocument) -> str:
    """Full file regeneration for new documents."""
    lines = []

    # Header metadata
    lines.append(f"<!-- taskmd:version={doc.version} -->")
    lines.append(f"<!-- taskmd:timezone={doc.timezone} -->")
    lines.append(f"<!-- taskmd:last_run={doc.last_run} -->")
    lines.append("")

    # Group tasks by section -> subsection (preserve insertion order)
    hierarchy = {}
    for task in doc.tasks:
        sec = task.section or "Uncategorized"
        sub = task.sub or "General"
        if sec not in hierarchy:
            hierarchy[sec] = {}
        if sub not in hierarchy[sec]:
            hierarchy[sec][sub] = []
        hierarchy[sec][sub].append(task)

    for sec, subs in hierarchy.items():
        lines.append(f"# {sec}")
        for sub, tasks in subs.items():
            lines.append(f"## {sub}")
            for task in tasks:
                lines.append(_format_task_line(task))
        lines.append("")

    # Trim trailing blanks
    while lines and not lines[-1].strip():
        lines.pop()

    return "\n".join(lines) + "\n"
