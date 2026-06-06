"""
Image Exporter for TaskMD (Phase 8).

Generates a static SVG (or PNG via cairosvg) task board snapshot.
No browser required; pure Python output.

SVG is always available (no extra deps).
PNG conversion requires:  pip install 'taskmd[export]'  (cairosvg)

Features:
  - Kanban-style 3-column layout  (Todo | In Progress | Done)
  - Heatmap colour bands on cards (overdue → red, due-soon → yellow, …)
  - Section/tag labels on each card
  - Overall stats header bar
  - Light and dark themes
  - Auto-height based on task count

Usage:
  tm export svg [--output board.svg] [--theme dark]
  tm export png [--output board.png] [--theme dark]
"""
from __future__ import annotations

import html as html_escape_module
import textwrap
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from taskmd.models import Task
from taskmd.ui.heatmap import (
    get_urgency_level,
    URGENCY_OVERDUE,
    URGENCY_DUE_TODAY,
    URGENCY_DUE_SOON,
    URGENCY_DUE_UPCOMING,
    URGENCY_IN_ATTENTION,
)


# ─── Themes ──────────────────────────────────────────────────────────────────

_LIGHT = {
    "page_bg":      "#f0f2f5",
    "header_bg":    "#4a6fa5",
    "header_text":  "#ffffff",
    "col_bg":       "#e8ecf0",
    "col_title":    "#2c3e6a",
    "card_bg":      "#ffffff",
    "card_border":  "#d0d4da",
    "card_text":    "#1a1a2e",
    "card_id":      "#6b82c8",
    "card_meta":    "#888888",
    "tag_bg":       "#dde3f0",
    "tag_text":     "#4a6fa5",
    "accent_overdue":   "#e53935",
    "accent_today":     "#f5a623",
    "accent_soon":      "#fdd835",
    "accent_upcoming":  "#4a9eff",
    "accent_attention": "#00bcd4",
    "accent_normal":    "#aaaaaa",
    "done_text":    "#aaaaaa",
    "pri_color":    "#e53935",
}

_DARK = {
    "page_bg":      "#1a1a2e",
    "header_bg":    "#0f3460",
    "header_text":  "#eaeaea",
    "col_bg":       "#16213e",
    "col_title":    "#90b4ff",
    "card_bg":      "#0f2040",
    "card_border":  "#2a3a5a",
    "card_text":    "#e0e0e0",
    "card_id":      "#7899e0",
    "card_meta":    "#778899",
    "tag_bg":       "#0f3460",
    "tag_text":     "#90b4ff",
    "accent_overdue":   "#ff5252",
    "accent_today":     "#ffb74d",
    "accent_soon":      "#fff176",
    "accent_upcoming":  "#64b5f6",
    "accent_attention": "#4dd0e1",
    "accent_normal":    "#778899",
    "done_text":    "#556677",
    "pri_color":    "#ff5252",
}


def _palette(theme: str) -> dict:
    return _DARK if theme == "dark" else _LIGHT


def _urgency_accent(task: Task, pal: dict) -> str:
    level = get_urgency_level(task)
    return {
        URGENCY_OVERDUE:    pal["accent_overdue"],
        URGENCY_DUE_TODAY:  pal["accent_today"],
        URGENCY_DUE_SOON:   pal["accent_soon"],
        URGENCY_DUE_UPCOMING: pal["accent_upcoming"],
        URGENCY_IN_ATTENTION: pal["accent_attention"],
    }.get(level, pal["accent_normal"])


def _e(s: str) -> str:
    """XML-escape a string."""
    return html_escape_module.escape(str(s))


# ─── SVG Layout constants ─────────────────────────────────────────────────────

HEADER_H = 70
COL_GAP   = 16
COL_PAD   = 12
CARD_H    = 70    # approximate per card
CARD_GAP  = 10
COL_TITLE_H = 38


