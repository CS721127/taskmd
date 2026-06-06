"""
PDF Exporter for TaskMD (Phase 8).

Generates a formatted PDF report using the `fpdf2` library (FPDF2 >= 2.7).

Install:  pip install 'taskmd[export]'   (fpdf2 is included)

Supports:
  tm export pdf                         → full task report
  tm export pdf --month 2026-04         → tasks due / completed in that month
  tm export pdf --output report.pdf     → custom output path
  tm export pdf --theme dark            → dark background variant

PDF structure:
  Page 1   – Cover: title, date, stats summary
  Page N…  – Section → Subsection → Task rows, with heatmap colour bands
             Plus a progress bar per section
"""
from __future__ import annotations

import os
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

from taskmd.models import Task
from taskmd.ui.heatmap import get_urgency_level, URGENCY_OVERDUE, URGENCY_DUE_TODAY, URGENCY_DUE_SOON


# ─── Optional dependency check ───────────────────────────────────────────────

def _check_fpdf():
    try:
        from fpdf import FPDF
        return FPDF
    except ImportError:
        raise ImportError(
            "The 'fpdf2' package is required for PDF export.\n"
            "Install it with: pip install 'taskmd[export]'\n"
            "or: pip install fpdf2>=2.7"
        )


# ─── Colour palettes ─────────────────────────────────────────────────────────

_THEME_LIGHT = {
    "bg":          (255, 255, 255),
    "cover_bg":    (74, 111, 165),
    "cover_text":  (255, 255, 255),
    "section_bg":  (74, 111, 165),
    "section_fg":  (255, 255, 255),
    "sub_bg":      (220, 228, 240),
    "sub_fg":      (40, 60, 100),
    "text":        (30, 30, 30),
    "done":        (100, 180, 100),
    "overdue":     (220, 50, 50),
    "due_today":   (230, 150, 30),
    "due_soon":    (200, 180, 30),
    "normal":      (80, 80, 80),
    "bar_done":    (74, 180, 74),
    "bar_empty":   (200, 210, 220),
    "id_color":    (120, 140, 200),
    "tag_bg":      (230, 235, 255),
    "tag_fg":      (60, 80, 160),
}

_THEME_DARK = {
    "bg":          (26, 26, 46),
    "cover_bg":    (15, 52, 96),
    "cover_text":  (234, 234, 234),
    "section_bg":  (15, 52, 96),
    "section_fg":  (234, 234, 234),
    "sub_bg":      (22, 33, 62),
    "sub_fg":      (180, 200, 234),
    "text":        (220, 220, 220),
    "done":        (100, 200, 100),
    "overdue":     (240, 80, 80),
    "due_today":   (245, 166, 35),
    "due_soon":    (220, 200, 40),
    "normal":      (180, 180, 180),
    "bar_done":    (100, 200, 100),
    "bar_empty":   (50, 70, 90),
    "id_color":    (120, 160, 230),
    "tag_bg":      (30, 50, 90),
    "tag_fg":      (150, 190, 255),
}


def _theme(name: str) -> dict:
    return _THEME_DARK if name == "dark" else _THEME_LIGHT


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _task_color(task: Task, palette: dict) -> tuple:
    level = get_urgency_level(task)
    if task.status == "[x]":
        return palette["done"]
    if level == URGENCY_OVERDUE:
        return palette["overdue"]
    if level == URGENCY_DUE_TODAY:
        return palette["due_today"]
    if level == URGENCY_DUE_SOON:
        return palette["due_soon"]
    return palette["text"]


def _status_sym(task: Task) -> str:
    return {"[x]": "[x]", "[-]": "[-]", "[ ]": "[ ]"}.get(task.status, "[ ]")


def _filter_by_month(tasks: List[Task], month: str) -> List[Task]:
    """Keep tasks relevant to YYYY-MM: due that month OR completed that month."""
    prefix = month  # e.g. "2026-04"
    result = []
    for t in tasks:
        if t.due and t.due.startswith(prefix):
            result.append(t)
        elif t.done_ts and t.done_ts[:7] == prefix:
            result.append(t)
    return result


def _group_by_section(tasks):
    groups = {}
    for t in tasks:
        sec = t.section or "Uncategorized"
        sub = t.sub or "General"
        groups.setdefault(sec, {}).setdefault(sub, []).append(t)
    return groups


def _section_stats(tasks):
    total = len(tasks)
    done  = sum(1 for t in tasks if t.status == "[x]")
    return done, total


# ─── PDF Builder ─────────────────────────────────────────────────────────────

