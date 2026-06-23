"""
Source Exporter for TaskMD.

Exports the *raw markdown source file itself* to a chosen location — as-is
(.md) or converted to a simplified plain-text format (.txt) — rather than
a derived report. This covers TODOs.md Issue 7:
  "用户应当也可以导出当前schedule的md源文件到指定位置，且可以将其转换为txt格式"
  (the user should also be able to export the current schedule's source .md
  file to a chosen location, and optionally convert it to .txt format).
"""
import re
from pathlib import Path
from typing import Optional


# Matches a hidden-metadata HTML comment trailing a task line, e.g.
# "<!-- id:t_01, due:2026-06-25, pri:3 -->"
_RE_META_COMMENT = re.compile(r"\s*<!--.*?-->\s*$")

# Matches the checkbox marker at the start of a task line: "- [ ]", "- [x]", "- [-]"
_RE_CHECKBOX = re.compile(r"^(\s*)-\s*\[([ xX\-])\]\s*")

# Matches a config/system HTML comment line on its own, e.g.
# "<!-- taskmd:version=2 -->"
_RE_STANDALONE_COMMENT = re.compile(r"^\s*<!--.*?-->\s*$")


def markdown_to_plain_text(md_content: str) -> str:
    """Convert TaskMD markdown source into a simple, readable plain-text outline.

    Rules:
      - Standalone config comments (<!-- taskmd:... -->) are dropped.
      - "# Section" headers become "SECTION" (uppercase, no markdown marker).
      - "## Subsection" headers become "  Subsection:" (indented).
      - Task lines keep their status as a bracketed tag ([DONE]/[IN PROGRESS]/
        [TODO]) instead of a checkbox, and drop the trailing hidden-metadata
        HTML comment block (since that's an internal storage detail, not
        something a plain-text reader needs).
      - Blank lines are preserved for readability.
    """
    status_label = {"x": "[DONE]", "X": "[DONE]", "-": "[IN PROGRESS]", " ": "[TODO]"}
    out_lines = []

    for raw_line in md_content.splitlines():
        line = raw_line.rstrip()

        if _RE_STANDALONE_COMMENT.match(line):
            continue  # drop internal config comments entirely

        if line.startswith("## "):
            out_lines.append(f"  {line[3:].strip()}:")
            continue

        if line.startswith("# "):
            out_lines.append(line[2:].strip().upper())
            continue

        m = _RE_CHECKBOX.match(line)
        if m:
            indent, mark = m.groups()
            rest = line[m.end():]
            rest = _RE_META_COMMENT.sub("", rest).strip()
            out_lines.append(f"{indent}  {status_label.get(mark, '[TODO]')} {rest}")
            continue

        out_lines.append(line)

    # Collapse 3+ consecutive blank lines down to 1 for readability
    text = "\n".join(out_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def export_source(
    source_path: Path,
    output_path: Path,
    as_txt: bool = False,
) -> str:
    """Export the raw task markdown source file to a chosen location.

    Args:
        source_path: Path to the live tasks.md (or .txt) file to export from.
        output_path: Destination path to write to.
        as_txt: If True, convert markdown syntax to a simplified plain-text
            outline (see `markdown_to_plain_text`). If False, copy the
            source content verbatim (still useful for picking a custom
            filename/location distinct from the live working file).

    Returns:
        The content that was written (also written to output_path).
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source task file not found: {source_path}")

    content = source_path.read_text(encoding="utf-8")
    if as_txt:
        content = markdown_to_plain_text(content)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return content