def _build_svg(tasks: List[Task], theme: str = "light") -> str:
    pal = _palette(theme)

    todo       = [t for t in tasks if t.status == "[ ]"]
    in_progress = [t for t in tasks if t.status == "[-]"]
    done       = [t for t in tasks if t.status == "[x]"]
    cols       = [("☐ Todo", todo), ("⟳ In Progress", in_progress), ("✓ Done", done)]

    max_cards  = max(len(todo), len(in_progress), len(done), 1)
    total_h    = HEADER_H + COL_TITLE_H + max_cards * (CARD_H + CARD_GAP) + COL_PAD * 2 + 20
    total_w    = 960
    col_w      = (total_w - 4 * COL_GAP) // 3

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(tasks)
    done_count = len(done)
    rate = f"{done_count / total * 100:.0f}%" if total else "0%"

    lines: List[str] = []

    # SVG root
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" '
        f'font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">'
    )

    # Background
    lines.append(f'<rect width="{total_w}" height="{total_h}" fill="{pal["page_bg"]}"/>')

    # Header bar
    lines.append(
        f'<rect x="0" y="0" width="{total_w}" height="{HEADER_H}" fill="{pal["header_bg"]}"/>'
    )
    lines.append(
        f'<text x="20" y="34" fill="{pal["header_text"]}" font-size="22" font-weight="bold">'
        f'📋 TaskMD Board</text>'
    )
    lines.append(
        f'<text x="20" y="56" fill="{pal["header_text"]}" font-size="12" opacity="0.8">'
        f'{_e(now)}  ·  Total: {total}  ·  Done: {done_count}  ·  Rate: {rate}</text>'
    )

    # Columns
    for col_idx, (col_label, col_tasks) in enumerate(cols):
        cx = COL_GAP + col_idx * (col_w + COL_GAP)
        cy = HEADER_H + 12

        # Column background
        col_h = total_h - HEADER_H - 20
        lines.append(
            f'<rect x="{cx}" y="{cy}" width="{col_w}" height="{col_h}" '
            f'rx="10" fill="{pal["col_bg"]}"/>'
        )

        # Column title
        lines.append(
            f'<text x="{cx + COL_PAD}" y="{cy + 24}" fill="{pal["col_title"]}" '
            f'font-size="14" font-weight="bold">{_e(col_label)} '
            f'<tspan font-size="11" opacity="0.7">({len(col_tasks)})</tspan></text>'
        )

        # Cards
        for card_idx, task in enumerate(col_tasks):
            card_x = cx + COL_PAD
            card_y = cy + COL_TITLE_H + card_idx * (CARD_H + CARD_GAP)
            card_w = col_w - COL_PAD * 2
            accent = _urgency_accent(task, pal)
            text_col = pal["done_text"] if task.status == "[x]" else pal["card_text"]

            # Card shadow (subtle)
            lines.append(
                f'<rect x="{card_x + 2}" y="{card_y + 2}" width="{card_w}" height="{CARD_H}" '
                f'rx="6" fill="#00000018"/>'
            )
            # Card body
            lines.append(
                f'<rect x="{card_x}" y="{card_y}" width="{card_w}" height="{CARD_H}" '
                f'rx="6" fill="{pal["card_bg"]}" stroke="{pal["card_border"]}" stroke-width="1"/>'
            )
            # Urgency left stripe
            lines.append(
                f'<rect x="{card_x}" y="{card_y}" width="4" height="{CARD_H}" '
                f'rx="3" fill="{accent}"/>'
            )

            # ID badge
            id_text = task.id[2:] if (task.id and task.id.startswith("t_")) else (task.id or "?")
            lines.append(
                f'<text x="{card_x + 12}" y="{card_y + 16}" '
                f'fill="{pal["card_id"]}" font-size="10" font-family="monospace">'
                f'[{_e(id_text)}]</text>'
            )

            # Priority stars
            if task.pri:
                stars = "★" * task.pri
                lines.append(
                    f'<text x="{card_x + card_w - 8}" y="{card_y + 16}" '
                    f'fill="{pal["pri_color"]}" font-size="10" text-anchor="end">'
                    f'{_e(stars)}</text>'
                )

            # Task name (truncate + wrap at ~38 chars)
            name = task.name[:40] + ("…" if len(task.name) > 40 else "")
            name_style = "text-decoration:line-through;opacity:0.5" if task.status == "[x]" else ""
            lines.append(
                f'<text x="{card_x + 12}" y="{card_y + 32}" '
                f'fill="{text_col}" font-size="11" font-weight="600" '
                f'style="{name_style}">{_e(name)}</text>'
            )

            # Due date
            meta_y = card_y + 46
            if task.due:
                lines.append(
                    f'<text x="{card_x + 12}" y="{meta_y}" '
                    f'fill="{accent}" font-size="9">📅 {_e(task.due)}</text>'
                )

            # Tags
            tag_x = card_x + 12
            tag_y = card_y + 58
            if task.tags:
                for tag in task.tags[:3]:
                    tag_label = f"#{tag}"
                    tag_w = len(tag_label) * 6 + 8
                    lines.append(
                        f'<rect x="{tag_x}" y="{tag_y - 9}" width="{tag_w}" height="12" '
                        f'rx="4" fill="{pal["tag_bg"]}"/>'
                    )
                    lines.append(
                        f'<text x="{tag_x + 4}" y="{tag_y}" '
                        f'fill="{pal["tag_text"]}" font-size="8">{_e(tag_label)}</text>'
                    )
                    tag_x += tag_w + 4

    lines.append("</svg>")
    return "\n".join(lines)