class _TaskPDF:
    """Thin wrapper around FPDF to build the task report."""

    PAGE_W = 210   # A4 mm
    MARGIN = 14

    def __init__(self, FPDF, palette: dict):
        self.p = palette
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=20)
        self.pdf.set_margins(self.MARGIN, self.MARGIN, self.MARGIN)

    def _set_bg(self):
        r, g, b = self.p["bg"]
        self.pdf.set_fill_color(r, g, b)
        self.pdf.rect(0, 0, self.PAGE_W, 297, "F")

    def _rgb(self, key: str):
        return self.p[key]

    def cover(self, stats: dict, title: str, subtitle: str):
        self.pdf.add_page()
        self._set_bg()

        # Cover band
        r, g, b = self.p["cover_bg"]
        self.pdf.set_fill_color(r, g, b)
        self.pdf.rect(0, 0, self.PAGE_W, 80, "F")

        # Title
        self.pdf.set_xy(self.MARGIN, 20)
        r, g, b = self.p["cover_text"]
        self.pdf.set_text_color(r, g, b)
        self.pdf.set_font("Helvetica", "B", 28)
        self.pdf.cell(0, 12, title, ln=True)

        self.pdf.set_font("Helvetica", "", 13)
        self.pdf.cell(0, 8, subtitle, ln=True)

        # Stats grid
        self.pdf.set_xy(self.MARGIN, 90)
        boxes = [
            ("Total",      str(stats.get("total", 0)),          self.p["text"]),
            ("Done",       str(stats.get("done", 0)),           self.p["done"]),
            ("In Progress",str(stats.get("in_progress", 0)),    self.p["due_today"]),
            ("Overdue",    str(stats.get("overdue", 0)),        self.p["overdue"]),
            ("Rate",       stats.get("completion_rate", "0%"),  self.p["bar_done"]),
        ]
        cell_w = (self.PAGE_W - 2 * self.MARGIN) / len(boxes)
        for label, value, color in boxes:
            x = self.pdf.get_x()
            y = self.pdf.get_y()
            # box background
            r2, g2, b2 = self.p["sub_bg"]
            self.pdf.set_fill_color(r2, g2, b2)
            self.pdf.rect(x, y, cell_w - 3, 24, "F")
            # value
            r3, g3, b3 = color
            self.pdf.set_text_color(r3, g3, b3)
            self.pdf.set_xy(x + 3, y + 3)
            self.pdf.set_font("Helvetica", "B", 16)
            self.pdf.cell(cell_w - 6, 8, value, ln=False)
            # label
            r4, g4, b4 = self.p["normal"]
            self.pdf.set_text_color(r4, g4, b4)
            self.pdf.set_xy(x + 3, y + 13)
            self.pdf.set_font("Helvetica", "", 8)
            self.pdf.cell(cell_w - 6, 6, label, ln=False)
            self.pdf.set_xy(x + cell_w, y)

    def section_header(self, name: str, done: int, total: int):
        self.pdf.ln(4)
        r, g, b = self.p["section_bg"]
        self.pdf.set_fill_color(r, g, b)
        x = self.MARGIN
        y = self.pdf.get_y()
        w = self.PAGE_W - 2 * self.MARGIN
        self.pdf.rect(x, y, w, 9, "F")

        r2, g2, b2 = self.p["section_fg"]
        self.pdf.set_text_color(r2, g2, b2)
        self.pdf.set_font("Helvetica", "B", 11)
        self.pdf.set_xy(x + 3, y + 1)
        self.pdf.cell(w * 0.6, 7, name, ln=False)

        # Progress bar
        bar_x = x + w * 0.65
        bar_w = w * 0.32
        bar_h = 4
        bar_y = y + 2.5
        r3, g3, b3 = self.p["bar_empty"]
        self.pdf.set_fill_color(r3, g3, b3)
        self.pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")
        if total > 0:
            ratio = done / total
            r4, g4, b4 = self.p["bar_done"]
            self.pdf.set_fill_color(r4, g4, b4)
            self.pdf.rect(bar_x, bar_y, bar_w * ratio, bar_h, "F")
        self.pdf.set_font("Helvetica", "", 7)
        r5, g5, b5 = self.p["section_fg"]
        self.pdf.set_text_color(r5, g5, b5)
        pct = int(done / total * 100) if total else 0
        self.pdf.set_xy(bar_x + bar_w + 2, y + 1.5)
        self.pdf.cell(12, 6, f"{done}/{total} ({pct}%)", ln=False)
        self.pdf.ln(9)

    def subsection_header(self, name: str):
        self.pdf.ln(1)
        r, g, b = self.p["sub_bg"]
        self.pdf.set_fill_color(r, g, b)
        x = self.MARGIN + 3
        y = self.pdf.get_y()
        w = self.PAGE_W - 2 * self.MARGIN - 6
        self.pdf.rect(x, y, w, 6, "F")
        r2, g2, b2 = self.p["sub_fg"]
        self.pdf.set_text_color(r2, g2, b2)
        self.pdf.set_font("Helvetica", "BI", 9)
        self.pdf.set_xy(x + 2, y + 0.5)
        self.pdf.cell(w - 4, 5, f"  {name}", ln=False)
        self.pdf.ln(7)

    def task_row(self, task: Task):
        color = _task_color(task, self.p)
        r, g, b = color
        sym = _status_sym(task)
        pri = task.pri  # integer or None — rendered below as "*" repeats

        y = self.pdf.get_y()
        x = self.MARGIN + 6

        # Soft zebra stripe for done tasks
        if task.status == "[x]":
            rd, gd, bd = self.p["bar_empty"]
            self.pdf.set_fill_color(rd, gd, bd)
            self.pdf.rect(x - 1, y - 0.5, self.PAGE_W - 2 * self.MARGIN - 8, 6.5, "F")

        # Status symbol
        self.pdf.set_text_color(r, g, b)
        self.pdf.set_font("Helvetica", "B", 9)
        self.pdf.set_xy(x, y)
        self.pdf.cell(6, 6, sym, ln=False)

        # ID
        ri, gi, bi = self.p["id_color"]
        self.pdf.set_text_color(ri, gi, bi)
        self.pdf.set_font("Helvetica", "", 8)
        self.pdf.cell(16, 6, f"[{task.id or '?'}]", ln=False)

        # Priority
        if pri:
            self.pdf.set_text_color(*self.p["overdue"])
            self.pdf.set_font("Helvetica", "B", 8)
            self.pdf.cell(12, 6, "*" * task.pri if task.pri else "", ln=False)
        else:
            self.pdf.cell(12, 6, "", ln=False)

        # Name (strip any non-latin-1 chars for fpdf2 core font compatibility)
        self.pdf.set_text_color(r, g, b)
        self.pdf.set_font("Helvetica", "B" if task.status != "[x]" else "", 9)
        name = task.name
        name_safe = name.encode("latin-1", errors="replace").decode("latin-1")
        avail = self.PAGE_W - 2 * self.MARGIN - 6 - 6 - 16 - 12 - 28
        self.pdf.cell(avail, 6, name_safe[:60] + ("..." if len(name_safe) > 60 else ""), ln=False)

        # Due date
        if task.due:
            self.pdf.set_font("Helvetica", "", 7)
            self.pdf.set_text_color(r, g, b)
            self.pdf.cell(28, 6, task.due, ln=False)

        self.pdf.ln(6)

        # Tags / note line (ASCII-safe)
        if task.tags or task.rem:
            self.pdf.set_x(x + 34)
            self.pdf.set_font("Helvetica", "I", 7)
            r2, g2, b2 = self.p["tag_fg"]
            self.pdf.set_text_color(r2, g2, b2)
            detail = ""
            if task.tags:
                detail += " ".join(f"#{t}" for t in task.tags)
            if task.rem:
                rem_safe = task.rem.encode("latin-1", errors="replace").decode("latin-1")
                detail += f"  <- {rem_safe}"
            self.pdf.cell(0, 4, detail[:100], ln=True)

    def add_tasks_page(self, groups: dict):
        self.pdf.add_page()
        self._set_bg()

        for section_name, subs in groups.items():
            all_tasks = [t for sub_tasks in subs.values() for t in sub_tasks]
            done, total = _section_stats(all_tasks)
            self.section_header(section_name, done, total)

            for sub_name, sub_tasks in subs.items():
                self.subsection_header(sub_name)
                for task in sub_tasks:
                    self.task_row(task)
                self.pdf.ln(1)

    def add_calendar_page(self, tasks: List[Task], month_str: str):
        """Add a monthly calendar grid page."""
        import calendar
        try:
            yr, mo = map(int, month_str.split("-"))
        except ValueError:
            return

        self.pdf.add_page()
        self._set_bg()

        # Month Title
        self.pdf.set_xy(self.MARGIN, self.MARGIN)
        self.pdf.set_font("Helvetica", "B", 18)
        self.pdf.set_text_color(*self.p["section_bg"])
        month_name = calendar.month_name[mo]
        self.pdf.cell(0, 10, f"{month_name} {yr}", ln=True, align="C")
        self.pdf.ln(5)

        # Draw Grid
        cal = calendar.Calendar(firstweekday=6) # Sun start
        weeks = cal.monthdays2calendar(yr, mo)
        
        col_w = (self.PAGE_W - 2 * self.MARGIN) / 7
        row_h = 35 # Grid row height
        
        # Headers
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        self.pdf.set_font("Helvetica", "B", 9)
        self.pdf.set_fill_color(*self.p["sub_bg"])
        self.pdf.set_text_color(*self.p["sub_fg"])
        for d in days:
            self.pdf.cell(col_w, 8, d, border=1, ln=False, align="C", fill=True)
        self.pdf.ln(8)

        # Day cells
        # Map tasks to days
        day_tasks = {}
        for t in tasks:
            if t.due and t.due.startswith(month_str):
                try:
                    d = int(t.due[8:10])
                    day_tasks.setdefault(d, []).append(t)
                except ValueError:
                    pass

        for week in weeks:
            start_y = self.pdf.get_y()
            # Draw background boxes
            for day_val, wd in week:
                x = self.pdf.get_x()
                self.pdf.set_fill_color(*self.p["bg"])
                self.pdf.rect(x, start_y, col_w, row_h, "D")
                
                if day_val != 0:
                    # Day number
                    self.pdf.set_xy(x + 2, start_y + 2)
                    self.pdf.set_font("Helvetica", "B", 8)
                    self.pdf.set_text_color(*self.p["normal"])
                    self.pdf.cell(8, 4, str(day_val))
                    
                    # Task names inside cell
                    tsks = day_tasks.get(day_val, [])
                    self.pdf.set_xy(x + 2, start_y + 7)
                    self.pdf.set_font("Helvetica", "", 6)
                    for t in tsks[:5]: # Max 5 per cell
                        color = _task_color(t, self.p)
                        self.pdf.set_text_color(*color)
                        name_short = (t.name[:18] + "..") if len(t.name) > 18 else t.name
                        name_safe = name_short.encode("latin-1", errors="replace").decode("latin-1")
                        self.pdf.set_x(x + 2)
                        self.pdf.cell(col_w-4, 4, f"• {name_safe}", ln=True)
                    if len(tsks) > 5:
                        self.pdf.set_x(x + 2)
                        self.pdf.cell(col_w-4, 4, f"+ {len(tsks)-5} more", ln=True)

                self.pdf.set_xy(x + col_w, start_y)
            self.pdf.ln(row_h)

    def output(self, path: Path) -> bytes:
        data = self.pdf.output()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return data


