"""
Quick Capture Syntax for TaskMD (Phase 7).

Parses a natural-language task string with inline tokens:
  #tag          → add tag
  !N or !       → priority (1–5; bare ! = 1)
  @YYYY-MM-DD   → due date
  @today        → due = today
  @tomorrow     → due = tomorrow
  @mon…@sun     → due = next matching weekday
  @+Nd          → due = today + N days
  ^YYYY-MM-DD   → start date  (same shorthands as @)
  /section      → section
  //subsection  → subsection
  [note text]   → rem (reminder/note)

Anything not matched by a token becomes the task name.

Examples
--------
  "Write report #work !3 @2026-04-25"
  "Buy milk #errand @tomorrow"
  "Review PR #dev !2 @+3d /Work //Docs"
  "Call dentist @mon [remember to bring insurance card]"

All tokens are case-insensitive for keywords (@today, etc.).
Unrecognised @/^ values are ignored with a warning.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional

# ─── Token regexes ────────────────────────────────────────────────────────────

# #tag — word chars, hyphen, digits
_RE_TAG = re.compile(r'#([\w\-]+)')

# !priority  — !1 … !5, or bare !
_RE_PRI = re.compile(r'!([1-5])?')

# @date  — many shorthand forms (see _parse_date_token), optionally suffixed
# with T-and-time for precise hour/minute (e.g. @tomorrowT14:30, @2026-06-25T09:00)
_RE_DUE = re.compile(r'@([\w+\-]+(?:T\d{2}:\d{2})?)')

# ^start-date (same shorthand + optional T-time suffix as @)
_RE_START = re.compile(r'\^([\w+\-]+(?:T\d{2}:\d{2})?)')

# //subsection (must come before /section)
_RE_SUB = re.compile(r'//([\w\s\-]+?)(?=\s|$|#|!|@|\^|/)')

# /section
_RE_SEC = re.compile(r'/([\w\s\-]+?)(?=\s|$|#|!|@|\^|/)')

# [reminder note]
_RE_REM = re.compile(r'\[([^\]]+)\]')

# ─── Weekday lookup ───────────────────────────────────────────────────────────

_WEEKDAYS = {
    "mon": 0, "monday": 0,
    "tue": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2,
    "thu": 3, "thursday": 3,
    "fri": 4, "friday": 4,
    "sat": 5, "saturday": 5,
    "sun": 6, "sunday": 6,
}


# ─── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class CaptureResult:
    name: str
    tags: List[str] = field(default_factory=list)
    pri: Optional[int] = None
    due: Optional[str] = None
    start: Optional[str] = None
    section: Optional[str] = None
    sub: Optional[str] = None
    rem: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


def _parse_date_token(token: str) -> Optional[str]:
    """
    Convert a date token string (without leading @ or ^) to YYYY-MM-DD,
    or to "YYYY-MM-DD HH:MM" if a precise time was attached.

    Supported formats:
      today, tomorrow, yesterday
      mon … sun  (next occurrence of weekday, ≥ tomorrow)
      next-mon … next-sun (same as above)
      +Nd        (today + N days)
      next-week (= +7d)
      2-weeks   (= +14d)  (3-weeks... also supported)
      YYYY-MM-DD (literal ISO date)
      YYYY-MM-DD HH:MM (literal datetime)

    Any of the above (including shorthands) may carry a "THH:MM" suffix to
    attach a precise time, e.g. "tomorrowT14:30", "monT09:00", "+3dT08:15"
    (TODOs.md Issue 5 — precise hour/minute due times).
    """
    # Split off an optional "THH:MM" time suffix before resolving the date part.
    time_suffix = ""
    m_time = re.fullmatch(r'(.+)T(\d{2}:\d{2})', token)
    if m_time:
        token = m_time.group(1)
        time_suffix = f" {m_time.group(2)}"

    today = date.today()
    token_lower = token.lower()

    if token_lower == "today":
        return today.isoformat() + time_suffix
    if token_lower == "tomorrow":
        return (today + timedelta(days=1)).isoformat() + time_suffix
    if token_lower == "yesterday":
        return (today - timedelta(days=1)).isoformat() + time_suffix

    # handle 'next-' prefix
    cleaned_token = token_lower.replace("next-", "")
    
    # weekday names
    if cleaned_token in _WEEKDAYS:
        target_wd = _WEEKDAYS[cleaned_token]
        days_ahead = (target_wd - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # always next occurrence, not today
        return (today + timedelta(days=days_ahead)).isoformat() + time_suffix

    if token_lower == "next-week":
        return (today + timedelta(days=7)).isoformat() + time_suffix
    
    # +Nd or -Nd  e.g. +3d, -5d
    m = re.fullmatch(r'([+-])?(\d+)d?', token_lower)
    if m:
        sign = -1 if m.group(1) == "-" else 1
        return (today + timedelta(days=sign * int(m.group(2)))).isoformat() + time_suffix
    
    # N-weeks
    m = re.fullmatch(r'(\d+)-weeks?', token_lower)
    if m:
        return (today + timedelta(days=int(m.group(1)) * 7)).isoformat() + time_suffix

    # ISO date literal or datetime
    m = re.fullmatch(r'(\d{4}-\d{2}-\d{2})(\s+\d{2}:\d{2})?', token)
    if m:
        return token + time_suffix  # Return exactly as matched (+ any T-time suffix)

    return None


# ─── Main parser ──────────────────────────────────────────────────────────────

def parse_quick_capture(text: str) -> CaptureResult:
    """
    Parse a quick-capture string and return a CaptureResult.

    Uses a scanner approach that processes the string to isolate tokens,
    giving precedence to tokens at the end of the string to avoid
    confusing them with paths or shell content at the start.
    """
    result = CaptureResult(name="")
    s = text.strip()

    # 1. Extract reminder note [text] first as it's the widest block
    m = _RE_REM.search(s)
    if m:
        result.rem = m.group(1).strip()
        s = _RE_REM.sub("", s, count=1).strip()

    # 2. Split into potential "words" but we must preserve spaces for the name
    # We will process tokens that appear at the end of the string one by one.
    
    words = s.split()
    if not words:
        if result.rem:
            return result
        result.warnings.append("Empty task input.")
        return result

    name_words = []
    
    # We use a simple state-based scanner that looks for tokens from right to left
    # But for ease of implementation, we can do multi-pass regex with word boundaries
    
    # Helper to remove a token safely if it exists at the end or is surrounded by spaces
    def extract_token(pattern, current_str):
        # We want to match exactly one of our tokens, but it must be a 'word'
        # pattern should have exactly one capture group for the value
        regex = re.compile(r'(?:^|\s)(' + pattern.pattern + r')(?=\s|$)')
        matches = list(regex.finditer(current_str))
        vals = []
        new_str = current_str
        for match in reversed(matches):
            vals.insert(0, match.group(1).strip())
            new_str = new_str[:match.start()] + (" " if match.start() > 0 and match.end() < len(new_str) else "") + new_str[match.end():]
        return vals, new_str.strip()

    # Subsections first (longest tokens)
    subs, s = extract_token(re.compile(r'//[\w\s\-]+?'), s)
    if subs: result.sub = subs[-1].lstrip('/')

    # Sections 
    secs, s = extract_token(re.compile(r'/[\w\s\-]+?'), s)
    if secs: result.section = secs[-1].lstrip('/')

    # Start dates
    starts, s = extract_token(re.compile(r'\^[\w+\-:]+'), s)
    for start in starts:
        parsed = _parse_date_token(start[1:])
        if parsed: result.start = parsed
        else: result.warnings.append(f"Unrecognised start date: {start}")

    # Due dates
    dues, s = extract_token(re.compile(r'@[\w+\-:]+'), s)
    for due in dues:
        parsed = _parse_date_token(due[1:])
        if parsed: result.due = parsed
        else: result.warnings.append(f"Unrecognised due date: {due}")

    # Priority
    pris, s = extract_token(re.compile(r'![1-5]?'), s)
    if pris:
        p = pris[-1][1:] # Remove !
        result.pri = int(p) if p else 1

    # Tags (can have multiple)
    tags, s = extract_token(re.compile(r'#[\w\-]+'), s)
    if tags:
        result.tags.extend([t[1:].lower() for t in tags])

    result.name = re.sub(r'\s{2,}', ' ', s).strip()
    if not result.name:
        result.warnings.append("Task name is empty after parsing tokens.")

    return result