# ─── Public API ──────────────────────────────────────────────────────────────

# ─── Public API ──────────────────────────────────────────────────────────────

def export_svg(
    tasks: List[Task],
    output_path: Optional[Path] = None,
    theme: str = "light",
) -> str:
    """
    Export tasks as a static SVG kanban board.

    Args:
        tasks:       Task list.
        output_path: Write to file if given (must end in .svg).
        theme:       "light" or "dark".

    Returns:
        SVG string (also written to file if output_path given).
    """
    svg = _build_svg(tasks, theme=theme)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(svg, encoding="utf-8")

    return svg


def export_png(
    tasks: List[Task],
    output_path: Optional[Path] = None,
    theme: str = "light",
    scale: float = 2.0,
    month: Optional[str] = None,
) -> bytes:
    """
    Export tasks as a PNG image.
    
    If 'month' is provided, it uses the Pillow-based calendar view.
    Otherwise, it uses the SVG kanban board and converts it to PNG via cairosvg.

    Args:
        tasks:       Task list.
        output_path: Write to file if given (must end in .png).
        theme:       "light" or "dark".
        scale:       DPI scale factor for SVG conversion.
        month:       If provided (YYYY-MM), generates a calendar image using Pillow.

    Returns:
        PNG bytes (also written to file if output_path given).
    """
    if month:
        return _export_png_calendar(tasks, month, output_path, theme)

    try:
        import cairosvg
    except ImportError:
        # Fallback to Pillow if cairosvg is missing?
        # For now, stick to the plan: if month is given, use Pillow. Else cairosvg.
        raise ImportError(
            "The 'cairosvg' package is required for PNG Kanban export.\n"
            "Install it with: pip install 'taskmd[export]'\n"
            "or use --month to get a calendar view via Pillow."
        )

    svg = _build_svg(tasks, theme=theme)
    png_bytes = cairosvg.svg2png(bytestring=svg.encode("utf-8"), scale=scale)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(png_bytes)

    return png_bytes


def _export_png_calendar(tasks: List[Task], month_str: str, output_path: Optional[Path], theme: str) -> bytes:
    """Render a monthly calendar as PNG using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise ImportError("The 'Pillow' package is required for calendar images. Install with: pip install Pillow")

    import calendar
    try:
        yr, mo = map(int, month_str.split("-"))
    except ValueError:
        raise ValueError(f"Invalid month format: {month_str}. Use YYYY-MM.")

    pal = _palette(theme)
    # Convert hex to RGB tuples
    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    # Simple palette map for Pillow
    p = {k: hex_to_rgb(v) for k, v in pal.items()}
    
    W, H = 1200, 1000
    img = Image.new("RGB", (W, H), p["page_bg"])
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to find a nice font, fallback to default
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 40)
        font_day = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 20)
        font_task = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 16)
    except:
        font_title = ImageFont.load_default()
        font_day = ImageFont.load_default()
        font_task = ImageFont.load_default()

    # Title
    month_name = calendar.month_name[mo]
    draw.text((W//2, 50), f"{month_name} {yr}", fill=p["header_bg"], font=font_title, anchor="mm")
    
    # Calendar Grid
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdays2calendar(yr, mo)
    
    margin = 50
    col_w = (W - 2 * margin) // 7
    row_h = (H - 150 - margin) // len(weeks)
    
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, d in enumerate(days):
        draw.text((margin + i * col_w + col_w//2, 110), d, fill=p["col_title"], font=font_day, anchor="mm")

    # Map tasks
    day_tasks = {}
    for t in tasks:
        if t.due and t.due.startswith(month_str):
            try:
                d = int(t.due[8:10])
                day_tasks.setdefault(d, []).append(t)
            except: pass

    for r, week in enumerate(weeks):
        for c, (day_val, wd) in enumerate(week):
            x = margin + c * col_w
            y = 130 + r * row_h
            
            # Cell border
            draw.rectangle([x, y, x + col_w, y + row_h], outline=p["card_border"], width=1)
            
            if day_val != 0:
                draw.text((x + 8, y + 8), str(day_val), fill=p["card_meta"], font=font_day)
                
                # Tasks
                tsks = day_tasks.get(day_val, [])
                for i, t in enumerate(tsks[:7]):
                    accent = hex_to_rgb(_urgency_accent(t, pal))
                    name = (t.name[:25] + "..") if len(t.name) > 25 else t.name
                    draw.text((x + 8, y + 40 + i * 22), f"• {name}", fill=accent, font=font_task)
                if len(tsks) > 7:
                    draw.text((x + 8, y + 40 + 7 * 22), f"+ {len(tsks)-7} more", fill=p["card_meta"], font=font_task)

    # Convert to bytes
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)
        
    return png_bytes