# ─── Public API ──────────────────────────────────────────────────────────────

def export_pdf(
    tasks: List[Task],
    output_path: Optional[Path] = None,
    month: Optional[str] = None,
    theme: str = "light",
    only_pending: bool = False,
) -> bytes:
    """
    Export tasks to a formatted PDF report.

    Args:
        tasks:       All tasks to consider.
        output_path: Where to write the PDF. Defaults to tasks_report.pdf.
        month:       Filter to tasks relevant to YYYY-MM (due or completed) and use calendar view.
        theme:       "light" or "dark".
        only_pending: If True, exclude completed tasks.

    Returns:
        PDF bytes (also written to output_path).
    """
    FPDF = _check_fpdf()
    palette = _theme(theme)

    # ── Filtering ────────────────────────────────────────────────────────
    filtered = tasks
    if month:
        filtered = _filter_by_month(filtered, month)
    if only_pending:
        filtered = [t for t in filtered if t.status != "[x]"]

    # ── Stats ────────────────────────────────────────────────────────────
    total = len(filtered)
    done  = sum(1 for t in filtered if t.status == "[x]")
    in_p  = sum(1 for t in filtered if t.status == "[-]")
    today = date.today().isoformat()
    overdue = sum(
        1 for t in filtered
        if t.due and t.due < today and t.status != "[x]"
    )
    rate = f"{done / total * 100:.1f}%" if total else "0%"
    stats = {
        "total": total, "done": done, "in_progress": in_p,
        "overdue": overdue, "completion_rate": rate,
    }

    # ── Title / subtitle ─────────────────────────────────────────────────
    title = "Monthly Calendar" if month else "TaskMD Report"
    if month:
        subtitle = f"Month: {month}  ·  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    else:
        subtitle = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    # ── Build PDF ────────────────────────────────────────────────────────
    builder = _TaskPDF(FPDF, palette)
    builder.cover(stats, title, subtitle)

    if month:
        builder.add_calendar_page(filtered, month)
        # Also add list view of the same tasks for detail
        builder.add_tasks_page(_group_by_section(filtered))
    else:
        groups = _group_by_section(filtered)
        if groups:
            builder.add_tasks_page(groups)

    # ── Output ───────────────────────────────────────────────────────────
    if output_path is None:
        output_path = Path("tasks_report.pdf")
    output_path = Path(output_path)
    return builder.output(output_path)
